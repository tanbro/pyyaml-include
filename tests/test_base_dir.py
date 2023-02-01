# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, print_function

import os
import unittest
from io import StringIO
from textwrap import dedent

import yaml

from yamlinclude import YamlIncludeConstructor
from ._internal import PYTHON_VERSION_MAYOR_MINOR, YAML_LOADERS, YAML1, YAML2


class BaseDirTestCase(unittest.TestCase):

    def setUp(self):
        for loader_cls in YAML_LOADERS:
            YamlIncludeConstructor.add_to_loader_class(loader_cls, base_dir=os.path.join('tests', 'data'))

    def tearDown(self):
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors[YamlIncludeConstructor.DEFAULT_TAG_NAME]

    def test_include_one_in_mapping(self):
        yml = '''
file1: !include include.d/1.yaml
        '''
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {'file1': YAML1})

    def test_continuous_including(self):
        yml = dedent('''
        foo:
            - !include include.d/1.yaml
            - !include include.d/2.yaml
        ''')
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {
                'foo': [YAML1, YAML2]
            })

    def test_include_two_in_mapping(self):
        yml = '''
a: A
file1: !include include.d/1.yaml
b: B
file2: !include include.d/2.yaml
c: C
        '''
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {
                'a': 'A',
                'file1': YAML1,
                'b': 'B',
                'file2': YAML2,
                'c': 'C',
            })

    def test_include_one_in_sequence(self):
        yml = '''
- !include include.d/1.yaml
        '''
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, [YAML1])

    def test_include_two_in_sequence(self):
        yml = '''
- a
- !include include.d/1.yaml
- b
- !include include.d/2.yaml
- c
        '''
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, ['a', YAML1, 'b', YAML2, 'c'])

    def test_include_file_not_exists(self):
        yml = '''
file: !include include.d/x.yaml
            '''
        if PYTHON_VERSION_MAYOR_MINOR >= '3.3':
            err_cls = FileNotFoundError
        else:
            err_cls = IOError
        for loader_cls in YAML_LOADERS:
            with self.assertRaises(err_cls):
                yaml.load(StringIO(yml), loader_cls)

    def test_include_wildcards(self):
        yml = '''
files: !include include.d/*.yaml
'''
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(
                sorted(data['files'], key=lambda m: m['name']),
                [YAML1, YAML2]
            )

    if PYTHON_VERSION_MAYOR_MINOR >= '3.5':

        def test_include_wildcards_1(self):
            yml = '''
files: !include [include.d/**/*.yaml, true]
'''
            for loader_cls in YAML_LOADERS:
                data = yaml.load(StringIO(yml), loader_cls)
                self.assertListEqual(
                    sorted(data['files'], key=lambda m: m['name']),
                    [YAML1, YAML2]
                )

        def test_include_wildcards_2(self):
            yml = '''
files: !include {pathname: include.d/**/*.yaml, recursive: true}
'''
            for loader_cls in YAML_LOADERS:
                data = yaml.load(StringIO(yml), loader_cls)
                self.assertListEqual(
                    sorted(data['files'], key=lambda m: m['name']),
                    [YAML1, YAML2]
                )


if __name__ == '__main__':
    unittest.main()
