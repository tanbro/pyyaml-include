from dataclasses import dataclass, field
from os import PathLike
from typing import Callable, Optional, Union

import fsspec


@dataclass
class BaseYamlIncludeCtor:
    fs: fsspec.AbstractFileSystem = field(
        default_factory=lambda: fsspec.filesystem("file"),
    )
    """:mod:`fsspec` File-system object to parse path/url and open including files. `LocalFileSystem` by default."""

    base_dir: Union[str, PathLike, Callable[[], Union[str, PathLike]], None] = None
    """Base directory to which search including YAML files in relative mode.

    * If is's ``None``, the actual base directory was decided by the :mod:`fsspec` file-system implementation in use.

        For example, the ``base_dir`` will default be `CWD` for ``LocalFileSystem``, and be the value of `client_kwargs.base_url` parameter for ``HTTPFileSystem``

    * If it's callable, the return value will be taken as the base directory.
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
            ``file`` - What returned by :func:`fsspec.open`, or the list member of :func:`fsspec.open_files`'s return value, will be passed to the argument.

            Type of the parameter is usually one of:

            * Subclass of :class:`io.IOBase`
            * Subclass of :class:`fsspec.spec.AbstractBufferedFile`

            Tip:
                **The type is NOT certain** however, because ``open`` methods of different :mod:`fsspec` file-system implementations are variable.

        arg3 (Type): `Loader` - :mod:`yaml`'s Loader class.

    Returns: Parsed result
    """
