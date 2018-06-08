# -*- coding: utf-8 -*-

__all__ = ['IncludeConstructor']

import os
import sys
from glob import iglob

import yaml

_PYTHON_VERSION_MAYOR_MINOR = sys.version_info[:2]


class IncludeConstructor:
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
        if '*' in pathname:
            result = []
            if _PYTHON_VERSION_MAYOR_MINOR < '3.5':
                iterator = iglob(pathname)
            else:
                iterator = iglob(pathname, recursive=recursive)
            for path in iterator:
                if os.path.isfile(path):
                    with open(path) as f:
                        result.append(yaml.load(f, type(loader)))
            return result
        else:
            with open(pathname) as f:
                return yaml.load(f, type(loader))
