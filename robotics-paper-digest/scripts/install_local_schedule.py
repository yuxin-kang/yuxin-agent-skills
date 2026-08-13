#!/usr/bin/env python3
"""Install or remove the local cron entry for the robotics paper digest."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPOSITORY_ROOT / "robotics-paper-digest" / "scripts" / "run_local_digest.py"
DATA_DIR = REPOSITORY_ROOT / ".local-data" / "robotics-paper-digest"
BEGIN_MARKER = "# BEGIN yuxin-agent-skills robotics-paper-digest"
END_MARKER = "# END yuxin-agent-skills robotics-paper-digest"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hour", type=int, default=8)
    parser.add_argument("--minute", type=int, default=30)
    parser.add_argument("--lookback-days", type=int, default=3)
    parser.add_argument("--remove", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def current_crontab() -> str:
    result = subprocess.run(["crontab", "-l"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        return result.stdout
    if "no crontab" in result.stderr.lower():
        return ""
    raise RuntimeError(result.stderr.strip() or "unable to read crontab")


def remove_managed_block(crontab: str) -> str:
    lines = crontab.splitlines()
    kept: list[str] = []
    managed = False
    for line in lines:
        if line == BEGIN_MARKER:
            managed = True
            continue
        if line == END_MARKER:
            managed = False
            continue
        if not managed:
            kept.append(line)
    return "\n".join(kept).strip()


def main() -> int:
    args = parse_args()
    if not 0 <= args.hour <= 23 or not 0 <= args.minute <= 59 or args.lookback_days < 1:
        raise SystemExit("hour must be 0-23, minute 0-59, and lookback-days positive")

    crontab = remove_managed_block(current_crontab())
    if not args.remove:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        command = " ".join(
            [
                shlex.quote(sys.executable),
                shlex.quote(str(RUNNER)),
                "--lookback-days",
                str(args.lookback_days),
                ">>",
                shlex.quote(str(DATA_DIR / "cron.log")),
                "2>&1",
            ]
        )
        entry = f"{args.minute} {args.hour} * * * {command}"
        managed_block = "\n".join([BEGIN_MARKER, entry, END_MARKER])
        crontab = "\n\n".join(part for part in [crontab, managed_block] if part)

    payload = crontab.rstrip() + "\n" if crontab else ""
    if args.dry_run:
        print(payload, end="")
        return 0
    subprocess.run(["crontab", "-"], input=payload, text=True, check=True)
    action = "removed" if args.remove else f"installed for {args.hour:02d}:{args.minute:02d} local time"
    print(f"Local robotics paper schedule {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
