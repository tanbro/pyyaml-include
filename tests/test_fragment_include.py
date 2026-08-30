"""
Tests for `path/to/file.yaml:key.subkey` fragment-extraction include syntax:
loads the file, then descends into the loaded mapping via `key.subkey`
(``.split(".")``), returning only that nested value.
"""

from io import StringIO

import pytest
import yaml

from yaml_include import Constructor

from ._internal import YAML_LOADERS
from .conftest import YAML_INCLUDE_TAG, cleanup_constructor


class TestFragmentInclude:
    @pytest.fixture(autouse=True)
    def setup_constructor(self, test_data_dir):
        self.ctor = Constructor(base_dir=str(test_data_dir))
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor(YAML_INCLUDE_TAG, self.ctor, loader_cls)
        yield
        cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_single_level_key(self, loader):
        yml = "value: !inc fragment.yaml:top"
        data = yaml.load(StringIO(yml), loader)
        assert data == {"value": {"mid": {"leaf": "fragment-value"}, "other": "ignored"}}

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_nested_key_path(self, loader):
        yml = "value: !inc fragment.yaml:top.mid.leaf"
        data = yaml.load(StringIO(yml), loader)
        assert data == {"value": "fragment-value"}

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_without_fragment_returns_whole_document(self, loader):
        yml = "value: !inc fragment.yaml"
        data = yaml.load(StringIO(yml), loader)
        assert data == {
            "value": {"top": {"mid": {"leaf": "fragment-value"}, "other": "ignored"}, "list_value": ["a", "b"]}
        }

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_unknown_key_raises(self, loader):
        yml = "value: !inc fragment.yaml:top.nope"
        with pytest.raises(KeyError):
            yaml.load(StringIO(yml), loader)

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_fragment_combined_with_at_relative(self, loader, test_data_dir, monkeypatch):
        monkeypatch.chdir(test_data_dir)
        yml = 'value: !inc "@fragment.yaml:top.mid.leaf"'
        data = yaml.load(StringIO(yml), loader)
        assert data == {"value": "fragment-value"}
