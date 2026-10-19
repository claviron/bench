"""Workload contracts without a listener, runner or external service."""

import io
import unittest

from claviron_bench.asgi import app as asgi
from claviron_bench.workloads import response
from claviron_bench.wsgi import app as wsgi


class WorkloadTests(unittest.TestCase):
    def test_plain_json_and_head(self):
        for path, expected in [
            ("/bench/plain", b"ok\n"),
            ("/bench/json", b'{"message":"ok"}'),
        ]:
            with self.subTest(path=path):
                status, headers, body = response(path, "GET")
                self.assertEqual(status, 200)
                self.assertEqual(body, expected)
                self.assertEqual(dict(headers)[b"content-length"], str(len(body)).encode())
                self.assertEqual(response(path, "HEAD"), (status, headers, b""))

    def test_echo_preserves_binary_and_errors_are_explicit(self):
        body = b"\x00\xffecho"
        status, headers, echoed = response("/bench/echo", "POST", body)
        self.assertEqual((status, echoed), (200, body))
        self.assertEqual(dict(headers)[b"content-type"], b"application/octet-stream")
        self.assertEqual(response("/missing", "GET")[0], 404)
        status, headers, body = response("/bench/plain", "POST")
        self.assertEqual((status, body), (405, b""))
        self.assertEqual(dict(headers)[b"allow"], b"GET, HEAD")

    def test_wsgi_reads_only_the_declared_body(self):
        for method, path, length in [("POST", "/bench/echo", 3), ("HEAD", "/bench/plain", 0)]:
            with self.subTest(method=method):
                captured = []
                body = b"".join(wsgi({
                    "REQUEST_METHOD": method, "PATH_INFO": path,
                    "CONTENT_LENGTH": str(length), "wsgi.input": io.BytesIO(b"abc-extra"),
                }, lambda status, headers: captured.append((status, dict(headers)))))
                self.assertEqual(captured[0][0], "200 OK")
                self.assertEqual(body, b"abc" if length else b"")
                self.assertEqual(captured[0][1]["content-length"], "3")


class AsgiTests(unittest.IsolatedAsyncioTestCase):
    async def call(self, scope, incoming):
        sent = []

        async def receive():
            return incoming.pop(0)

        async def send(message):
            sent.append(message)

        await asgi(scope, receive, send)
        return sent

    async def test_chunked_echo(self):
        sent = await self.call({"type": "http", "path": "/bench/echo", "method": "POST"}, [
            {"type": "http.request", "body": b"\x00", "more_body": True},
            {"type": "http.request", "body": b"\xff", "more_body": False},
        ])
        self.assertEqual(sent[0]["status"], 200)
        self.assertEqual(sent[1]["body"], b"\x00\xff")

    async def test_disconnect_does_not_send_a_response(self):
        sent = await self.call({"type": "http", "path": "/bench/echo", "method": "POST"}, [
            {"type": "http.disconnect"},
        ])
        self.assertEqual(sent, [])

    async def test_lifespan(self):
        sent = await self.call({"type": "lifespan"}, [
            {"type": "lifespan.startup"}, {"type": "lifespan.shutdown"},
        ])
        self.assertEqual([event["type"] for event in sent], [
            "lifespan.startup.complete", "lifespan.shutdown.complete",
        ])


class FastapiTests(unittest.IsolatedAsyncioTestCase):
    async def test_adapter_preserves_workload_responses(self):
        try:
            from fastapi import Request
            from claviron_bench.fastapi import bench
        except ModuleNotFoundError:
            self.skipTest("The optional FastAPI dependency is not installed")
        for method, path in [("GET", "/bench/json"), ("HEAD", "/bench/plain"), ("POST", "/bench/echo")]:
            with self.subTest(method=method):
                async def receive():
                    return {"type": "http.request", "body": b"\xffecho"}

                request = Request({
                    "type": "http", "method": method, "path": path,
                    "query_string": b"", "headers": [], "scheme": "http",
                    "server": ("example.test", 80),
                }, receive)
                reply = await bench(request)
                status, headers, body = response(path, method, b"\xffecho")
                self.assertEqual(reply.status_code, status)
                self.assertEqual(reply.body, body)
                for name, value in headers:
                    self.assertEqual(reply.headers[name.decode()], value.decode())


if __name__ == "__main__":
    unittest.main()
