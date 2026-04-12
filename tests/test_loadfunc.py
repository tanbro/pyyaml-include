"""Load function tests - pytest version"""

from textwrap import dedent

import pytest
import yaml

from yaml_include import (
    Constructor,
    lazy_load,
    load,
)

from ._internal import YAML1, YAML2, YAML_LOADERS
from .conftest import YAML_INCLUDE_TAG, cleanup_constructor

# ===== Load Function Fixtures =====


@pytest.fixture(scope="module")
def loadfunc_ctor():
    """Create constructor for load() function tests"""
    ctor = Constructor(base_dir="tests/data", autoload=False)
    for loader_cls in YAML_LOADERS:
        yaml.add_constructor("!inc", ctor, loader_cls)

    yield ctor

    # Cleanup
    cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)


# ===== Load Function Tests =====


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_load_normal(loadfunc_ctor, loader_cls):
    """Test load() function in normal mode"""
    yaml_string = dedent(
        """
        list:
            - !inc include.d/1.yaml
            - !inc include.d/2.yaml
        dict:
            yaml1: !inc include.d/1.yaml
            yaml2: !inc include.d/2.yaml
        """
    ).strip()
    d0 = yaml.load(yaml_string, loader_cls)
    d1 = load(d0, loader_cls, loadfunc_ctor)
    assert YAML1 == d1["list"][0]
    assert YAML2 == d1["list"][1]
    assert YAML1 == d1["dict"]["yaml1"]
    assert YAML2 == d1["dict"]["yaml2"]


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_load_inplace(loadfunc_ctor, loader_cls):
    """Test load() function in inplace mode"""
    yaml_string = dedent(
        """
        list:
            - !inc include.d/1.yaml
            - !inc include.d/2.yaml
        dict:
            yaml1: !inc include.d/1.yaml
            yaml2: !inc include.d/2.yaml
        """
    ).strip()
    d0 = yaml.load(yaml_string, loader_cls)
    load(d0, loader_cls, loadfunc_ctor, inplace=True)
    assert YAML1 == d0["list"][0]
    assert YAML2 == d0["list"][1]
    assert YAML1 == d0["dict"]["yaml1"]
    assert YAML2 == d0["dict"]["yaml2"]


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_load_nested(loadfunc_ctor, loader_cls):
    """Test load() function in nested mode"""
    yaml_string = dedent(
        """
        nested: !inc nested.yaml
        """
    ).strip()
    d0 = yaml.load(yaml_string, loader_cls)
    d1 = load(d0, loader_cls, loadfunc_ctor, nested=True)
    assert YAML1 == d1["nested"]["list"][0]
    assert YAML2 == d1["nested"]["list"][1]
    assert YAML1 == d1["nested"]["dict"]["yaml1"]
    assert YAML2 == d1["nested"]["dict"]["yaml2"]


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_load_inplace_nested(loadfunc_ctor, loader_cls):
    """Test load() function in inplace nested mode"""
    yaml_string = dedent(
        """
        nested: !inc nested.yaml
        """
    ).strip()
    d0 = yaml.load(yaml_string, loader_cls)
    load(d0, loader_cls, loadfunc_ctor, inplace=True, nested=True)
    assert YAML1 == d0["nested"]["list"][0]
    assert YAML2 == d0["nested"]["list"][1]
    assert YAML1 == d0["nested"]["dict"]["yaml1"]
    assert YAML2 == d0["nested"]["dict"]["yaml2"]


# ===== Lazy Load Function Tests =====


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_lazy_load_inplace(loadfunc_ctor, loader_cls):
    """Test lazy_load() function in inplace mode"""
    yaml_string = dedent(
        """
        list:
            - !inc include.d/1.yaml
            - !inc include.d/2.yaml
        dict:
            yaml1: !inc include.d/1.yaml
            yaml2: !inc include.d/2.yaml
        """
    ).strip()
    d0 = yaml.load(yaml_string, loader_cls)
    for _ in lazy_load(d0, loader_cls, loadfunc_ctor):
        pass
    assert YAML1 == d0["list"][0]
    assert YAML2 == d0["list"][1]
    assert YAML1 == d0["dict"]["yaml1"]
    assert YAML2 == d0["dict"]["yaml2"]


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_lazy_load_inplace_nested(loadfunc_ctor, loader_cls):
    """Test lazy_load() function in inplace nested mode"""
    yaml_string = dedent(
        """
        nested: !inc nested.yaml
        """
    ).strip()
    d0 = yaml.load(yaml_string, loader_cls)
    for _ in lazy_load(d0, loader_cls, loadfunc_ctor, nested=True):
        pass
    assert YAML1 == d0["nested"]["list"][0]
    assert YAML2 == d0["nested"]["list"][1]
    assert YAML1 == d0["nested"]["dict"]["yaml1"]
    assert YAML2 == d0["nested"]["dict"]["yaml2"]
