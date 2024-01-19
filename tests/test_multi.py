import unittest
from textwrap import dedent

import yaml

from yamlinclude import YamlInclude

YAML1 = {"name": "1"}
YAML2 = {"name": "2"}


class MultiLoaderTestCase(unittest.TestCase):
    constructor = YamlInclude(base_dir="tests/data")

    def setUp(self):
        yaml.add_constructor("!inc", self.constructor)

    def test_full_load_all_yaml(self):
        txt = dedent(
            """
            ---
            file1: !inc include.d/1.yaml

            ---
            file2: !inc include.d/2.yaml
            """
        ).strip()
        iterable = yaml.full_load_all(txt)
        for i, data in enumerate(iterable):
            if i == 0:
                self.assertDictEqual(data, {"file1": YAML1})
            elif i == 1:
                self.assertDictEqual(data, {"file2": YAML2})
            else:
                raise RuntimeError()
