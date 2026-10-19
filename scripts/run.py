#!/usr/bin/env python3
"""Run declared HTTP/1 load rounds without owning the target server."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite positive number")
    return number


def natural(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def processes(pids):
    if not pids:
        return {}
    result = subprocess.run(
        ["ps", "-p", ",".join(map(str, pids)), "-o", "pid=", "-o", "rss=", "-o", "lstart="],
        capture_output=True, text=True,
    )
    if result.returncode not in (0, 1) or result.stderr.strip():
        raise RuntimeError(f"RSS sampling failed: {result.stderr.strip()}")
    entries = {}
    for line in result.stdout.splitlines():
        pid, rss, started = line.strip().split(maxsplit=2)
        entries[int(pid)] = (int(rss), started)
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--url", required=True, help="complete workload URL")
    parser.add_argument("--workload", required=True, choices=["plain", "json", "echo"])
    parser.add_argument("--body", type=Path, help="required only for echo")
    parser.add_argument("--connections", required=True, type=natural)
    parser.add_argument("--threads", required=True, type=natural)
    parser.add_argument("--duration", required=True, type=positive, help="seconds per load round")
    parser.add_argument("--timeout", required=True, type=positive, help="request timeout in seconds")
    parser.add_argument("--rounds", required=True, type=natural)
    parser.add_argument("--rest", required=True, type=positive, help="seconds of rest after every round")
    parser.add_argument("--sample-interval", required=True, type=positive, help="RSS cadence in seconds")
    parser.add_argument("--pid", action="append", type=natural, default=[])
    parser.add_argument("--output", required=True, type=Path, help="new result directory")
    args = parser.parse_args()
    url = urlsplit(args.url)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.fragment:
        parser.error("URL must be HTTP(S), without embedded credentials or a fragment")
    if args.threads > args.connections:
        parser.error("threads cannot exceed connections")
    if (args.workload == "echo") != (args.body is not None):
        parser.error("echo requires --body; other workloads do not accept it")
    wrk = shutil.which("wrk")
    if wrk is None:
        parser.error("wrk must already be installed on PATH")
    args.pid = list(dict.fromkeys(args.pid))
    initial = processes(args.pid)
    if set(initial) != set(args.pid):
        parser.error("all requested PIDs must exist before measurement")
    payload = args.body.read_bytes() if args.body else None
    args.output.mkdir(parents=True, exist_ok=False)
    metadata = {
        "started_at": timestamp(), "label": args.label,
        "parameters": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
        "platform": platform.platform(), "python": sys.version,
        "wrk_version": subprocess.run([wrk, "--version"], capture_output=True, text=True).stdout.strip(),
        "protocol": "HTTP/1", "memory_metric": "RSS KiB, not physical footprint",
        "initial_processes": initial, "rounds": [], "outcome": "incomplete",
    }
    if payload is not None:
        metadata["body"] = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    command = [
        wrk, "--latency", "-c", str(args.connections), "-t", str(args.threads),
        "-d", f"{args.duration:g}s", "--timeout", f"{args.timeout:g}s",
    ]
    if args.body:
        command.extend(["-s", str(Path(__file__).with_name("echo.lua"))])
    command.append(args.url)
    if args.body:
        command.extend(["--", str(args.body.resolve())])
    metadata["command"] = command
    active = None
    memory_changed = False
    try:
        request = Request(args.url, data=payload, headers={"Content-Type": "application/octet-stream"} if payload is not None else {})
        with urlopen(request, timeout=args.timeout) as reply:
            content = reply.read()
            expected_type = {"plain": "text/plain", "json": "application/json", "echo": "application/octet-stream"}[args.workload]
            if reply.status != 200 or reply.headers.get_content_type() != expected_type:
                raise RuntimeError("Preflight returned an unexpected status or content type")
            valid = (
                content == b"ok\n" if args.workload == "plain" else
                json.loads(content) == {"message": "ok"} if args.workload == "json" else
                content == payload
            )
            if not valid or reply.url != args.url:
                raise RuntimeError("Preflight response did not match the requested workload URL")
        metadata["preflight"] = "passed"
        with (args.output / "memory.csv").open("w", newline="") as memory:
            writer = csv.writer(memory)
            writer.writerow(["time_utc", "round", "phase", "pid", "rss_kib", "state"])

            def sample(round_number, phase):
                nonlocal memory_changed
                current = processes(args.pid)
                for pid in args.pid:
                    entry = current.get(pid)
                    state = "missing" if entry is None else "same" if entry[1] == initial[pid][1] else "replaced"
                    if state != "same":
                        memory_changed = True
                    writer.writerow([timestamp(), round_number, phase, pid, entry[0] if state == "same" else "", state])
                memory.flush()

            for number in range(1, args.rounds + 1):
                print(f"Round {number}/{args.rounds}: load", flush=True)
                record = {"round": number, "load_started_at": timestamp()}
                metadata["rounds"].append(record)
                sample(number, "load")
                log_path = args.output / f"round-{number:02d}.txt"
                with log_path.open("w") as log:
                    active = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
                    while True:
                        try:
                            record["exit_code"] = active.wait(timeout=args.sample_interval)
                            break
                        except subprocess.TimeoutExpired:
                            sample(number, "load")
                    active = None
                record["load_ended_at"] = timestamp()
                sample(number, "load")
                text = log_path.read_text()
                record["reported_errors"] = bool(re.search(r"Socket errors:|Non-2xx or 3xx responses:", text))
                if record["exit_code"] != 0:
                    raise RuntimeError(f"wrk failed in round {number}; see {log_path}")
                print(f"Round {number}/{args.rounds}: rest", flush=True)
                record["rest_started_at"] = timestamp()
                rest_end = time.monotonic() + args.rest
                while True:
                    sample(number, "rest")
                    remaining = rest_end - time.monotonic()
                    if remaining <= 0:
                        break
                    time.sleep(min(args.sample_interval, remaining))
                record["rest_ended_at"] = timestamp()
        metadata["process_identity_changed"] = memory_changed
        failed = memory_changed or any(row["reported_errors"] for row in metadata["rounds"])
        metadata["outcome"] = "completed_with_errors" if failed else "completed"
        return 1 if failed else 0
    except (Exception, KeyboardInterrupt) as error:
        metadata["outcome"] = "interrupted" if isinstance(error, KeyboardInterrupt) else "failed"
        metadata["error"] = str(error) or type(error).__name__
        print(metadata["error"], file=sys.stderr)
        return 1
    finally:
        if active is not None and active.poll() is None:
            # Only the load generator belongs to this script; never signal the server.
            try:
                active.send_signal(signal.SIGINT)
            except ProcessLookupError:
                pass
            active.wait()
        metadata["ended_at"] = timestamp()
        (args.output / "run.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(f"Results: {args.output}")


if __name__ == "__main__":
    raise SystemExit(main())
