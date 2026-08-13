#!/usr/bin/env python3
"""Run a Meme Scene Explorer job on Higgsfield Seedance 2.5."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKELETON_PATH = ROOT / "examples" / "skeleton.txt"
WORLD_TOKEN = "{world}"
DEFAULT_WORLD = "a complete believable physical location that matches and elevates the meme's energy"
MEDIA_URL_RE = re.compile(r"https://[^\s]+?\.(?:mp4|mov|webm)(?:\?[^\s]*)?", re.I)
ANY_URL_RE = re.compile(r"https://[^\s]+")
AUTH_RE = re.compile(r"session expired|not authenticated|please log in|unauthorized", re.I)
CREDITS_RE = re.compile(r"([\d,]+(?:\.\d+)?)\s*credits", re.I)
RECOVERY_HINT = (
    "If the job was submitted it may still be running — find it with: higgsfield generate list"
)

# Enums accepted by seedance_2_5 (`higgsfield model get seedance_2_5`).
ASPECTS = ("auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16")
RESOLUTIONS = ("480p", "720p")


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def require_higgsfield() -> str:
    path = shutil.which("higgsfield")
    if not path:
        die(
            "higgsfield CLI not found. Install it (macOS, Linux, Windows):\n"
            "  npm install -g @higgsfield/cli\n"
            "Then log in:\n"
            "  higgsfield auth login"
        )
    return path


def require_auth(hf: str) -> str:
    """Returns the `account status` output so the caller can read the balance."""
    try:
        proc = subprocess.run(
            [hf, "account", "status"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        die("higgsfield account status timed out after 60s. Check your network, then retry.")
    except OSError as exc:
        die(f"could not run higgsfield: {exc}")
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if proc.returncode == 0 and not AUTH_RE.search(out):
        return out
    if AUTH_RE.search(out):
        die("not logged in. Run: higgsfield auth login")
    die(f"higgsfield account status failed (exit {proc.returncode}):\n{out or '(no output)'}")


def parse_credits(text: str) -> float | None:
    match = CREDITS_RE.search(text or "")
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def estimate_cost(hf: str, prompt: str, args: argparse.Namespace) -> float | None:
    """Price this run. `generate cost` creates no job and spends nothing.

    Media does not affect the price, so the still is not uploaded just to ask.
    """
    cmd = [
        hf,
        "generate",
        "cost",
        "seedance_2_5",
        "--duration",
        str(args.duration),
        "--aspect_ratio",
        args.aspect,
        "--resolution",
        args.resolution,
        "--generate_audio",
        "true",
    ]
    try:
        proc = subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=90)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return parse_credits(proc.stdout)


def check_budget(hf: str, prompt: str, args: argparse.Namespace, status: str) -> None:
    """Say what the run costs before spending it. Silent if the numbers cannot be read."""
    cost = estimate_cost(hf, prompt, args)
    if cost is None:
        return
    balance = parse_credits(status)
    if balance is None:
        print(f"this run costs about {cost:g} credits", file=sys.stderr)
        return
    if balance < cost:
        die(
            f"this run needs about {cost:g} credits and the account has {balance:g}. "
            "Add credits at https://higgsfield.ai, then retry."
        )
    print(f"this run costs about {cost:g} credits (balance {balance:g})", file=sys.stderr)


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        if args.world:
            die("--world only fills the built-in skeleton. Drop --world, or drop --prompt-file.")
        path = Path(args.prompt_file).expanduser()
        if not path.is_file():
            die(f"prompt file not found: {path}")
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            die(f"prompt file is empty: {path}")
        if WORLD_TOKEN in text:
            die(
                f"prompt file still contains the {WORLD_TOKEN} placeholder: {path}\n"
                "Name a real place there, or drop --prompt-file and pass --world instead."
            )
        return text
    if not SKELETON_PATH.is_file():
        die(f"skeleton missing: {SKELETON_PATH}")
    world = (args.world or DEFAULT_WORLD).strip()
    return SKELETON_PATH.read_text(encoding="utf-8").replace(WORLD_TOKEN, world).strip()


def run_job(hf: str, image: Path, prompt: str, args: argparse.Namespace) -> str:
    cmd = [
        hf,
        "generate",
        "create",
        "seedance_2_5",
        "--mode",
        "omni_reference",
        "--image-references",
        str(image),
        "--duration",
        str(args.duration),
        "--aspect_ratio",
        args.aspect,
        "--resolution",
        args.resolution,
        "--generate_audio",
        "true",
        "--wait",
        "--wait-timeout",
        args.wait_timeout,
        "--wait-interval",
        "5s",
    ]
    print("submitting Seedance 2.5 job…", file=sys.stderr)
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except OSError as exc:
        die(f"could not run higgsfield: {exc}")

    # The CLI reads the prompt from stdin when no --prompt flag is given. Feed it
    # from a thread so a prompt larger than the pipe buffer cannot deadlock us.
    def feed() -> None:
        try:
            proc.stdin.write(prompt)
            proc.stdin.close()
        except (OSError, ValueError):
            pass

    writer = threading.Thread(target=feed, daemon=True)
    writer.start()

    # Relay the CLI's progress live; the wait can run for many minutes.
    chunks = []
    for line in proc.stdout:
        sys.stderr.write(line)
        sys.stderr.flush()
        chunks.append(line)
    writer.join(timeout=5)
    proc.stdin.close()
    proc.stdout.close()
    proc.wait()

    text = "".join(chunks)
    if proc.returncode != 0:
        detail = text.strip() or f"higgsfield exited {proc.returncode}"
        die(f"{detail}\n{RECOVERY_HINT}")
    match = MEDIA_URL_RE.search(text)
    if not match:
        other = ANY_URL_RE.search(text)
        hint = f"\nlast URL printed: {other.group(0).rstrip(').,]')}" if other else ""
        die(f"job finished but printed no video URL.{hint}\n{RECOVERY_HINT}")
    url = match.group(0).rstrip(").,]")
    print(url)
    return url


def unique_dest(dest_dir: Path, stem: str) -> Path:
    """Never clobber an earlier take — Seedance has no seed, so it is unrepeatable."""
    dest = dest_dir / f"{stem}_mse.mp4"
    n = 2
    while dest.exists():
        dest = dest_dir / f"{stem}_mse-{n}.mp4"
        n += 1
    return dest


def download(url: str, dest_dir: Path, stem: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = unique_dest(dest_dir, stem)
    print(f"saving {dest}", file=sys.stderr)
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "html" in ctype or "json" in ctype:
                die(f"expected a video, got {ctype} from {url}")
            with dest.open("wb") as fh:
                shutil.copyfileobj(resp, fh)
    except urllib.error.URLError as exc:
        die(f"download failed: {exc}")
    return dest


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Meme Scene Explorer: restage a meme still with Seedance 2.5."
    )
    p.add_argument("image", help="Path to the meme still")
    p.add_argument(
        "--prompt-file",
        help="Filled 15-stage prompt. If omitted, the generic skeleton is used.",
    )
    p.add_argument(
        "--world",
        help='Physical setting for the skeleton, e.g. "dusty farm at golden hour". '
        "Not valid with --prompt-file.",
    )
    p.add_argument("--out", default=".", help="Directory to save the mp4 (default: cwd)")
    p.add_argument(
        "--aspect", default="21:9", choices=ASPECTS, help="Aspect ratio (default: 21:9)"
    )
    p.add_argument(
        "--resolution", default="720p", choices=RESOLUTIONS, help="Resolution (default: 720p)"
    )
    p.add_argument("--duration", type=int, default=15, help="Seconds (default: 15)")
    p.add_argument("--wait-timeout", default="20m", help="Higgsfield wait timeout (default: 20m)")
    p.add_argument(
        "--no-download",
        action="store_true",
        help="Print the URL only; do not save a local file",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    if args.duration < 1:
        die(f"--duration must be at least 1 second, got {args.duration}")
    image = Path(args.image).expanduser().resolve()
    if not image.is_file():
        die(f"image not found: {image}")
    hf = require_higgsfield()
    status = require_auth(hf)
    prompt = load_prompt(args)
    check_budget(hf, prompt, args, status)
    url = run_job(hf, image, prompt, args)
    if not args.no_download:
        dest = download(url, Path(args.out).expanduser(), image.stem)
        print(dest)


if __name__ == "__main__":
    main(sys.argv[1:])
