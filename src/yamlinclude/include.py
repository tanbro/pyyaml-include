# -*- coding: utf-8 -*-

"""
Include YAML files within YAML
"""

__all__ = ['YamlIncludeConstructor']

import os
import re
from glob import iglob
from sys import version_info

import yaml

_PYTHON_VERSION_MAYOR_MINOR = '{0[0]}.{0[1]}'.format(version_info)

_RE_GLOB_WILDCARDS = re.compile(r'^.*(\*|\?|\[!*.+\]).*$')


class YamlIncludeConstructor:
    """The `include constructor` for PyYAML's loader
    """

    DEFAULT_TAG = '!include'

    def __call__(self, loader, node):
        args = []
        kwargs = {}
        if isinstance(node, yaml.nodes.ScalarNode):
            args = [loader.construct_scalar(node)]
        elif isinstance(node, yaml.nodes.SequenceNode):
            args = loader.construct_sequence(node)
        elif isinstance(node, yaml.nodes.MappingNode):
            kwargs = loader.construct_mapping(node)
        else:
            raise ValueError('Unsupported yaml node {0!r}'.format(node))
        return self._include(loader, *args, **kwargs)

    @classmethod
    def _include(cls, loader, pathname, recursive=False):
        if _RE_GLOB_WILDCARDS.match(pathname):
            result = []
            if _PYTHON_VERSION_MAYOR_MINOR >= '3.5':
                iterator = iglob(pathname, recursive=recursive)
            else:
                iterator = iglob(pathname)
            for path in iterator:
                if os.path.isfile(path):
                    with open(path) as f:
                        result.append(yaml.load(f, type(loader)))
            return result
        else:
            with open(pathname) as f:
                return yaml.load(f, type(loader))
