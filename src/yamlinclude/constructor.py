"""
Include other YAML files in YAML
"""

from os import PathLike
from typing import Callable, Optional, Union

import fsspec
import yaml

from .data import YamlIncludeData


__all__ = ["YamlIncludeCtor"]


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

    def __init__(
        self,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        base_dir: Union[str, PathLike, Callable[[], Union[str, PathLike]], None] = None,
        auto_load: bool = True,
        custom_loader: Optional[Callable] = None,
    ):
        """
        Args:
            fs:
                :mod:`fsspec` File-system object to parse path/url and open including files. `LocalFileSystem` by default.
            base_dir:
                Base directory to which search including YAML files in relative mode.

                * If is's ``None``, the actual base directory was decided by the :mod:`fsspec` file-system implementation in use.

                  For example, the ``base_dir`` will default be `CWD` for ``LocalFileSystem``, and be the value of `client_kwargs.base_url` parameter for ``HTTPFileSystem``

                * If it's callable, the return value will be taken as the base directory.

            custom_loader:
                Custom loader/parser function called when a including file to be parsed.

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
        self._fs: fsspec.AbstractFileSystem = fsspec.filesystem("file") if fs is None else fs
        self._base_dir = base_dir
        self._auto_load = auto_load
        self._custom_loader = custom_loader

    def __call__(self, loader, node: yaml.nodes.Node):
        if isinstance(node, yaml.nodes.ScalarNode):
            value = loader.construct_scalar(node)
            tag = YamlIncludeData(urlpath=value)
        elif isinstance(node, yaml.nodes.SequenceNode):
            value = loader.construct_sequence(node)
            tag = YamlIncludeData(urlpath=value[0], sequence_param=value[1:])
        elif isinstance(node, yaml.nodes.MappingNode):
            value = loader.construct_mapping(node)
            tag = YamlIncludeData(
                urlpath=value["urlpath"],
                mapping_param={k: v for k, v in value.items() if k != "urlpath"},
            )
        else:  # pragma: no cover
            raise ValueError(f"PyYAML node {node!r} is not supported by {type(self)}")
        if self._auto_load:
            return tag.load(type(loader), self._fs, self._base_dir, self._custom_loader)
        else:
            return tag
