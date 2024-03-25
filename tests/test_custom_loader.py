from pathlib import Path
import unittest
import json
from textwrap import dedent
import yaml

from yaml_include import Constructor


from ._internal import YAML_LOADERS


class DummyLoaderTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ctor = Constructor(base_dir="tests/data", custom_loader=cls.my_loader)
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", ctor, loader_cls)

    @classmethod
    def my_loader(cls, path, file, *args, **kwargs):
        return "EMPTY"

    def test_1(self):
        yml = dedent(
            """
            content: !inc empty
            """
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(yml, loader_cls)
            self.assertEqual(data["content"], "EMPTY")


class JsonLoaderTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ctor = Constructor(
            base_dir="tests/data",
            custom_loader=lambda path, file, *args, **kwargs: cls.json_loader(file),
        )
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", ctor, loader_cls)

    @classmethod
    def json_loader(cls, file):
        return json.load(file)

    def test_1(self):
        with open("tests/data/include.d/1.json") as fp:
            d0 = json.load(fp)
        yml = dedent(
            """
            content: !inc include.d/1.json
            """
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(yml, loader_cls)
            d1 = data["content"]
            self.assertDictEqual(d0, d1)


class JsonYamlLoaderTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ctor = Constructor(
            base_dir="tests/data",
            custom_loader=cls.my_loader,
        )
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", ctor, loader_cls)

    @classmethod
    def my_loader(cls, path, file, loader_type, *args, **kwargs):
        path = file.path

        if Path(path).suffix == ".json":
            return json.load(file)
        if Path(path).suffix in (".yaml", "yml"):
            return yaml.load(file, loader_type)
        return RuntimeError(f"not supported file ‘{path}’ ({file})")

    def test_json_wildcards(self):
        with open("tests/data/include.d/1.json") as fp:
            d1 = json.load(fp)
        with open("tests/data/include.d/2.json") as fp:
            d2 = json.load(fp)
        yml = dedent(
            """
            content: !inc include.d/*.json
            """
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(yml, loader_cls)
            self.assertListEqual(sorted(data["content"], key=lambda m: m["name"]), [d1, d2])

    def test_yaml_wildcards(self):
        with open("tests/data/include.d/1.yaml") as fp:
            d1 = yaml.full_load(fp)
        with open("tests/data/include.d/2.yaml") as fp:
            d2 = yaml.full_load(fp)
        yml = dedent(
            """
            content: !inc include.d/*.yaml
            """
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(yml, loader_cls)
            self.assertListEqual(sorted(data["content"], key=lambda m: m["name"]), [d1, d2])

    def test_json_yaml(self):
        with open("tests/data/include.d/1.json") as fp:
            d1 = json.load(fp)
        with open("tests/data/include.d/2.yaml") as fp:
            d2 = yaml.full_load(fp)
        yml = dedent(
            """
            - !inc include.d/1.json
            - !inc include.d/2.yaml
            """
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(yml, loader_cls)
            self.assertListEqual(data, [d1, d2])

    def test_json_yaml_full_url(self):
        with open("tests/data/include.d/1.json") as fp:
            d1 = json.load(fp)
        with open("tests/data/include.d/2.yaml") as fp:
            d2 = yaml.full_load(fp)
        yml = dedent(
            f"""
            - !inc file://{Path().absolute().as_posix()}/tests/data/include.d/1.json
            - !inc file://{Path().absolute().as_posix()}/tests/data/include.d/2.yaml
            """
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(yml, loader_cls)
            self.assertListEqual(data, [d1, d2])

    def test_json_yaml_wildcards(self):
        with open("tests/data/include.d/1.json") as fp:
            json1 = json.load(fp)
        with open("tests/data/include.d/2.json") as fp:
            json2 = json.load(fp)
        with open("tests/data/include.d/1.yaml") as fp:
            yaml1 = yaml.full_load(fp)
        with open("tests/data/include.d/2.yaml") as fp:
            yaml2 = yaml.full_load(fp)
        yml = dedent(
            f"""
            !inc file://{Path().absolute().as_posix()}/tests/data/include.d/*
            """
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(yml, loader_cls)
            self.assertListEqual(sorted(data, key=lambda m: m["name"]), [json1, yaml1, json2, yaml2])


if __name__ == "__main__":
    unittest.main()
