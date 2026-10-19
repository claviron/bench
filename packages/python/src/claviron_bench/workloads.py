"""Wire semantics shared by benchmark adapters; no transport or framework state."""

import json


def response(path, method, body=b""):
    allowed = {
        "/bench/plain": ("GET", "HEAD"),
        "/bench/json": ("GET", "HEAD"),
        "/bench/echo": ("POST",),
    }.get(path)
    if allowed is None:
        return 404, [(b"content-type", b"text/plain")], b"not found\n"
    if method not in allowed:
        return 405, [(b"allow", ", ".join(allowed).encode())], b""
    if path == "/bench/plain":
        content, content_type = b"ok\n", b"text/plain"
    elif path == "/bench/json":
        content = json.dumps({"message": "ok"}, separators=(",", ":")).encode()
        content_type = b"application/json"
    else:
        content, content_type = body, b"application/octet-stream"
    headers = [(b"content-type", content_type), (b"content-length", str(len(content)).encode())]
    return 200, headers, b"" if method == "HEAD" else content
