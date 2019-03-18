# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os
import unittest
from io import StringIO
from sys import stderr, version_info

import yaml

from yamlinclude import YamlIncludeConstructor

_PYTHON_VERSION_MAYOR_MINOR = '{0[0]}.{0[1]}'.format(version_info)


class AddToMultiLoaderTestCase(unittest.TestCase):
    YAML1 = {'name': '1'}
    YAML2 = {'name': '2'}
    YAML_ZH_CN = {'name': '中文'}

    @staticmethod
    def YAML_SORT_KEY(n):
        return n['name']

    def setUp(self):
        if yaml.__version__ < '4.0':
            from yaml import BaseLoader, SafeLoader, Loader
            self.loader_classes = [BaseLoader, SafeLoader, Loader]
        elif yaml.__version__ >= '5.0':
            from yaml import BaseLoader, SafeLoader, Loader, FullLoader
            self.loader_classes = [BaseLoader, SafeLoader, Loader, FullLoader]
        else:
            raise RuntimeError('Un-supported pyyaml version')

        try:
            from yaml import CBaseLoader, CSafeLoader, CLoader
        except ImportError as err:
            print(err, file=stderr)
        else:
            self.loader_classes.append(CLoader)

        for loader_cls in self.loader_classes:
            YamlIncludeConstructor.add_to_loader_class(loader_cls)

    def test_include_single_in_top(self):
        yml = '''
!include tests/data/include.d/1.yaml
        '''
        for loader_cls in self.loader_classes:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, self.YAML1)

    def test_include_non_ascii_single_in_top(self):
        yml = '''
!include tests/data/zh_cn.yaml
            '''
        for loader_cls in self.loader_classes:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, self.YAML_ZH_CN)

    def test_include_one_in_mapping(self):
        yml = '''
file1: !include tests/data/include.d/1.yaml
        '''
        for loader_cls in self.loader_classes:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {'file1': self.YAML1})

    def test_include_two_in_mapping(self):
        yml = '''
file1: !include tests/data/include.d/1.yaml
file2: !include tests/data/include.d/2.yaml
        '''
        for loader_cls in self.loader_classes:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {
                'file1': self.YAML1,
                'file2': self.YAML2,
            })

    def test_include_one_in_sequence(self):
        yml = '''
- !include tests/data/include.d/1.yaml
        '''
        for loader_cls in self.loader_classes:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, [self.YAML1])

    def test_include_two_in_sequence(self):
        yml = '''
- !include tests/data/include.d/1.yaml
- !include tests/data/include.d/2.yaml
        '''
        for loader_cls in self.loader_classes:
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
        for loader_cls in self.loader_classes:
            with self.assertRaises(err_cls):
                yaml.load(StringIO(yml), loader_cls)

    def test_include_recursive(self):
        yml = '''
!include tests/data/0.yaml
            '''
        for loader_cls in self.loader_classes:
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
        for loader_cls in self.loader_classes:
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
        for loader_cls in self.loader_classes:
            for yml in ymllist:
                data = yaml.load(StringIO(yml), loader_cls)
                self.assertIsInstance(data, list)
                self.assertListEqual(
                    sorted(data, key=self.YAML_SORT_KEY),
                    [self.YAML1, self.YAML2]
                )


if __name__ == '__main__':
    unittest.main()
