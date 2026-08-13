#!/usr/bin/env python3
"""Tests for scripts/explore.py. Real code, real files, no mocks."""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import explore  # noqa: E402


def ns(**kw) -> argparse.Namespace:
    base = dict(prompt_file=None, world=None)
    base.update(kw)
    return argparse.Namespace(**base)


def make_standin(tmp: Path, script: str, name: str = "higgsfield") -> str:
    """Write an executable stand-in for the higgsfield binary and return its path."""
    py = tmp / f"{name}_standin.py"
    py.write_text(script, encoding="utf-8")
    if os.name == "nt":
        launcher = tmp / f"{name}.bat"
        launcher.write_text(f'@echo off\r\n"{sys.executable}" "{py}" %*\r\n', encoding="utf-8")
    else:
        launcher = tmp / name
        launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{py}" "$@"\n', encoding="utf-8")
        launcher.chmod(0o755)
    return str(launcher)


class LoadPrompt(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_skeleton_substitutes_world(self) -> None:
        prompt = explore.load_prompt(ns(world="a dusty farm at golden hour"))
        self.assertIn("a dusty farm at golden hour", prompt)
        self.assertNotIn(explore.WORLD_TOKEN, prompt)

    def test_skeleton_falls_back_to_default_world(self) -> None:
        prompt = explore.load_prompt(ns())
        self.assertIn(explore.DEFAULT_WORLD, prompt)
        self.assertNotIn(explore.WORLD_TOKEN, prompt)

    def test_braces_in_skeleton_are_literal(self) -> None:
        """A user editing the skeleton must not hit a str.format KeyError."""
        edited = self.tmp / "skeleton.txt"
        edited.write_text(
            explore.SKELETON_PATH.read_text(encoding="utf-8") + "\nuse {brackets} here\n",
            encoding="utf-8",
        )
        original = explore.SKELETON_PATH
        explore.SKELETON_PATH = edited
        self.addCleanup(setattr, explore, "SKELETON_PATH", original)
        prompt = explore.load_prompt(ns(world="a farm"))
        self.assertIn("use {brackets} here", prompt)
        self.assertIn("a farm", prompt)

    def test_prompt_file_is_used_verbatim(self) -> None:
        f = self.tmp / "filled.txt"
        f.write_text("stage one, stage two", encoding="utf-8")
        self.assertEqual(explore.load_prompt(ns(prompt_file=str(f))), "stage one, stage two")

    def test_world_with_prompt_file_is_rejected(self) -> None:
        f = self.tmp / "filled.txt"
        f.write_text("stage one", encoding="utf-8")
        with self.assertRaises(SystemExit):
            explore.load_prompt(ns(prompt_file=str(f), world="a farm"))

    def test_unfilled_placeholder_is_rejected(self) -> None:
        """Passing the raw skeleton as --prompt-file must not ship '{world}' to a paid job."""
        with self.assertRaises(SystemExit):
            explore.load_prompt(ns(prompt_file=str(explore.SKELETON_PATH)))

    def test_empty_prompt_file_is_rejected(self) -> None:
        f = self.tmp / "empty.txt"
        f.write_text("   \n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            explore.load_prompt(ns(prompt_file=str(f)))

    def test_missing_prompt_file_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            explore.load_prompt(ns(prompt_file=str(self.tmp / "nope.txt")))


class UrlExtraction(unittest.TestCase):
    def test_media_urls_match(self) -> None:
        for text, want in [
            ("Job done. https://cdn.higgsfield.ai/out/a.mp4", "https://cdn.higgsfield.ai/out/a.mp4"),
            ("Result: https://cdn.x/a.mp4?sig=z&exp=1", "https://cdn.x/a.mp4?sig=z&exp=1"),
            ("ok (https://cdn.x/y.webm).", "https://cdn.x/y.webm"),
        ]:
            m = explore.MEDIA_URL_RE.search(text)
            self.assertIsNotNone(m, text)
            self.assertEqual(m.group(0).rstrip(").,]"), want)

    def test_non_media_urls_do_not_match(self) -> None:
        """A dashboard or pricing link must never be treated as the result video."""
        for text in [
            "Visit https://higgsfield.ai/pricing to add credits.",
            "Timeout. Check https://higgsfield.ai/dashboard/jobs/abc-123",
        ]:
            self.assertIsNone(explore.MEDIA_URL_RE.search(text), text)
            self.assertIsNotNone(explore.ANY_URL_RE.search(text), text)


class OutputNaming(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_does_not_clobber_earlier_takes(self) -> None:
        first = explore.unique_dest(self.tmp, "puppy")
        self.assertEqual(first.name, "puppy_mse.mp4")
        first.write_bytes(b"take one")
        second = explore.unique_dest(self.tmp, "puppy")
        self.assertEqual(second.name, "puppy_mse-2.mp4")
        second.write_bytes(b"take two")
        self.assertEqual(explore.unique_dest(self.tmp, "puppy").name, "puppy_mse-3.mp4")
        self.assertEqual(first.read_bytes(), b"take one")


class ArgParsing(unittest.TestCase):
    def test_defaults_match_the_locked_contract(self) -> None:
        a = explore.parse_args(["meme.jpg"])
        self.assertEqual((a.duration, a.aspect, a.resolution), (15, "21:9", "720p"))

    def test_invalid_enums_are_rejected_before_the_api_call(self) -> None:
        for bad in [["m.jpg", "--aspect", "2.39:1"], ["m.jpg", "--resolution", "1080p"]]:
            with self.assertRaises(SystemExit):
                explore.parse_args(bad)

    def test_valid_enums_are_accepted(self) -> None:
        self.assertEqual(explore.parse_args(["m.jpg", "--aspect", "16:9"]).aspect, "16:9")
        self.assertEqual(explore.parse_args(["m.jpg", "--resolution", "480p"]).resolution, "480p")


class RequireAuth(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def standin(self, out: str, code: int) -> str:
        return make_standin(self.tmp, f"import sys\nprint({out!r})\nsys.exit({code})\n")

    def test_logged_in_returns_the_status_line(self) -> None:
        out = explore.require_auth(
            self.standin("you@example.com - starter plan, 109 credits", 0)
        )
        self.assertIn("109 credits", out)

    def test_expired_session_says_log_in(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit):
                explore.require_auth(self.standin("session expired", 1))
        self.assertIn("higgsfield auth login", err.getvalue())

    def test_other_failures_are_not_reported_as_an_auth_problem(self) -> None:
        """A 5xx or a dropped network must not send the user to re-run auth login."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit):
                explore.require_auth(self.standin("dial tcp: connection refused", 1))
        self.assertIn("connection refused", err.getvalue())
        self.assertNotIn("auth login", err.getvalue())


class Budget(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.args = explore.parse_args(["m.jpg"])

    def costs(self, out: str, code: int = 0) -> str:
        return make_standin(self.tmp, f"import sys\nprint({out!r})\nsys.exit({code})\n")

    def test_parses_both_cli_number_formats(self) -> None:
        self.assertEqual(explore.parse_credits("97.5 credits"), 97.5)
        self.assertEqual(explore.parse_credits("me@x.com - starter plan, 109 credits"), 109.0)
        self.assertEqual(explore.parse_credits("1,250 credits"), 1250.0)
        self.assertIsNone(explore.parse_credits("unlimited plan"))
        self.assertIsNone(explore.parse_credits(""))

    def test_reports_the_price_when_affordable(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            explore.check_budget(self.costs("97.5 credits"), "p", self.args, "109 credits")
        self.assertIn("97.5 credits", err.getvalue())
        self.assertIn("balance 109", err.getvalue())

    def test_refuses_to_submit_when_the_balance_is_short(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit):
                explore.check_budget(self.costs("97.5 credits"), "p", self.args, "40 credits")
        self.assertIn("needs about 97.5", err.getvalue())

    def test_unreadable_numbers_never_block_the_run(self) -> None:
        """A CLI output change must not stop a user who can actually pay."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            explore.check_budget(self.costs("some new format"), "p", self.args, "109 credits")
            explore.check_budget(self.costs("97.5 credits"), "p", self.args, "enterprise plan")
        self.assertIn("97.5 credits", err.getvalue())

    def test_a_failing_cost_call_never_blocks_the_run(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            explore.check_budget(self.costs("boom", 1), "p", self.args, "109 credits")


class RunJob(unittest.TestCase):
    """Exercise run_job's real stdin, streaming, and URL-extraction paths.

    The binary is a stand-in that honours the CLI's contract — read the prompt from
    stdin, print progress, print a result URL. The real CLI's side of that contract is
    covered by LiveHiggsfield below; submitting an actual job costs ~97.5 credits.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def standin(self, output: str, code: int = 0) -> str:
        return make_standin(
            self.tmp,
            "import sys\n"
            "data = sys.stdin.read()\n"
            "print('submitting job')\n"
            "print('prompt-bytes:', len(data))\n"
            f"print({output!r})\n"
            f"sys.exit({code})\n",
        )

    def test_prompt_goes_over_stdin_and_progress_is_relayed(self) -> None:
        hf = self.standin("done https://cdn.x/take.mp4")
        err, out = io.StringIO(), io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            url = explore.run_job(
                hf, Path("m.jpg"), "x" * 40, explore.parse_args(["m.jpg"])
            )
        self.assertEqual(url, "https://cdn.x/take.mp4")
        self.assertIn("prompt-bytes: 40", err.getvalue())
        self.assertIn("submitting job", err.getvalue())
        self.assertEqual(out.getvalue().strip(), "https://cdn.x/take.mp4")

    def test_nonzero_exit_stops_the_run(self) -> None:
        hf = self.standin("boom", code=2)
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                explore.run_job(hf, Path("m.jpg"), "p", explore.parse_args(["m.jpg"]))

    def test_non_media_url_is_not_returned_as_the_result(self) -> None:
        hf = self.standin("Timed out. See https://higgsfield.ai/dashboard/jobs/abc")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                explore.run_job(hf, Path("m.jpg"), "p", explore.parse_args(["m.jpg"]))
        self.assertIn("no video URL", err.getvalue())
        self.assertIn("https://higgsfield.ai/dashboard/jobs/abc", err.getvalue())
        self.assertIn("higgsfield generate list", err.getvalue())

    def test_failure_after_submission_tells_you_how_to_recover(self) -> None:
        hf = self.standin("boom", code=2)
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                explore.run_job(hf, Path("m.jpg"), "p", explore.parse_args(["m.jpg"]))
        self.assertIn("higgsfield generate list", err.getvalue())

    def test_large_prompt_does_not_deadlock(self) -> None:
        """A prompt bigger than the OS pipe buffer must not hang the writer."""
        hf = self.standin("ok https://cdn.x/big.mp4")
        big = "x" * 300_000
        result = {}

        def go() -> None:
            result["url"] = explore.run_job(
                hf, Path("m.jpg"), big, explore.parse_args(["m.jpg"])
            )

        worker = threading.Thread(target=go, daemon=True)
        worker.start()
        worker.join(timeout=60)
        self.assertFalse(worker.is_alive(), "run_job deadlocked writing a large prompt")
        self.assertEqual(result["url"], "https://cdn.x/big.mp4")


class Cli(unittest.TestCase):
    """Drive the script as a user would."""

    def run_script(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "explore.py"), *args],
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_help_works(self) -> None:
        proc = self.run_script("--help")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--prompt-file", proc.stdout)

    def test_missing_image_exits_nonzero(self) -> None:
        proc = self.run_script(str(ROOT / "does-not-exist.jpg"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("image not found", proc.stderr)

    def test_zero_duration_is_rejected(self) -> None:
        proc = self.run_script(str(ROOT / "does-not-exist.jpg"), "--duration", "0")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--duration", proc.stderr)


@unittest.skipUnless(shutil.which("higgsfield"), "higgsfield CLI not installed")
class LiveHiggsfield(unittest.TestCase):
    """Validate the real param set against the real API. Costs no credits."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.hf = shutil.which("higgsfield")
        status = subprocess.run(
            [cls.hf, "account", "status"], capture_output=True, text=True, timeout=60
        )
        if status.returncode != 0:
            raise unittest.SkipTest("higgsfield not logged in")

    def test_model_accepts_every_locked_param(self) -> None:
        proc = subprocess.run(
            [self.hf, "model", "get", "seedance_2_5"],
            capture_output=True,
            text=True,
            timeout=90,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for token in ["omni_reference", "21:9", "720p", "generate_audio", "image_references"]:
            self.assertIn(token, proc.stdout, f"{token} missing from seedance_2_5 params")

    def test_prompt_is_accepted_on_stdin(self) -> None:
        """explore.py sends no --prompt flag; the CLI must read stdin. No job is created."""
        args = explore.parse_args(["m.jpg"])
        proc = subprocess.run(
            [
                self.hf, "generate", "cost", "seedance_2_5",
                "--duration", str(args.duration),
                "--aspect_ratio", args.aspect,
                "--resolution", args.resolution,
                "--generate_audio", "true",
            ],
            input="a quiet test prompt",
            capture_output=True,
            text=True,
            timeout=90,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("credits", proc.stdout.lower())
        self.assertNotIn("prompt", proc.stderr.lower())


if __name__ == "__main__":
    unittest.main()
