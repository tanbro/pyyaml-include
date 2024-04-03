"""
Include other YAML files in YAML
"""

import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from itertools import chain
from os import PathLike
from pathlib import Path
from typing import Any, Optional, Union
from urllib.parse import urlsplit, urlunsplit

if sys.version_info >= (3, 9):
    from collections.abc import Callable, Generator
else:
    from typing import Callable, Generator

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

import fsspec
import yaml

from .data import Data

if sys.version_info >= (3, 12):  # pragma: no cover
    from ._yaml_types import TYamlLoaderTypes
else:  # pragma: no cover
    from ._yaml_types_backward import TYamlLoaderTypes

__all__ = ["Constructor"]

WILDCARDS_PATTERN = re.compile(
    r"^(.*)([\*\?\[\]]+)(.*)$"
)  # We support "**", "?" and "[..]". We do not support "^" for pattern negation.


def load_open_file(
    file,
    loader_type: TYamlLoaderTypes,
    path: str,
    custom_loader: Optional[Callable[[str, Any, TYamlLoaderTypes], Any]] = None,
) -> Any:
    if custom_loader is None:
        return yaml.load(file, loader_type)
    return custom_loader(path, file, loader_type)


@dataclass
class Constructor:
    """The include constructor for PyYAML Loaders

    Use :func:`yaml.add_constructor` to register it on PyYAML's Loaders.

    Example:

        #. In Python source code, register it to a Loader class::

            import yaml
            import yaml_include

            yaml.add_constructor("!inc", yaml_include.Constructor(), yaml.Loader)

        #. In a YAML file, write ``!inc`` tags to include other YAML files. We can:

            * include file in local file system, absolute or relative

                .. code:: yaml

                    file: !inc /absolute/dir/of/foo/baz.yml

                .. code:: yaml

                    file: !inc ../../foo/baz.yml

            * include file from a website

                .. code:: yaml

                    file: !inc http://localhost:8080/foo/baz.yml

            * include file by wildcards

                .. code:: yaml

                    files: !inc foo/**/*.yml

        #. load the YAML in python::

            data = yaml.load(yaml_string, yaml.Loader)

           The variable ``data`` containers the parsed Python object(s) from including file(s)
    """

    fs: fsspec.AbstractFileSystem = field(
        default_factory=lambda: fsspec.filesystem("file"),
    )
    """:mod:`fsspec` File-system object to parse path/url and open including files. `LocalFileSystem` by default."""

    base_dir: Union[str, PathLike, Callable[[], Union[str, PathLike]], None] = None
    """Base directory to which open or search including YAML files in relative mode.

    * If it is ``None``, the actual base directory was decided by the :mod:`fsspec` file-system implementation in use.
      For example, the ``base_dir`` is default to be ``cwd`` for ``LocalFileSystem``, and be the value of ``client_kwargs.base_url`` for ``HTTPFileSystem``.
    * Else if it is callable, the actual base directory will be it's return value.
    * Else it will be used directly as the actual base directory.
    """

    autoload: bool = True
    """Whether if open and parse including file(s) when called.

    * If ``True``:
      open including file(s) then parse its/their content with current PyYAML Loader, and returns the parsed result.
    * If ``False``:
      will **NOT** open including file(s), the return value is a :class:`.Data` object stores include statement.
    """

    custom_loader: Optional[Callable[[str, Any, TYamlLoaderTypes], Any]] = None
    """Custom loader/parser function called when an including file is about to parse.

    If ``None``, parse the file as ordinary YAML with current `Loader` class.

    Else it shall be a callable object, as the replacement of ordinary YAML `Loader`.

    Example:
        The parameter may be like::

            def my_loader(urlpath, file, Loader):
                if urlpath.endswith(".json):
                    return json.load(file)
                if urlpath.endswith(".toml):
                    return toml.load(file)
                return yaml.load(file, Loader)

    The definition of the callable parameter is:

    Args:

        arg1(str):
            url or path of the file.

            Pass-in value of the argument may be:

            * Original url/path string defined in YAML, in the case of:
                * neither wildcard nor scheme exists in the include statement (eg: ``!inc foo/baz.yml``),
                * either wildcard and scheme exists in the include statement (eg: ``!inc http://host/foo/*.yml``)
            * Each file name returned by :meth:`fsspec.spec.AbstractFileSystem.glob`,
              if there be wildcard and no scheme in the include statement (eg: ``!inc foobar/**/*.yml``).

        arg2(typing.Any):
            What returned by :func:`fsspec.open` or member of :func:`fsspec.open_files`'s returned list will be passed to the argument.

            Type of the parameter is usually one of:

            * Subclass of :class:`io.IOBase`
            * Subclass of :class:`fsspec.spec.AbstractBufferedFile`

            Tip:
                **The type is NOT certain** however, because ``open`` methods of different :mod:`fsspec` file-system implementations are variable.

        arg3(typing.Type):
            Type of `PyYAML`'s Loader class in use.

    Returns:
        typing.Any: Parsed result
    """

    @contextmanager
    def managed_autoload(self, autoload: bool) -> Generator[Self, None, None]:
        """``with`` statement context manager for :attr:`autoload`

        Args:
            autoload: Temporary value of :attr:`autoload` to be set inside the ``with`` statement
        """
        saved, self.autoload = self.autoload, bool(autoload)
        try:
            yield self
        finally:
            self.autoload = saved

    def __call__(self, loader, node):
        if isinstance(node, yaml.ScalarNode):
            params = loader.construct_scalar(node)
            data = Data(params)
        elif isinstance(node, yaml.SequenceNode):
            params = loader.construct_sequence(node)
            data = Data(params[0], sequence_params=params[1:])
        elif isinstance(node, yaml.MappingNode):
            params = loader.construct_mapping(node)
            data = Data(
                params["urlpath"],
                mapping_params={k: v for k, v in params.items() if k != "urlpath"},
            )
        else:  # pragma: no cover
            raise TypeError(
                f"Type of node for {type(self)} expects one of {yaml.ScalarNode}, {yaml.SequenceNode} and {yaml.MappingNode}, but actually {type(node)}"
            )
        if self.autoload:
            return self.load(type(loader), data)
        else:
            return data

    def load(self, loader_type: TYamlLoaderTypes, data: Data) -> Any:
        """The method will be invoked once the PyYAML's Loader class call the constructor.
        It happens when an include state tag(eg: ``"!inc"``) is met.

        Args:
            loader_type: Type of current in-use PyYAML Loader class
            data: The data class of the include statement

        Returns:
            Data from the actual included YAML file, which is parsed by a PyYAML's Loader class.

        Caution:
            It's mainly invoked in :func:`yaml.load`, and **NOT advised to call it yourself**.

        Note:
            Additional positional or named parameters in YAML include statement are passed to ``*args`` and ``**kwargs`` in :attr:`.Data.sequence_params` and :attr:`.Data.mapping_params`.
            The class will pass them to :mod:`fsspec`'s :mod:`fsspec` File-system as implementation specific options.

            Note:
                To use positional in YAML include statement is discouraged.

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
              :attr:`.Data.sequence_params` and :attr:`.Data.mapping_params` of ``data`` will be passed to :func:`fsspec.open_files` as ``*args`` and ``**kwargs``

              Example:

                The YAML

                .. code:: yaml

                    key: !inc {urlpath: s3://my-bucket/*.yml.gz, compression: gzip}

                means::

                    with fsspec.open_files("s3://my-bucket/*.yml.gz", compression="gzip") as files:
                        for file in files:
                            yaml.load(file, Loader)

            * If there is no protocol/scheme, and no wildcard defined in YAML including,
              :attr:`.Data.sequence_params` and :attr:`.Data.mapping_params` of ``data`` will be passed to :mod:`fsspec` file-system implementation's ``open`` function (derive from :meth:`fsspec.spec.AbstractFileSystem.open`) as ``*args`` and ``**kwargs``

            * If there is no protocol/scheme, and also wildcard defined in YAML including, the situation is complex:
                * If the include statement is in a positional-parameter form:
                    * If count of argument is one,
                        it will be passed to of :meth:`fsspec.spec.AbstractFileSystem.glob`'s  ``maxdepth`` argument;
                    * If count of argument is more than one:
                        * First of them will be passed to :mod:`fsspec` file system implementation's ``glob`` method (derived from :meth:`fsspec.spec.AbstractFileSystem.glob`)
                        * Second of them will be passed to :mod:`fsspec` file system implementation's ``open`` method (derived from :meth:`fsspec.spec.AbstractFileSystem.open`)
                        * Others will be ignored
                * If the include statement is in a named-parameter form, the class will:
                    * Find a key named `glob`, then pass the corresponding data to :mod:`fsspec` file system implementation's ``glob`` method (derived from :meth:`fsspec.spec.AbstractFileSystem.glob`)
                    * Find a key named `open`, then pass the corresponding data to :mod:`fsspec` file system implementation's ``open`` method (derived from :meth:`fsspec.spec.AbstractFileSystem.open`)

                Example:

                    * The YAML

                        .. code:: yaml

                            key: !inc [foo/**/*.yml, 2]

                        means::

                            for file in fs.glob("foo/**/*.yml", maxdepth=2):
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
        base_dir = self.base_dir
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
            if WILDCARDS_PATTERN.match(urlpath):
                # if wildcards in path, return a Sequence/List
                result = []
                with fsspec.open_files(urlpath, *data.sequence_params, **data.mapping_params) as ofs:
                    for of_ in ofs:
                        data = load_open_file(of_, loader_type, urlpath, self.custom_loader)
                        result.append(data)
                return result
            # else if no wildcard, returns a single object
            with fsspec.open(urlpath, *data.sequence_params, **data.mapping_params) as of_:
                assert not isinstance(of_, list)
                result = load_open_file(of_, loader_type, urlpath, self.custom_loader)
                return result

        # if no protocol / scheme in path, we shall use the `fs` object
        if WILDCARDS_PATTERN.match(urlpath):
            urlpath = Path(urlpath).as_posix()
            # if wildcard in path, returns a List
            glob_params = open_params = None
            if data.sequence_params:
                if len(data.sequence_params) > 1:
                    glob_params, open_params = data.sequence_params[:2]
                elif len(data.sequence_params) == 1:
                    glob_params = data.sequence_params[0]
            elif data.mapping_params:
                glob_params = data.mapping_params.get("glob")
                open_params = data.mapping_params.get("open")

            if glob_params is None:
                glob_fn = lambda: self.fs.glob(urlpath)  # noqa: E731
            elif isinstance(glob_params, dict):
                # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
                if "maxdepth" in glob_params:
                    glob_params["maxdepth"] = int(glob_params["maxdepth"])
                glob_fn = lambda: self.fs.glob(urlpath, **glob_params)  # noqa: E731
            elif isinstance(glob_params, (list, set)):
                # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
                glob_params = list(glob_params)
                if glob_params:
                    glob_params[0] = int(glob_params[0])
                glob_fn = lambda: self.fs.glob(urlpath, *glob_params)  # noqa: E731
            else:
                # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
                maxdepth = int(glob_params)
                glob_fn = lambda: self.fs.glob(urlpath, maxdepth)  # noqa: E731

            if open_params is None:
                open_fn = lambda x: self.fs.open(x)  # noqa: E731
            elif isinstance(open_params, dict):
                open_fn = lambda x: self.fs.open(x, **open_params)  # noqa: E731
            elif isinstance(open_params, (list, set)):
                open_fn = lambda x: self.fs.open(x, *open_params)  # noqa: E731
            else:
                open_fn = lambda x: self.fs.open(x, open_params)  # noqa: E731

            result = []
            for file in glob_fn():
                assert isinstance(file, str)
                with open_fn(file) as of_:
                    data = load_open_file(of_, loader_type, file, self.custom_loader)
                    result.append(data)
            return result

        # else if no wildcards, return a single object
        with self.fs.open(urlpath, *data.sequence_params, **data.mapping_params) as of_:
            result = load_open_file(of_, loader_type, urlpath, self.custom_loader)
            return result
