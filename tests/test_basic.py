"""
Basic functionality tests for pyyaml-include (pytest version)

Tests core behaviors of YAML include functionality:
- Basic include operations (mapping and sequence)
- Wildcard matching
- Filesystem variants (default, file://, HTTP)
- Flatten options
"""

from io import StringIO
from textwrap import dedent

import fsspec  # type: ignore[import-untyped]
import pytest
import yaml

from yaml_include import Constructor

from ._internal import YAML1, YAML2, YAML_LOADERS
from .conftest import YAML_INCLUDE_TAG, cleanup_constructor, sort_by_name

# ===== Basic Include Tests =====


class TestBasicInclude:
    """Basic YAML include functionality tests (using default filesystem)"""

    @pytest.fixture(autouse=True)
    def setup_constructor(self, test_data_dir):
        """Setup constructor and register to all YAML loaders"""
        self.ctor = Constructor(base_dir=str(test_data_dir))
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", self.ctor, loader_cls)

        yield

        # Cleanup: remove constructor registration
        cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_include_one_in_mapping(self, loader):
        """Test including a single file in mapping"""
        yml = """
file1: !inc include.d/1.yaml
        """
        data = yaml.load(StringIO(yml), loader)
        assert data == {"file1": YAML1}

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_continuous_including(self, loader):
        """Test continuous including of multiple files"""
        yml = dedent(
            """
            foo:
                - !inc include.d/1.yaml
                - !inc include.d/2.yaml
            """
        )
        data = yaml.load(StringIO(yml), loader)
        assert data == {"foo": [YAML1, YAML2]}

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_include_two_in_mapping(self, loader):
        """Test including two files in mapping"""
        yml = """
a: A
file1: !inc include.d/1.yaml
b: B
file2: !inc include.d/2.yaml
c: C
        """
        data = yaml.load(StringIO(yml), loader)
        assert data == {
            "a": "A",
            "file1": YAML1,
            "b": "B",
            "file2": YAML2,
            "c": "C",
        }

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_include_one_in_sequence(self, loader):
        """Test including a single file in sequence"""
        yml = """
- !inc include.d/1.yaml
        """
        data = yaml.load(StringIO(yml), loader)
        assert data == [YAML1]

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_include_two_in_sequence(self, loader):
        """Test including two files in sequence"""
        yml = """
- a
- !inc include.d/1.yaml
- b
- !inc include.d/2.yaml
- c
        """
        data = yaml.load(StringIO(yml), loader)
        assert data == ["a", YAML1, "b", YAML2, "c"]

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_include_file_not_exists(self, loader):
        """Test including non-existent file"""
        yml = """
file: !inc include.d/x.yaml
            """
        with pytest.raises(FileNotFoundError):
            yaml.load(StringIO(yml), loader)

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_include_wildcards(self, loader):
        """Test wildcard include"""
        yml = """
files: !inc include.d/*.yaml
"""
        data = yaml.load(StringIO(yml), loader)
        assert sort_by_name(data["files"]) == [YAML1, YAML2]

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_include_wildcards_1(self, loader):
        """Test wildcard include (with maxdepth parameter)"""
        yml = """
files: !inc [include.d/**/*.yaml, [1]]
"""
        data = yaml.load(StringIO(yml), loader)
        assert sort_by_name(data["files"]) == [YAML1, YAML2]

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_include_wildcards_2(self, loader):
        """Test wildcard include (with maxdepth dict parameter)"""
        yml = """
files: !inc [include.d/**/*.yaml, {maxdepth: 1}]
"""
        data = yaml.load(StringIO(yml), loader)
        assert sort_by_name(data["files"]) == [YAML1, YAML2]

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_include_wildcards_3(self, loader):
        """Test wildcard include (complete dict format)"""
        yml = """
files: !inc {urlpath: include.d/**/*.yaml, glob: {maxdepth: 1}, open: {}}
"""
        data = yaml.load(StringIO(yml), loader)
        assert sort_by_name(data["files"]) == [YAML1, YAML2]

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_include_wildcards_3_1(self, loader):
        """Test wildcard include (rb mode)"""
        yml = """
files: !inc {urlpath: include.d/**/*.yaml, glob: {maxdepth: 1}, open: rb}
"""
        data = yaml.load(StringIO(yml), loader)
        assert sort_by_name(data["files"]) == [YAML1, YAML2]

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_include_wildcards_4(self, loader):
        """Test wildcard include (three-parameter format)"""
        yml = """
files: !inc [include.d/**/*.yaml, {maxdepth: 1}, []]
"""
        data = yaml.load(StringIO(yml), loader)
        assert sort_by_name(data["files"]) == [YAML1, YAML2]

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_include_wildcards_5(self, loader):
        """Test wildcard include (shorthand maxdepth)"""
        yml = """
files: !inc [include.d/**/*.yaml, 1]
"""
        data = yaml.load(StringIO(yml), loader)
        assert sort_by_name(data["files"]) == [YAML1, YAML2]

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_flatten_true(self, loader, test_data_dir):
        """Test flatten option set to true"""
        yml = dedent(
            """
            items: !inc {urlpath: "include3.d/*.yml", flatten: true}
            """
        )

        # Build expected results
        two_dim_sequence = []
        for pth in test_data_dir.glob("include3.d/*.yml"):
            two_dim_sequence.append(yaml.load(pth.read_bytes(), loader))
        flattened_sequence = sorted([member for data in two_dim_sequence for member in data])

        data = yaml.load(StringIO(yml), loader)
        result = sorted(data["items"])
        assert result == flattened_sequence

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_flatten_false_or_default(self, loader, test_data_dir):
        """Test flatten option set to false or default"""
        yml1 = dedent(
            """
            items: !inc {urlpath: "include3.d/*.yml", flatten: false}
            """
        )
        yml2 = dedent(
            """
            items: !inc "include3.d/*.yml"
            """
        )

        # Build expected results
        two_dim_sequence = []
        for pth in test_data_dir.glob("include3.d/*.yml"):
            two_dim_sequence.append(yaml.load(pth.read_bytes(), loader))
        two_dim_sequence = sorted(two_dim_sequence)

        data1 = yaml.load(StringIO(yml1), loader)
        result1 = data1["items"]
        assert result1 == two_dim_sequence

        data2 = yaml.load(StringIO(yml2), loader)
        result2 = data2["items"]
        assert result2 == two_dim_sequence


