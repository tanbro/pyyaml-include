import unittest
from textwrap import dedent

import yaml
from yamlinclude import YamlIncludeCtor, YamlIncludeData

from ._internal import YAML_LOADERS


class DataClassTestCase(unittest.TestCase):
    ctor = YamlIncludeCtor(base_dir="tests/data")

    @classmethod
    def setUpClass(cls):
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", cls.ctor, loader_cls)

    @classmethod
    def tearDownClass(cls) -> None:
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors["!inc"]

    def test_simple_managed_autoload(self):
        yaml_string = dedent(
            """
            yaml1: !inc include.d/1.yaml
            """
        ).strip()
        for loader_cls in YAML_LOADERS:
            with self.ctor.managed_autoload(False):
                d = yaml.load(yaml_string, loader_cls)
                self.assertIsInstance(d["yaml1"], YamlIncludeData)
                self.assertEqual(d["yaml1"].urlpath, "include.d/1.yaml")
