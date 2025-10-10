"""
Include other YAML files in YAML
"""

from __future__ import annotations

import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from itertools import chain
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable, Iterator, Mapping, Optional, Sequence, Type, TypeVar, Union
from urllib.parse import urlsplit, urlunsplit

if sys.version_info >= (3, 10):  # pragma: no cover
    from typing import TypeGuard
else:  # pragma: no cover
    from typing_extensions import TypeGuard

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

import fsspec  # type: ignore[import-untyped]
import yaml

from .data import Data

if TYPE_CHECKING:  # pragma: no cover
    from yaml.cyaml import _CLoader
    from yaml.loader import _Loader
    from yaml.reader import _ReadStream

    OpenFileT = TypeVar("OpenFileT", bound=_ReadStream)
    LoaderTypeT = TypeVar("LoaderTypeT", bound=Type[Union[_Loader, _CLoader]])


__all__ = ["Constructor"]

WILDCARDS_PATTERN = re.compile(
    r"^(.*)([\*\?\[\]]+)(.*)$"
)  # We support "**", "?" and "[..]". We do not support "^" for pattern negation.


if yaml.__with_libyaml__:  # pragma: no cover
    DEFAULT_YAML_LOAD_FUNCTION = lambda x: yaml.load(x, yaml.CSafeLoader)  # noqa: E731
else:  # pragma: no cover
    DEFAULT_YAML_LOAD_FUNCTION = yaml.safe_load


def load_open_file(
    file: OpenFileT,
    loader_type: LoaderTypeT,
    path: str,
    custom_loader: Optional[Callable[[str, OpenFileT, LoaderTypeT], Any]] = None,
) -> Any:
    if custom_loader is None:
        return yaml.load(file, loader_type)
    return custom_loader(path, file, loader_type)


