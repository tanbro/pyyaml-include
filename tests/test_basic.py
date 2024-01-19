from __future__ import annotations
import unittest
from io import StringIO
from textwrap import dedent

import fsspec
import yaml

from yamlinclude import YamlInclude

from ._internal import YAML1, YAML2, YAML_LOADERS



class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if cls is BaseTestCase:
            raise unittest.SkipTest(f"{cls.__name__} is an abstract base class")
        else:
            super().setUpClass()

    def test_include_one_in_mapping(self):
        yml = """
file1: !inc include.d/1.yaml
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {"file1": YAML1})

    def test_continuous_including(self):
        yml = dedent(
            """
            foo:
                - !inc include.d/1.yaml
                - !inc include.d/2.yaml
            """
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {"foo": [YAML1, YAML2]})

    def test_include_two_in_mapping(self):
        yml = """
a: A
file1: !inc include.d/1.yaml
b: B
file2: !inc include.d/2.yaml
c: C
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(
                data,
                {
                    "a": "A",
                    "file1": YAML1,
                    "b": "B",
                    "file2": YAML2,
                    "c": "C",
                },
            )

    def test_include_one_in_sequence(self):
        yml = """
- !inc include.d/1.yaml
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, [YAML1])

    def test_include_two_in_sequence(self):
        yml = """
- a
- !inc include.d/1.yaml
- b
- !inc include.d/2.yaml
- c
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, ["a", YAML1, "b", YAML2, "c"])

    def test_include_file_not_exists(self):
        yml = """
file: !inc include.d/x.yaml
            """
        for loader_cls in YAML_LOADERS:
            with self.assertRaises(FileNotFoundError):
                yaml.load(StringIO(yml), loader_cls)

    def test_include_wildcards(self):
        yml = """
files: !inc include.d/*.yaml
"""
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(sorted(data["files"], key=lambda m: m["name"]), [YAML1, YAML2])

    def test_include_wildcards_1(self):
        yml = """
files: !inc [include.d/**/*.yaml, 3]
"""
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(sorted(data["files"], key=lambda m: m["name"]), [YAML1, YAML2])

    def test_include_wildcards_2(self):
        yml = """
files: !inc {pathname: include.d/**/*.yaml, maxdepth: 3}
"""
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(sorted(data["files"], key=lambda m: m["name"]), [YAML1, YAML2])


class DefaultFsBasicTestCase(BaseTestCase):
    def setUp(self):
        for loader_cls in YAML_LOADERS:
            ctor = YamlInclude(base_dir="tests/data")
            yaml.add_constructor("!inc", ctor, loader_cls)

    def tearDown(self):
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors["!inc"]


class FileFsBasicTestCase(BaseTestCase):
    def setUp(self):
        for loader_cls in YAML_LOADERS:
            ctor = YamlInclude(fs=fsspec.filesystem("file"), base_dir="tests/data")
            yaml.add_constructor("!inc", ctor, loader_cls)

    def tearDown(self):
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors["!inc"]


if __name__ == "__main__":
    unittest.main()
