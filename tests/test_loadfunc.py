import unittest
from textwrap import dedent

import yaml

from yaml_include import (
    Constructor,
    lazy_load,
    load,
)

from ._internal import YAML1, YAML2, YAML_LOADERS


class LoadFuncTestCase(unittest.TestCase):
    ctor = Constructor(base_dir="tests/data", autoload=False)

    @classmethod
    def setUpClass(cls):
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", cls.ctor, loader_cls)

    @classmethod
    def tearDownClass(cls) -> None:
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors["!inc"]  # type: ignore[attr-defined]

    def test_normal(self):
        yaml_string = dedent(
            """
            list:
                - !inc include.d/1.yaml
                - !inc include.d/2.yaml
            dict:
                yaml1: !inc include.d/1.yaml
                yaml2: !inc include.d/2.yaml
            """
        ).strip()
        for loader_cls in YAML_LOADERS:
            d0 = yaml.load(yaml_string, loader_cls)
            d1 = load(d0, loader_cls, self.ctor)
            self.assertDictEqual(YAML1, d1["list"][0])
            self.assertDictEqual(YAML2, d1["list"][1])
            self.assertDictEqual(YAML1, d1["dict"]["yaml1"])
            self.assertDictEqual(YAML2, d1["dict"]["yaml2"])

    def test_inplace(self):
        yaml_string = dedent(
            """
            list:
                - !inc include.d/1.yaml
                - !inc include.d/2.yaml
            dict:
                yaml1: !inc include.d/1.yaml
                yaml2: !inc include.d/2.yaml
            """
        ).strip()
        for loader_cls in YAML_LOADERS:
            d0 = yaml.load(yaml_string, loader_cls)
            load(d0, loader_cls, self.ctor, inplace=True)
            self.assertDictEqual(YAML1, d0["list"][0])
            self.assertDictEqual(YAML2, d0["list"][1])
            self.assertDictEqual(YAML1, d0["dict"]["yaml1"])
            self.assertDictEqual(YAML2, d0["dict"]["yaml2"])

    def test_nested(self):
        yaml_string = dedent(
            """
            nested: !inc nested.yaml
            """
        ).strip()
        for loader_cls in YAML_LOADERS:
            d0 = yaml.load(yaml_string, loader_cls)
            d1 = load(d0, loader_cls, self.ctor, nested=True)
            self.assertDictEqual(YAML1, d1["nested"]["list"][0])
            self.assertDictEqual(YAML2, d1["nested"]["list"][1])
            self.assertDictEqual(YAML1, d1["nested"]["dict"]["yaml1"])
            self.assertDictEqual(YAML2, d1["nested"]["dict"]["yaml2"])

    def test_inplace_nested(self):
        yaml_string = dedent(
            """
            nested: !inc nested.yaml
            """
        ).strip()
        for loader_cls in YAML_LOADERS:
            d0 = yaml.load(yaml_string, loader_cls)
            load(d0, loader_cls, self.ctor, inplace=True, nested=True)
            self.assertDictEqual(YAML1, d0["nested"]["list"][0])
            self.assertDictEqual(YAML2, d0["nested"]["list"][1])
            self.assertDictEqual(YAML1, d0["nested"]["dict"]["yaml1"])
            self.assertDictEqual(YAML2, d0["nested"]["dict"]["yaml2"])


class LazyLoadFuncTestCase(unittest.TestCase):
    ctor = Constructor(base_dir="tests/data", autoload=False)

    @classmethod
    def setUpClass(cls):
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", cls.ctor, loader_cls)

    @classmethod
    def tearDownClass(cls) -> None:
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors["!inc"]  # type: ignore[attr-defined]

    def test_inplace(self):
        yaml_string = dedent(
            """
            list:
                - !inc include.d/1.yaml
                - !inc include.d/2.yaml
            dict:
                yaml1: !inc include.d/1.yaml
                yaml2: !inc include.d/2.yaml
            """
        ).strip()
        for loader_cls in YAML_LOADERS:
            d0 = yaml.load(yaml_string, loader_cls)
            for _ in lazy_load(d0, loader_cls, self.ctor):
                pass
            self.assertDictEqual(YAML1, d0["list"][0])
            self.assertDictEqual(YAML2, d0["list"][1])
            self.assertDictEqual(YAML1, d0["dict"]["yaml1"])
            self.assertDictEqual(YAML2, d0["dict"]["yaml2"])

    def test_inplace_nested(self):
        yaml_string = dedent(
            """
            nested: !inc nested.yaml
            """
        ).strip()
        for loader_cls in YAML_LOADERS:
            d0 = yaml.load(yaml_string, loader_cls)
            for _ in lazy_load(d0, loader_cls, self.ctor, nested=True):
                pass
            self.assertDictEqual(YAML1, d0["nested"]["list"][0])
            self.assertDictEqual(YAML2, d0["nested"]["list"][1])
            self.assertDictEqual(YAML1, d0["nested"]["dict"]["yaml1"])
            self.assertDictEqual(YAML2, d0["nested"]["dict"]["yaml2"])
