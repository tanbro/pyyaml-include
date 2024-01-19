import http.server
import socket
import sys
import threading
import unittest
from pathlib import Path
from textwrap import dedent
from time import sleep
from warnings import warn

import fsspec
import yaml

from yamlinclude import YamlInclude


def _get_best_family(*address):
    infos = socket.getaddrinfo(
        *address,
        type=socket.SOCK_STREAM,
        flags=socket.AI_PASSIVE,
    )
    family, type, proto, canonname, sockaddr = next(iter(infos))
    return family, sockaddr


class CustomHttpServer(http.server.ThreadingHTTPServer):
    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self)


httpd: http.server.HTTPServer


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
    try:
        httpd.serve_forever()
    except OSError as err:
        if sys.platform.startswith("win") and err.errno == 10038:
            warn(f"{err}")
        else:
            raise
    finally:
        httpd.shutdown()


class HttpTestCase(unittest.TestCase):
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

    @classmethod
    def tearDownClass(cls):
        httpd.server_close()
        cls.server_thread.join()
        del yaml.Loader.yaml_constructors['!inc']
        yaml.Loader.construct_object

    def test_rel(self):
        file1_content = yaml.load(
            Path("tests/data/include.d/1.yaml").read_text(), yaml.Loader
        )
        yml = dedent(
            """
            file1: !inc include.d/1.yaml
            """
        )
        data = yaml.load(yml, yaml.Loader)
        self.assertDictEqual(data, {"file1": file1_content})

    def test_abs(self):
        file1_content = yaml.load(
            Path("tests/data/include.d/1.yaml").read_text(), yaml.Loader
        )
        yml = dedent(
            """
            file1: !inc /tests/data/include.d/1.yaml
            """
        )
        data = yaml.load(yml, yaml.Loader)
        self.assertDictEqual(data, {"file1": file1_content})

    def test_http_url(self):
        file1_content = yaml.load(
            Path("tests/data/include.d/1.yaml").read_text(), yaml.Loader
        )
        host, port = httpd.socket.getsockname()[:2]
        yml = dedent(
            f"""
            file1: !inc http://{host}:{port}/tests/data/include.d/1.yaml
            """
        )
        data = yaml.load(yml, yaml.Loader)
        self.assertDictEqual(data, {"file1": file1_content})

    def test_file_rel_url(self):
        file1_content = yaml.load(
            Path("tests/data/include.d/1.yaml").read_text(), yaml.Loader
        )
        yml = dedent(
            """
            file1: !inc file://tests/data/include.d/1.yaml
            """
        )
        data = yaml.load(yml, yaml.Loader)
        self.assertDictEqual(data, {"file1": file1_content})

    def test_file_abs_url(self):
        file1_content = yaml.load(
            Path("tests/data/include.d/1.yaml").read_text(), yaml.Loader
        )
        yml = dedent(
            f"""
            file1: !inc file://{Path().absolute().as_posix()}/tests/data/include.d/1.yaml
            """
        )
        data = yaml.load(yml, yaml.Loader)
        self.assertDictEqual(data, {"file1": file1_content})


if __name__ == "__main__":
    unittest.main()
