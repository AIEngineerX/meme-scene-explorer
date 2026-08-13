#!/usr/bin/env python3
"""Run a Meme Scene Explorer job on Higgsfield Seedance 2.5."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKELETON_PATH = ROOT / "examples" / "skeleton.txt"
DEFAULT_WORLD = "a complete believable physical location that matches and elevates the meme's energy"
URL_RE = re.compile(r"https://[^\s]+?\.(?:mp4|mov|webm)(?:\?[^\s]*)?", re.I)
ANY_URL_RE = re.compile(r"https://[^\s]+")


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def require_higgsfield() -> str:
    path = shutil.which("higgsfield")
    if not path:
        die(
            "higgsfield CLI not found. Install:\n"
            "  curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh"
        )
    return path


def require_auth(hf: str) -> None:
    try:
        proc = subprocess.run(
            [hf, "account", "status"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except OSError as exc:
        die(f"could not run higgsfield: {exc}")
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0 or re.search(
        r"session expired|not authenticated|please log in", out, re.I
    ):
        die("not logged in. Run: higgsfield auth login")


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        path = Path(args.prompt_file)
        if not path.is_file():
            die(f"prompt file not found: {path}")
        return path.read_text(encoding="utf-8").strip()
    if not SKELETON_PATH.is_file():
        die(f"skeleton missing: {SKELETON_PATH}")
    world = (args.world or DEFAULT_WORLD).strip()
    return SKELETON_PATH.read_text(encoding="utf-8").format(world=world).strip()


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
    proc = subprocess.run(cmd, input=prompt, text=True, capture_output=True)
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode != 0:
        die(text.strip() or f"higgsfield exited {proc.returncode}")
    match = URL_RE.search(text) or ANY_URL_RE.search(text)
    if not match:
        print(text.strip())
        die("job finished but no result URL was printed")
    url = match.group(0).rstrip(").,]")
    print(url)
    return url


def download(url: str, dest_dir: Path, stem: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{stem}_mse.mp4"
    print(f"saving {dest}", file=sys.stderr)
    urllib.request.urlretrieve(url, dest)
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
        help='Physical setting when using the skeleton, e.g. "dusty farm at golden hour"',
    )
    p.add_argument("--out", default=".", help="Directory to save the mp4 (default: cwd)")
    p.add_argument("--aspect", default="21:9", help="Aspect ratio (default: 21:9)")
    p.add_argument("--resolution", default="720p", help="Resolution (default: 720p)")
    p.add_argument("--duration", type=int, default=15, help="Seconds (default: 15)")
    p.add_argument("--wait-timeout", default="20m", help="Higgsfield wait timeout")
    p.add_argument(
        "--no-download",
        action="store_true",
        help="Print the URL only; do not save a local file",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    image = Path(args.image).expanduser().resolve()
    if not image.is_file():
        die(f"image not found: {image}")
    hf = require_higgsfield()
    require_auth(hf)
    prompt = load_prompt(args)
    url = run_job(hf, image, prompt, args)
    if not args.no_download:
        dest = download(url, Path(args.out).expanduser(), image.stem)
        print(dest)


if __name__ == "__main__":
    main(sys.argv[1:])
