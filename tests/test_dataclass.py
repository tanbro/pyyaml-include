from textwrap import dedent

import pytest
import yaml

from yaml_include import Constructor, Data

from ._internal import YAML_LOADERS
from .conftest import YAML_INCLUDE_TAG, cleanup_constructor


@pytest.fixture(scope="module")
def dataclass_constructor(test_data_dir):
    """Create constructor with base_dir and register !inc tag for dataclass tests"""
    ctor = Constructor(base_dir=str(test_data_dir))

    # Register constructor for all loaders
    for loader_cls in YAML_LOADERS:
        yaml.add_constructor(YAML_INCLUDE_TAG, ctor, loader_cls)

    yield ctor

    # Cleanup: unregister constructor
    cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)


@pytest.mark.usefixtures("dataclass_constructor")
def test_simple_managed_autoload(dataclass_constructor):
    """Test managed_autoload context manager"""
    yaml_string = dedent(
        """
        yaml1: !inc include.d/1.yaml
        """
    ).strip()

    for loader_cls in YAML_LOADERS:
        with dataclass_constructor.managed_autoload(False):
            assert not dataclass_constructor.autoload
            d = yaml.load(yaml_string, loader_cls)
            assert isinstance(d["yaml1"], Data)
            assert d["yaml1"].urlpath == "include.d/1.yaml"
        assert dataclass_constructor.autoload
