import os
import unittest
from io import StringIO
from sys import version_info

import yaml

from yamlinclude import YamlIncludeConstructor

from ._internal import YAML1, YAML2, YAML_LOADERS


class DefaultLoaderTestCase(unittest.TestCase):
    def setUp(self):
        YamlIncludeConstructor.add_to_loader_class()

    if yaml.__version__ < "6.0":

        def test_no_loader_class_argument(self):
            yml = "!include tests/data/include.d/1.yaml"
            if yaml.__version__ >= "5.0" and version_info >= (3, 2):
                with self.assertWarns(yaml.YAMLLoadWarning):  # type: ignore
                    data = yaml.load(StringIO(yml))  # type: ignore
            else:
                data = yaml.load(StringIO(yml))  # type: ignore
            self.assertDictEqual(data, YAML1)


class MultiLoadersTestCase(unittest.TestCase):
    def setUp(self):
        for loader_cls in YAML_LOADERS:
            YamlIncludeConstructor.add_to_loader_class(loader_cls)

    def tearDown(self):
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors[YamlIncludeConstructor.DEFAULT_TAG_NAME]

    def test_include_one_in_mapping(self):
        yml = """
file1: !include tests/data/include.d/1.yaml
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {"file1": YAML1})

    def test_include_two_in_mapping(self):
        yml = """
file1: !include tests/data/include.d/1.yaml
file2: !include tests/data/include.d/2.yaml
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(
                data,
                {
                    "file1": YAML1,
                    "file2": YAML2,
                },
            )

    def test_include_one_in_sequence(self):
        yml = """
file:
    - !include tests/data/include.d/1.yaml
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {"file": [YAML1]})

    def test_include_two_in_sequence(self):
        yml = """
- !include tests/data/include.d/1.yaml
- !include tests/data/include.d/2.yaml
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, [YAML1, YAML2])

    def test_include_file_not_exists(self):
        yml = """
file: !include tests/data/include.d/x.yaml
            """
        if version_info >= (3, 3):
            err_cls = FileNotFoundError
        else:
            err_cls = IOError
        for loader_cls in YAML_LOADERS:
            with self.assertRaises(err_cls):
                yaml.load(StringIO(yml), loader_cls)

    def test_include_recursive(self):
        yml = """
file: !include tests/data/0.yaml
            """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(
                data["file"],
                {
                    "files": [YAML1, YAML2],
                    "file1": YAML1,
                    "file2": YAML2,
                },
            )

    def test_include_abs(self):
        dirpath = os.path.abspath("")
        yml = """
file: !include {0}/tests/data/include.d/1.yaml
        """.format(
            dirpath
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data["file"], YAML1)

    def test_include_wildcards(self):
        ymllist = [
            """
files: !include tests/data/include.d/*.yaml
"""
        ]
        if version_info >= (3, 5):
            ymllist.extend(
                [
                    """
files: !include [tests/data/include.d/**/*.yaml, true]
""",
                    """
files: !include {pathname: tests/data/include.d/**/*.yaml, recursive: true}
""",
                ]
            )
        for loader_cls in YAML_LOADERS:
            for yml in ymllist:
                data = yaml.load(StringIO(yml), loader_cls)
                self.assertListEqual(sorted(data["files"], key=lambda m: m["name"]), [YAML1, YAML2])


class JsonTestCase(unittest.TestCase):
    def setUp(self):
        for loader_cls in YAML_LOADERS:
            YamlIncludeConstructor.add_to_loader_class(loader_cls)

    def tearDown(self):
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors[YamlIncludeConstructor.DEFAULT_TAG_NAME]

    def test_include_one_in_mapping(self):
        yml = """
file1: !include tests/data/include.d/1.json
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {"file1": YAML1})

    def test_include_two_in_mapping(self):
        yml = """
file1: !include tests/data/include.d/1.json
file2: !include tests/data/include.d/2.json
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(
                data,
                {
                    "file1": YAML1,
                    "file2": YAML2,
                },
            )

    def test_include_one_in_sequence(self):
        yml = """
file:
    - !include tests/data/include.d/1.json
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {"file": [YAML1]})

    def test_include_two_in_sequence(self):
        yml = """
