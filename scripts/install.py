#!/usr/bin/env python3
"""Link this skill into every coding-agent skills directory on the machine."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "meme-scene-explorer"

# Relative to the user's home. Only used when the parent already exists,
# except ~/.agents/skills which is created — it is the cross-runtime home.
HOME_TARGETS = [
    (Path(".agents") / "skills", True),
    (Path(".claude") / "skills", False),
    (Path(".codex") / "skills", False),
    (Path(".cursor") / "skills", False),
    (Path(".gemini") / "skills", False),
    (Path(".grok") / "skills", False),
    (Path(".github") / "skills", False),
    (Path(".config") / "opencode" / "skills", False),
    (Path(".windsurf") / "skills", False),
]


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def link_or_copy(src: Path, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        try:
            if dest.resolve() == src.resolve():
                return "already"
        except OSError:
            pass
        try:
            dest.unlink()
        except OSError:
            shutil.rmtree(dest)
    if os.name == "nt":
        try:
            import _winapi

            _winapi.CreateJunction(str(src), str(dest))
            return "junction"
        except OSError:
            pass
    try:
        os.symlink(src, dest, target_is_directory=True)
        return "symlink"
    except OSError:
        pass
    shutil.copytree(src, dest)
    return "copy"


def project_target(project: Path) -> Path:
    return project / ".agents" / "skills" / NAME


def main(argv: list[str]) -> None:
    p = argparse.ArgumentParser(
        description="Install Meme Scene Explorer into local coding-agent skill dirs."
    )
    p.add_argument(
        "--project",
        nargs="?",
        const=".",
        help="Also install into <dir>/.agents/skills (default: cwd if flag present)",
    )
    p.add_argument(
        "--home",
        default=str(Path.home()),
        help="Home directory to scan for agent skill folders",
    )
    args = p.parse_args(argv)

    if not (ROOT / "SKILL.md").is_file():
        die(f"SKILL.md missing in {ROOT}")

    home = Path(args.home).expanduser()
    installed = []

    for rel, always in HOME_TARGETS:
        parent = home / rel
        if not always and not parent.parent.exists():
            continue
        dest = parent / NAME
        kind = link_or_copy(ROOT, dest)
        installed.append((dest, kind))

    if args.project is not None:
        dest = project_target(Path(args.project).expanduser().resolve())
        kind = link_or_copy(ROOT, dest)
        installed.append((dest, kind))

    if not installed:
        die("no agent skill directories found")

    print(f"skill: {ROOT}")
    for dest, kind in installed:
        print(f"  {kind:8} {dest}")


if __name__ == "__main__":
    main(sys.argv[1:])
