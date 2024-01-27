import unittest
from textwrap import dedent

import yaml

from yamlinclude import YamlIncludeCtor

from ._internal import YAML1, YAML2, YAML_LOADERS


class MultiLoaderTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ctor = YamlIncludeCtor(base_dir="tests/data")
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", ctor, loader_cls)

    @classmethod
    def tearDownClass(cls) -> None:
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors["!inc"]

    def test_load_all(self):
        yml_txt = dedent(
            """
            ---
            data: !inc include.d/1.yaml

            ---
            data: !inc include.d/2.yaml
            """
        )
        for Loader in YAML_LOADERS:
            for i, data in enumerate(yaml.load_all(yml_txt, Loader)):
                if i == 0:
                    self.assertDictEqual(data, {"data": YAML1})
                elif i == 1:
                    self.assertDictEqual(data, {"data": YAML2})
                else:
                    raise RuntimeError()
