#!/usr/bin/env python3
"""Tests for scripts/install.py. Real links, real directories, no mocks."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import install  # noqa: E402


def make_link(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        import _winapi

        _winapi.CreateJunction(str(src), str(dest))
    else:
        os.symlink(src, dest, target_is_directory=True)


class LinkOrCopy(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = self.tmp / "clone"
        self.src.mkdir()
        (self.src / "SKILL.md").write_text("skill", encoding="utf-8")
        self.dest = self.tmp / "skills" / install.NAME

    def test_fresh_install_links(self) -> None:
        kind = install.link_or_copy(self.src, self.dest)
        self.assertIn(kind, ("junction", "symlink", "copy"))
        self.assertTrue((self.dest / "SKILL.md").is_file())

    def test_reinstall_is_idempotent(self) -> None:
        install.link_or_copy(self.src, self.dest)
        self.assertEqual(install.link_or_copy(self.src, self.dest), "already")

    def test_dangling_link_is_replaced(self) -> None:
        """A junction left by a clone that has since moved is dangling: relink, do not crash."""
        old = self.tmp / "oldclone"
        old.mkdir()
        (old / "SKILL.md").write_text("old", encoding="utf-8")
        make_link(old, self.dest)
        shutil.rmtree(old)
        self.assertFalse(self.dest.exists())
        self.assertFalse(self.dest.is_symlink())
        self.assertTrue(os.path.lexists(self.dest))

        kind = install.link_or_copy(self.src, self.dest)
        self.assertIn(kind, ("junction", "symlink", "copy"))
        self.assertEqual((self.dest / "SKILL.md").read_text(encoding="utf-8"), "skill")

    def test_existing_directory_is_kept_without_force(self) -> None:
        self.dest.mkdir(parents=True)
        (self.dest / "my-notes.md").write_text("hand written", encoding="utf-8")
        self.assertEqual(install.link_or_copy(self.src, self.dest), "exists")
        self.assertEqual(
            (self.dest / "my-notes.md").read_text(encoding="utf-8"), "hand written"
        )

    def test_existing_directory_is_replaced_with_force(self) -> None:
        self.dest.mkdir(parents=True)
        (self.dest / "my-notes.md").write_text("hand written", encoding="utf-8")
        kind = install.link_or_copy(self.src, self.dest, force=True)
        self.assertIn(kind, ("junction", "symlink", "copy"))
        self.assertFalse((self.dest / "my-notes.md").exists())
        self.assertTrue((self.dest / "SKILL.md").is_file())

    def test_dest_inside_src_is_refused(self) -> None:
        """--project on the clone root would otherwise nest the repo inside itself."""
        dest = install.project_target(self.src)
        self.assertEqual(install.link_or_copy(self.src, dest), "self")
        self.assertFalse(dest.exists())

    def test_dest_equal_to_src_is_refused(self) -> None:
        self.assertEqual(install.link_or_copy(self.src, self.src), "self")


class Cli(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def run_script(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "install.py"), *args],
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_installs_into_a_sandboxed_home(self) -> None:
        home = self.tmp / "home"
        (home / ".claude").mkdir(parents=True)
        proc = self.run_script("--home", str(home))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((home / ".agents" / "skills" / install.NAME / "SKILL.md").is_file())
        self.assertTrue((home / ".claude" / "skills" / install.NAME / "SKILL.md").is_file())
        # .codex was absent, so it must be skipped rather than created.
        self.assertFalse((home / ".codex").exists())

    def test_project_pointing_at_the_repo_is_refused(self) -> None:
        proc = self.run_script("--home", str(self.tmp / "home"), "--project", str(ROOT))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("nest the repo inside", proc.stderr)
        self.assertFalse((ROOT / ".agents").exists())

    def test_project_into_a_real_app_works(self) -> None:
        app = self.tmp / "app"
        app.mkdir()
        proc = self.run_script("--home", str(self.tmp / "home"), "--project", str(app))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((app / ".agents" / "skills" / install.NAME / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
