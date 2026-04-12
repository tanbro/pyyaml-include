from textwrap import dedent

import pytest
import yaml

from yaml_include import Constructor

from .conftest import YAML_INCLUDE_TAG, cleanup_constructor


@pytest.fixture(scope="session")
def deep_constructor(test_data_dir, yaml_loaders):
    """Configure constructor for deep nesting tests, register all loaders"""
    ctor = Constructor(base_dir=str(test_data_dir))

    # Register constructor to all YAML loaders
    for loader_cls in yaml_loaders:
        yaml.add_constructor(YAML_INCLUDE_TAG, ctor, loader_cls)

    yield ctor

    # Cleanup: remove constructor registration
    cleanup_constructor(YAML_INCLUDE_TAG, yaml_loaders)


def test_nested_include(deep_constructor):
    """Test deep nested YAML include functionality"""
    yml_txt = dedent(
        """
        root: !inc include2.d/0.yml
        """
    )
    data = yaml.load(yml_txt, yaml.Loader)

    expected = {
        "root": {
            "1": {"value": "1"},
            "a": {"deep": {"path": {"test": {"1": {"value": "1"}}}}},
        }
    }

    assert data == expected