# ===== FileFs Tests =====


class TestFileFs:
    """Tests using fsspec file:// filesystem"""

    @pytest.fixture(autouse=True)
    def setup_constructor(self):
        """Setup file:// constructor"""
        self.ctor = Constructor(fs=fsspec.filesystem("file"), base_dir=lambda: "tests/data")
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", self.ctor, loader_cls)

        yield

        # Cleanup
        for loader_cls in YAML_LOADERS:
            if "!inc" in loader_cls.yaml_constructors:
                del loader_cls.yaml_constructors["!inc"]

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_abs(self, loader, absolute_path):
        """Test absolute path"""
        yml = dedent(
            f"""
            file1: !inc {absolute_path.as_posix()}/tests/data/include.d/1.yaml
            """
        )
        data = yaml.load(StringIO(yml), loader)
        assert data == {"file1": YAML1}

    @pytest.mark.parametrize("loader", YAML_LOADERS, ids=lambda cls: cls.__name__)
    def test_scheme_abs(self, loader, absolute_path):
        """Test absolute path with file:// scheme"""
        yml = dedent(
            f"""
            file1: !inc file://{absolute_path.as_posix()}/tests/data/include.d/1.yaml
            """
        )
        data = yaml.load(yml, yaml.Loader)
        assert data == {"file1": YAML1}


# ===== HTTP Filesystem Tests =====


class TestHTTPFs:
    """Tests using HTTP filesystem"""

    @pytest.fixture(autouse=True)
    def setup_constructor(self, http_server):
        """Setup HTTP constructor"""
        host, port = http_server["host"], http_server["port"]
        self.ctor = Constructor(
            fs=fsspec.filesystem("http", client_kwargs=dict(base_url=f"http://{host}:{port}")),
            base_dir="tests/data",
        )
        yaml.add_constructor("!inc", self.ctor, yaml.Loader)
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", self.ctor, loader_cls)

        yield

        # Cleanup
        for loader_cls in YAML_LOADERS:
            if "!inc" in loader_cls.yaml_constructors:
                del loader_cls.yaml_constructors["!inc"]

    def test_full_url(self, http_server):
        """Test full HTTP URL"""
        host, port = http_server["host"], http_server["port"]
        yml = dedent(
            f"""
            file1: !inc http://{host}:{port}/tests/data/include.d/1.yaml
            """
        )
        data = yaml.load(yml, yaml.Loader)
        assert data == {"file1": YAML1}

    def test_wildcards_full_url(self, http_server):
        """Test wildcard HTTP URL"""
        host, port = http_server["host"], http_server["port"]
        yml = dedent(
            f"""
            files: !inc http://{host}:{port}/tests/data/include.d/*.yaml
            """
        )
        data = yaml.load(yml, yaml.Loader)
        assert sort_by_name(data["files"]) == [YAML1, YAML2]


# ===== No Base Directory Tests =====


class TestNoBaseDir:
    """Tests without setting base directory"""

    @pytest.fixture(autouse=True)
    def setup_constructor(self):
        """Setup constructor without base directory"""
        self.ctor = Constructor()
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", self.ctor, loader_cls)

        yield

        # Cleanup
        for loader_cls in YAML_LOADERS:
            if "!inc" in loader_cls.yaml_constructors:
                del loader_cls.yaml_constructors["!inc"]

    def test_yaml2(self):
        """Test including file from current directory"""
        yml = dedent(
            """
            file1: !inc tests/data/include.d/2.yaml
            """
        )
        data = yaml.load(yml, yaml.Loader)
        assert data == {"file1": YAML2}
