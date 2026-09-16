#!/usr/bin/env python3
"""Download one current Octoparse RuleFile into an id-slug directory."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


DEFAULT_API_BASE = "https://webapi.octoparse.com/v1/templateService"
MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
HTTP_TIMEOUT_SECONDS = 60
MAX_ATTEMPTS = 3


class WorkflowError(RuntimeError):
    pass


def request_json(url, token=None):
    headers = {"Accept": "application/json", "User-Agent": "octoparse-template-repair/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    last_error = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            with urlopen(Request(url, headers=headers), timeout=HTTP_TIMEOUT_SECONDS) as response:
                payload = json.load(response)
            if payload.get("error") is not None:
                raise WorkflowError(f"Admin API returned an error: {payload['error']}")
            if "data" not in payload:
                raise WorkflowError("Admin API response is missing data")
            return payload["data"]
        except HTTPError as exc:
            if 400 <= exc.code < 500:
                raise WorkflowError(f"Admin API HTTP {exc.code}") from exc
            last_error = exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
        if attempt + 1 < MAX_ATTEMPTS:
            time.sleep(0.5 * (2**attempt))
    raise WorkflowError(f"Admin API request failed after {MAX_ATTEMPTS} attempts: {last_error}")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_slug(slug):
    if not slug or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", slug):
        raise WorkflowError(f"Unsafe or missing template slug: {slug!r}")
    return slug


def rule_filename(rule_url, version_type):
    name = Path(unquote(urlparse(rule_url).path)).name
    if name and name not in {".", ".."} and "\x00" not in name:
        return name
    suffix = ".py" if version_type == 8 else ".rule"
    return f"rule-file{suffix}"


def existing_metadata(path, expected):
    if not path.exists():
        return False
    try:
        actual = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot validate existing metadata: {path}") from exc
    if actual != expected:
        raise WorkflowError(
            f"Existing metadata differs from the current Admin API snapshot: {path}"
        )
    return True


def write_exclusive(path, content):
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        if path.read_bytes() != content:
            raise WorkflowError(f"Concurrent or existing metadata conflict: {path}")
        return
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def download_rule_file(rule_url, target_directory, destination):
    request = Request(rule_url, headers={"User-Agent": "octoparse-template-repair/1.0"})
    temp_path = None
    try:
        with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
                raise WorkflowError("RuleFile exceeds the 50 MiB safety limit")
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=".rulefile-",
                suffix=".part",
                dir=target_directory,
                delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                size = 0
                digest = hashlib.sha256()
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_DOWNLOAD_BYTES:
                        raise WorkflowError("RuleFile exceeds the 50 MiB safety limit")
                    handle.write(chunk)
                    digest.update(chunk)
                handle.flush()
                os.fsync(handle.fileno())
        if size == 0:
            raise WorkflowError("Downloaded RuleFile is empty")
        try:
            os.link(temp_path, destination)
        except FileExistsError:
            if sha256_file(destination) != digest.hexdigest():
                raise WorkflowError(f"Existing RuleFile differs; refusing to overwrite: {destination}")
        return size, digest.hexdigest()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise WorkflowError(f"RuleFile download failed: {type(exc).__name__}") from exc
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-id", required=True, type=int)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument(
        "--token-env",
        default="OCTOPARSE_ADMIN_TOKEN",
        help="Optional bearer-token environment variable name",
    )
    args = parser.parse_args()

    if args.template_id <= 0:
        raise WorkflowError("template ID must be positive")
    api_base = args.api_base.rstrip("/")
    token = os.environ.get(args.token_env)
    template = request_json(f"{api_base}/admin/templates/{args.template_id}", token)
    if template.get("id") != args.template_id:
        raise WorkflowError("Template response ID does not match the requested ID")
    current = template.get("currentVersion") or {}
    version_id = current.get("templateVersionId")
    if not isinstance(version_id, int) or version_id <= 0:
        raise WorkflowError("Template has no valid current version ID")
    version = request_json(
        f"{api_base}/admin/templates/{args.template_id}/versions/{version_id}", token
    )
    if version.get("templateId") != args.template_id or version.get("id") != version_id:
        raise WorkflowError("Version response does not match the requested current version")
    rule_url = version.get("ruleFile")
    if not isinstance(rule_url, str) or not rule_url.strip():
        raise WorkflowError("Current version has no RuleFile URL")

    slug = validate_slug(template.get("slug"))
    workspace = Path(args.workspace).expanduser().resolve()
    if not workspace.is_dir():
        raise WorkflowError(f"Workspace is not a directory: {workspace}")
    target_directory = workspace / f"{args.template_id}-{slug}"
    target_directory.mkdir(mode=0o755, exist_ok=True)
    if target_directory.is_symlink():
        raise WorkflowError(f"Target directory must not be a symlink: {target_directory}")
    fixed_directory = target_directory / "fixed"
    fixed_directory.mkdir(mode=0o755, exist_ok=True)
    if fixed_directory.is_symlink():
        raise WorkflowError(f"Fixed directory must not be a symlink: {fixed_directory}")

    destination = target_directory / rule_filename(rule_url, version.get("type"))
    metadata = {
        "templateId": args.template_id,
        "templateName": template.get("name"),
        "slug": slug,
        "currentVersionId": version_id,
        "version": version.get("version"),
        "type": version.get("type"),
        "ruleFile": rule_url,
        "parameters": version.get("parameters"),
        "settings": version.get("settings"),
    }
    metadata_path = target_directory / "template-metadata.json"
    existing_metadata(metadata_path, metadata)
    size, digest = download_rule_file(rule_url, target_directory, destination)
    metadata_bytes = (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    write_exclusive(metadata_path, metadata_bytes)

    result = {
        "directory": str(target_directory),
        "rule_file": str(destination),
        "bytes": size,
        "sha256": digest,
        "template_id": args.template_id,
        "slug": slug,
        "current_version_id": version_id,
        "version": version.get("version"),
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    try:
        main()
    except WorkflowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
