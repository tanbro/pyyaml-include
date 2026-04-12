"""Multi-document YAML tests - pytest version"""

from textwrap import dedent

import pytest
import yaml

from tests._internal import YAML1, YAML2, YAML_LOADERS
from yaml_include import Constructor

from .conftest import YAML_INCLUDE_TAG, cleanup_constructor


@pytest.fixture(scope="class")
def multi_constructor():
    """Configure constructor for multi-document tests"""
    ctor = Constructor(base_dir="tests/data")
    yield ctor
    # Cleanup: remove all registered constructors
    cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)


@pytest.fixture(scope="class")
def multi_loaders(multi_constructor):
    """Configure all loaders for multi-document tests"""
    for loader_cls in YAML_LOADERS:
        yaml.add_constructor(YAML_INCLUDE_TAG, multi_constructor, loader_cls)
    return YAML_LOADERS


@pytest.mark.parametrize("loader_cls", YAML_LOADERS, ids=lambda cls: cls.__name__)
def test_load_all(multi_loaders, loader_cls):
    """Test multi-document YAML loading"""

    yml_txt = dedent(
        """
        ---
        data: !inc include.d/1.yaml

        ---
        data: !inc include.d/2.yaml
        """
    )

    docs = list(yaml.load_all(yml_txt, loader_cls))

    # Assert: should have two documents
    assert len(docs) == 2

    # Assert: first document should contain YAML1 data
    assert docs[0] == {"data": YAML1}

    # Assert: second document should contain YAML2 data
    assert docs[1] == {"data": YAML2}
