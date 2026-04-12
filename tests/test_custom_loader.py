"""Custom loader tests - pytest version"""

import json
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

from yaml_include import Constructor

from ._internal import YAML_LOADERS
from .conftest import YAML_INCLUDE_TAG, cleanup_constructor, sort_by_name

# ===== Dummy Loader Fixtures =====


@pytest.fixture(scope="module")
def dummy_loader_ctor():
    """Create constructor with dummy loader"""

    def my_loader(path, file, *args, **kwargs):
        return "EMPTY"

    ctor = Constructor(base_dir="tests/data", custom_loader=my_loader)
    for loader_cls in YAML_LOADERS:
        yaml.add_constructor("!inc", ctor, loader_cls)

    yield ctor

    # Cleanup
    cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)


# ===== JSON Loader Fixtures =====


@pytest.fixture(scope="module")
def json_loader_ctor():
    """Create constructor with JSON loader"""

    def json_loader(file):
        return json.load(file)

    ctor = Constructor(
        base_dir="tests/data",
        custom_loader=lambda path, file, *args, **kwargs: json_loader(file),
    )
    for loader_cls in YAML_LOADERS:
        yaml.add_constructor("!inc", ctor, loader_cls)

    yield ctor

    # Cleanup
    cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)


# ===== JSON/YAML Loader Fixtures =====


@pytest.fixture(scope="module")
def json_yaml_loader_ctor():
    """Create constructor with mixed JSON/YAML loader"""

    def my_loader(path, file, loader_type, *args, **kwargs):
        path = file.path

        if Path(path).suffix == ".json":
            return json.load(file)
        if Path(path).suffix in (".yaml", ".yml"):
            return yaml.load(file, loader_type)
        return RuntimeError(f"not supported file '{path}' ({file})")

    ctor = Constructor(
        base_dir="tests/data",
        custom_loader=my_loader,
    )
    for loader_cls in YAML_LOADERS:
        yaml.add_constructor("!inc", ctor, loader_cls)

    yield ctor

    # Cleanup
    cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)


# ===== Dummy Loader Tests =====


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_dummy_loader_returns_empty(dummy_loader_ctor, loader_cls):
    """Test dummy loader returns 'EMPTY'"""
    yml = dedent(
        """
        content: !inc empty
        """
    )
    data = yaml.load(yml, loader_cls)
    assert data["content"] == "EMPTY"


# ===== JSON Loader Tests =====


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_json_loader_loads_json_files(json_loader_ctor, loader_cls, test_data_dir):
    """Test JSON loader correctly loads JSON files"""
    with open(test_data_dir / "include.d" / "1.json") as fp:
        d0 = json.load(fp)

    yml = dedent(
        """
        content: !inc include.d/1.json
        """
    )
    data = yaml.load(yml, loader_cls)
    d1 = data["content"]
    assert d0 == d1


# ===== JSON/YAML Mixed Loader Tests =====


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_json_wildcards(json_yaml_loader_ctor, loader_cls, test_data_dir):
    """Test JSON wildcard loading"""
    with open(test_data_dir / "include.d" / "1.json") as fp:
        d1 = json.load(fp)
    with open(test_data_dir / "include.d" / "2.json") as fp:
        d2 = json.load(fp)

    yml = dedent(
        """
        content: !inc include.d/*.json
        """
    )
    data = yaml.load(yml, loader_cls)
    assert sort_by_name(data["content"]) == [d1, d2]


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_yaml_wildcards(json_yaml_loader_ctor, loader_cls, test_data_dir):
    """Test YAML wildcard loading"""
    with open(test_data_dir / "include.d" / "1.yaml") as fp:
        d1 = yaml.full_load(fp)
    with open(test_data_dir / "include.d" / "2.yaml") as fp:
        d2 = yaml.full_load(fp)

    yml = dedent(
        """
        content: !inc include.d/*.yaml
        """
    )
    data = yaml.load(yml, loader_cls)
    assert sort_by_name(data["content"]) == [d1, d2]


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_json_yaml_mixed_files(json_yaml_loader_ctor, loader_cls, test_data_dir):
    """Test mixed JSON and YAML file loading"""
    with open(test_data_dir / "include.d" / "1.json") as fp:
        d1 = json.load(fp)
    with open(test_data_dir / "include.d" / "2.yaml") as fp:
        d2 = yaml.full_load(fp)

    yml = dedent(
        """
        - !inc include.d/1.json
        - !inc include.d/2.yaml
        """
    )
    data = yaml.load(yml, loader_cls)
    assert data == [d1, d2]


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_json_yaml_full_url(json_yaml_loader_ctor, loader_cls, test_data_dir, absolute_path):
    """Test JSON and YAML file loading with full URL"""
    with open(test_data_dir / "include.d" / "1.json") as fp:
        d1 = json.load(fp)
    with open(test_data_dir / "include.d" / "2.yaml") as fp:
        d2 = yaml.full_load(fp)

    abs_path = absolute_path.as_posix()
    yml = dedent(
        f"""
        - !inc file://{abs_path}/tests/data/include.d/1.json
        - !inc file://{abs_path}/tests/data/include.d/2.yaml
        """
    )
    data = yaml.load(yml, loader_cls)
    assert data == [d1, d2]


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_json_yaml_wildcards_full_url(json_yaml_loader_ctor, loader_cls, test_data_dir, absolute_path):
    """Test JSON and YAML wildcard loading with full URL"""
    with open(test_data_dir / "include.d" / "1.json") as fp:
        json1 = json.load(fp)
    with open(test_data_dir / "include.d" / "2.json") as fp:
        json2 = json.load(fp)
    with open(test_data_dir / "include.d" / "1.yaml") as fp:
        yaml1 = yaml.full_load(fp)
    with open(test_data_dir / "include.d" / "2.yaml") as fp:
        yaml2 = yaml.full_load(fp)

    abs_path = absolute_path.as_posix()
    yml = dedent(
        f"""
        !inc file://{abs_path}/tests/data/include.d/*
        """
    )
    data = yaml.load(yml, loader_cls)
    assert sort_by_name(data) == [json1, yaml1, json2, yaml2]
