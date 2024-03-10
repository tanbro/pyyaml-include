"""
Include other YAML files in YAML
"""

from contextlib import contextmanager
from dataclasses import dataclass

import yaml

from .base_constructor import BaseYamlIncludeCtor
from .data import YamlIncludeData
from .utils import load

__all__ = ["YamlIncludeCtor"]


@dataclass
class YamlIncludeCtor(BaseYamlIncludeCtor):
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

    autoload: bool = True

    @contextmanager
    def managed_autoload(self, autoload: bool = True):
        saved = self.autoload
        self.autoload = bool(autoload)
        try:
            yield self
        finally:
            self.autoload = saved

    def __call__(self, loader, node: yaml.nodes.Node):
        if isinstance(node, yaml.nodes.ScalarNode):
            param = loader.construct_scalar(node)
            data = YamlIncludeData(urlpath=param)
        elif isinstance(node, yaml.nodes.SequenceNode):
            param = loader.construct_sequence(node)
            data = YamlIncludeData(urlpath=param[0], sequence_param=param[1:])
        elif isinstance(node, yaml.nodes.MappingNode):
            param = loader.construct_mapping(node)
            data = YamlIncludeData(
                urlpath=param["urlpath"],
                mapping_param={k: v for k, v in param.items() if k != "urlpath"},
            )
        else:  # pragma: no cover
            raise ValueError(f"PyYAML node {node!r} is not supported by {type(self)}")
        if self.autoload:
            return load(type(loader), self, data)
        else:
            return data
