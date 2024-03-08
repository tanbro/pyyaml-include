import unittest
from textwrap import dedent

import yaml
from yamlinclude import YamlIncludeData, YamlIncludeCtor, YamlIncludeRepr

from ._internal import YAML_DUMPERS, YAML_LOADERS


class DumpTestCase(unittest.TestCase):
    base_dir = "tests/data"

    @classmethod
    def setUpClass(cls):
        ctor = YamlIncludeCtor(base_dir=cls.base_dir, auto_load=False)
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", ctor, loader_cls)
        repr_ = YamlIncludeRepr("inc")
        for dumper_cls in YAML_DUMPERS:
            yaml.add_representer(YamlIncludeData, repr_, dumper_cls)

    @classmethod
    def tearDownClass(cls) -> None:
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors["!inc"]
        for dumper_cls in YAML_DUMPERS:
            del dumper_cls.yaml_representers[YamlIncludeData]

    def test_serialize(self):
        yaml_string = dedent(
            """
            yaml1: !inc {urlpath: include.d/1.yaml, maxdepth: 4}
            yaml2: !inc {urlpath: include.d/2.yaml, maxdepth: 4}
            """
        ).strip()
        for loader_cls in YAML_LOADERS:
            d = yaml.load(yaml_string, loader_cls)
            for dumper_cls in YAML_DUMPERS:
                s = yaml.dump(d, None, dumper_cls)
                d1 = yaml.load(s, loader_cls)
                print(s)
                print(d1)
                print()
                print()
                self.assertDictEqual(d, d1)
