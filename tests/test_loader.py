# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os
import unittest
from io import StringIO

import yaml

from yamlinclude import YamlIncludeConstructor
from ._internel import PYTHON_VERSION_MAYOR_MINOR, YAML_LOADERS, YAML1, YAML2, YAML_ZH_CN


class DefaultLoaderTestCase(unittest.TestCase):

    def setUp(self):
        if yaml.__version__ >= '5.0':
            self.LOADER = yaml.FullLoader
        else:
            self.LOADER = yaml.Loader

        YamlIncludeConstructor.add_to_loader_class()
        self.assertIn(YamlIncludeConstructor.DEFAULT_TAG_NAME, self.LOADER.yaml_constructors)

    def tearDown(self):
        del self.LOADER.yaml_constructors[YamlIncludeConstructor.DEFAULT_TAG_NAME]

    def test_no_loader_class_argument(self):
        yml = '!include tests/data/include.d/1.yaml'
        if yaml.__version__ >= '5.0' and PYTHON_VERSION_MAYOR_MINOR >= '3.2':
            with self.assertWarns(yaml.YAMLLoadWarning):
                data = yaml.load(StringIO(yml))
        else:
            data = yaml.load(StringIO(yml))
        self.assertDictEqual(data, YAML1)


class MultiLoadersTestCase(unittest.TestCase):

    def setUp(self):
        for loader_cls in YAML_LOADERS:
            YamlIncludeConstructor.add_to_loader_class(loader_cls)

    def tearDown(self):
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors[YamlIncludeConstructor.DEFAULT_TAG_NAME]

    def test_include_one_in_mapping(self):
        yml = '''
file1: !include tests/data/include.d/1.yaml
        '''
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {'file1': YAML1})

    def test_include_two_in_mapping(self):
        yml = '''
file1: !include tests/data/include.d/1.yaml
file2: !include tests/data/include.d/2.yaml
        '''
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {
                'file1': YAML1,
                'file2': YAML2,
            })

    def test_include_one_in_sequence(self):
        yml = '''
- !include tests/data/include.d/1.yaml
        '''
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, [YAML1])

    def test_include_two_in_sequence(self):
        yml = '''
- !include tests/data/include.d/1.yaml
- !include tests/data/include.d/2.yaml
        '''
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, [YAML1, YAML2])

    def test_include_file_not_exists(self):
        yml = '''
!include tests/data/include.d/x.yaml
            '''
        if PYTHON_VERSION_MAYOR_MINOR >= '3.3':
            err_cls = FileNotFoundError
        else:
            err_cls = IOError
        for loader_cls in YAML_LOADERS:
            with self.assertRaises(err_cls):
                yaml.load(StringIO(yml), loader_cls)

    def test_include_recursive(self):
        yml = '''
!include tests/data/0.yaml
            '''
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {
                'files': [YAML1, YAML2],
                'file1': YAML1,
                'file2': YAML2,
            })

    def test_include_abs(self):
        dirpath = os.path.abspath('')
        yml = '''
!include {0}/tests/data/include.d/1.yaml
        '''.format(dirpath)
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, YAML1)

    def test_include_wildcards(self):
        ymllist = ['''
!include tests/data/include.d/*.yaml
''']
        if PYTHON_VERSION_MAYOR_MINOR >= '3.5':
            ymllist.extend(['''
!include [tests/data/include.d/**/*.yaml, true]
''', '''
!include {pathname: tests/data/include.d/**/*.yaml, recursive: true}
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
