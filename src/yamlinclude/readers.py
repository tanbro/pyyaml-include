# -*- coding: utf-8 -*-

"""readers for different type of files
"""

import json
import re

try:
    import tomllib
except ImportError:
    tomllib = None
from configparser import ConfigParser
from typing import Type

import yaml

try:
    import toml
except ImportError:
    toml = None

__all__ = [
    "READER_TABLE",
    "get_reader_class_by_path",
    "get_reader_class_by_name",
    "Reader",
    "IniReader",
    "JsonReader",
    "TomlReader",
    "YamlReader",
    "PlainTextReader",
]


class Reader:
    def __init__(self, path, encoding, *args, **kwargs):
        self._path = path
        self._encoding = encoding

    def __call__(self):
        raise NotImplementedError()


class IniReader(Reader):
    def __init__(self, path, *args, **kwargs):
        super().__init__(path, encoding=None)

    def __call__(self):
        parser = ConfigParser()
        parser.read(self._path)
        result = {}
        for section in parser.sections():
            d = result[section] = {}
            section_obj = parser[section]
            for key in section_obj:
                d[key] = section_obj[key]
        return result


class JsonReader(Reader):
    def __call__(self):
        with open(self._path, encoding=self._encoding) as fp:
            return json.load(fp)


class TomlReader(Reader):
    def __call__(self):
        if tomllib is not None:
            with open(self._path, "rb") as fp:
                return tomllib.load(fp)
        elif toml is not None:
            with open(self._path, encoding=self._encoding) as fp:
                return toml.load(fp)
        else:
            raise RuntimeError(
                'Un-supported file "{0}".\n'
                "`pip install toml` shall solve this problem.".format(self._path)
            )


class YamlReader(Reader):
    def __init__(self, path, encoding, loader, persist_anchors, *args, **kwargs):
        super().__init__(path, encoding)
        self._loader_class = type(loader)
        self._persist_anchors = persist_anchors
        if self._persist_anchors:
            self.anchors = loader.anchors

    def __call__(self):
        with open(self._path, encoding=self._encoding) as fp:
            if self._persist_anchors:
                loader = self._loader_class(fp)
                if self.anchors:
                    loader.anchors = self.anchors
                try:
                    return loader.get_single_data()
                finally:
                    loader.dispose()
            else:
                return yaml.load(fp, self._loader_class)  # type: ignore


class PlainTextReader(Reader):
    def __call__(self):
        with open(self._path, encoding=self._encoding) as fp:
            return fp.read()


READER_TABLE = [
    (
        re.compile(r"^.+\.(([yY][mM][lL])|([Yy][aA][mM][lL]))$"),
        YamlReader,
    ),  # *.yml, *.yaml
    (re.compile(r"^.+\.[jJ][sS][oO][nN]$"), JsonReader),  # *.json
    (re.compile(r"^.+\.[iI][nN][iI]$"), IniReader),  # *.ini
    (re.compile(r"^.+\.[tT][oO][mL][lL]$"), TomlReader),  # *.toml
    (re.compile(r"^.+\.[tT][xX][tT]$"), PlainTextReader),  # *.txt
]


def get_reader_class_by_name(name: str):
    name = name.strip().lower()
    if name == "ini":
        return IniReader
    if name == "json":
        return JsonReader
    if name == "toml":
        return TomlReader
    if name in ("plain", "plaintext", "plain_text", "plain-text", "text", "txt"):
        return PlainTextReader
    if name in ("yaml", "yml"):
        return YamlReader
    raise ValueError('Un-supported name reader "{0}"'.format(name))


def get_reader_class_by_path(path: str, table=None) -> Type[Reader]:
    if table is None:
        table = READER_TABLE
    for pat, clz in table:
        if re.match(pat, path):
            return clz
    raise RuntimeError('Un-supported file name "{}"'.format(path))
