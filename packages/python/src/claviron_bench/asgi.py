"""Dependency-free ASGI benchmark workload application."""

from .workloads import response


async def app(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            event = await receive()
            if event["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif event["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
    if scope["type"] != "http":
        raise ValueError("Only HTTP and lifespan scopes are supported")
    body = bytearray()
    while True:
        event = await receive()
        if event["type"] == "http.disconnect":
            return
        if event["type"] != "http.request":
            raise ValueError("Expected an HTTP request event")
        body.extend(event.get("body", b""))
        if not event.get("more_body", False):
            break
    status, headers, content = response(scope["path"], scope["method"], bytes(body))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": content})
