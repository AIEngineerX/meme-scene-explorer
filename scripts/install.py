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


def is_link(path: Path) -> bool:
    """True for symlinks and for Windows junctions, which are not symlinks to Python."""
    if path.is_symlink():
        return True
    if os.name == "nt":
        try:
            return bool(os.readlink(path))
        except (OSError, ValueError):
            return False
    return False


def points_at(dest: Path, src: Path) -> bool:
    try:
        return dest.resolve() == src.resolve()
    except OSError:
        return False


def remove(path: Path) -> None:
    try:
        path.unlink()
        return
    except OSError:
        pass
    shutil.rmtree(path)


def link_or_copy(src: Path, dest: Path, force: bool = False) -> str:
    """Point dest at src. Returns what was done, or why it was left alone."""
    if dest == src or src in dest.parents:
        return "self"
    # lexists, not exists: a junction left behind by a clone that has since moved
    # is dangling, so exists() and is_symlink() are both False for it.
    if os.path.lexists(dest):
        if points_at(dest, src):
            return "already"
        if not is_link(dest) and not force:
            return "exists"
        remove(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
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
    p.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing meme-scene-explorer directory (deletes what is there)",
    )
    args = p.parse_args(argv)

    if not (ROOT / "SKILL.md").is_file():
        die(f"SKILL.md missing in {ROOT}")

    home = Path(args.home).expanduser()
    results = []

    for rel, always in HOME_TARGETS:
        parent = home / rel
        if not always and not parent.parent.exists():
            continue
        dest = parent / NAME
        results.append((dest, link_or_copy(ROOT, dest, args.force)))

    if args.project is not None:
        project = Path(args.project).expanduser().resolve()
        if project == ROOT or ROOT in project.parents:
            die(
                "--project points at the skill itself, which would nest the repo inside "
                "its own .agents/skills.\nPass the path of the app you want to vendor it into."
            )
        dest = project_target(project)
        results.append((dest, link_or_copy(ROOT, dest, args.force)))

    print(f"skill: {ROOT}")
    for dest, kind in results:
        print(f"  {kind:9} {dest}")

    if any(kind == "exists" for _, kind in results):
        print(
            "\nSome targets already hold a different meme-scene-explorer directory and were "
            "left alone.\nRe-run with --force to replace them — that deletes those directories.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main(sys.argv[1:])
