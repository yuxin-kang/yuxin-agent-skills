#!/usr/bin/env python3
"""Small end-to-end test for the bundled paper-digest scripts."""

from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "robotics-paper-digest"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        state = temp / "seen.json"
        state.write_text('{"seen": [], "updated_at": null}\n', encoding="utf-8")
        papers = temp / "papers.json"
        report = temp / "reports" / "2026-08-13.md"
        index = temp / "reports" / "README.md"
        duplicate_feed = temp / "duplicate-feed.xml"
        feed_root = ET.parse(ROOT / "tests" / "fixtures" / "arxiv_sample.xml").getroot()
        first_entry = next(element for element in feed_root if element.tag.endswith("entry"))
        feed_root.append(copy.deepcopy(first_entry))
        ET.ElementTree(feed_root).write(duplicate_feed, encoding="utf-8", xml_declaration=True)

        run(
            "python3",
            str(SKILL / "scripts" / "fetch_arxiv.py"),
            "--profile",
            str(SKILL / "references" / "default-profile.json"),
            "--state",
            str(state),
            "--output",
            str(papers),
            "--feed-file",
            str(duplicate_feed),
            "--now",
            "2026-08-13T00:00:00Z",
        )
        payload = json.loads(papers.read_text(encoding="utf-8"))
        assert payload["cutoff"].startswith("2026-08-10")
        assert payload["candidate_count"] == 2
        assert payload["selected_count"] == 2
        assert payload["papers"][0]["arxiv_id"] == "2608.12345"
        assert payload["papers"][0]["relevance_score"] > payload["papers"][1]["relevance_score"]

        run(
            "python3",
            str(SKILL / "scripts" / "render_digest.py"),
            "--input",
            str(papers),
            "--output",
            str(report),
            "--state",
            str(state),
            "--index",
            str(index),
            "--allow-extractive-fallback",
        )
        assert "Depth Memory for Humanoid Stair Loco-Manipulation" in report.read_text(encoding="utf-8")
        assert "2026-08-13" in index.read_text(encoding="utf-8")
        assert set(json.loads(state.read_text(encoding="utf-8"))["seen"]) == {"2608.12345", "2608.12346"}

        second_pass = temp / "second-pass.json"
        run(
            "python3",
            str(SKILL / "scripts" / "fetch_arxiv.py"),
            "--profile",
            str(SKILL / "references" / "default-profile.json"),
            "--state",
            str(state),
            "--output",
            str(second_pass),
            "--feed-file",
            str(duplicate_feed),
            "--now",
            "2026-08-13T00:00:00Z",
            "--lookback-days",
            "7",
        )
        assert json.loads(second_pass.read_text(encoding="utf-8"))["selected_count"] == 0

        rss_state = temp / "rss-seen.json"
        rss_state.write_text('{"seen": [], "updated_at": null}\n', encoding="utf-8")
        rss_papers = temp / "rss-papers.json"
        run(
            "python3",
            str(SKILL / "scripts" / "fetch_arxiv.py"),
            "--profile",
            str(SKILL / "references" / "default-profile.json"),
            "--state",
            str(rss_state),
            "--output",
            str(rss_papers),
            "--feed-file",
            str(ROOT / "tests" / "fixtures" / "arxiv_rss_sample.xml"),
            "--now",
            "2026-08-13T00:00:00Z",
            "--lookback-days",
            "7",
        )
        rss_payload = json.loads(rss_papers.read_text(encoding="utf-8"))
        assert rss_payload["selected_count"] == 2
        assert rss_payload["papers"][0]["arxiv_id"] == "2608.22345"
        assert rss_payload["papers"][0]["authors"] == ["Ada Robot", "Bo Control"]
        assert rss_payload["papers"][0]["abstract"].startswith("We learn a depth-conditioned")

    print("robotics-paper-digest tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
