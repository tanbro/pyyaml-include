# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import unittest

from textwrap import dedent

import yaml

from yamlinclude import YamlIncludeConstructor

YAML1 = {'name': '1'}
YAML2 = {'name': '2'}


class MultiLoaderTestCase(unittest.TestCase):

    constructor = YamlIncludeConstructor()

    def setUp(self):
        yaml.add_constructor('!include', self.constructor)

    def test_full_load_all_yaml(self):
        txt = dedent('''
        ---
        file1: !include tests/data/include.d/1.yaml

        ---
        file2: !include tests/data/include.d/2.yaml
        ''').strip()
        iterable = yaml.full_load_all(txt)
        for i, data in enumerate(iterable):
            if i == 0:
                self.assertEqual(data, {'file1': YAML1})
            elif i == 1:
                self.assertEqual(data, {'file2': YAML2})
            else:
                raise RuntimeError()
