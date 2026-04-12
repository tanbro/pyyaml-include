"""Tests for YAML dump/serialization with yaml_include."""

from textwrap import dedent

import pytest
import yaml

from yaml_include import Constructor, Data, Representer, load

from ._internal import YAML1, YAML2, YAML_DUMPERS, YAML_LOADERS
from .conftest import YAML_INCLUDE_TAG, cleanup_constructor, cleanup_representer

# ===== Test Data Fixtures =====


@pytest.fixture(scope="session")
def yaml_test_data():
    """Cached test YAML data (reuses _internal.py loaded data)."""
    return {
        "yaml1": YAML1,
        "yaml2": YAML2,
    }


# ===== Fixtures for Constructor and Representer Registration =====


@pytest.fixture(scope="session")
def dump_constructor():
    """Constructor instance for dump tests (no autoload)."""
    return Constructor(base_dir="tests/data", autoload=False)


@pytest.fixture(scope="session")
def dump_representer():
    """Representer instance for dump tests."""
    return Representer("inc")


@pytest.fixture(scope="session")
def registered_yaml_classes(dump_constructor, dump_representer):
    """
    Register constructor and representer with all YAML loaders and dumpers.

    This fixture handles the dual registration pattern needed for round-trip
    serialization tests. It registers:
    - Constructor with all loaders (for loading !inc tags)
    - Representer with all dumpers (for dumping Data objects)

    Returns a tuple of (loaders_list, dumpers_list).
    """
    # Register constructor with all loaders
    for loader_cls in YAML_LOADERS:
        yaml.add_constructor("!inc", dump_constructor, loader_cls)

    # Register representer with all dumpers
    for dumper_cls in YAML_DUMPERS:
        yaml.add_representer(Data, dump_representer, dumper_cls)

    yield YAML_LOADERS, YAML_DUMPERS

    # Cleanup: unregister constructor and representer
    cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)
    cleanup_representer(Data, YAML_DUMPERS)


# ===== Helper Functions =====


def _test_round_trip_combinations(yaml_string, dump_constructor, loaders, dumpers, expected_data, inplace=False):
    """
    Test all loader × dumper combinations for round-trip serialization.

    Args:
        yaml_string: YAML string with !inc tags
        dump_constructor: Constructor instance for loading
        loaders: List of YAML loader classes
        dumpers: List of YAML dumper classes
        expected_data: Dict with expected values to assert
        inplace: Whether to use inplace mode (default: False)
    """
    for loader_cls in loaders:
        d = yaml.load(yaml_string, loader_cls)
        for dumper_cls in dumpers:
            s = yaml.dump(d, None, dumper_cls)
            d1 = yaml.load(s, loader_cls)

            if inplace:
                load(d1, loader_cls, dump_constructor, inplace=True)
                result = d1
            else:
                result = load(d1, loader_cls, dump_constructor)

            # Assert all expected key-value pairs
            for key, expected_value in expected_data.items():
                # Support nested key paths like "list.0" or "dict.yaml1"
                if "." in key:
                    parts = key.split(".")
                    actual = result
                    for part in parts:
                        if part.isdigit():
                            actual = actual[int(part)]
                        else:
                            actual = actual[part]
                else:
                    actual = result[key]

                assert expected_value == actual, f"Mismatch at {key} with {loader_cls.__name__} and {dumper_cls.__name__}"


# ===== Test Functions =====


@pytest.mark.unit
def test_extract(
    registered_yaml_classes,
    dump_constructor,
    yaml_test_data,
):
    """
    Test extraction mode of round-trip serialization.

    This test verifies that:
    1. YAML with !inc tags can be loaded
    2. Data objects can be dumped back to YAML
    3. The dumped YAML can be loaded again
    4. The Data objects can be extracted and loaded with load()
    """
    loaders, dumpers = registered_yaml_classes
    yaml1 = yaml_test_data["yaml1"]
    yaml2 = yaml_test_data["yaml2"]

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

    expected = {
        "list.0": yaml1,
        "list.1": yaml2,
        "dict.yaml1": yaml1,
        "dict.yaml2": yaml2,
    }

    _test_round_trip_combinations(yaml_string, dump_constructor, loaders, dumpers, expected)


@pytest.mark.unit
def test_inplace(
    registered_yaml_classes,
    dump_constructor,
    yaml_test_data,
):
    """
    Test inplace mode of round-trip serialization.

    This test verifies that:
    1. YAML with !inc tags can be loaded
    2. Data objects can be dumped back to YAML
    3. The dumped YAML can be loaded again
    4. The Data objects can be loaded inplace with load()
    """
    loaders, dumpers = registered_yaml_classes
    yaml1 = yaml_test_data["yaml1"]
    yaml2 = yaml_test_data["yaml2"]

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

    expected = {
        "list.0": yaml1,
        "list.1": yaml2,
        "dict.yaml1": yaml1,
        "dict.yaml2": yaml2,
    }

    _test_round_trip_combinations(yaml_string, dump_constructor, loaders, dumpers, expected, inplace=True)


@pytest.mark.unit
def test_dump_sequence_params(
    registered_yaml_classes,
    dump_constructor,
    yaml_test_data,
):
    """
    Test round-trip serialization with sequence parameters.

    Verifies that include tags with sequence parameters (e.g., !inc [file, r])
    are correctly preserved through dump/load cycles.
    """
    loaders, dumpers = registered_yaml_classes
    yaml1 = yaml_test_data["yaml1"]

    yaml_string = dedent(
        """
        data: !inc [include.d/1.yaml, r]
        """
    ).strip()

    expected = {"data": yaml1}
    _test_round_trip_combinations(yaml_string, dump_constructor, loaders, dumpers, expected)


@pytest.mark.unit
def test_dump_mapping_params(
    registered_yaml_classes,
    dump_constructor,
    yaml_test_data,
):
    """
    Test round-trip serialization with mapping parameters.

    Verifies that include tags with mapping parameters (e.g., !inc {urlpath: file, mode: r})
    are correctly preserved through dump/load cycles.
    """
    loaders, dumpers = registered_yaml_classes
    yaml1 = yaml_test_data["yaml1"]

    yaml_string = dedent(
        """
        data: !inc {urlpath: include.d/1.yaml, mode: r}
        """
    ).strip()

    expected = {"data": yaml1}
    _test_round_trip_combinations(yaml_string, dump_constructor, loaders, dumpers, expected)
