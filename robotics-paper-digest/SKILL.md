---
name: robotics-paper-digest
description: Find, screen, deduplicate, and summarize newly released robotics papers for daily or ad-hoc research digests. Use when asked for the latest robotics, humanoid, legged locomotion, loco-manipulation, robot learning, perception, sim-to-real, whole-body control, or safety papers; when maintaining a recurring paper watch; or when comparing new papers with an active robotics project. Prefer primary paper pages and clearly separate peer-reviewed papers, preprints, project pages, and company demonstrations.
---

# Robotics Paper Digest

Produce an evidence-bounded robotics paper digest rather than a list of titles.

## Workflow

1. Define the date window and research focus. Default to the last 3 days and the profile in [default-profile.json](references/default-profile.json). Use the user-provided day count when supplied.
2. Run `scripts/fetch_arxiv.py` for a reproducible arXiv `cs.RO` sweep. For an exhaustive or venue-specific request, additionally search official proceedings, OpenReview, publisher pages, and author project pages.
3. Deduplicate by stable arXiv ID, DOI, or exact title. Treat revisions as updates to an existing paper unless the user explicitly asks for version changes.
4. Rank candidates by topical relevance, then inspect every high-priority paper through its primary abstract/full-text page before making detailed claims.
5. For each selected paper, record:
   - problem and claimed contribution;
   - method principle and important implementation tricks;
   - sensing modality and deployment inputs;
   - control hierarchy and action interface;
   - robot/platform and real-robot evidence;
   - evidence limitations;
   - relation to the user's current project.
6. Use the structure in [report-schema.md](references/report-schema.md). Keep facts from the paper separate from your inference.
7. Save reports and seen-ID state only to a local, git-ignored path. Update the state only after the report is written successfully. Never commit or upload generated paper data unless the user explicitly asks.

## Evidence Rules

- Prefer the paper PDF/HTML, official proceedings, DOI page, and official project page.
- Mark arXiv-only work as a preprint. Do not infer acceptance from a project page alone.
- Use company blogs only as demonstration evidence and never as proof of an unpublished method or sensor modality.
- Do not infer RGB, depth, LiDAR, hierarchy, autonomy, payload, or real-world success from a video frame or title.
- Quote quantitative results only after locating the corresponding table, figure, caption, or experiment text.
- Phrase search completeness as “within the reviewed public literature,” not as an absolute absence claim.
- If only metadata and abstracts are available, label the output as abstract-level screening.

## Bundled Automation

Use the local runner for recurring or manual runs. It defaults to the latest 3 days; when the user enters another day
count in the prompt, pass that value through `--lookback-days`.

```bash
python3 robotics-paper-digest/scripts/run_local_digest.py
python3 robotics-paper-digest/scripts/run_local_digest.py --lookback-days 7
```

Install the default local schedule (daily at 08:30 system-local time, 3-day lookback) with:

```bash
python3 robotics-paper-digest/scripts/install_local_schedule.py
```

`render_digest.py` uses the OpenAI Responses API when `OPENAI_API_KEY` is present. Never print, commit, or persist that secret. Without a key, allow the extractive fallback only when the user accepts an abstract-level digest; interactive Codex usage should instead summarize the verified primary sources directly.

This repository intentionally contains no GitHub Actions workflow. Recurring execution must use a local scheduler, and
all generated metadata, state, reports, and logs must remain under the git-ignored `.local-data/` and `.local-output/`
directories unless the user explicitly chooses another local path.
The fetcher prefers the arXiv Atom API and falls back to the official category RSS feed when shared CI IPs are
rate-limited. Reports record which transport was used; RSS fallback covers the current announcement batch rather than
guaranteeing the full lookback window.
