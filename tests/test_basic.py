import http.server
import socket
import threading
import unittest
from io import StringIO
from pathlib import Path
from textwrap import dedent
from time import sleep

import fsspec
import yaml

from yamlinclude import YamlInclude

from ._internal import YAML1, YAML2, YAML_LOADERS, YAML_ZH_CN


class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if cls is BaseTestCase:
            raise unittest.SkipTest(f"{cls.__name__} is an abstract base class")
        else:
            super().setUpClass()

    def test_include_one_in_mapping(self):
        yml = """
file1: !inc include.d/1.yaml
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {"file1": YAML1})

    def test_continuous_including(self):
        yml = dedent(
            """
            foo:
                - !inc include.d/1.yaml
                - !inc include.d/2.yaml
            """
        )
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(data, {"foo": [YAML1, YAML2]})

    def test_include_two_in_mapping(self):
        yml = """
a: A
file1: !inc include.d/1.yaml
b: B
file2: !inc include.d/2.yaml
c: C
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertDictEqual(
                data,
                {
                    "a": "A",
                    "file1": YAML1,
                    "b": "B",
                    "file2": YAML2,
                    "c": "C",
                },
            )

    def test_include_one_in_sequence(self):
        yml = """
- !inc include.d/1.yaml
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, [YAML1])

    def test_include_two_in_sequence(self):
        yml = """
- a
- !inc include.d/1.yaml
- b
- !inc include.d/2.yaml
- c
        """
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(data, ["a", YAML1, "b", YAML2, "c"])

    def test_include_file_not_exists(self):
        yml = """
file: !inc include.d/x.yaml
            """
        for loader_cls in YAML_LOADERS:
            with self.assertRaises(FileNotFoundError):
                yaml.load(StringIO(yml), loader_cls)

    def test_include_wildcards(self):
        yml = """
files: !inc include.d/*.yaml
"""
        for loader_cls in YAML_LOADERS:
            data = yaml.load(StringIO(yml), loader_cls)
            print(data)
            break
            self.assertListEqual(
                sorted(data["files"], key=lambda m: m["name"]), [YAML1, YAML2]
            )

    def test_include_wildcards_1(self):
        yml = """
files: !inc [include.d/**/*.yaml, [1]]
"""
        for loader_cls in YAML_LOADERS:
            # if any(
            #     name in loader_cls.__name__ for name in ("BaseLoader", "SafeLoader")
            # ):
            #     continue  # BaseLoader 和 SafeLoader不支持 !! 操作符!
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(
                sorted(data["files"], key=lambda m: m["name"]), [YAML1, YAML2]
            )

    def test_include_wildcards_2(self):
        yml = """
files: !inc [include.d/**/*.yaml, {maxdepth: 1}]
"""
        for loader_cls in YAML_LOADERS:
            # if any(name in loader_cls.__name__ for name in ("BaseLoader", "SafeLoader")):
            #     continue # BaseLoader 和 SafeLoader不支持 !! 操作符!
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(
                sorted(data["files"], key=lambda m: m["name"]), [YAML1, YAML2]
            )

    def test_include_wildcards_3(self):
        yml = """
files: !inc {urlpath: include.d/**/*.yaml, glob: {maxdepth: 1}, open: {}}
"""
        for loader_cls in YAML_LOADERS:
            # if any(name in loader_cls.__name__ for name in ("BaseLoader", "SafeLoader")):
            #     continue # BaseLoader 和 SafeLoader不支持 !! 操作符!
            data = yaml.load(StringIO(yml), loader_cls)
            self.assertListEqual(
                sorted(data["files"], key=lambda m: m["name"]), [YAML1, YAML2]
            )

    def test_abs_path(self):
        yml = dedent(
            f"""
            file1: !inc file://{Path().absolute().as_posix()}/tests/data/include.d/1.yaml
            """
        )
        data = yaml.load(yml, yaml.Loader)
        self.assertDictEqual(data, {"file1": YAML1})


class DefaultFsBasicTestCase(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ctor = YamlInclude(base_dir="tests/data")
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", ctor, loader_cls)

    @classmethod
    def tearDownClass(cls) -> None:
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors["!inc"]


class FileFsBasicTestCase(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ctor = YamlInclude(fs=fsspec.filesystem("file"), base_dir="tests/data")
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", ctor, loader_cls)

    @classmethod
    def tearDownClass(cls) -> None:
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors["!inc"]


def _get_best_family(*address):
    infos = socket.getaddrinfo(
        *address,
        type=socket.SOCK_STREAM,
        flags=socket.AI_PASSIVE,
    )
    family, type, proto, canonname, sockaddr = next(iter(infos))
    return family, sockaddr


httpd: http.server.HTTPServer


class CustomHttpServer(http.server.ThreadingHTTPServer):
    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self)


def serve_http(
    HandlerClass=http.server.SimpleHTTPRequestHandler,
    ServerClass=CustomHttpServer,
    protocol="HTTP/1.1",
    port=0,
    bind="127.0.0.1",
):
    """Test the HTTP request handler class.

    This runs an HTTP server on port 8000 (or the port argument).
    """
    global httpd
    ServerClass.address_family, addr = _get_best_family(bind, port)
    HandlerClass.protocol_version = protocol
    httpd = ServerClass(addr, HandlerClass)  # type: ignore
    host, port = httpd.socket.getsockname()[:2]
    url_host = f"[{host}]" if ":" in host else host
    print(f"Serving HTTP on {host} port {port} " f"(http://{url_host}:{port}/) ...")
    httpd.serve_forever()


class SimpleHttpBasicTestCase(BaseTestCase):
    server_thread: threading.Thread

    @classmethod
    def setUpClass(cls):
        cls.server_thread = threading.Thread(target=serve_http)
        cls.server_thread.start()
        sleep(1)
        host, port = httpd.socket.getsockname()[:2]
        ctor = YamlInclude(
            fs=fsspec.filesystem(
                "http", client_kwargs=dict(base_url=f"http://{host}:{port}")
            ),
            base_dir="/tests/data",
        )
        yaml.add_constructor("!inc", ctor, yaml.Loader)
        for loader_cls in YAML_LOADERS:
            yaml.add_constructor("!inc", ctor, loader_cls)

    @classmethod
    def tearDownClass(cls):
        httpd.shutdown()
        cls.server_thread.join()
        for loader_class in YAML_LOADERS:
            del loader_class.yaml_constructors["!inc"]

    def setUp(self) -> None:
        self.assertTrue(self.server_thread.is_alive())

    def test_yaml1(self):
        host, port = httpd.socket.getsockname()[:2]
        yml = dedent(
            f"""
            file1: !inc http://{host}:{port}/tests/data/include.d/1.yaml
            """
        )
        data = yaml.load(yml, yaml.Loader)
        self.assertDictEqual(data, {"file1": YAML1})

    def test_independent_http_url_and_zh_cn(self):
        host, port = httpd.socket.getsockname()[:2]
        yml = dedent(
            f"""
            file1: !inc http://{host}:{port}/tests/data/zh_cn.yaml
            """
        )
        data = yaml.load(yml, yaml.Loader)
        self.assertDictEqual(data, {"file1": YAML_ZH_CN})


if __name__ == "__main__":
    unittest.main()
