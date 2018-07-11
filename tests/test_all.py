# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, print_function

import os
import unittest
from io import StringIO
from sys import version_info, stderr

import yaml

from yamlinclude import YamlIncludeConstructor

_PYTHON_VERSION_MAYOR_MINOR = '{0[0]}.{0[1]}'.format(version_info)


class YamlIncludeTestCase(unittest.TestCase):
    LOADER_CLASSES = []

    YAML1 = {'name': '1'}
    YAML2 = {'name': '2'}

    @staticmethod
    def YAML_SORT_KEY(n):
        return n['name']

    def setUp(self):
        from yaml import SafeLoader, Loader
        self.LOADER_CLASSES = [SafeLoader, Loader]
        try:
            from yaml import CSafeLoader
        except ImportError as err:
            print(err, file=stderr)
        else:
            self.LOADER_CLASSES.append(CSafeLoader)
        try:
            from yaml import CLoader
        except ImportError as err:
            print(err, file=stderr)
        else:
            self.LOADER_CLASSES.append(CLoader)

        for loader_cls in self.LOADER_CLASSES:
            YamlIncludeConstructor.add_to_loader_class(loader_cls)

    def test_include_single_in_top(self):
        yml = '''
!include tests/data/include.d/1.yaml
        '''
        for loader_cls in self.LOADER_CLASSES:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, self.YAML1)

    def test_include_non_ascii_single_in_top(self):
            yml = '''
    !include tests/data/zh_cn.yaml
            '''
            for loader_cls in self.LOADER_CLASSES:
                data = yaml.load(StringIO(yml), loader_cls)
                self.assertDictEqual(data, self.YAML1)

    def test_include_one_in_mapping(self):
        yml = '''
file1: !include tests/data/include.d/1.yaml
        '''
        for loader_cls in self.LOADER_CLASSES:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {'file1': self.YAML1})

    def test_include_two_in_mapping(self):
        yml = '''
file1: !include tests/data/include.d/1.yaml
file2: !include tests/data/include.d/2.yaml
        '''
        for loader_cls in self.LOADER_CLASSES:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {
                'file1': self.YAML1,
                'file2': self.YAML2,
            })

    def test_include_one_in_sequence(self):
        yml = '''
- !include tests/data/include.d/1.yaml
        '''
        for loader_cls in self.LOADER_CLASSES:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, [self.YAML1])

    def test_include_two_in_sequence(self):
        yml = '''
- !include tests/data/include.d/1.yaml
- !include tests/data/include.d/2.yaml
        '''
        for loader_cls in self.LOADER_CLASSES:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, [self.YAML1, self.YAML2])

    def test_include_file_not_exists(self):
        yml = '''
!include tests/data/include.d/x.yaml
            '''
        if _PYTHON_VERSION_MAYOR_MINOR >= '3.3':
            err_cls = FileNotFoundError
        else:
            err_cls = IOError
        for loader_cls in self.LOADER_CLASSES:
            with self.assertRaises(err_cls):
                yaml.load(StringIO(yml), loader_cls)

    def test_include_recursive(self):
        yml = '''
!include tests/data/0.yaml
            '''
        for loader_cls in self.LOADER_CLASSES:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {
                'files': [self.YAML1, self.YAML2],
                'file1': self.YAML1,
                'file2': self.YAML2,
            })

    def test_include_abs(self):
        dirpath = os.path.abspath('')
        yml = '''
!include {0}/tests/data/include.d/1.yaml
        '''.format(dirpath)
        for loader_cls in self.LOADER_CLASSES:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, self.YAML1)

    def test_include_wildcards(self):
        ymllist = ['''
!include tests/data/include.d/*.yaml
''']
        if _PYTHON_VERSION_MAYOR_MINOR >= '3.5':
            ymllist.extend(['''
!include [tests/data/include.d/**/*.yaml, true]
''', '''
!include {pathname: tests/data/include.d/**/*.yaml, recursive: true}
'''])
        for loader_cls in self.LOADER_CLASSES:
            for yml in ymllist:
                data = yaml.load(StringIO(yml), loader_cls)
                self.assertIsInstance(data, list)
                self.assertListEqual(
                    sorted(data, key=self.YAML_SORT_KEY),
                    [self.YAML1, self.YAML2]
                )


if __name__ == '__main__':
    unittest.main()
