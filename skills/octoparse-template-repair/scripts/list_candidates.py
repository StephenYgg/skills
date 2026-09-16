#!/usr/bin/env python3
"""List eligible Octoparse template repair records from Feishu Base."""

import argparse
import json
import shutil
import subprocess
import sys


DEFAULT_BASE_URL = (
    "https://skieer.feishu.cn/base/VTEKb8osiaTbgoshGRhc2JQ0nsb"
    "?table=tblEsTqAFIAgzkQv&view=vewW32R8DZ"
)
DEFAULT_OWNER = "杨伟铭"
DEFAULT_STATUS = "新提交"
FIELDS = ["模板ID", "模板名称", "当前状态", "负责人", "问题描述", "问题参数"]
PAGE_SIZE = 200
MAX_PAGES = 100


class WorkflowError(RuntimeError):
    pass


def run_lark(arguments):
    command = ["lark-cli", *arguments]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=90,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-1000:]
        raise WorkflowError(f"lark-cli failed ({completed.returncode}): {detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise WorkflowError("lark-cli did not return JSON") from exc
    if not payload.get("ok"):
        raise WorkflowError(f"lark-cli returned an error: {payload.get('error') or payload}")
    return payload.get("data") or {}


def resolve_target(base_url):
    data = run_lark(["base", "+url-resolve", "--url", base_url, "--as", "user"])
    base_token = data.get("base_token")
    table_id = data.get("table_id")
    view_id = data.get("view_id")
    if not base_token or not table_id:
        raise WorkflowError("Base URL did not resolve to a base token and table ID")
    return base_token, table_id, view_id


def resolve_owner(owner_name):
    data = run_lark(
        [
            "contact",
            "+search-user",
            "--query",
            owner_name,
            "--exclude-external-users",
            "--as",
            "user",
            "--format",
            "json",
        ]
    )
    matches = [
        user
        for user in data.get("users", [])
        if (user.get("localized_name") or user.get("name")) == owner_name
    ]
    unique = {user.get("open_id"): user for user in matches if user.get("open_id")}
    if len(unique) != 1:
        raise WorkflowError(
            f"Expected one exact user named {owner_name!r}, found {len(unique)}"
        )
    return next(iter(unique.values()))


def record_pages(base_token, table_id, view_id, filter_value):
    records = []
    offset = 0
    for _ in range(MAX_PAGES):
        arguments = [
            "base",
            "+record-list",
            "--base-token",
            base_token,
            "--table-id",
            table_id,
        ]
        if view_id:
            arguments.extend(["--view-id", view_id])
        arguments.extend(["--filter-json", json.dumps(filter_value, ensure_ascii=False)])
        for field in FIELDS:
            arguments.extend(["--field-id", field])
        arguments.extend(
            [
                "--offset",
                str(offset),
                "--limit",
                str(PAGE_SIZE),
                "--format",
                "json",
                "--as",
                "user",
            ]
        )
        data = run_lark(arguments)
        rows = data.get("data") or []
        record_ids = data.get("record_id_list") or []
        fields = data.get("fields") or []
        if len(rows) != len(record_ids):
            raise WorkflowError("Base response row and record ID counts differ")
        for record_id, row in zip(record_ids, rows):
            records.append({"record_id": record_id, **dict(zip(fields, row))})
        if not data.get("has_more"):
            return records
        if not rows:
            raise WorkflowError("Base returned has_more=true with an empty page")
        offset += len(rows)
    raise WorkflowError(f"Base query exceeded the safety cap of {MAX_PAGES} pages")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--owner", default=DEFAULT_OWNER)
    parser.add_argument("--status", default=DEFAULT_STATUS)
    args = parser.parse_args()

    if shutil.which("lark-cli") is None:
        raise WorkflowError("lark-cli is not installed or not on PATH")

    base_token, table_id, view_id = resolve_target(args.base_url)
    owner = resolve_owner(args.owner)
    status_condition = ["当前状态", "==", [args.status]]
    empty_filter = {
        "logic": "and",
        "conditions": [status_condition, ["负责人", "empty", None]],
    }
    owner_filter = {
        "logic": "and",
        "conditions": [
            status_condition,
            ["负责人", "intersects", [{"id": owner["open_id"]}]],
        ],
    }

    empty_records = record_pages(base_token, table_id, view_id, empty_filter)
    owner_records = record_pages(base_token, table_id, view_id, owner_filter)
    records_by_id = {
        record["record_id"]: record for record in [*empty_records, *owner_records]
    }

    def sort_key(record):
        value = str(record.get("模板ID") or "")
        if value.isdigit():
            return 0, int(value), record["record_id"]
        return 1, value, record["record_id"]

    records = sorted(records_by_id.values(), key=sort_key)
    result = {
        "base_url": args.base_url,
        "table_id": table_id,
        "view_id": view_id,
        "status": args.status,
        "owner": {"name": args.owner, "open_id": owner["open_id"]},
        "counts": {
            "owner_empty": len(empty_records),
            "owner_matches": len(owner_records),
            "eligible_unique": len(records),
        },
        "records": records,
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    try:
        main()
    except (WorkflowError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
