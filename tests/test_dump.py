import unittest
from textwrap import dedent

import yaml
from yamlinclude import (
    YamlIncludeData,
    YamlIncludeCtor,
    YamlIncludeRepr,
    yamlinclude_load,
    yamlinclude_lazy_load,
)

from ._internal import YAML_DUMPERS, YAML_LOADERS, YAML1, YAML2


class DumpTestCase(unittest.TestCase):
    ctor = YamlIncludeCtor(base_dir="tests/data", autoload=False)
    repr = YamlIncludeRepr("inc")

    @classmethod
    def setUpClass(cls):
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", cls.ctor, loader_cls)
        for dumper_cls in YAML_DUMPERS:
            yaml.add_representer(YamlIncludeData, cls.repr, dumper_cls)

    @classmethod
    def tearDownClass(cls) -> None:
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors["!inc"]
        for dumper_cls in YAML_DUMPERS:
            del dumper_cls.yaml_representers[YamlIncludeData]

    def test_extract(self):
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
            d = yaml.load(yaml_string, loader_cls)
            for dumper_cls in YAML_DUMPERS:
                s = yaml.dump(d, None, dumper_cls)
                d1 = yaml.load(s, loader_cls)
                d2 = yamlinclude_load(d1, loader_cls, self.ctor)
                self.assertDictEqual(YAML1, d2["list"][0])
                self.assertDictEqual(YAML2, d2["list"][1])
                self.assertDictEqual(YAML1, d2["dict"]["yaml1"])
                self.assertDictEqual(YAML2, d2["dict"]["yaml2"])

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
            d = yaml.load(yaml_string, loader_cls)
            for dumper_cls in YAML_DUMPERS:
                s = yaml.dump(d, None, dumper_cls)
                d1 = yaml.load(s, loader_cls)
                yamlinclude_load(d1, loader_cls, self.ctor, inplace=True)
                self.assertDictEqual(YAML1, d1["list"][0])
                self.assertDictEqual(YAML2, d1["list"][1])
                self.assertDictEqual(YAML1, d1["dict"]["yaml1"])
                self.assertDictEqual(YAML2, d1["dict"]["yaml2"])

    def test_iterable(self):
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
            d = yaml.load(yaml_string, loader_cls)
            for dumper_cls in YAML_DUMPERS:
                s = yaml.dump(d, None, dumper_cls)
                d1 = yaml.load(s, loader_cls)

                for _ in yamlinclude_lazy_load(d1, loader_cls, self.ctor):
                    pass
                self.assertDictEqual(YAML1, d1["list"][0])
                self.assertDictEqual(YAML2, d1["list"][1])
                self.assertDictEqual(YAML1, d1["dict"]["yaml1"])
                self.assertDictEqual(YAML2, d1["dict"]["yaml2"])
