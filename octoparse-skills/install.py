#!/usr/bin/env python3
"""Preview or install this collection as directory symlinks, without overwrites."""

import argparse
import os
from pathlib import Path


def install(source, destination, apply=False):
    source = Path(source).resolve()
    destination = Path(destination).expanduser()
    skills = sorted(path for path in source.iterdir() if (path / "SKILL.md").is_file())
    if not skills:
        raise ValueError("No skills found")
    actions = []
    for skill in skills:
        link = destination / skill.name
        if os.path.lexists(link):
            if link.is_symlink() and link.resolve() == skill.resolve():
                actions.append((link, skill, "already-linked"))
                continue
            raise FileExistsError(f"Refusing to replace existing path: {link}")
        actions.append((link, skill, "create-link"))
    created = []
    if apply:
        destination.mkdir(parents=True, exist_ok=True)
        try:
            for link, skill, action in actions:
                if action == "create-link":
                    link.symlink_to(skill, target_is_directory=True)
                    created.append((link, skill))
        except OSError:
            for link, skill in reversed(created):
                if link.is_symlink() and os.readlink(link) == str(skill):
                    link.unlink()
            raise
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        actions = install(Path(__file__).parent, args.destination, args.apply)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    for link, skill, action in actions:
        print(f"{action}: {link} -> {skill}")
    if not args.apply:
        print("Preview only; pass --apply to install.")


if __name__ == "__main__":
    main()
