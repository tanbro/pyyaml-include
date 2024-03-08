from itertools import chain
from os import PathLike
from pathlib import Path
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Sequence, Union
from urllib.parse import urlsplit, urlunsplit

import fsspec
import fsspec.core
import fsspec.spec
import yaml

if sys.version_info < (3, 12):
    from .types_backward import TYamlLoaderTypes
else:
    from .types import TYamlLoaderTypes


__all__ = ["YamlIncludeData"]


@dataclass
class YamlIncludeData:
    """A ``dataclass`` store YAML including statement"""

    urlpath: str
    """url/path of the YAML including statement
    """

    sequence_param: Sequence[Any] = field(default_factory=list)
    """sequence parameters of the YAML including statement.

    default: an empty list
    """

    mapping_param: Mapping[str, Any] = field(default_factory=dict)
    """mapping parameters of the YAML including statement

    default: an empty dictionary
    """

    _wildcards_re_pat = re.compile(
        r"^(.*)([\*\?\[\]]+)(.*)$"
    )  # We support "**", "?" and "[..]". We do not support "^" for pattern negation.

    @staticmethod
    def _load_open_file(file, loader_type, path, custom_loader):
        if custom_loader is None:
            return yaml.load(file, loader_type)
        return custom_loader(path, file, loader_type)

    def load(
        self,
        loader_type: TYamlLoaderTypes,
        fs: fsspec.AbstractFileSystem,
        base_dir: Union[str, PathLike, Callable[[], Union[str, PathLike]], None] = None,
        custom_loader: Optional[Callable] = None,
    ):
        """The method will be invoked once the PyYAML's Loader class call the constructor.
        It happens when meet an including tag(eg: ``"!inc"``).

        Args:

            loader_type: Type of current in-use PyYAML loader

            urlpath:
                urlpath can be either absolute (like `/usr/src/Python-1.5/*.yml`) or relative (like `../../Tools/*/*.yml`), and can contain shell-style wildcards.

                We support ``"**"``, ``"?"`` and ``"[..]"``. We do not support ``"^"`` for pattern negation.
                The ``maxdepth`` option is applied on the first ``"**"`` found in the path.

                Warning:
                    Using the ``"**"`` pattern in large directory trees or remote files may consume an inordinate amount of time.

            data:
                The data class of the including statement

        Returns:
            Data of included YAML file, pared to python object

        Danger:
            It's called by `PyYAML`, and it's **NOT advised to call it yourself**.

        Note:
            Additional positional or named parameters in YAML including express are passed to ``*args`` and ``**kwargs``.
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
        urlpath = self.urlpath
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
            if self._wildcards_re_pat.match(urlpath):
                # if wildcards in path, return a Sequence/List
                result = []
                with fsspec.open_files(urlpath, *self.sequence_param, **self.mapping_param) as ofs:
                    for of_ in ofs:
                        data = self._load_open_file(of_, loader_type, urlpath, custom_loader)
                        result.append(data)
                return result
            # else if no wildcard, returns a single object
            with fsspec.open(urlpath, *self.sequence_param, **self.mapping_param) as of_:
                assert not isinstance(of_, list)
                result = self._load_open_file(of_, loader_type, urlpath, custom_loader)
                return result

        # if no protocol / scheme in path, we shall use the `fs` object
        if self._wildcards_re_pat.match(urlpath):
            urlpath = Path(urlpath).as_posix()
            # if wildcard in path, returns a List
            glob_params = open_params = None
            if self.sequence_param:
                if len(self.sequence_param) > 1:
                    glob_params, open_params = self.sequence_param[:2]
                elif len(self.sequence_param) == 1:
                    glob_params = self.sequence_param[0]
            if self.mapping_param:
                glob_params = self.mapping_param.get("glob")
                open_params = self.mapping_param.get("open")

            if glob_params is None:
                glob_fn = lambda: fs.glob(urlpath)  # noqa: E731
            elif isinstance(glob_params, dict):
                # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
                if "maxdepth" in glob_params:
                    glob_params["maxdepth"] = int(glob_params["maxdepth"])
                glob_fn = lambda: fs.glob(urlpath, **glob_params)  # noqa: E731
            elif isinstance(glob_params, (list, set)):
                # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
                glob_params = list(glob_params)
                if glob_params:
                    glob_params[0] = int(glob_params[0])
                glob_fn = lambda: fs.glob(urlpath, *glob_params)  # noqa: E731
            else:
                # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
                maxdepth = int(glob_params)
                glob_fn = lambda: fs.glob(urlpath, maxdepth)  # noqa: E731

            if open_params is None:
                open_fn = lambda x: fs.open(x)  # noqa: E731
            elif isinstance(open_params, dict):
                open_fn = lambda x: fs.open(x, **open_params)  # noqa: E731
            elif isinstance(open_params, (list, set)):
                open_fn = lambda x: fs.open(x, *open_params)  # noqa: E731
            else:
                open_fn = lambda x: fs.open(x, open_params)  # noqa: E731

            result = []
            for file in glob_fn():
                with open_fn(file) as of_:
                    data = self._load_open_file(of_, loader_type, file, custom_loader)
                    result.append(data)
            return result

        # else if no wildcards, return a single object
        with fs.open(urlpath, *self.sequence_param, **self.mapping_param) as of_:
            result = self._load_open_file(of_, loader_type, urlpath, custom_loader)
            return result
