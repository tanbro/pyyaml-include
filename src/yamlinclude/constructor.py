# -*- coding: utf-8 -*-

"""
Include YAML files within YAML
"""
import os
import re
from glob import iglob
from sys import version_info

import yaml

__all__ = ['YamlIncludeConstructor']

PYTHON_MAYOR_MINOR = '{0[0]}.{0[1]}'.format(version_info)

WILDCARDS_REGEX = re.compile(r'^.*(\*|\?|\[!?.+\]).*$')


class YamlIncludeConstructor:
    """The `include constructor` for PyYAML's loader

    You can use :func:`yaml.add_constructor` to add it into loader.
    """

    TAG = '!include'

    def __call__(self, loader, node):
        args = []
        kwargs = {}
        if isinstance(node, yaml.nodes.ScalarNode):
            args = [loader.construct_scalar(node)]
        elif isinstance(node, yaml.nodes.SequenceNode):
            args = loader.construct_sequence(node)
        elif isinstance(node, yaml.nodes.MappingNode):
            kwargs = loader.construct_mapping(node)
        return self._include(loader, *args, **kwargs)

    @classmethod
    def _include(cls, loader, pathname, recursive=False):
        if WILDCARDS_REGEX.match(pathname):
            result = []
            if PYTHON_MAYOR_MINOR >= '3.5':
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

    @classmethod
    def add_to_loader_class(cls, loader_cls=None, tag=''):
        """
        Create an instance of the constructor, and add it to the YAML `Loader` class

        :param loader_cls:
          The `Loader` class add constructor to.

          :default: ``None``: Add to PyYAML's default `Loader`

        :type loader_cls: type(yaml.SafeLoader) | type(yaml.Loader) | type(yaml.CSafeLoader) | type(yaml.CLoader)

        :param str tag:
          tag name for the include constructor.

          :default: ``""``: use :attr:`TAG` as tag name.

        :return: New created object
        :rtype: YamlIncludeConstructor
        """
        if tag is None:
            tag = ''
        tag = tag.strip()
        if not tag:
            tag = cls.TAG
        instance = cls()
        if loader_cls is None:
            yaml.add_constructor(tag, instance)
        else:
            yaml.add_constructor(tag, instance, loader_cls)
        return instance
