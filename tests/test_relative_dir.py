# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, print_function

import os
import unittest
from io import BytesIO, StringIO
from textwrap import dedent

from contextlib import suppress
import yaml
import tempfile

from yamlinclude import YamlIncludeConstructor
from yamlinclude.constructor import YamlIncludeFileTypeException, YamlIncludeLibYamlException
from _internel import PYTHON_VERSION_MAYOR_MINOR, YAML_LOADERS, YAML1, YAML2


EXAMPLE_DIR = "tests/data/include.d"


class BaseRelativeDirTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.mkdtemp()
        cls.addClassCleanup(lambda: os.rmdir(cls._tmpdir))
        cls._include_path = os.path.join(cls._tmpdir, "include.d")
        os.mkdir(cls._include_path)
        cls.addClassCleanup(lambda: os.rmdir(cls._include_path))
        files = os.listdir(EXAMPLE_DIR)
        for example_file in files:
            with open(os.path.join(EXAMPLE_DIR, example_file)) as f:
                _content = f.read()
            with open(os.path.join(cls._include_path, example_file), "w") as f:
                f.write(_content)
            cls.addClassCleanup(lambda: os.remove(os.path.join(cls._include_path, example_file)))

    def create_yaml(self, yml):
        test_file_path = os.path.join(self._tmpdir, "test.yml")
        with open(test_file_path, "w") as f:
            f.write(yml)

        def remove_yaml():
            with suppress(FileNotFoundError):
                os.remove(test_file_path)

        self.addCleanup(remove_yaml)
        f = open(test_file_path, "r")
        self.addCleanup(lambda: f.close())

        return f


class RelativeDirTestCase(BaseRelativeDirTestCase):
    non_c_loaders = [loader for loader in YAML_LOADERS if loader.__module__ != "yaml.cyaml"]

    def setUp(self):
        for loader_cls in self.non_c_loaders:
            YamlIncludeConstructor.add_to_loader_class(loader_cls, relative=True)

    def tearDown(self):
        for loader_class in self.non_c_loaders:
            del loader_class.yaml_constructors[YamlIncludeConstructor.DEFAULT_TAG_NAME]

    def test_include_one_in_mapping(self):
        yml = '''
file1: !include include.d/1.yaml
        '''
        for loader_cls in self.non_c_loaders:
            data = yaml.load(self.create_yaml(yml), loader_cls)
            self.assertDictEqual(data, {'file1': YAML1})

    def test_continuous_including(self):
        yml = dedent('''
        foo:
            - !include include.d/1.yaml
            - !include include.d/2.yaml
        ''')
        for loader_cls in self.non_c_loaders:
            data = yaml.load(self.create_yaml(yml), loader_cls)
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
        for loader_cls in self.non_c_loaders:
            data = yaml.load(self.create_yaml(yml), loader_cls)
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
        for loader_cls in self.non_c_loaders:
            data = yaml.load(self.create_yaml(yml), loader_cls)
            self.assertListEqual(data, [YAML1])

    def test_include_two_in_sequence(self):
        yml = '''
- a
- !include include.d/1.yaml
- b
- !include include.d/2.yaml
- c
        '''
        for loader_cls in self.non_c_loaders:
            data = yaml.load(self.create_yaml(yml), loader_cls)
            self.assertListEqual(data, ['a', YAML1, 'b', YAML2, 'c'])

    def test_include_file_not_exists(self):
        yml = '''
file: !include include.d/x.yaml
            '''
        if PYTHON_VERSION_MAYOR_MINOR >= '3.3':
            err_cls = FileNotFoundError
        else:
            err_cls = IOError
        for loader_cls in self.non_c_loaders:
            with self.assertRaises(err_cls):
                yaml.load(self.create_yaml(yml), loader_cls)

    def test_include_wildcards(self):
        yml = '''
files: !include include.d/*.yaml
'''
        for loader_cls in self.non_c_loaders:
            data = yaml.load(self.create_yaml(yml), loader_cls)
            self.assertListEqual(
                sorted(data['files'], key=lambda m: m['name']),
                [YAML1, YAML2]
            )

    if PYTHON_VERSION_MAYOR_MINOR >= '3.5':

        def test_include_wildcards_1(self):
            yml = '''
files: !include [include.d/**/*.yaml, true]
'''
            for loader_cls in self.non_c_loaders:
                data = yaml.load(self.create_yaml(yml), loader_cls)
                self.assertListEqual(
                    sorted(data['files'], key=lambda m: m['name']),
                    [YAML1, YAML2]
                )

        def test_include_wildcards_2(self):
            yml = '''
files: !include {pathname: include.d/**/*.yaml, recursive: true}
'''
            for loader_cls in self.non_c_loaders:
                data = yaml.load(self.create_yaml(yml), loader_cls)
                self.assertListEqual(
                    sorted(data['files'], key=lambda m: m['name']),
                    [YAML1, YAML2]
                )


class LibYamlExceptionRelativeDirExceptionTest(BaseRelativeDirTestCase):
    c_loaders = [loader for loader in YAML_LOADERS if loader.__module__ == "yaml.cyaml"]

    def setUp(self):
        for loader_cls in self.c_loaders:
            YamlIncludeConstructor.add_to_loader_class(loader_cls, relative=True)

    def tearDown(self):
        for loader_class in self.c_loaders:
            del loader_class.yaml_constructors[YamlIncludeConstructor.DEFAULT_TAG_NAME]

    def test_c_loaders(self):
        yml = '''
file1: !include include.d/1.yaml
        '''
        for loader_cls in self.c_loaders:
            with self.assertRaises(YamlIncludeLibYamlException):
                yaml.load(self.create_yaml(yml), loader_cls)


class FileTypeExceptionRelativeDirExceptionTest(BaseRelativeDirTestCase):
    non_c_loaders = [loader for loader in YAML_LOADERS if loader.__module__ != "yaml.cyaml"]

    def setUp(self):
        for loader_cls in self.non_c_loaders:
            YamlIncludeConstructor.add_to_loader_class(loader_cls, relative=True)

    def tearDown(self):
        for loader_class in self.non_c_loaders:
            del loader_class.yaml_constructors[YamlIncludeConstructor.DEFAULT_TAG_NAME]

    def test_stringio(self):
        yml = '''
file1: !include include.d/1.yaml
        '''
        for loader_cls in self.non_c_loaders:
            with self.assertRaises(YamlIncludeFileTypeException):
                yaml.load(StringIO(yml), loader_cls)

    def test_bytesio(self):
        yml = '''
file1: !include include.d/1.yaml
        '''
        for loader_cls in self.non_c_loaders:
            with self.assertRaises(YamlIncludeFileTypeException):
                yaml.load(BytesIO(yml.encode("utf-8")), loader_cls)
