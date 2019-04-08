# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, print_function

import os
import unittest
from io import StringIO

import yaml

from yamlinclude import YamlIncludeConstructor
from ._internel import PYTHON_VERSION_MAYOR_MINOR, YAML_LOADERS, YAML1, YAML2


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

    def test_include_two_in_mapping(self):
        yml = '''
file1: !include include.d/1.yaml
file2: !include include.d/2.yaml
        '''
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {
                'file1': YAML1,
                'file2': YAML2,
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
- !include include.d/1.yaml
- !include include.d/2.yaml
        '''
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, [YAML1, YAML2])

    def test_include_file_not_exists(self):
        yml = '''
!include include.d/x.yaml
            '''
        if PYTHON_VERSION_MAYOR_MINOR >= '3.3':
            err_cls = FileNotFoundError
        else:
            err_cls = IOError
        for loader_cls in YAML_LOADERS:
            with self.assertRaises(err_cls):
                yaml.load(StringIO(yml), loader_cls)

    def test_include_wildcards(self):
        ymllist = ['''
!include include.d/*.yaml
''']
        if PYTHON_VERSION_MAYOR_MINOR >= '3.5':
            ymllist.extend(['''
!include [include.d/**/*.yaml, true]
''', '''
!include {pathname: include.d/**/*.yaml, recursive: true}
'''])
        for loader_cls in YAML_LOADERS:
            for yml in ymllist:
                data = yaml.load(StringIO(yml), loader_cls)
                self.assertIsInstance(data, list)
                self.assertListEqual(
                    sorted(data, key=lambda m: m['name']),
                    [YAML1, YAML2]
                )


if __name__ == '__main__':
    unittest.main()
