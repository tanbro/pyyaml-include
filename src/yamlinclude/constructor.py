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
from typing import Any, Callable, Generator, Optional, Union

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

from urllib.parse import urlsplit, urlunsplit

import fsspec
import yaml

from .data import YamlIncludeData

if sys.version_info < (3, 12):
    from .yamltypes_backward import TYamlLoaderTypes
else:
    from .yamltypes import TYamlLoaderTypes

__all__ = ["YamlIncludeCtor"]

WILDCARDS_RE_PAT = re.compile(
    r"^(.*)([\*\?\[\]]+)(.*)$"
)  # We support "**", "?" and "[..]". We do not support "^" for pattern negation.


def _load_of(file, loader_type, path, custom_loader):
    if custom_loader is None:
        return yaml.load(file, loader_type)
    return custom_loader(path, file, loader_type)


@dataclass
class YamlIncludeCtor:
    """The include constructor for PyYAML Loaders

    Use :func:`yaml.add_constructor` to register it on PyYAML's Loaders.

    Example:

        #. In Python source code, register it to a Loader class::

            import yaml

            from yamlinclude import YamlIncludeCtor

            yaml.add_constructor("!inc", YamlIncludeCtor(), yaml.Loader)

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
    """Base directory to which search including YAML files in relative mode.

    * If is's ``None``, the actual base directory was decided by the :mod:`fsspec` file-system implementation in use.
      For example, the ``base_dir`` is default to be `CWD` for ``LocalFileSystem``, and be the value of `client_kwargs.base_url` parameter for ``HTTPFileSystem``.
    * If it's callable, the actual base directory will be it's return value.
    """

    custom_loader: Optional[Callable] = None
    """Custom loader/parser function called when a including file to be parsed.

    If ``None``, parse the file as ordinary YAML with current `Loader` class.

    Else if not ``None``, it shall be a callable object like::

        def my_loader(urlpath, file, Loader):
            if file.path.endswith(".json):
                return json.load(file)
            if file.path.endswith(".toml):
                return toml.load(file)
            return yaml.load(file, Loader)

    Args:

        arg1(str): ``urlpath`` - url / path of the file.

            Pass-in value of the parameter is:

            * original url/path defined in YAML, if no wildcard in the including statement.
            * file name returned by :meth:`fsspec.spec.AbstractFileSystem.glob`, if wildcard in the including statement.

            Tip:
                * If YAML include statement has both scheme and wildcard (eg: ``http://host/foo/*.yml``), pass-in value of the argument will NOT be the url/path of matched file, it will be the original ``urlpath`` string defined in YAML instead.
                * But if we didn't write scheme in YAML include statement, and assigned a :mod:`fsspec` File-system object to ``fs`` argument correctly, it will be the name of matched file.

        arg2(Any):
            ``file`` - What returned by :func:`fsspec.open` or member of :func:`fsspec.open_files`'s returned list will be passed to the argument.

            Type of the parameter is usually one of:

            * Subclass of :class:`io.IOBase`
            * Subclass of :class:`fsspec.spec.AbstractBufferedFile`

            Tip:
                **The type is NOT certain** however, because ``open`` methods of different :mod:`fsspec` file-system implementations are variable.

        arg3 (Type): `Loader` - :mod:`yaml`'s Loader class.

    Returns: Parsed result
    """

    autoload: bool = True
    """Whether if open and parse including file(s) when called.

    * If ``True``:  the constructor will open including file(s) then parse it/them with current PyYAML Loader, and returns the parsed result.
    * If ``False``: the constructor will **NOT** open including file(s), the return value is a :class:`.YamlIncludeData` object which stores the include statement.
    """

    @contextmanager
    def managed_autoload(self, autoload: bool) -> Generator[Self, Any, None]:
        """``with`` statement context manager for :attr:`autoload`

        Args:
            autoload:
                Temporary value of :attr:`autoload` in the ``with`` statement context manager
        """
        saved = self.autoload
        self.autoload = bool(autoload)
        try:
            yield self
        finally:
            self.autoload = saved

    def __call__(self, loader, node: yaml.nodes.Node):
        if isinstance(node, yaml.nodes.ScalarNode):
            params = loader.construct_scalar(node)
            data = YamlIncludeData(urlpath=params)
        elif isinstance(node, yaml.nodes.SequenceNode):
            params = loader.construct_sequence(node)
            data = YamlIncludeData(urlpath=params[0], sequence_params=params[1:])
        elif isinstance(node, yaml.nodes.MappingNode):
            params = loader.construct_mapping(node)
            data = YamlIncludeData(
                urlpath=params["urlpath"],
                mapping_params={k: v for k, v in params.items() if k != "urlpath"},
            )
        else:  # pragma: no cover
            raise ValueError(f"PyYAML node {node!r} is not supported by {type(self)}")
        if self.autoload:
            return self.load(type(loader), data)
        else:
            return data

    def load(
        self,
        loader_type: TYamlLoaderTypes,
        data: YamlIncludeData,
    ) -> Any:
        """The method will be invoked once the PyYAML's Loader class call the constructor.
        It happens when an include state tag(eg: ``"!inc"``) is met.

        Args:
            loader_type: Type of current in-use PyYAML loader class
            data: The data class of the including statement

        Returns:
            Data of the actual included YAML file, return the python object by parsing the file's content

        Danger:
            It's mainly invoked in :func:`yaml.load`, and **NOT advised to call it yourself**.

        Note:
            Additional positional or named parameters in YAML include statement are passed to ``*args`` and ``**kwargs`` in :attr:`.YamlIncludeData.sequence_params` and :attr:`.YamlIncludeData.mapping_params`.
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
              :attr:`.YamlIncludeData.sequence_params` and :attr:`.YamlIncludeData.mapping_params` of ``data`` will be passed to :func:`fsspec.open_files` as ``*args`` and ``**kwargs``

              Example:

                The YAML

                .. code:: yaml

                    key: !inc {urlpath: s3://my-bucket/*.yml.gz, compression: gzip}

                means::

                    with fsspec.open_files("s3://my-bucket/*.yml.gz", compression="gzip") as files:
                        for file in files:
                            yaml.load(file, Loader)

            * If there is no protocol/scheme, and no wildcard defined in YAML including,
              :attr:`.YamlIncludeData.sequence_params` and :attr:`.YamlIncludeData.mapping_params` of ``data`` will be passed to :mod:`fsspec` file-system implementation's ``open`` function (derive from :meth:`fsspec.spec.AbstractFileSystem.open`) as ``*args`` and ``**kwargs``

            * If there is no protocol/scheme, and also wildcard defined in YAML including, the situation is complex:
                * If the include statement is in a positional-parameter form:
                    * If count of argument is one,
                        it will be passed to of :meth:`fsspec.spec.AbstractFileSystem.glob`'s  ``maxdepth`` argument;
                    * If count of argument is more than one:
                        # First of them will be passed to :mod:`fsspec` file system implementation's ``glob`` method (derived from :meth:`fsspec.spec.AbstractFileSystem.glob`)
                        # Second of them will be passed to :mod:`fsspec` file system implementation's ``open`` method (derived from :meth:`fsspec.spec.AbstractFileSystem.open`)
                        # Others will be ignored
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
            if WILDCARDS_RE_PAT.match(urlpath):
                # if wildcards in path, return a Sequence/List
                result = []
                with fsspec.open_files(urlpath, *data.sequence_params, **data.mapping_params) as ofs:
                    for of_ in ofs:
                        data = _load_of(of_, loader_type, urlpath, self.custom_loader)
                        result.append(data)
                return result
            # else if no wildcard, returns a single object
            with fsspec.open(urlpath, *data.sequence_params, **data.mapping_params) as of_:
                assert not isinstance(of_, list)
                result = _load_of(of_, loader_type, urlpath, self.custom_loader)
                return result

        # if no protocol / scheme in path, we shall use the `fs` object
        if WILDCARDS_RE_PAT.match(urlpath):
            urlpath = Path(urlpath).as_posix()
            # if wildcard in path, returns a List
            glob_params = open_params = None
            if data.sequence_params:
                if len(data.sequence_params) > 1:
                    glob_params, open_params = data.sequence_params[:2]
                elif len(data.sequence_params) == 1:
                    glob_params = data.sequence_params[0]
            if data.mapping_params:
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
                with open_fn(file) as of_:
                    data = _load_of(of_, loader_type, file, self.custom_loader)
                    result.append(data)
            return result

        # else if no wildcards, return a single object
        with self.fs.open(urlpath, *data.sequence_params, **data.mapping_params) as of_:
            result = _load_of(of_, loader_type, urlpath, self.custom_loader)
            return result
