# -*- coding: utf-8 -*-

"""readers for different type of files
"""

import io
import json
import re

import yaml

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

try:
    import toml
except ImportError:
    toml = None


__all__ = ['READER_TABLE', 'get_reader_class_by_path', 'get_reader_class_by_name',
           'Reader', 'IniReader', 'JsonReader', 'TomlReader', 'YamlReader']


def get_reader_class_by_name(name):  # type:(str)->type
    name = name.strip().lower()
    if name == 'ini':
        return IniReader
    if name == 'json':
        return JsonReader
    if name == 'toml':
        return TomlReader
    if name in ('plain', 'plaintext', 'plain_text', 'plain-text', 'text', 'txt'):
        return PlainTextReader
    if name in ('yaml', 'yml'):
        return YamlReader
    raise ValueError('Un-supported name reader "{0}"'.format(name))


def get_reader_class_by_path(path, table=None):  # type:(str)->type
    table = table or READER_TABLE
    for pat, clz in table:
        if re.match(pat, path):
            return clz
    raise RuntimeError('Un-supported file name "{}"'.format(path))


class Reader(object):
    # pylint: disable=too-few-public-methods
    def __init__(self, path, encoding, *args, **kwargs):  # pylint:disable=unused-argument
        self._path = path
        self._encoding = encoding

    def __call__(self):
        raise NotImplementedError()


class IniReader(Reader):
    # pylint: disable=too-few-public-methods
    def __init__(self, path, *args, **kwargs):  # pylint:disable=unused-argument
        super(IniReader, self).__init__(path, None, *args, **kwargs)

    def __call__(self):
        config = configparser.ConfigParser()
        config.read(self._path)
        result = {}
        for section in config.sections():
            d = result[section] = {}
            section_obj = config[section]
            for key in section_obj:
                d[key] = section_obj[key]
        return result


class JsonReader(Reader):
    # pylint: disable=too-few-public-methods
    def __call__(self):
        with io.open(self._path, encoding=self._encoding) as fp:
            return json.load(fp)


class TomlReader(Reader):
    # pylint: disable=too-few-public-methods
    def __call__(self):
        if toml is None:
            raise RuntimeError(
                'Un-supported file "{0}".\n'
                '`pip install toml` shall solve this problem.'.format(self._path)
            )
        with io.open(self._path, encoding=self._encoding) as fp:
            return toml.load(fp)


class YamlReader(Reader):
    # pylint: disable=too-few-public-methods
    def __init__(self, path, encoding, loader_class, *args, **kwargs):  # pylint:disable=unused-argument
        super(YamlReader, self).__init__(path, encoding)
        self._loader_class = loader_class

    def __call__(self):
        with io.open(self._path, encoding=self._encoding) as fp:
            return yaml.load(fp, self._loader_class)


class PlainTextReader(Reader):
    # pylint: disable=too-few-public-methods
    def __call__(self):
        with io.open(self._path, encoding=self._encoding) as fp:
            return fp.read()


READER_TABLE = [
    (re.compile(r'^.+\.(([yY][mM][lL])|([Yy][aA][mM][lL]))$'), YamlReader),
    (re.compile(r'^.+\.[jJ][sS][oO][nN]$'), JsonReader),
    (re.compile(r'^.+\.[iI][nN][iI]$'), IniReader),
    (re.compile(r'^.+\.[tT][oO][mL][lL]$'), TomlReader),
    (re.compile(r'^.+\.[tT][xX][tT]$'), PlainTextReader),
]
