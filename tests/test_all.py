from __future__ import unicode_literals, absolute_import

import os
import unittest
from io import StringIO
from sys import version_info

_PYTHON_VERSION_MAYOR_MINOR = '{0[0]}.{0[1]}'.format(version_info)

import yaml

from yamlinclude import YamlIncludeConstructor


class YamlIncludeTestCase(unittest.TestCase):
    LOADERS = []

    def setUp(self):
        from yaml import SafeLoader, Loader
        self.LOADERS = [SafeLoader, Loader]
        try:
            from yaml import CSafeLoader
        except ImportError:
            pass
        else:
            self.LOADERS.append(CSafeLoader)
        try:
            from yaml import CLoader
        except ImportError:
            pass
        else:
            self.LOADERS.append(CLoader)
        for loader in self.LOADERS:
            loader.add_constructor(YamlIncludeConstructor.DEFAULT_TAG, YamlIncludeConstructor())

    def test_include_single_in_top(self):
        yml = '''
!include tests/data/include.d/1.yaml
        '''
        for loader in self.LOADERS:
            data = yaml.load(StringIO(yml), loader)
            self.assertDictEqual(data, {'name': '1'})

    def test_include_one_in_mapping(self):
        yml = '''
file1: !include tests/data/include.d/1.yaml
        '''
        for loader in self.LOADERS:
            data = yaml.load(StringIO(yml), loader)
            self.assertDictEqual(data, {'file1': {'name': '1'}})

    def test_include_two_in_mapping(self):
        yml = '''
file1: !include tests/data/include.d/1.yaml
file2: !include tests/data/include.d/2.yaml
        '''
        for loader in self.LOADERS:
            data = yaml.load(StringIO(yml), loader)
            self.assertDictEqual(data, {
                'file1': {'name': '1'},
                'file2': {'name': '2'},
            })

    def test_include_one_in_sequence(self):
        yml = '''
- !include tests/data/include.d/1.yaml
        '''
        for loader in self.LOADERS:
            data = yaml.load(StringIO(yml), loader)
            self.assertListEqual(data, [{'name': '1'}])

    def test_include_two_in_sequence(self):
        yml = '''
- !include tests/data/include.d/1.yaml
- !include tests/data/include.d/2.yaml
        '''
        for loader in self.LOADERS:
            data = yaml.load(StringIO(yml), loader)
            self.assertListEqual(data, [{'name': '1'}, {'name': '2'}])

    def test_include_recursive(self):
        yml = '''
!include tests/data/0.yaml
            '''
        for loader in self.LOADERS:
            data = yaml.load(StringIO(yml), loader)
            self.assertDictEqual(data, {
                'files': [{'name': '1'}, {'name': '2'}],
                'file1': {'name': '1'},
                'file2': {'name': '2'}
            })

    def test_include_abs(self):
        dirpath = os.path.abspath('')
        yml = '''
!include {0}/tests/data/include.d/1.yaml
        '''.format(dirpath)
        for loader in self.LOADERS:
            data = yaml.load(StringIO(yml), loader)
            self.assertDictEqual(data, {'name': '1'})

    def test_include_wildcards(self):
        yml = '''
!include tests/data/include.d/*.yaml
        '''
        for loader in self.LOADERS:
            data = yaml.load(StringIO(yml), loader)
            self.assertIsInstance(data, list)
            self.assertListEqual(sorted(data, key=lambda n: n['name']), [{'name': '1'}, {'name': '2'}])

    if _PYTHON_VERSION_MAYOR_MINOR >= '3.5':

        def test_include_recursive_seqargs(self):
            yml = '''
!include [tests/data/include.d/**/*.yaml, true]
            '''
            for loader in self.LOADERS:
                data = yaml.load(StringIO(yml), loader)
                self.assertIsInstance(data, list)
                self.assertListEqual(sorted(data, key=lambda n: n['name']), [{'name': '1'}, {'name': '2'}])

        def test_include_recursive_namedargs(self):
            yml = '''
!include {pathname: tests/data/include.d/**/*.yaml, recursive: true}
            '''
            for loader in self.LOADERS:
                data = yaml.load(StringIO(yml), loader)
                self.assertIsInstance(data, list)
                self.assertListEqual(sorted(data, key=lambda n: n['name']), [{'name': '1'}, {'name': '2'}])


if __name__ == '__main__':
    unittest.main()
