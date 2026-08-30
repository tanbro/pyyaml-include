"""
Tests for sigil-added features:

- ``@``-relative include paths (resolved against the directory of the
  including file, not `base_dir` / the current working directory).
- ``$ENV``-style environment variable expansion in include urlpaths.
"""

import os
from io import StringIO

import pytest
import yaml

from yaml_include import Constructor

from ._internal import YAML_LOADERS
from .conftest import YAML_INCLUDE_TAG, cleanup_constructor


class TestAtRelativeInclude:
    """`@`-relative resolution: relative to the directory of the including file."""

    @pytest.fixture(autouse=True)
    def setup_constructor(self, test_data_dir):
        self.ctor = Constructor(base_dir=str(test_data_dir))
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor(YAML_INCLUDE_TAG, self.ctor, loader_cls)
        yield
        cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_at_relative_resolves_to_including_file_dir(self, loader):
        """`@nested/target.yaml` in `atinclude/outer.yaml` resolves relative to
        `atinclude/`, not `base_dir` (the top-level `tests/data` dir)."""
        yml = "outer: !inc atinclude/outer.yaml"
        data = yaml.load(StringIO(yml), loader)
        assert data == {"outer": {"key": {"value": "hello-from-nested"}}}

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_at_relative_top_level_falls_back_to_cwd(self, loader, test_data_dir, monkeypatch):
        """A top-level `@`-relative include (no including file yet) falls back to cwd."""
        monkeypatch.chdir(test_data_dir)
        yml = 'file1: !inc "@include.d/1.yaml"'
        data = yaml.load(StringIO(yml), loader)
        assert data == {"file1": {"name": "1"}}


class TestEnvVarExpansion:
    """`$ENV`-style environment variable expansion in include urlpaths."""

    @pytest.fixture(autouse=True)
    def setup_constructor(self, test_data_dir):
        self.ctor = Constructor(base_dir=str(test_data_dir))
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor(YAML_INCLUDE_TAG, self.ctor, loader_cls)
        yield
        cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_expandvars_in_urlpath(self, loader, monkeypatch):
        monkeypatch.setenv("PYYAML_INCLUDE_TEST_DIR", "include.d")
        yml = "file1: !inc $PYYAML_INCLUDE_TEST_DIR/1.yaml"
        data = yaml.load(StringIO(yml), loader)
        assert data == {"file1": {"name": "1"}}

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_expandvars_combined_with_at_relative(self, loader, monkeypatch, test_data_dir):
        # Top-level `@`-relative includes fall back to cwd (there is no including file yet).
        monkeypatch.chdir(test_data_dir)
        monkeypatch.setenv("PYYAML_INCLUDE_TEST_FILE", "outer.yaml")
        yml = 'outer: !inc "@atinclude/$PYYAML_INCLUDE_TEST_FILE"'
        data = yaml.load(StringIO(yml), loader)
        assert data == {"outer": {"key": {"value": "hello-from-nested"}}}
