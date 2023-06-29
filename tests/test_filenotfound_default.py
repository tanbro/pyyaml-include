import os
import unittest
from io import StringIO
from textwrap import dedent

import yaml

from yamlinclude import YamlIncludeConstructor

from ._internal import YAML_LOADERS


class DefaultValueTestCase(unittest.TestCase):
    def setUp(self):
        for loader_cls in YAML_LOADERS:
            YamlIncludeConstructor.add_to_loader_class(loader_cls, base_dir=os.path.join("tests", "data"))

    def tearDown(self):
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors[YamlIncludeConstructor.DEFAULT_TAG_NAME]

    def test_include_string_default(self):
        yml = dedent(
            """
            file1: !include {pathname: include.d/not_exist.yaml, default: not found}
            """
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {"file1": "not found"})

    def test_include_one_notfound(self):
        yml = dedent(
            """
            file1: !include include.d/not_exist.yaml
            """
        )
        for loader_cls in YAML_LOADERS:
            with self.assertRaises(FileNotFoundError):
                yaml.load(StringIO(yml), loader_cls)

    def test_include_two_default(self):
        yml = dedent(
            """
            file1: !include {pathname: include.d/not_exist_1.yaml, default: boo1}
            file2: !include {pathname: include.d/not_exist_2.yaml, default: boo2}
            """
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {"file1": "boo1", "file2": "boo2"})

    def test_include_one_default_one_notfound(self):
        yml = dedent(
            """
            file1: !include {pathname: include.d/not_exist_1.yaml, default: "boo1"}
            file2: !include {pathname: include.d/not_exist_2.yaml}
            """
        )
        for loader_cls in YAML_LOADERS:
            with self.assertRaises(FileNotFoundError):
                yaml.load(StringIO(yml), loader_cls)

    def test_include_non_scalar_default(self):
        yml = dedent(
            """
            file1: !include {pathname: include.d/not_exist1.yaml, default: []}
            file2: !include {pathname: include.d/not_exist2.yaml, default: {}}
            """
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(
                data,
                {
                    "file1": [],
                    "file2": {},
                },
            )


if __name__ == "__main__":
    unittest.main()
