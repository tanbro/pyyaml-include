import re
import sys
from itertools import chain
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import fsspec
import yaml

if sys.version_info < (3, 12):
    from .yamltypes_backward import TYamlLoaderTypes
else:
    from .yamltypes import TYamlLoaderTypes

from .base_constructor import BaseYamlIncludeCtor
from .data import YamlIncludeData


def load(
    loader_type: TYamlLoaderTypes,
    constructor: BaseYamlIncludeCtor,
    data: YamlIncludeData,
) -> Any:
    """The method will be invoked once the PyYAML's Loader class call the constructor.
    It happens when meet an including tag(eg: ``"!inc"``).

    Args:
        loader_type: Type of current in-use PyYAML loader class
        constructor: include constructor to use
        data: The data class of the including statement

    Returns:
        Data of the actual included YAML file, return the python object by parsing the file's content

    Danger:
        It's called by `PyYAML`, and it's **NOT advised to call it yourself**.

    Note:
        Additional positional or named parameters in YAML including express are passed to ``*args`` and ``**kwargs`` in :attr:`YamlIncludeData.sequence_param` and :attr:`YamlIncludeData.mapping_param`.
        The class will pass them to :mod:`fsspec`'s :mod:`fsspec` File-system as implementation specific options.

        To use positional in YAML including express is discouraged.

        * If there is a protocol/scheme, and no wildcard defined in YAML including,
            ``*args`` and ``**kwargs`` will be passed to :func:`fsspec.open`.

            Example:

            The YAML

            .. code:: yaml

                key: !inc {urlpath: s3://my-bucket/my-file.yml.gz, compression: gzip}

            means::

                with fsspec.open("s3://my-bucket/my-file.yml.gz", compression="gzip") as f:
                    yaml.load(f, Loader)


        * If there is a protocol/scheme, and also wildcard defined in YAML including,
            :attr:`YamlIncludeData.sequence_param` and :attr:`YamlIncludeData.mapping_param` of ``data`` will be passed to :func:`fsspec.open_files` as ``*args`` and ``**kwargs``

            Example:

            The YAML

            .. code:: yaml

                key: !inc {urlpath: s3://my-bucket/*.yml.gz, compression: gzip}

            means::

                with fsspec.open_files("s3://my-bucket/*.yml.gz", compression="gzip") as files:
                    for file in files:
                        yaml.load(file, Loader)

        * If there is no protocol/scheme, and no wildcard defined in YAML including,
            :attr:`YamlIncludeData.sequence_param` and :attr:`YamlIncludeData.mapping_param` of ``data`` will be passed to :mod:`fsspec` file-system implementation's ``open`` function (derive from :meth:`fsspec.spec.AbstractFileSystem.open`) as ``*args`` and ``**kwargs``

        * If there is no protocol/scheme, and also wildcard defined in YAML including, the situation is complex:

            * If the including express is in a positional-parameter form:
                * If count of argument is one,
                    it will be passed to of :meth:`fsspec.spec.AbstractFileSystem.glob`'s  ``maxdepth`` argument;
                * If count of argument is more than one:
                    # First of them will be passed to :mod:`fsspec` file system implementation's ``glob`` method (derived from :meth:`fsspec.spec.AbstractFileSystem.glob`)
                    # Second of them will be passed to :mod:`fsspec` file system implementation's ``open`` method (derived from :meth:`fsspec.spec.AbstractFileSystem.open`)
                    # Others will be ignored

            * If the including express is in a named-parameter form, the class will:
                * Find a key named `glob`, then pass the corresponding data to :mod:`fsspec` file system implementation's ``glob`` method (derived from :meth:`fsspec.spec.AbstractFileSystem.glob`)
                * Find a key named `open`, then pass the corresponding data to :mod:`fsspec` file system implementation's ``open`` method (derived from :meth:`fsspec.spec.AbstractFileSystem.open`)

            Example:

                * The YAML

                    .. code:: yaml

                        key: !inc [foo/**/*.yml, 2]

                    means::

                        for file in fs.glob("foo/**/*.yml.gz", maxdepth=2):
                            with fs.open(file) as fp:
                                yaml.load(fp, Loader)

                * The YAML

                    .. code:: yaml

                        key: !inc {urlpath: foo/**/*.yml.gz, glob: {maxdepth: 2}, open: {compression: gzip}}

                    means::

                        for file in fs.glob("foo/**/*.yml.gz", maxdepth=2):
                            with fs.open(file, compression=gzip) as fp:
                                yaml.load(fp, Loader)
    """
    base_dir = constructor.base_dir
    urlpath = data.urlpath

    url_sr = urlsplit(urlpath)
    if base_dir is not None:
        if callable(base_dir):
            base_dir = Path(base_dir())
        else:
            base_dir = Path(base_dir)
        if url_sr.scheme:
            urlpath = urlunsplit(
                chain(
                    url_sr[:2],
                    (base_dir.joinpath(url_sr[2]).as_posix(),),
                    url_sr[3:],
                )
            )
        else:
            urlpath = base_dir.joinpath(urlpath).as_posix()

    # If protocol/scheme in path, we shall open it directly with fs's default open method
    if url_sr.scheme:
        if WILDCARDS_RE_PAT.match(urlpath):
            # if wildcards in path, return a Sequence/List
            result = []
            with fsspec.open_files(urlpath, *data.sequence_param, **data.mapping_param) as ofs:
                for of_ in ofs:
                    data = load_of(of_, loader_type, urlpath, constructor.custom_loader)
                    result.append(data)
            return result
        # else if no wildcard, returns a single object
        with fsspec.open(urlpath, *data.sequence_param, **data.mapping_param) as of_:
            assert not isinstance(of_, list)
            result = load_of(of_, loader_type, urlpath, constructor.custom_loader)
            return result

    # if no protocol / scheme in path, we shall use the `fs` object
    if WILDCARDS_RE_PAT.match(urlpath):
        urlpath = Path(urlpath).as_posix()
        # if wildcard in path, returns a List
        glob_params = open_params = None
        if data.sequence_param:
            if len(data.sequence_param) > 1:
                glob_params, open_params = data.sequence_param[:2]
            elif len(data.sequence_param) == 1:
                glob_params = data.sequence_param[0]
        if data.mapping_param:
            glob_params = data.mapping_param.get("glob")
            open_params = data.mapping_param.get("open")

        if glob_params is None:
            glob_fn = lambda: constructor.fs.glob(urlpath)  # noqa: E731
        elif isinstance(glob_params, dict):
            # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
            if "maxdepth" in glob_params:
                glob_params["maxdepth"] = int(glob_params["maxdepth"])
            glob_fn = lambda: constructor.fs.glob(urlpath, **glob_params)  # noqa: E731
        elif isinstance(glob_params, (list, set)):
            # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
            glob_params = list(glob_params)
            if glob_params:
                glob_params[0] = int(glob_params[0])
            glob_fn = lambda: constructor.fs.glob(urlpath, *glob_params)  # noqa: E731
        else:
            # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
            maxdepth = int(glob_params)
            glob_fn = lambda: constructor.fs.glob(urlpath, maxdepth)  # noqa: E731

        if open_params is None:
            open_fn = lambda x: constructor.fs.open(x)  # noqa: E731
        elif isinstance(open_params, dict):
            open_fn = lambda x: constructor.fs.open(x, **open_params)  # noqa: E731
        elif isinstance(open_params, (list, set)):
            open_fn = lambda x: constructor.fs.open(x, *open_params)  # noqa: E731
        else:
            open_fn = lambda x: constructor.fs.open(x, open_params)  # noqa: E731

        result = []
        for file in glob_fn():
            with open_fn(file) as of_:
                data = load_of(of_, loader_type, file, constructor.custom_loader)
                result.append(data)
        return result

    # else if no wildcards, return a single object
    with constructor.fs.open(urlpath, *data.sequence_param, **data.mapping_param) as of_:
        result = load_of(of_, loader_type, urlpath, constructor.custom_loader)
        return result


WILDCARDS_RE_PAT = re.compile(
    r"^(.*)([\*\?\[\]]+)(.*)$"
)  # We support "**", "?" and "[..]". We do not support "^" for pattern negation.


def load_of(file, loader_type, path, custom_loader):
    if custom_loader is None:
        return yaml.load(file, loader_type)
    return custom_loader(path, file, loader_type)
