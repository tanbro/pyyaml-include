import io
import unittest
from textwrap import dedent

import yaml

from yamlinclude import YamlIncludeConstructor


# Required for new reader_table
class Reader(object):
    # pylint: disable=too-few-public-methods
    def __init__(self, path, encoding, *args, **kwargs):  # pylint:disable=unused-argument
        self._path = path
        self._encoding = encoding

    def __call__(self):
        raise NotImplementedError()


# Required for new reader_table


class YamlReader(Reader):
    # pylint: disable=too-few-public-methods
    def __init__(self, path, encoding, loader, *args, **kwargs):  # pylint:disable=unused-argument
        super(YamlReader, self).__init__(path, encoding)
        self._loader_class = type(loader)

    def __call__(self):
        with io.open(self._path, encoding=self._encoding) as fp:
            return yaml.load(fp, self._loader_class)  # type: ignore


class CustomReaderTestCase(unittest.TestCase):
    YAML_STRING = dedent(
        """
        1_yml: !inc tests/data/include.d/1.yaml
        2_yml: !inc tests/data/include.d/2.yaml
        1_j2: !inc tests/data/include.d/1.j2
        2_j2: !inc tests/data/include.d/2.j2
        """
    )

    @classmethod
    def setUpClass(cls):
        reader_table = [
            (r"^.+\.(([yY][mM][lL])|([Yy][aA][mM][lL]))$", YamlReader),
            (r"^.+\.([j][2])$", YamlReader),
        ]
        constructor = YamlIncludeConstructor(reader_map=reader_table)
        yaml.FullLoader.add_constructor("!inc", constructor)

    def test_custom_reader(self):
        # Read the main yaml file and include the other yaml files.
        yaml.load(self.YAML_STRING, Loader=yaml.FullLoader)
