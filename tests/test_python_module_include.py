"""
Tests for `@modulename/relative/path.yaml` include syntax: resolves relative
to the imported Python module's package directory
(``importlib.import_module("modulename").__path__``).
"""

import types
from io import StringIO

import pytest
import yaml

from yaml_include import Constructor
from yaml_include import constructor as constructor_module

from ._internal import YAML_LOADERS
from .conftest import YAML_INCLUDE_TAG, cleanup_constructor


class TestPythonModuleInclude:
    @pytest.fixture(autouse=True)
    def setup_constructor(self, test_data_dir):
        self.ctor = Constructor(base_dir=str(test_data_dir), allow_module_include=True)
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
        ctor = Constructor(base_dir="/some/unrelated/dir/that/does/not/exist", allow_module_include=True)
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

    def test_non_package_module_falls_back_instead_of_raising_attributeerror(self, test_data_dir, monkeypatch):
        """`os.path` is importable but has no `__path__` (it's not a package). This must fall
        back to plain `@`-relative resolution, not raise a raw `AttributeError`."""
        monkeypatch.chdir(test_data_dir)
        yml = 'file1: !inc "@os.path/x.yaml"'
        with pytest.raises(FileNotFoundError):
            yaml.load(StringIO(yml), yaml.SafeLoader)

    def test_namespace_package_tries_all_path_entries(self, loader=yaml.SafeLoader):
        """A module whose `__path__` has multiple entries (namespace package) must be resolved
        by trying every entry, not just the first, e.g. when the file lives under a later entry."""
        fake_module = types.SimpleNamespace(
            __path__=[
                "/no/such/directory/at/all",
                str((__import__("pathlib").Path(__file__).parent / "fixture_pkg").resolve()),
            ]
        )

        def fake_import_module(name):
            assert name == "fake.namespace.pkg"
            return fake_module

        original = constructor_module.importlib.import_module
        constructor_module.importlib.import_module = fake_import_module
        try:
            yml = 'file1: !inc "@fake.namespace.pkg/data/module_include.yaml"'
            data = yaml.load(StringIO(yml), loader)
            assert data == {"file1": {"value": "hello-from-module"}}
        finally:
            constructor_module.importlib.import_module = original


class TestModuleIncludeDisabledByDefault:
    """`allow_module_include` defaults to `False`: `@modulename/path` must not trigger an
    implicit `importlib.import_module()` call unless explicitly opted in."""

    @pytest.fixture(autouse=True)
    def setup_constructor(self, test_data_dir):
        self.ctor = Constructor(base_dir=str(test_data_dir))
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor(YAML_INCLUDE_TAG, self.ctor, loader_cls)
        yield
        cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)

    def test_default_constructor_never_imports_module(self):
        assert self.ctor.allow_module_include is False

    def test_module_syntax_falls_back_to_at_relative_when_disabled(self, test_data_dir, monkeypatch):
        """With the flag left at its default (`False`), `@tests.fixture_pkg/...` must NOT import
        `tests.fixture_pkg` -- it must be treated as a plain `@`-relative path, which does not
        exist relative to cwd, so this must raise `FileNotFoundError`, never succeed via import."""
        monkeypatch.chdir(test_data_dir)
        yml = 'file1: !inc "@tests.fixture_pkg/data/module_include.yaml"'
        with pytest.raises(FileNotFoundError):
            yaml.load(StringIO(yml), yaml.SafeLoader)

    def test_module_import_not_attempted_when_disabled(self, monkeypatch, test_data_dir):
        """Directly assert `importlib.import_module` is never called when the flag is off."""
        monkeypatch.chdir(test_data_dir)
        calls = []
        original = constructor_module.importlib.import_module

        def spy_import_module(name):
            calls.append(name)
            return original(name)

        monkeypatch.setattr(constructor_module.importlib, "import_module", spy_import_module)
        yml = 'file1: !inc "@tests.fixture_pkg/data/module_include.yaml"'
        with pytest.raises(FileNotFoundError):
            yaml.load(StringIO(yml), yaml.SafeLoader)
        assert calls == []
