import unittest
from textwrap import dedent

import yaml
from yaml_include import Constructor

from ._internal import YAML_LOADERS


class DataClassTestCase(unittest.TestCase):
    ctor = Constructor(base_dir="tests/data")

    @classmethod
    def setUpClass(cls):
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", cls.ctor, loader_cls)

    def test_one(self):
        yml_txt = dedent(
            """
            root: !inc include2.d/0.yml
            """
        )
        data = yaml.load(yml_txt, yaml.Loader)
        self.assertDictEqual(
            data,
            {
                "root": {
                    "1": {"value": "1"},
                    "a": {"deep": {"path": {"test": {"1": {"value": "1"}}}}},
                }
            },
        )
