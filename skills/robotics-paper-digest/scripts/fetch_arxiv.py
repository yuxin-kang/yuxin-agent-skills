#!/usr/bin/env python3
"""Fetch and rank recent arXiv robotics papers using only the Python standard library."""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import http.client
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ARXIV_API = "https://export.arxiv.org/api/query"
ARXIV_RSS = "https://rss.arxiv.org/rss"
ATOM = {"atom": "http://www.w3.org/2005/Atom"}
RSS = {
    "arxiv": "http://arxiv.org/schemas/atom",
    "dc": "http://purl.org/dc/elements/1.1/",
}
USER_AGENT = "yuxin-agent-skills/robotics-paper-digest (+https://github.com/yuxin-kang/yuxin-agent-skills)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lookback-days", type=int, default=7)
    parser.add_argument("--max-results", type=int, default=100)
    parser.add_argument("--max-papers", type=int, default=20)
    parser.add_argument("--include-seen", action="store_true")
    parser.add_argument("--feed-file", type=Path, help="Parse a local Atom fixture instead of calling arXiv")
    parser.add_argument("--now", help="UTC ISO timestamp used for deterministic tests")
    return parser.parse_args()


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def stable_arxiv_id(url: str) -> str:
    value = url.rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"v\d+$", "", value)


def parse_timestamp(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def parse_atom(root: ET.Element) -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ATOM):
        entry_url = normalize_space(entry.findtext("atom:id", default="", namespaces=ATOM))
        links = {
            node.attrib.get("rel", "alternate"): node.attrib.get("href", "")
            for node in entry.findall("atom:link", ATOM)
        }
        categories = [node.attrib.get("term", "") for node in entry.findall("atom:category", ATOM)]
        papers.append(
            {
                "arxiv_id": stable_arxiv_id(entry_url),
                "title": normalize_space(entry.findtext("atom:title", default="", namespaces=ATOM)),
                "abstract": normalize_space(entry.findtext("atom:summary", default="", namespaces=ATOM)),
                "authors": [
                    normalize_space(author.findtext("atom:name", default="", namespaces=ATOM))
                    for author in entry.findall("atom:author", ATOM)
                ],
                "published": normalize_space(entry.findtext("atom:published", default="", namespaces=ATOM)),
                "updated": normalize_space(entry.findtext("atom:updated", default="", namespaces=ATOM)),
                "categories": categories,
                "url": links.get("alternate") or entry_url,
                "pdf_url": links.get("related", ""),
            }
        )
    return papers


def parse_rss(root: ET.Element) -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []
    for item in root.findall("./channel/item"):
        url = normalize_space(item.findtext("link", default=""))
        published_raw = normalize_space(item.findtext("pubDate", default=""))
        published = email.utils.parsedate_to_datetime(published_raw).astimezone(dt.timezone.utc).isoformat()
        description = normalize_space(item.findtext("description", default=""))
        abstract = re.sub(
            r"^arXiv:\S+\s+Announce Type:\s+\S+\s+Abstract:\s*", "", description, flags=re.IGNORECASE
        )
        creator = normalize_space(item.findtext("dc:creator", default="", namespaces=RSS))
        arxiv_id = stable_arxiv_id(url)
        papers.append(
            {
                "arxiv_id": arxiv_id,
                "title": normalize_space(item.findtext("title", default="")),
                "abstract": abstract,
                "authors": [normalize_space(author) for author in creator.split(",") if normalize_space(author)],
                "published": published,
                "updated": published,
                "categories": [node.text or "" for node in item.findall("category")],
                "url": url,
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
            }
        )
    return papers


def parse_feed(payload: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(payload)
    if root.tag == "rss":
        return parse_rss(root)
    return parse_atom(root)


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                break
            if attempt < 2:
                time.sleep(2**attempt)
        except (http.client.IncompleteRead, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2**attempt)
    raise RuntimeError(f"request failed: {last_error}")


def fetch_feed(query: str, max_results: int, feed_file: Path | None) -> tuple[bytes, str]:
    if feed_file:
        return feed_file.read_bytes(), "local fixture"
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    try:
        return download(f"{ARXIV_API}?{params}"), "Atom API"
    except RuntimeError as api_error:
        category_match = re.fullmatch(r"cat:([A-Za-z.-]+)", query.strip())
        if not category_match:
            raise RuntimeError(f"arXiv API failed and query has no RSS fallback: {api_error}") from api_error
        category = category_match.group(1)
        try:
            return download(f"{ARXIV_RSS}/{category}"), "RSS fallback"
        except RuntimeError as rss_error:
            raise RuntimeError(f"arXiv API and RSS fallback failed: {api_error}; {rss_error}") from rss_error


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def keyword_matches(text: str, weighted_keywords: dict[str, int]) -> tuple[int, list[str]]:
    score = 0
    matches: list[str] = []
    lowered = text.lower()
    for keyword, weight in weighted_keywords.items():
        pattern = rf"(?<![a-z0-9]){re.escape(keyword.lower())}(?![a-z0-9])"
        if re.search(pattern, lowered):
            score += int(weight)
            matches.append(keyword)
    return score, matches


def rank_paper(paper: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    text = f"{paper['title']} {paper['abstract']}"
    primary_score, primary_matches = keyword_matches(text, profile.get("priority_keywords", {}))
    secondary_score, secondary_matches = keyword_matches(text, profile.get("secondary_keywords", {}))
    paper["relevance_score"] = primary_score + secondary_score
    paper["matched_keywords"] = primary_matches + secondary_matches
    return paper


def main() -> int:
    args = parse_args()
    if args.lookback_days < 1 or args.max_results < 1 or args.max_papers < 1:
        raise SystemExit("lookback-days, max-results and max-papers must be positive")

    profile = load_json(args.profile, {})
    state = load_json(args.state, {"seen": []})
    seen = set(state.get("seen", []))
    now = parse_timestamp(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=args.lookback_days)
    payload, transport = fetch_feed(profile.get("query", "cat:cs.RO"), args.max_results, args.feed_file)

    candidates: list[dict[str, Any]] = []
    feed_ids: set[str] = set()
    for paper in parse_feed(payload)[: args.max_results]:
        if paper["arxiv_id"] in feed_ids:
            continue
        feed_ids.add(paper["arxiv_id"])
        if not paper["published"] or parse_timestamp(paper["published"]) < cutoff:
            continue
        paper["is_new"] = paper["arxiv_id"] not in seen
        if not args.include_seen and not paper["is_new"]:
            continue
        candidates.append(rank_paper(paper, profile))

    candidates.sort(key=lambda item: (item["relevance_score"], item["published"]), reverse=True)
    selected = candidates[: args.max_papers]
    result = {
        "generated_at": now.isoformat(),
        "cutoff": cutoff.isoformat(),
        "source": "arXiv",
        "transport": transport,
        "query": profile.get("query", "cat:cs.RO"),
        "profile": profile.get("name", "unnamed"),
        "candidate_count": len(candidates),
        "selected_count": len(selected),
        "papers": selected,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Selected {len(selected)} of {len(candidates)} recent papers -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
