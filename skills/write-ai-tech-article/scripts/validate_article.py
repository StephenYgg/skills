#!/usr/bin/env python3
"""Validate a publishable Markdown article and its local image package."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


MODE_LIMITS = {
    "article": {
        "min_units": 650,
        "max_units": 1100,
        "min_images": 3,
        "max_images": 4,
    },
    "post": {"min_units": 100, "max_units": 250, "min_images": 1, "max_images": 6},
}

RESTRICTED_MARKERS = (
    "/Users/",
    "OneDrive-",
    "octopus-projects",
    "projects-octoparse",
    "raw/projects-octoparse",
    "wiki/octopus-services",
    "tools/out/",
)

PLACEHOLDER_MARKERS = ("TODO", "TBD", "[待补]", "[待核实]", "<insert")
IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
CODE_FENCE_PATTERN = re.compile(r"```.*?```", re.DOTALL)


def strip_non_content(markdown: str) -> str:
    text = FRONTMATTER_PATTERN.sub("", markdown, count=1)
    text = CODE_FENCE_PATTERN.sub("", text)
    text = IMAGE_PATTERN.sub("", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s+.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[`*_~>\[\](){}|#-]", " ", text)
    return text


def count_content_units(markdown: str) -> int:
    text = strip_non_content(markdown)
    cjk_count = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", text))
    latin_word_count = len(re.findall(r"[A-Za-z0-9]+(?:[._+-][A-Za-z0-9]+)*", text))
    return cjk_count + latin_word_count


def validate_article(markdown_path: Path, mode: str) -> list[str]:
    errors: list[str] = []
    limits = MODE_LIMITS[mode]

    if not markdown_path.is_file():
        return [f"Markdown file does not exist: {markdown_path}"]

    markdown = markdown_path.read_text(encoding="utf-8")
    package_root = markdown_path.parent.resolve()

    if not re.search(r"^#\s+\S", markdown, flags=re.MULTILINE):
        errors.append("Publishable Markdown must contain an H1 title.")

    units = count_content_units(markdown)
    if not limits["min_units"] <= units <= limits["max_units"]:
        errors.append(
            f"{mode} content length is {units}; expected "
            f"{limits['min_units']}-{limits['max_units']} content units."
        )

    images = IMAGE_PATTERN.findall(markdown)
    if not limits["min_images"] <= len(images) <= limits["max_images"]:
        errors.append(
            f"{mode} references {len(images)} images; expected "
            f"{limits['min_images']}-{limits['max_images']}."
        )

    for alt_text, raw_target in images:
        if not alt_text.strip():
            errors.append(f"Image has empty alt text: {raw_target}")
        if raw_target.startswith(("http://", "https://", "data:")):
            errors.append(f"Image must be a local relative file: {raw_target}")
            continue

        target = Path(raw_target)
        if target.is_absolute():
            errors.append(f"Image path must be relative: {raw_target}")
            continue

        resolved = (package_root / target).resolve()
        try:
            resolved.relative_to(package_root)
        except ValueError:
            errors.append(f"Image path escapes the package directory: {raw_target}")
            continue

        if not resolved.is_file():
            errors.append(f"Referenced image does not exist: {raw_target}")

    for companion in ("evidence.md", "image-manifest.md"):
        if not (package_root / companion).is_file():
            errors.append(f"Required companion file is missing: {companion}")

    lowered = markdown.lower()
    for marker in PLACEHOLDER_MARKERS:
        if marker.lower() in lowered:
            errors.append(f"Unresolved placeholder found: {marker}")

    for marker in RESTRICTED_MARKERS:
        if marker.lower() in lowered:
            errors.append(f"Private or restricted path marker found: {marker}")

    if "[[" in markdown or "]]" in markdown:
        errors.append("Obsidian wikilinks are not allowed in publishable Markdown.")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path, help="Publishable Markdown file")
    parser.add_argument("--mode", choices=sorted(MODE_LIMITS), required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = validate_article(args.markdown, args.mode)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    units = count_content_units(args.markdown.read_text(encoding="utf-8"))
    images = len(IMAGE_PATTERN.findall(args.markdown.read_text(encoding="utf-8")))
    print(f"OK: {args.markdown} ({units} content units, {images} images)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
