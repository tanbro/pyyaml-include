"""
Include YAML files within YAML
"""

from os import PathLike
from pathlib import Path
from typing import Callable, Optional, Type, Union
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

    def __call__(self, loader, node: yaml.nodes.Node):
        if isinstance(node, yaml.nodes.ScalarNode):
            value = loader.construct_scalar(node)
            return self.load(type(loader), value)
        elif isinstance(node, yaml.nodes.SequenceNode):
            value = loader.construct_sequence(node)
            return self.load(type(loader), *value)
        elif isinstance(node, yaml.nodes.MappingNode):
            value = loader.construct_mapping(node)
            return self.load(type(loader), **value)
        else:  # pragma: no cover
            raise ValueError(f"PyYAML node {node!r} is not supported by {type(self)}")

    def load(self, loader_type: Type, urlpath: str, *args, **kwargs):
        """Once the constructor was added to PyYAML loader class,
        the loader class will invoke this function to include other YAML files when meet an including tag(eg: ``"!inc"``).

        Args:

            loader_type:
                Type of PyYAML's loader class

            urlpath:
                urlpath can be either absolute (like `/usr/src/Python-1.5/*.yml`) or relative (like `../../Tools/*/*.yml`), and can contain shell-style wildcards

                We support "**", "?" and "[..]". We do not support "^" for pattern negation.
                The `maxdepth` option is applied on the first "**" found in the path.

                Note:
                    Using the ``"**"`` pattern in large directory trees or remote files may consume an inordinate amount of time.

            kwargs:
                may have additional :mod:`fsspec` backend-specific options

        Returns:
            Data of included YAML file, pared to python object

        Warning:
            It's called by `PyYAML`, and do NOT call it yourself.
        """
        # full protocol and path
        if urlsplit(urlpath).scheme:
            # scheme://path format, relative path and wildcards are not supported!
            with fsspec.open(urlpath, *args, **kwargs) as fp:
                return yaml.load(fp, loader_type)  # type:ignore

        if self._base_dir is None:
            urlpath = Path(urlpath).as_posix()
        else:
            if callable(self._base_dir):
                base_dir = Path(self._base_dir())
            else:
                base_dir = Path(self._base_dir)
            urlpath = base_dir.joinpath(urlpath).as_posix()

        # wildcards
        if any(c in urlpath for c in "*?[]"):
            glob_params = open_params = None
            if args:
                if len(args) > 1:
                    glob_params, open_params = args[:2]
                elif len(args) == 1:
                    glob_params = args[0]
            if kwargs:
                glob_params = kwargs.get("glob")
                open_params = kwargs.get("open")

            if glob_params is None:
                fn_glob = lambda: self._fs.glob(urlpath)  # noqa: E731
            elif isinstance(glob_params, dict):
                # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
                if glob_params.get("maxdepth") is not None:
                    glob_params["maxdepth"] = int(glob_params["maxdepth"])
                fn_glob = lambda: self._fs.glob(urlpath, **glob_params)  # noqa: E731
            elif isinstance(glob_params, (list, set)):
                # special for maxdepth, because PyYAML sometimes treat number as string for constructor's parameter
                if len(glob_params) > 0:
                    glob_params = list(glob_params)
                    glob_params[0] = int(glob_params[0])
                fn_glob = lambda: self._fs.glob(urlpath, *glob_params)  # noqa: E731
            else:
                fn_glob = lambda: self._fs.glob(urlpath, glob_params)  # noqa: E731

            if open_params is None:
                fn_open = lambda x: self._fs.open(x)  # noqa: E731
            elif isinstance(open_params, dict):
                fn_open = lambda x: self._fs.open(x, **open_params)  # noqa: E731
            elif isinstance(open_params, (list, set)):
                fn_open = lambda x: self._fs.open(x, *open_params)  # noqa: E731
            else:
                fn_open = lambda x: self._fs.open(x, open_params)  # noqa: E731

            result = []
            for pth in fn_glob():
                with fn_open(pth) as fp:
                    result.append(yaml.load(fp, loader_type))
            return result

        # no wildcards
        with self._fs.open(urlpath, *args, **kwargs) as fp:
            return yaml.load(fp, loader_type)
