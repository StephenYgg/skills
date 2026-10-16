#!/usr/bin/env python3
"""Offline CLI fixture. Only reads/writes its explicit test state file."""

import json
import os
from pathlib import Path
import sys


state_path = Path(os.environ["OCTOPARSE_SKILL_TEST_STATE"])
state = json.loads(state_path.read_text())
arguments = [value for value in sys.argv[1:] if value != "--json"]
if arguments == ["info"]:
    data = {"environment": state["environment"]}
elif arguments[:3] == ["datahub", "job", "get"]:
    assert arguments[3] == state["job"]["id"]
    data = state["job"]
elif arguments[:3] == ["datahub", "job", "update"]:
    assert arguments[3] == state["job"]["id"]
    request = json.loads(Path(arguments[arguments.index("--file") + 1]).read_text())
    state["job"] = request
    state["writes"] += 1
    state_path.write_text(json.dumps(state))
    data = state["job"]
elif arguments[:3] == ["datahub", "seatunnel", "status"]:
    assert arguments[3] == state["runtime"]["jobId"]
    data = state["runtime"]
else:
    raise SystemExit("Offline fixture rejected unexpected command")
print(json.dumps({"status": "success", "data": data}))
