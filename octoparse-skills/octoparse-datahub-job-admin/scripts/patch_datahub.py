#!/usr/bin/env python3
"""Preview/apply a narrow bccc Job or Plan replacement, without printing secrets."""

import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile


class ContractError(Exception):
    pass


FIELDS = {
    "job": ("id", "name", "description", "jobType", "jobConfig", "jobParameters"),
    "plan": ("name", "description", "cron", "runType"),
}


def call(args):
    try:
        result = subprocess.run(["bccc", *args, "--json"], capture_output=True,
                                text=True, timeout=45, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ContractError("bccc unavailable or timed out; re-read server state before retrying") from None
    try:
        envelope = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise ContractError("Invalid bccc response; raw output withheld") from None
    if result.returncode or envelope.get("status") != "success":
        raise ContractError("bccc request failed; raw output withheld; re-read before retrying")
    return envelope.get("data")


def check_environment(expected):
    if call(["info"]).get("environment") != expected:
        raise ContractError("bccc environment does not match --environment")


def body(kind, document):
    try:
        result = {key: copy.deepcopy(document[key]) for key in FIELDS[kind]}
    except KeyError:
        raise ContractError("Definition is missing required replacement fields") from None
    if kind == "job":
        try:
            result["jobParameters"] = [{key: item[key] for key in ("name", "description")}
                                       for item in result["jobParameters"]]
        except (KeyError, TypeError):
            raise ContractError("Invalid job parameter definitions") from None
    return result


def validate(kind, request, original):
    if not isinstance(request["name"], str) or not request["name"].strip():
        raise ContractError("name must be a nonempty string")
    if not isinstance(request["description"], str):
        raise ContractError("description must be a string")
    if kind == "job":
        if request["id"] != original["id"]:
            raise ContractError("Job identity cannot be changed")
        if len(request["name"]) > 64 or len(request["description"]) > 128:
            raise ContractError("Job name/description exceeds CLI limits")
        if type(request["jobType"]) is not int or request["jobType"] not in range(4):
            raise ContractError("Invalid jobType")
        if not isinstance(request["jobConfig"], str) or not request["jobConfig"].strip():
            raise ContractError("jobConfig must be a nonempty serialized string")
        if not isinstance(request["jobParameters"], list):
            raise ContractError("jobParameters must be a list")
    else:
        if request["name"] != original["name"]:
            raise ContractError("Plan rename needs separate recurring-job cleanup; not supported here")
        if type(request["runType"]) is not int or request["runType"] not in range(3):
            raise ContractError("Invalid runType")
        if not isinstance(request["cron"], str) or not request["cron"].strip():
            raise ContractError("cron must be a nonempty string")


def patch_definition(kind, identity, patch, environment, apply=False):
    if not isinstance(patch, dict) or not patch:
        raise ContractError("Patch must be a nonempty object")
    if set(patch) - (set(FIELDS[kind]) - {"id"}):
        raise ContractError("Patch contains unsupported fields; Steps must be updated separately")
    check_environment(environment)
    original = call(["datahub", kind, "get", identity])
    if original.get("id") != identity:
        raise ContractError("Response does not match requested definition ID")
    before = body(kind, original)
    request = {**before, **patch}
    validate(kind, request, before)
    changed = sorted(key for key in patch if request[key] != before[key])
    report = {"environment": environment, "kind": kind, "id": identity,
              "changedFields": changed, "applied": False}
    if not apply or not changed:
        return report
    check_environment(environment)
    fresh = call(["datahub", kind, "get", identity])
    if fresh.get("id") != identity or body(kind, fresh) != before or (kind == "plan" and fresh.get("jobPlanSteps") != original.get("jobPlanSteps")):
        raise ContractError("Definition changed concurrently; refusing replacement")
    # Private transient full bodies may contain secrets; never print them.
    with tempfile.TemporaryDirectory(prefix="datahub-patch-") as directory:
        path = Path(directory) / "request.json"
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(request, output, ensure_ascii=False)
        call(["datahub", kind, "update", identity, "--file", str(path), "--yes"])
    persisted = call(["datahub", kind, "get", identity])
    if persisted.get("id") != identity or body(kind, persisted) != request:
        raise ContractError("Readback differs after update; do not blindly retry")
    if kind == "plan" and persisted.get("jobPlanSteps") != original.get("jobPlanSteps"):
        raise ContractError("Plan Steps changed during update; investigate before retrying")
    report["applied"] = True
    report["preservedFieldsVerified"] = True
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=FIELDS, required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        patch = json.loads(args.patch.read_text(encoding="utf-8"))
        result = patch_definition(args.kind, args.id, patch, args.environment, args.apply)
    except (ContractError, OSError, ValueError) as error:
        # File/JSON errors can carry secret substrings; do not echo them.
        message = str(error) if isinstance(error, ContractError) else "Cannot read/parse patch file; details withheld"
        parser.exit(1, message + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
