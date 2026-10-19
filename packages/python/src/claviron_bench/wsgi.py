"""Dependency-free WSGI benchmark workload application."""

from http import HTTPStatus

from .workloads import response


def app(environ, start_response):
    length = int(environ.get("CONTENT_LENGTH") or "0")
    body = environ["wsgi.input"].read(length) if length else b""
    status, headers, content = response(environ["PATH_INFO"], environ["REQUEST_METHOD"], body)
    start_response(
        f"{status} {HTTPStatus(status).phrase}",
        [(name.decode("ascii"), value.decode("ascii")) for name, value in headers],
    )
    return [content]
