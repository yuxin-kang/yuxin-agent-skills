#!/usr/bin/env python3
"""Run the robotics paper digest locally and persist only git-ignored data."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPOSITORY_ROOT / "robotics-paper-digest"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lookback-days", type=int, default=3)
    parser.add_argument("--max-results", type=int, default=100)
    parser.add_argument("--max-papers", type=int, default=20)
    parser.add_argument("--data-dir", type=Path, default=REPOSITORY_ROOT / ".local-data" / "robotics-paper-digest")
    parser.add_argument(
        "--output-dir", type=Path, default=REPOSITORY_ROOT / ".local-output" / "robotics-paper-digest"
    )
    parser.add_argument("--feed-file", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--now", help=argparse.SUPPRESS)
    parser.add_argument("--require-openai", action="store_true")
    return parser.parse_args()


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=REPOSITORY_ROOT, check=True)


def main() -> int:
    args = parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    state_path = args.data_dir / "seen.json"
    papers_path = args.data_dir / "papers.json"
    fetch_command = [
        sys.executable,
        str(SKILL_ROOT / "scripts" / "fetch_arxiv.py"),
        "--profile",
        str(SKILL_ROOT / "references" / "default-profile.json"),
        "--state",
        str(state_path),
        "--output",
        str(papers_path),
        "--lookback-days",
        str(args.lookback_days),
        "--max-results",
        str(args.max_results),
        "--max-papers",
        str(args.max_papers),
    ]
    if args.feed_file:
        fetch_command.extend(["--feed-file", str(args.feed_file)])
    if args.now:
        fetch_command.extend(["--now", args.now])
    run(fetch_command)

    payload = json.loads(papers_path.read_text(encoding="utf-8"))
    report_date = payload.get("generated_at", "")[:10]
    if not report_date:
        raise RuntimeError("fetch output has no generated_at date")
    report_path = args.output_dir / f"{report_date}.md"
    render_command = [
        sys.executable,
        str(SKILL_ROOT / "scripts" / "render_digest.py"),
        "--input",
        str(papers_path),
        "--output",
        str(report_path),
        "--state",
        str(state_path),
        "--index",
        str(args.output_dir / "README.md"),
    ]
    if not args.require_openai:
        render_command.append("--allow-extractive-fallback")
    run(render_command)

    mode = "OpenAI" if os.environ.get("OPENAI_API_KEY", "").strip() else "abstract fallback"
    print(f"Local digest complete: {report_path} ({payload.get('selected_count', 0)} papers, {mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
