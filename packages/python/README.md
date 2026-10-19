# Python workloads

Install the PyPI package into the application's existing environment, not the
system interpreter:

```sh
python -m pip install claviron-bench
```

Choose one entry point in your runner's existing configuration:

- ASGI: `claviron_bench.asgi:app`
- WSGI: `claviron_bench.wsgi:app`
- FastAPI: `claviron_bench.fastapi:app` (install the `[fastapi]` extra or use the
  application's existing FastAPI dependency).

An existing FastAPI application can explicitly `include_router` using
`claviron_bench.fastapi.router`. It then keeps its own middleware/lifespan.
The ASGI/WSGI adapters are baseline applications, not universal interceptors.
Use the runner's own lifecycle and configuration; this package owns no sockets.

Echo buffers the incoming body. The runner remains responsible for body limits.
The WSGI adapter reads the server-provided `CONTENT_LENGTH`; compare requests
with a known length, not unspecified-length streaming uploads. No worker count,
timeout, TLS policy or response cache is installed by this package.

The distribution is `claviron-bench`; the import package is `claviron_bench`.
It contains pure Python workloads, not the native Gufi module or a runner.
