#!/usr/bin/env python3
"""Bounded read-only SeaTunnel status observations; never emit raw failed rows."""

import argparse
import json
import re
import subprocess
import time
from datetime import datetime, timezone


class MonitorError(Exception):
    pass


def call(args):
    try:
        response = subprocess.run(["bccc", *args, "--json"], capture_output=True,
                                  text=True, timeout=30, check=False)
        envelope = json.loads(response.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        raise MonitorError("Status request unavailable; raw output withheld") from None
    if response.returncode or envelope.get("status") != "success":
        raise MonitorError("Status request failed; raw output withheld")
    return envelope.get("data")


def summary(document):
    error = document.get("errorMsg") or ""
    known = []
    for marker, label in [
        ("Value length is beyond the capacity", "column_capacity"),
        ("too many filtered rows", "filtered_rows"),
        ("Access denied", "access_denied"),
        ("Communications link failure", "connection_failure"),
    ]:
        if marker in error:
            known.append(label)
    capacities = [int(value) for value in re.findall(r"\bcapacity=(\d+)\b", error)]
    metrics = document.get("metrics") or {}
    return {
        "observedAt": datetime.now(timezone.utc).isoformat(),
        "jobId": str(document.get("jobId", "")),
        "status": document.get("jobStatus"),
        "sourceReceived": metrics.get("SourceReceivedCount"),
        "sinkWritten": metrics.get("SinkWriteCount"),
        "hasError": bool(error),
        "errorCategories": known,
        "reportedCapacities": sorted(set(capacities)),
    }


def monitor(environment, runtime_id, interval, duration, emit=print):
    if not re.fullmatch(r"[1-9][0-9]{0,18}", runtime_id) or int(runtime_id) > 9223372036854775807:
        raise MonitorError("Runtime ID must be a positive Int64 string")
    if not 5 <= interval <= 300 or not 0 <= duration <= 900:
        raise MonitorError("Use interval 5..300 seconds and duration 0..900 seconds")
    if call(["info"]).get("environment") != environment:
        raise MonitorError("bccc environment does not match --environment")
    deadline = time.monotonic() + duration
    while True:
        if call(["info"]).get("environment") != environment:
            raise MonitorError("bccc environment changed during monitoring")
        document = call(["datahub", "seatunnel", "status", runtime_id])
        if str(document.get("jobId")) != runtime_id:
            raise MonitorError("Response does not match requested runtime ID")
        observed = summary(document)
        emit(json.dumps(observed))
        state = str(observed["status"] or "").upper()
        if state in {"FAILED", "CANCELED", "CANCELLED"}:
            return 2
        if state == "FINISHED" or time.monotonic() >= deadline:
            return 0
        remaining = deadline - time.monotonic()
        if remaining < interval:
            return 0
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--runtime-id", required=True)
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--duration", type=int, default=300)
    args = parser.parse_args()
    try:
        result = monitor(args.environment, args.runtime_id, args.interval, args.duration)
    except MonitorError as error:
        parser.exit(1, str(error) + "\n")
    raise SystemExit(result)


if __name__ == "__main__":
    main()
