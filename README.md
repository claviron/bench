# Claviron Bench

Reusable Python/PHP workloads and explicit measurement scripts. This is an
independent, multi-language project, not a server, runner or interpreter extension.
The native Rust baseline stays in `claviron-bench`; it is not copied here.

## Layout

- `packages/python`: dependency-free ASGI and WSGI applications, plus an
  optional FastAPI adapter.
- `packages/php`: plain PHP entry point, Laravel route file and Symfony
  attribute controller, distributed through one optional Composer package.
- `scripts/run.py`: repeated HTTP/1 load rounds through `wrk`, with explicit
  rest periods and optional per-PID RSS samples.
- `scripts/exec.sh`: optional resource/allocator settings around a caller's
  existing launch command. No build or runner-specific command is invented.
- `results`: local raw output and metadata, ignored by Git.

The source repository is `claviron/bench`. The PHP package is `claviron/bench`
on Packagist, using the `Claviron\Bench` namespace. Its distribution repository,
`claviron/php-bench`, receives only the PHP package and license, with
`composer.json` at its root. Python's `claviron-bench` package lives under
`packages/python` and is imported as `claviron_bench`;
JavaScript workloads can be added independently under `packages/javascript`.
These are language-level workloads, not Gufi or Lumenize runtime bindings.

## Workload contract

| Path | Method | Response |
| --- | --- | --- |
| `/bench/plain` | GET, HEAD | `ok\n`, `text/plain` |
| `/bench/json` | GET, HEAD | Per-request serialization of `{"message":"ok"}` |
| `/bench/echo` | POST | Exact input bytes, `application/octet-stream` |

The language echo adapters buffer request bodies; Claviron's native echo can
stream them. Record body size and do not describe this as identical streaming
behavior. HEAD returns the GET response headers without its body. All workloads
avoid persistence and intentional waits. Framework middleware remains part of
the measured application; adapters do not silently disable it.

Use language/framework routes rather than a runner's native Rust interceptor
when measuring Python or PHP. An application running under Gufi or Lumenize
does not by itself make a native `/bench` handler a language measurement.

## Install in an application

See [Python adapters](packages/python/README.md) and
[PHP/framework adapters](packages/php/README.md). Install them in development
environments only; route registration is explicit, not package auto-discovery.
Existing application repositories remain independent and are not moved here.

PHP applications install `claviron/bench` from Packagist as a development
dependency and explicitly register its routes. No sibling checkout or Composer
path repository is required. Keep application entry points, middleware and
lifespans unchanged. Refresh cached framework configuration and routes when
changing a benchmark boot flag. Install optional benchmark dependencies before
enabling their routes; a lockfile alone does not install them.

## Measure an already-running server

The following numbers are illustrative caller choices, not script defaults:

```sh
python3 scripts/run.py \
  --label symfony-lumenize-orbit \
  --url https://bench.example.test/bench/json \
  --workload json \
  --connections 1024 --threads 8 --duration 60 --timeout 10 \
  --rounds 5 --rest 60 --sample-interval 1 \
  --pid 1234 --pid 1235 \
  --output results/symfony-lumenize-orbit
```

Output paths must not already exist. The script verifies the endpoint response
before generating load; this single request is not a defined warm-up period.
For echo, supply `--body FILE`. URL query strings are supported. `wrk` measures
HTTP/1, including over TLS; it does not measure HTTP/2 or HTTP/3. Certificate
validation occurs during the Python preflight; configure trust externally.

Each round retains raw `wrk` output. `run.json` records caller parameters,
platform/tool versions, commands, phase timing and outcomes. `memory.csv`
records RSS in KiB for each PID during both load and rest. Only those PIDs are
sampled; worker replacements are not silently substituted. A vanished PID is
recorded as missing. RSS is neither heap allocation nor macOS physical footprint.
The load generator shares the host unless you run this script elsewhere.

The script does not retry failures, clear Orbit SHM, change service settings,
adjust logging or restart between rounds. Check raw output for socket errors
and non-success responses before using throughput numbers.

## Launch settings

```sh
scripts/exec.sh --open-files 8192 --mimalloc-purge-delay 0 -- \
  ./start-application.sh --bench --release --no-build
```

Settings apply only to the launched command and its descendants. The underlying
launch script still owns build/start behavior. Omit settings to keep inherited
values. A mimalloc setting has no effect on a runner that does not use mimalloc.
No privileged system/launchd configuration is changed.

## Comparison discipline

Record application/runner/framework versions, release/debug mode, worker count,
allocator settings, transport, TLS, body size and server-side logs with a run.
Keep these inputs fixed when comparing memory across rounds. Compare the same
language workload on different runners, or native versus language handlers on
one runner; do not blend both axes into an unexplained speed claim.

No server has been started and no live measurements have been made as part of
creating this project.
