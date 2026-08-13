#!/usr/bin/env python3
"""Render a Chinese robotics digest, using the Responses API when configured."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


RESPONSES_API = "https://api.openai.com/v1/responses"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-5-mini"))
    parser.add_argument("--allow-extractive-fallback", action="store_true")
    return parser.parse_args()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def sentence_excerpt(abstract: str, limit: int = 420) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", abstract.strip())
    excerpt = " ".join(sentences[:2]).strip()
    if len(excerpt) > limit:
        excerpt = excerpt[: limit - 1].rstrip() + "…"
    return excerpt or "摘要未提供。"


def paper_payload(data: dict[str, Any]) -> str:
    blocks = []
    for index, paper in enumerate(data.get("papers", []), 1):
        blocks.append(
            "\n".join(
                [
                    f"[{index}] {paper['title']}",
                    f"Authors: {', '.join(paper.get('authors', []))}",
                    f"Published: {paper.get('published', '')}",
                    f"Categories: {', '.join(paper.get('categories', []))}",
                    f"Matched keywords: {', '.join(paper.get('matched_keywords', []))}",
                    f"URL: {paper.get('url', '')}",
                    f"Abstract: {paper.get('abstract', '')}",
                ]
            )
        )
    return "\n\n".join(blocks)


def extract_response_text(response: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                chunks.append(content["text"])
    if not chunks and isinstance(response.get("output_text"), str):
        chunks.append(response["output_text"])
    if not chunks:
        raise RuntimeError("Responses API returned no output_text")
    return "\n".join(chunks).strip()


def generate_with_openai(data: dict[str, Any], api_key: str, model: str) -> str:
    instructions = (
        "你是严谨的机器人论文编辑。只根据提供的 arXiv 元数据和摘要生成中文 Markdown 日报。"
        "不得编造传感器、控制频率、机器人平台、实机结果、venue 或定量数字。摘要未披露就明确写‘摘要未披露，需精读全文’。"
        "区分事实与推断。选 3–8 篇最值得精读的论文展开，其余紧凑列出。"
        "每篇展开项包含：一句话、方法原理、可能重要的 trick、与人形/腿式/操作研究的关系、证据边界、原文链接。"
        "标题使用‘# 机器人论文日报｜YYYY-MM-DD’，并包含今日概览、必读论文、其他新论文、建议精读顺序。"
    )
    prompt = (
        f"生成时间：{data.get('generated_at')}\n"
        f"检索来源：{data.get('source')} / {data.get('query')} / {data.get('transport', '未记录')}\n"
        f"研究配置：{data.get('profile')}\n"
        f"候选数：{data.get('candidate_count')}，入选数：{data.get('selected_count')}\n\n"
        f"论文：\n{paper_payload(data)}"
    )
    request_data = json.dumps(
        {"model": model, "instructions": instructions, "input": prompt}, ensure_ascii=False
    ).encode("utf-8")
    request = urllib.request.Request(
        RESPONSES_API,
        data=request_data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return extract_response_text(json.loads(response.read().decode("utf-8")))
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2**attempt)
    raise RuntimeError(f"Responses API request failed after 3 attempts: {last_error}")


def render_extractive(data: dict[str, Any]) -> str:
    report_date = data.get("generated_at", "")[:10] or dt.date.today().isoformat()
    papers = data.get("papers", [])
    lines = [
        f"# 机器人论文日报｜{report_date}",
        "",
        "> 模式：摘要级证据抽取（未配置或未成功调用模型）；以下内容不代替全文精读。",
        f"> 来源：{data.get('source')} `{data.get('query')}` / {data.get('transport', '未记录')}；入选 {len(papers)} 篇。",
        "",
        "## 今日概览",
        "",
    ]
    if not papers:
        lines.extend(["本次检索窗口内没有尚未记录的新论文。", ""])
    else:
        keyword_counts: dict[str, int] = {}
        for paper in papers:
            for keyword in paper.get("matched_keywords", []):
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        top_keywords = sorted(keyword_counts.items(), key=lambda item: (-item[1], item[0]))[:8]
        summary = "、".join(f"{key}（{count}）" for key, count in top_keywords) or "未命中重点关键词"
        lines.extend([f"- 高频关注点：{summary}", f"- 新论文数量：{len(papers)}", ""])

    lines.extend(["## 新论文", ""])
    for index, paper in enumerate(papers, 1):
        authors = ", ".join(paper.get("authors", [])[:5])
        if len(paper.get("authors", [])) > 5:
            authors += ", et al."
        lines.extend(
            [
                f"### {index}. {paper['title']}",
                "",
                f"- 作者：{authors or '未提供'}",
                f"- 首次公开：{paper.get('published', '')[:10]}",
                f"- 相关关键词：{', '.join(paper.get('matched_keywords', [])) or '未命中'}",
                f"- 摘要要点（原文抽取）：{sentence_excerpt(paper.get('abstract', ''))}",
                "- 证据边界：仅核验 arXiv 元数据和摘要；方法 trick、传感模态、层级、平台与实机结果需精读全文。",
                f"- 链接：{paper.get('url', '')}",
                "",
            ]
        )
    lines.extend(["## 建议精读顺序", ""])
    if papers:
        for index, paper in enumerate(papers[:5], 1):
            lines.append(f"{index}. {paper['title']}（相关性分数 {paper.get('relevance_score', 0)}）")
    else:
        lines.append("本日无新增论文。")
    lines.append("")
    return "\n".join(lines)


def normalize_model_report(report: str, date: str, data: dict[str, Any], model: str) -> str:
    heading = f"# 机器人论文日报｜{date}"
    lines = report.splitlines()
    if lines and lines[0].startswith("# "):
        lines[0] = heading
    else:
        lines = [heading, "", *lines]
    evidence = (
        f"> 生成模式：OpenAI Responses API / `{model}`；来源：{data.get('source')} "
        f"`{data.get('query')}` / {data.get('transport', '未记录')}。"
        "详细方法与实验主张仍需回到论文全文核验。"
    )
    lines[1:1] = ["", evidence]
    return "\n".join(lines).rstrip() + "\n"


def update_state(path: Path, papers: list[dict[str, Any]]) -> None:
    state = load_json(path, {"seen": []})
    seen = set(state.get("seen", []))
    seen.update(paper["arxiv_id"] for paper in papers)
    payload = {"seen": sorted(seen), "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_index(path: Path, reports_dir: Path) -> None:
    reports = sorted(
        (item for item in reports_dir.glob("????-??-??.md") if item.name != path.name), reverse=True
    )
    lines = [
        "# Robotics Paper Digests",
        "",
        "每日机器人论文简报由本地定时任务自动生成。",
        "",
        "## Reports",
        "",
    ]
    if reports:
        lines.extend(f"- [{item.stem}]({item.name})" for item in reports)
    else:
        lines.append("当前还没有生成日报。")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    data = load_json(args.input, {})
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    report_date = data.get("generated_at", "")[:10] or dt.date.today().isoformat()

    if api_key:
        try:
            report = normalize_model_report(
                generate_with_openai(data, api_key, args.model), report_date, data, args.model
            )
        except RuntimeError:
            if not args.allow_extractive_fallback:
                raise
            report = render_extractive(data)
    elif args.allow_extractive_fallback:
        report = render_extractive(data)
    else:
        raise SystemExit("OPENAI_API_KEY is missing; pass --allow-extractive-fallback for abstract-only output")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.rstrip() + "\n", encoding="utf-8")
    update_state(args.state, data.get("papers", []))
    if args.index:
        update_index(args.index, args.output.parent)
    print(f"Rendered {len(data.get('papers', []))} papers -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
