"""
pytest configuration and shared fixtures

This file provides for the pyyaml-include test suite:
1. Shared test fixtures
2. Custom marker configuration
3. Parametrized test support
4. Helper functions for common test patterns
"""

import http.server
import os
import socket
import threading
from pathlib import Path
from time import sleep
from warnings import warn

import pytest
import yaml

from yaml_include import Constructor, Data

# ===== Constants =====

YAML_INCLUDE_TAG = "!inc"


# ===== Basic Fixtures =====


@pytest.fixture(scope="session")
def test_data_dir():
    """Test data directory"""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def yaml_loaders():
    """All available YAML loaders"""
    from yaml import BaseLoader, FullLoader, Loader, SafeLoader, UnsafeLoader

    loaders = [BaseLoader, SafeLoader, Loader, FullLoader, UnsafeLoader]

    # Add C extension loaders (if available)
    try:
        from yaml import CBaseLoader, CFullLoader, CLoader, CSafeLoader, CUnsafeLoader

        loaders.extend([CBaseLoader, CSafeLoader, CLoader, CFullLoader, CUnsafeLoader])
    except ImportError as err:
        warn(f"PyYAML C extensions not available: {err}")

    return loaders


def _get_yaml_loaders():
    """Helper function to get YAML loaders (for parametrization)"""
    from yaml import BaseLoader, FullLoader, Loader, SafeLoader, UnsafeLoader

    loaders = [BaseLoader, SafeLoader, Loader, FullLoader, UnsafeLoader]

    try:
        from yaml import CBaseLoader, CFullLoader, CLoader, CSafeLoader, CUnsafeLoader

        loaders.extend([CBaseLoader, CSafeLoader, CLoader, CFullLoader, CUnsafeLoader])
    except ImportError as err:
        warn(f"PyYAML C extensions not available: {err}")

    return loaders


@pytest.fixture(scope="session")
def expected_test_data(test_data_dir):
    """Preloaded expected test data"""
    yaml1 = yaml.safe_load((test_data_dir / "include.d" / "1.yaml").read_text())
    yaml2 = yaml.safe_load((test_data_dir / "include.d" / "2.yaml").read_text())
    zh_cn = yaml.safe_load((test_data_dir / "zh_cn.yaml").read_text(encoding="utf-8"))
    return {"yaml1": yaml1, "yaml2": yaml2, "zh_cn": zh_cn}


# ===== Constructor Fixtures =====


@pytest.fixture
def base_constructor():
    """Base constructor (using default filesystem)"""
    return Constructor()


@pytest.fixture
def constructor_with_base_dir(test_data_dir):
    """Constructor with base directory"""
    return Constructor(base_dir=str(test_data_dir))


@pytest.fixture(scope="session")
def absolute_path():
    """Cached absolute path for the project (avoid recomputing)"""
    return Path().absolute()


# ===== Constructor Registration Fixtures =====


@pytest.fixture(scope="session")
def registered_yaml_classes_session():
    """
    Register constructor and representer with all YAML loaders/dumpers for session scope.

    This is a session-scoped fixture for tests that need constructor registration
    but don't modify the constructor during tests.

    Yields a tuple of (loaders_list, dumpers_list, constructor, representer).
    """
    from ._internal import YAML_DUMPERS, YAML_LOADERS

    # Create constructor and representer
    constructor = Constructor(base_dir="tests/data")
    representer = None  # Only create if needed

    # Register constructor with all loaders
    for loader_cls in YAML_LOADERS:
        yaml.add_constructor(YAML_INCLUDE_TAG, constructor, loader_cls)

    yield {
        "loaders": YAML_LOADERS,
        "dumpers": YAML_DUMPERS,
        "constructor": constructor,
        "representer": representer,
    }

    # Cleanup
    cleanup_constructor(YAML_INCLUDE_TAG, YAML_LOADERS)


# ===== Loader Parametrization Fixtures =====


@pytest.fixture(params=_get_yaml_loaders())
def any_loader(request):
    """Parametrized loader fixture - tests will run for each loader"""
    return request.param


@pytest.fixture(params=["SafeLoader", "Loader"])
def common_loader(request):
    """Parametrized fixture for common loaders"""
    from yaml import Loader, SafeLoader

    return {"SafeLoader": SafeLoader, "Loader": Loader}[request.param]


# ===== HTTP Server Fixtures =====


@pytest.fixture
def http_server():
    """Configure test HTTP server (mimicking original implementation)"""

    class CustomHttpServer(http.server.ThreadingHTTPServer):
        def finish_request(self, request, client_address):
            self.RequestHandlerClass(request, client_address, self)

    httpd = None

    def serve_http():
        """Start HTTP server"""
        nonlocal httpd
        # getaddrinfo returns (family, type, proto, canonname, sockaddr)
        info = socket.getaddrinfo("127.0.0.1", 0)[0]
        family = info[0]
        addr = info[4]
        CustomHttpServer.address_family = family
        HandlerClass = http.server.SimpleHTTPRequestHandler
        httpd = CustomHttpServer(addr, HandlerClass)  # pyright: ignore[reportArgumentType]
        # Switch to project root directory so /tests/data path resolves correctly
        project_root = Path(__file__).parent.parent
        old_cwd = Path.cwd()
        os.chdir(project_root)
        try:
            httpd.serve_forever()
        finally:
            os.chdir(old_cwd)

    # Start HTTP server in background thread
    server_thread = threading.Thread(target=serve_http, daemon=True)
    server_thread.start()
    sleep(1)  # Wait for server to start

    # Get server address
    assert httpd is not None
    host, port = httpd.socket.getsockname()[:2]  # pyright: ignore[reportGeneralTypeIssues]

    yield {"host": host, "port": port, "httpd": httpd}

    # Cleanup
    httpd.shutdown()
    server_thread.join(timeout=5)


# ===== Test Data Fixtures =====


@pytest.fixture
def sample_yaml_content():
    """Sample YAML content"""
    return """
file1: !inc include.d/1.yaml
file2: !inc include.d/2.yaml
"""


# ===== Helper Functions =====


def cleanup_constructor(tag=YAML_INCLUDE_TAG, loaders=None):
    """
    Cleanup constructor registration from YAML loaders.

    Args:
        tag: The YAML tag to remove (default: "!inc")
        loaders: List of loader classes to cleanup (default: all available loaders)
    """
    if loaders is None:
        loaders = _get_yaml_loaders()

    for loader_cls in loaders:
        loader_cls.yaml_constructors.pop(tag, None)


def cleanup_representer(data_class=Data, dumpers=None):
    """
    Cleanup representer registration from YAML dumpers.

    Args:
        data_class: The data class to remove (default: Data)
        dumpers: List of dumper classes to cleanup (default: all available dumpers)
    """
    if dumpers is None:
        from yaml import Dumper, SafeDumper

        dumpers = [Dumper, SafeDumper]
        try:
            from yaml import CDumper, CSafeDumper

            dumpers.extend([CDumper, CSafeDumper])
        except ImportError:
            pass

    for dumper_cls in dumpers:
        dumper_cls.yaml_representers.pop(data_class, None)


def sort_by_name(data):
    """Sort list of dicts by 'name' key (common test pattern)"""
    return sorted(data, key=lambda m: m["name"])
