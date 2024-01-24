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

__all__ = ["YamlInclude", "version", "version_tuple"]


class YamlInclude:
    """The include constructor for PyYAML Loaders

    Use :func:`yaml.add_constructor` to add it to PyYAML's Loaders.

    Example:

        #. In Python source code, add it to a Loader class::

            import yaml

            from yamlinclude import YamlInclude

            yaml.add_constructor("!inc", YamlInclude, yaml.Loader)

        #. In YAML files, use ``!inc`` to load other YAML files, we can:

            * include file in local file system, by absolute or relative path

                .. code:: yaml

                    file: !inc /absolute/dir/of/foo/baz.yml

                .. code:: yaml

                    file: !inc ../../foo/baz.yml

            * include file from a website, arguments can be set in a mapping form

                .. code:: yaml

                    file: !inc {urlpath: http://localhost:8080/foo/baz.yml, encoding: utf8}

            * include file by wildcards

                .. code:: yaml

                    files: !inc foo/*.yml

        #. load the YAML in python source code::

            data = yaml.load(yaml_string, yaml.Loader)

           The variable ``data`` containers the parsed Python object(s) from including file(s)
    """

    def __init__(
        self,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        base_dir: Union[str, PathLike, Callable[[], Union[str, PathLike]], None] = None,
    ):
        """
        Args:
            fs:
                :mod:`fsspec` File-system object to parse path/url and open including files
            base_dir:
                Base directory to which search including YAML files in relative mode
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

    def load(self, loader, urlpath: str, **kwargs):
        """Once the constructor was added to PyYAML loader class,
        the loader class will invoke this function to include other YAML files when meet an including tag(eg: ``"!inc"``).

        Args:

            loader:
                Instance of PyYAML's loader class

            urlpath:
                urlpath can be either absolute (like `/usr/src/Python-1.5/*.yml`) or relative (like `../../Tools/*/*.yml`), and can contain shell-style wildcards

                We support "**", "?" and "[..]". We do not support "^" for pattern negation.
                The `maxdepth` option is applied on the first "**" found in the path.

                Note:
                    Using the ``"**"`` pattern in large directory trees or remote files may consume an inordinate amount of time.

            kwargs:
                may have additional :mod:`fsspec` backend-specific options

        Returns:
            Data of included YAML file, in Python data type

        Warning:
            It's called by `PyYAML`, and do NOT call it yourself.
        """
        Loader_class = type(loader)

        if kwargs.get("maxdepth") is not None:
            kwargs["maxdepth"] = int(kwargs["maxdepth"])

        # scheme://path format, relative path and wildcards are not supported!
        if urlsplit(urlpath).scheme:
            with fsspec.open(urlpath, **kwargs) as fp:
                return yaml.load(fp, Loader_class)  # type:ignore

        if self._base_dir is None:
            urlpath = Path(urlpath).as_posix()
        else:
            if callable(self._base_dir):
                base_dir = Path(self._base_dir())
            else:
                base_dir = Path(self._base_dir)
            urlpath = base_dir.joinpath(urlpath).as_posix()

        # wildcards?
        if any(c in urlpath for c in "*?[]"):
            result = []
            for file in self._fs.glob(urlpath, **kwargs):
                with self._fs.open(file) as fp:
                    result.append(yaml.load(fp, Loader_class))
            return result
        else:
            with self._fs.open(urlpath, **kwargs) as fp:
                return yaml.load(fp, Loader_class)
