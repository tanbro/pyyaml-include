"""
Tests for `@modulename/relative/path.yaml` include syntax: resolves relative
to the imported Python module's package directory
(``importlib.import_module("modulename").__path__``).
"""

from io import StringIO

import pytest
import yaml

from yaml_include import Constructor

from ._internal import YAML_LOADERS
from .conftest import YAML_INCLUDE_TAG, cleanup_constructor


class TestPythonModuleInclude:
    @pytest.fixture(autouse=True)
    def setup_constructor(self, test_data_dir):
        self.ctor = Constructor(base_dir=str(test_data_dir))
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor(YAML_INCLUDE_TAG, self.ctor, loader_cls)
        yield
        cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_module_relative_include(self, loader):
        yml = 'file1: !inc "@tests.fixture_pkg/data/module_include.yaml"'
        data = yaml.load(StringIO(yml), loader)
        assert data == {"file1": {"value": "hello-from-module"}}

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_module_relative_include_ignores_base_dir(self, loader):
        """Module-relative includes are already absolute; `base_dir` must not be re-applied."""
        ctor = Constructor(base_dir="/some/unrelated/dir/that/does/not/exist")
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor(YAML_INCLUDE_TAG, ctor, loader_cls)
        try:
            yml = 'file1: !inc "@tests.fixture_pkg/data/module_include.yaml"'
            data = yaml.load(StringIO(yml), loader)
            assert data == {"file1": {"value": "hello-from-module"}}
        finally:
            cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)

    def test_unresolvable_module_falls_back_to_at_relative(self, test_data_dir, monkeypatch):
        """If `modulename` in `@modulename/path` isn't importable, it's not module syntax after
        all -- fall back to plain `@`-relative resolution of the whole path."""
        monkeypatch.chdir(test_data_dir)
        yml = 'file1: !inc "@no.such.module/x.yaml"'
        with pytest.raises(FileNotFoundError):
            yaml.load(StringIO(yml), yaml.SafeLoader)