- !include tests/data/include.d/1.json
- !include tests/data/include.d/2.json
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, [YAML1, YAML2])

    def test_include_file_not_exists(self):
        yml = """
file: !include tests/data/include.d/x.json
            """
        if version_info >= (3, 3):
            err_cls = FileNotFoundError
        else:
            err_cls = IOError
        for loader_cls in YAML_LOADERS:
            with self.assertRaises(err_cls):
                yaml.load(StringIO(yml), loader_cls)

    def test_include_abs(self):
        dirpath = os.path.abspath("")
        yml = """
file: !include {0}/tests/data/include.d/1.json
        """.format(
            dirpath
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data["file"], YAML1)

    def test_include_wildcards(self):
        ymllist = [
            """
files: !include tests/data/include.d/*.json
"""
        ]
        if version_info >= (3, 5):
            ymllist.extend(
                [
                    """
files: !include [tests/data/include.d/**/*.json, true]
""",
                    """
files: !include {pathname: tests/data/include.d/**/*.yaml, recursive: true}
""",
                ]
            )
        for loader_cls in YAML_LOADERS:
            for yml in ymllist:
                data = yaml.load(StringIO(yml), loader_cls)
                self.assertListEqual(sorted(data["files"], key=lambda m: m["name"]), [YAML1, YAML2])


class TomlTestCase(unittest.TestCase):
    def setUp(self):
        for loader_cls in YAML_LOADERS:
            YamlIncludeConstructor.add_to_loader_class(loader_cls)

    def tearDown(self):
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors[YamlIncludeConstructor.DEFAULT_TAG_NAME]

    def test_include_one_in_mapping(self):
        yml = """
file1: !include tests/data/include.d/1.toml
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {"file1": YAML1})

    def test_include_two_in_mapping(self):
        yml = """
file1: !include tests/data/include.d/1.toml
file2: !include tests/data/include.d/2.toml
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(
                data,
                {
                    "file1": YAML1,
                    "file2": YAML2,
                },
            )

    def test_include_one_in_sequence(self):
        yml = """
file:
    - !include tests/data/include.d/1.toml
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {"file": [YAML1]})

    def test_include_two_in_sequence(self):
        yml = """
- !include tests/data/include.d/1.toml
- !include tests/data/include.d/2.toml
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, [YAML1, YAML2])

    def test_include_file_not_exists(self):
        yml = """
file: !include tests/data/include.d/x.toml
            """
        if version_info >= (3, 3):
            err_cls = FileNotFoundError
        else:
            err_cls = IOError
        for loader_cls in YAML_LOADERS:
            with self.assertRaises(err_cls):
                yaml.load(StringIO(yml), loader_cls)

    def test_include_abs(self):
        dirpath = os.path.abspath("")
        yml = """
file: !include {0}/tests/data/include.d/1.toml
        """.format(
            dirpath
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data["file"], YAML1)

    def test_include_wildcards(self):
        ymllist = [
            """
files: !include tests/data/include.d/*.toml
"""
        ]
        if version_info >= (3, 5):
            ymllist.extend(
                [
                    """
files: !include [tests/data/include.d/**/*.toml, true]
""",
                    """
files: !include {pathname: tests/data/include.d/**/*.yaml, recursive: true}
""",
                ]
            )
        for loader_cls in YAML_LOADERS:
            for yml in ymllist:
                data = yaml.load(StringIO(yml), loader_cls)
                self.assertListEqual(sorted(data["files"], key=lambda m: m["name"]), [YAML1, YAML2])


class PlainTextTestCase(unittest.TestCase):
    def setUp(self):
        YamlIncludeConstructor.add_to_loader_class()

    def test_txt(self):
        yml = "text: !include tests/data/include.d/1.txt"
        if yaml.__version__ >= "6.0":
            data = yaml.load(StringIO(yml), yaml.Loader)
        elif yaml.__version__ >= "5.0" and version_info >= (3, 2):
            with self.assertWarns(yaml.YAMLLoadWarning):  # type: ignore
                data = yaml.load(StringIO(yml))  # type: ignore
        else:
            data = yaml.load(StringIO(yml))  # type: ignore
        with open("tests/data/include.d/1.txt") as fp:
            s = fp.read()
        self.assertDictEqual(data, {"text": s})


class ReaderTestCase(unittest.TestCase):
    def setUp(self):
        YamlIncludeConstructor.add_to_loader_class()

    def test_txt(self):
        yml = "text: !include {pathname: tests/data/include.d/1.json, reader: txt}"
        if yaml.__version__ >= "6.0":
            data = yaml.load(StringIO(yml), yaml.Loader)
        elif "6.0" > yaml.__version__ >= "5.0" and version_info >= (3, 2):
            with self.assertWarns(yaml.YAMLLoadWarning):  # type: ignore
                data = yaml.load(StringIO(yml))  # type: ignore
        else:
            data = yaml.load(StringIO(yml))  # type: ignore
        with open("tests/data/include.d/1.json") as fp:
            s = fp.read()
        self.assertDictEqual(data, {"text": s})


if __name__ == "__main__":
    unittest.main()