@dataclass
class Constructor:
    """The include constructor for PyYAML Loaders

    Use :func:`yaml.add_constructor` to register it with PyYAML's Loaders.

    Example:

        #. In Python source code, register it with a Loader class::

            import yaml
            import yaml_include

            yaml.add_constructor("!inc", yaml_include.Constructor(), yaml.Loader)

        #. In a YAML file, use ``!inc`` tags to include other YAML files. You can:

            * Include a file from the local file system, either absolute or relative:

                .. code-block:: yaml

                    file: !inc /absolute/dir/of/foo/baz.yml

                .. code-block:: yaml

                    file: !inc ../../foo/baz.yml

            * Include a file from a website:

                .. code-block:: yaml

                    file: !inc http://localhost:8080/foo/baz.yml

            * Include files by wildcard:

                .. code-block:: yaml

                    files: !inc foo/**/*.yml

        #. Load the YAML in Python::

            data = yaml.load(yaml_string, yaml.Loader)

           The variable ``data`` contains the parsed Python object(s) from the included file(s).
    """

    fs: fsspec.AbstractFileSystem = field(default_factory=lambda: fsspec.filesystem("file"))
    """:mod:`fsspec` File-system object used to parse paths/URLs and open included files. Defaults to `LocalFileSystem`."""

    base_dir: Union[str, PathLike, Callable[[], Union[str, PathLike]], None] = None
    """Base directory used to open or search for included YAML files in relative mode.

    * If it is ``None``:
      The actual base directory is determined by the :mod:`fsspec` file-system implementation in use.

      - For example, for ``LocalFileSystem``, the default base directory is the current working directory (``cwd``).
      - For ``HTTPFileSystem``, the base directory is set to the value of ``client_kwargs.base_url``.

    * If it is callable:
      The actual base directory will be the return value of the callable.

    * Otherwise:
      It will be used directly as the actual base directory.
    """

    autoload: bool = True
    """Determines whether to open and parse included file(s) when called.

    * If ``True``:
      Open the included file(s), parse their content using the current PyYAML Loader, and return the parsed result.

    * If ``False``:
      Do not open the included file(s). Instead, return a :class:`.Data` object that stores the include statement.
    """

    custom_loader: Optional[Callable[[str, _ReadStream, Type[Union[_Loader, _CLoader]]], Any]] = None
    """Custom loader/parser function called when an included file is about to be parsed.

    If ``None``, the file is parsed as ordinary YAML using the current `Loader` class.

    Otherwise, it should be a callable object that replaces the ordinary YAML `Loader`.

    Example:
        The parameter may be defined as follows::

            def my_loader(urlpath, file, Loader):
                if urlpath.endswith(".json"):
                    return json.load(file)
                if urlpath.endswith(".toml"):
                    return toml.load(file)
                return yaml.load(file, Loader)

    The definition of the callable parameter is:

    Args:
        urlpath (str):
            URL or path of the file.

            The value passed to this argument may be:

            - The original URL/path string defined in YAML, in cases where:
                - Neither a wildcard nor a scheme is present in the include statement (e.g., ``!inc foo/baz.yml``).
                - Either a wildcard or a scheme is present in the include statement (e.g., ``!inc http://host/foo/*.yml``).
            - Each file name returned by :meth:`fsspec.spec.AbstractFileSystem.glob`,
              if a wildcard is present but no scheme in the include statement (e.g., ``!inc foobar/**/*.yml``).

        file (bytes | str | SupportsRead[bytes | str]):
            The object returned by :func:`fsspec.open` or a member of the list returned by :func:`fsspec.open_files`.

            This parameter will be used in :func:`yaml.load` and can be:

            - An instance of :class:`bytes` or :class:`str`.
            - An object that implements the following interface::

                class SupportsRead(bytes | str):
                    def read(self, length: int = ...) -> bytes | str: ...

            Tip:
                The ``open`` method of :mod:`fsspec` file-system implementations typically returns a :class:`fsspec.spec.AbstractBufferedFile` object.
                However, the exact type is not guaranteed, as ``open`` methods can vary across different :mod:`fsspec` file-system implementations.

        Loader (typing.Type):
            The type (not an instance) of the `PyYAML` `Loader` currently in use.

    Returns:
        typing.Any: The parsed result.
    """

    @contextmanager
    def managed_autoload(self, autoload: bool) -> Iterator[Self]:
        """Context manager for temporarily setting the :attr:`autoload` attribute.

        This context manager allows you to set a temporary value for :attr:`autoload` within a ``with`` statement.
        The original value is restored once the block is exited.

        Args:
            autoload: The temporary value to assign to :attr:`autoload` within the ``with`` statement.

        Yields:
            The current instance of :class:`.Constructor`.

        Example:

            ::

                ctor = yaml_include.Constructor()
                # autoload is True here

                with ctor.managed_autoload(False):
                    # temporary set autoload to False
                    yaml.full_load(YAML_TEXT)
                # autoload restore True automatic
        """
        saved, self.autoload = self.autoload, bool(autoload)
        try:
            yield self
        finally:
            self.autoload = saved

    def __call__(self, loader: Union[_Loader, _CLoader], node: yaml.Node) -> Union[Data, Any]:
        val: Union[Sequence, Mapping, str]
        if isinstance(node, yaml.ScalarNode):
            val = loader.construct_scalar(node)
            if isinstance(val, str):
                data = Data(val)
            else:  # pragma: no cover
                raise TypeError(f"{type(val)}")
        elif isinstance(node, yaml.SequenceNode):
            val = loader.construct_sequence(node)
            data = Data(val[0], sequence_params=val[1:])
        elif isinstance(node, yaml.MappingNode):
            val = loader.construct_mapping(node)
            if is_kwds(val):
                kdargs = {
                    "urlpath": val["urlpath"],
                    "mapping_params": {k: v for k, v in val.items() if k not in ("urlpath", "flatten")},
                }
                if (flatten := val.get("flatten")) is not None:
                    if isinstance(flatten, str):
                        flatten = DEFAULT_YAML_LOAD_FUNCTION(flatten)
                    if not isinstance(flatten, bool):  # pragma: no cover
                        raise ValueError("`flatten` must be a boolean")
                    kdargs["flatten"] = flatten
                data = Data(**kdargs)
            else:  # pragma: no cover
                raise ValueError("not all keys type of the YAML mapping node are identifier string")
        else:  # pragma: no cover
            raise TypeError(f"{type(node)}")
        if self.autoload:
            return self.load(type(loader), data)
        else:
            return data

    def load(self, loader_type: Type[Union[_Loader, _CLoader]], data: Data) -> Any:
        """This method is invoked when the PyYAML Loader class encounters an include tag (e.g., ``!inc``).

        Args:
            loader_type: The type of the current PyYAML Loader class in use.
            data: The data object representing the include statement.

        Returns:
            Data from the included YAML file, parsed by a PyYAML Loader class.

        Caution:
            This method is primarily invoked internally by :func:`yaml.load`. **It is not recommended to call this method directly.**

        Notes:
            - Additional positional or named parameters in YAML include statements are passed to ``*args`` and ``**kwargs`` in :attr:`.Data.sequence_params` and :attr:`.Data.mapping_params`. These parameters are then forwarded to the :mod:`fsspec` File-system as implementation-specific options.
            - The use of positional parameters in YAML include statements is discouraged.

        The function operates as follows:

        - If there is a protocol/scheme and no wildcard in the YAML include:

          ``*args`` and ``**kwargs`` are passed to :func:`fsspec.open`.

        Example:
            The YAML

            .. code-block:: yaml

                key: !inc {urlpath: s3://my-bucket/my-file.yml.gz, compression: gzip}

            translates to:

            .. code-block:: python

                with fsspec.open("s3://my-bucket/my-file.yml.gz", compression="gzip") as f:
                    yaml.load(f, Loader)

        - If there is a protocol/scheme and a wildcard in the YAML include:

          :attr:`.Data.sequence_params` and :attr:`.Data.mapping_params` of ``data`` are passed to :func:`fsspec.open_files` as its ``*args`` and ``**kwargs`` arguments.

        Example:
            The YAML

            .. code-block:: yaml

                key: !inc {urlpath: s3://my-bucket/*.yml.gz, compression: gzip}

            translates to:

            .. code-block:: python

                with fsspec.open_files("s3://my-bucket/*.yml.gz", compression="gzip") as files:
                    for file in files:
                        yaml.load(file, Loader)

        - If there is no protocol/scheme and no wildcard in the YAML include:

          :attr:`.Data.sequence_params` and :attr:`.Data.mapping_params` of ``data`` are passed to the :mod:`fsspec` file-system's ``open`` method (derived from :meth:`fsspec.spec.AbstractFileSystem.open`) as ``*args`` and ``**kwargs``.

        - If there is no protocol/scheme and a wildcard in the YAML include, the behavior depends on the form of the include statement:

          - For positional-parameter form:

            - If there is one argument, it is passed to :meth:`fsspec.spec.AbstractFileSystem.glob`'s ``maxdepth`` parameter.

            - If there are multiple arguments:

              - The first argument is passed to the ``glob`` method.
              - The second argument is passed to the ``open`` method.
              - Additional arguments are ignored.

          - For named-parameter form:

            - A key named `glob` passes its value to the ``glob`` method.
            - A key named `open` passes its value to the ``open`` method.

        Examples:

            - The YAML

              .. code-block:: yaml

                  key: !inc [foo/**/*.yml, 2]

              translates to:

              .. code-block:: python

                  for file in fs.glob("foo/**/*.yml", maxdepth=2):
                      with fs.open(file) as fp:
                          yaml.load(fp, Loader)

            - The YAML

              .. code-block:: yaml

                  key: !inc {urlpath: foo/**/*.yml.gz, glob: {maxdepth: 2}, open: {compression: gzip}}

              translates to:

              .. code-block:: python

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
                urlpath = urlunsplit(chain(url_sr[:2], (base_dir.joinpath(url_sr[2]).as_posix(),), url_sr[3:]))
            else:
                urlpath = base_dir.joinpath(urlpath).as_posix()

        # If protocol/scheme in path, we shall open it directly with fs's default open method
        if url_sr.scheme:
            if WILDCARDS_PATTERN.match(urlpath):
                # if wildcards in path, return a Sequence/List
                result = []
                with fsspec.open_files(urlpath, *data.sequence_params, **data.mapping_params) as ofs:
                    for of_ in ofs:
                        loaded_data = load_open_file(of_, loader_type, urlpath, self.custom_loader)
                        result.append(loaded_data)
                return result
            # else if no wildcard, returns a single object
            with fsspec.open(urlpath, *data.sequence_params, **data.mapping_params) as of_:
                if isinstance(of_, list):  # pragma: no cover
                    raise RuntimeError(f"`fsspec.open()` returns a `list` ({of_})")
                result = load_open_file(of_, loader_type, urlpath, self.custom_loader)
                return result

        # if no protocol / scheme in path, we shall use the `fs` object
        if WILDCARDS_PATTERN.match(urlpath):
            urlpath = Path(urlpath).as_posix()
            # if wildcard in path, returns a List
            glob_params: Union[Mapping[str, Any], Iterable, None] = None
            open_params: Union[Mapping[str, Any], Iterable, None] = None
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
            elif isinstance(glob_params, Mapping):
                # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
                kv_args = {**glob_params}
                if "maxdepth" in kv_args:
                    kv_args["maxdepth"] = int(kv_args["maxdepth"])
                glob_fn = lambda: self.fs.glob(urlpath, **kv_args)  # noqa: E731
            elif isinstance(glob_params, Iterable) and not isinstance(glob_params, (str, bytes)):
                # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
                pos_args = list(glob_params)
                if pos_args:
                    pos_args[0] = int(pos_args[0])
                glob_fn = lambda: self.fs.glob(urlpath, *pos_args)  # noqa: E731
            else:
                # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
                try:
                    maxdepth = int(glob_params)
                except ValueError:
                    maxdepth = None
                glob_fn = lambda: self.fs.glob(urlpath, maxdepth=maxdepth)  # noqa: E731

            if open_params is None:
                open_fn = lambda x: self.fs.open(x)  # noqa: E731
            elif isinstance(open_params, Mapping):
                open_fn = lambda x: self.fs.open(x, **open_params)  # noqa: E731
            elif isinstance(open_params, Iterable) and not isinstance(open_params, (str, bytes)):
                open_fn = lambda x: self.fs.open(x, *open_params)  # noqa: E731
            elif isinstance(open_params, str):
                mode = str(open_params)
                open_fn = lambda x: self.fs.open(x, mode=mode)  # noqa: E731
            else:  # pragma: no cover
                raise ValueError("invalid open parameter")

            result = []
            for file in glob_fn():
                if not isinstance(file, str):  # pragma: no cover
                    raise RuntimeError(f"`fs.glob()` function does not return a `str` ({file})")
                with open_fn(file) as of_:
                    loaded_data = load_open_file(of_, loader_type, file, self.custom_loader)
                    result.append(loaded_data)
            if data.flatten:
                return [child for item in result for child in item]
            else:
                return result

        # else if no wildcards, return a single object
        with self.fs.open(urlpath, *data.sequence_params, **data.mapping_params) as of_:
            result = load_open_file(of_, loader_type, urlpath, self.custom_loader)
            return result


def is_kwds(val) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(val, Mapping) and all(isinstance(k, str) and k.isidentifier() for k in val)
