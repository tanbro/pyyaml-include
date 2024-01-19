"""
Include YAML files within YAML
"""

from os import PathLike
from pathlib import Path
from typing import Callable, Optional, Union
from urllib.parse import urlsplit

import fsspec
import yaml

from ._version import __version__, __version_tuple__, version, version_tuple


class YamlInclude:
    """The `include constructor` for PyYAML Loaders

    Use :func:`yaml.add_constructor` to add it into loader.

    Example:

        ::

            import yaml
            from yamlinclude import YamlInclude

            yaml.add_constructor("!inc", YamlInclude)

        In YAML files, use ``!inc`` to load other YAML files as below::

            baz: !inc /absolute/dir/of/foo/baz.yml

        ::

            data: !inc {pathname: http://localhost:8080/dir/**/*.yml, maxdepth: 1}

        ::

            conf: !inc ./conf/*.yml
    """

    def __init__(
        self,
        fs=None,
        base_dir: Union[str, PathLike, Callable[[], Union[str, PathLike]], None] = None,
    ):
        """
        Args:
            base_dir: Base directory where search including YAML files

                :default: ``""``:  include YAML files from current working directory.
        """
        self._fs = fsspec.filesystem("file") if fs is None else fs
        self._base_dir = base_dir

    def __call__(self, loader, node):
        args = []
        kwargs = {}
        if isinstance(node, yaml.nodes.ScalarNode):
            args = [loader.construct_scalar(node)]
        elif isinstance(node, yaml.nodes.SequenceNode):
            args = loader.construct_sequence(node)
        elif isinstance(node, yaml.nodes.MappingNode):
            kwargs = loader.construct_mapping(node)
        else:  # pragma: no cover
            raise ValueError(
                f"PyYAML node type {node!r} is not supported by {type(self)}"
            )
        return self.load(loader, *args, **kwargs)

    def load(self, loader, pathname: str, maxdepth: Optional[int] = None):
        """Once add the constructor to PyYAML loader class,
        the loader will invoke this function to include other YAML files when parsing a ``"!include"`` tag.

        Args:

            loader:
                Instance of PyYAML's loader class

            pathname (str):
                pathname can be either absolute (like `/usr/src/Python-1.5/*.yml`) or relative (like `../../Tools/*/*.yml`), and can contain shell-style wildcards

                glob-matching is supported:

                * If the path ends with ‘/’, only folders are returned.
                * We support "**", "?" and "[..]". We do not support "^" for pattern negation.
                * The `maxdepth` option is applied on the first "**" found in the path

            .. note:: Using the ``"**"`` pattern in large directory trees may consume an inordinate amount of time.

        Return:
            included YAML file, in Python data type

        Warning:
            It's called by :mod:`yaml`. Do NOT call it yourself.
        """
        Loader = type(loader)

        # scheme://path format, relative path and wildcards are not supported!
        if urlsplit(pathname).scheme:
            with fsspec.open(pathname) as fp:
                return yaml.load(fp, Loader)  # type:ignore

        if maxdepth is not None:
            maxdepth = int(maxdepth)
        if self._base_dir is None:
            pathname = Path(pathname).as_posix()
        else:
            if callable(self._base_dir):
                base_dir = Path(self._base_dir())
            else:
                base_dir = Path(self._base_dir)
            pathname = base_dir.joinpath(pathname).as_posix()

        # wildcards?
        if any(c in pathname for c in "*?[]"):
            result = []
            for file in self._fs.glob(pathname, maxdepth):
                with self._fs.open(file) as fp:
                    result.append(yaml.load(fp, Loader))
            return result

        with self._fs.open(pathname) as fp:
            return yaml.load(fp, Loader)
