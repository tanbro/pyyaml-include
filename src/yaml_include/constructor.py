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
    from yaml import Node
    from yaml.constructor import _Scalar  # type: ignore[attr-defined]
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

    Use :func:`yaml.add_constructor` to register it on PyYAML's Loaders.

    Example:

        #. In Python source code, register it to a Loader class::

            import yaml
            import yaml_include

            yaml.add_constructor("!inc", yaml_include.Constructor(), yaml.Loader)

        #. In a YAML file, write ``!inc`` tags to include other YAML files. We can:

            * include file in local file system, absolute or relative

                .. code-block:: yaml

                    file: !inc /absolute/dir/of/foo/baz.yml

                .. code-block:: yaml

                    file: !inc ../../foo/baz.yml

            * include file from a website

                .. code-block:: yaml

                    file: !inc http://localhost:8080/foo/baz.yml

            * include file by wildcards

                .. code-block:: yaml

                    files: !inc foo/**/*.yml

        #. load the YAML in python::

            data = yaml.load(yaml_string, yaml.Loader)

           The variable ``data`` containers the parsed Python object(s) from including file(s)
    """

    fs: fsspec.AbstractFileSystem = field(default_factory=lambda: fsspec.filesystem("file"))
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

    custom_loader: Optional[Callable[[str, _ReadStream, Type[Union[_Loader, _CLoader]]], Any]] = None
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

        arg2(bytes | str | SupportsRead[bytes | str]):
            What returned by :func:`fsspec.open`, or member of :func:`fsspec.open_files`'s returned list, will be set to the argument.

            The parameter may later be used in :func:`yaml.load`, it could be:

            * :class:`bytes` or :class:`str`

            * An object implements ::

                class SupportsRead(bytes | str):
                    def read(self, length: int = ..., /) -> bytes | str: ...

            Tip:
                The ``open`` method of :mod:`fsspec` file-system implementations usually returns a :class:`fsspec.spec.AbstractBufferedFile` object.
                However, **the type is NOT certain**, because ``open`` methods of different :mod:`fsspec` file-system implementations are variable.

        arg3(typing.Type):
            Type (**not instance**) of `PyYAML`'s Loader currently in use.

    Returns:
        typing.Any: Parsed result
    """

    @contextmanager
    def managed_autoload(self, autoload: bool) -> Iterator[Self]:
        """``with`` statement context manager for :attr:`autoload`

        Args:
            autoload: Temporary value of :attr:`autoload` to be set inside the ``with`` statement
        """
        saved, self.autoload = self.autoload, bool(autoload)
        try:
            yield self
        finally:
            self.autoload = saved

    def __call__(self, loader: Union[_Loader, _CLoader], node: Node) -> Union[Data, Any]:
        val: Union[_Scalar, Sequence, Mapping]
        if is_yaml_scalar_node(node):
            val = loader.construct_scalar(node)
            if isinstance(val, str):
                data = Data(val)
            else:  # pragma: no cover
                raise TypeError(f"{type(val)}")
        elif is_yaml_sequence_node(node):
            val = loader.construct_sequence(node)
            data = Data(val[0], sequence_params=val[1:])
        elif is_yaml_mapping_node(node):
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

        The function works as blow description:

        * If there is a protocol/scheme, and no wildcard defined in YAML including,
          ``*args`` and ``**kwargs`` will be passed to :func:`fsspec.open`.

            Example:
                The YAML

                .. code-block:: yaml

                    key: !inc {urlpath: s3://my-bucket/my-file.yml.gz, compression: gzip}

                means::

                    with fsspec.open("s3://my-bucket/my-file.yml.gz", compression="gzip") as f:
                        yaml.load(f, Loader)

        * If there is a protocol/scheme, and also wildcard defined in YAML including,
          :attr:`.Data.sequence_params` and :attr:`.Data.mapping_params` of ``data`` will be passed to :func:`fsspec.open_files` as it's ``*args`` and ``**kwargs`` arguments.

            Example:
                The YAML

                .. code-block:: yaml

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
                The YAML

                .. code-block:: yaml

                    key: !inc [foo/**/*.yml, 2]

                means::

                    for file in fs.glob("foo/**/*.yml", maxdepth=2):
                        with fs.open(file) as fp:
                            yaml.load(fp, Loader)

            Example:
                The YAML

                .. code-block:: yaml

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


def is_yaml_scalar_node(node) -> TypeGuard[yaml.ScalarNode]:
    return isinstance(node, yaml.ScalarNode)


def is_yaml_sequence_node(node) -> TypeGuard[yaml.SequenceNode]:
    return isinstance(node, yaml.SequenceNode)


def is_yaml_mapping_node(node) -> TypeGuard[yaml.MappingNode]:
    return isinstance(node, yaml.MappingNode)


def is_kwds(val) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(val, Mapping) and all(isinstance(k, str) and k.isidentifier() for k in val)
