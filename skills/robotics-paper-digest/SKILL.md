---
name: robotics-paper-digest
description: Find, screen, deduplicate, and summarize newly released robotics papers for daily or ad-hoc research digests. Use when asked for the latest robotics, humanoid, legged locomotion, loco-manipulation, robot learning, perception, sim-to-real, whole-body control, or safety papers; when maintaining a recurring paper watch; or when comparing new papers with an active robotics project. Prefer primary paper pages and clearly separate peer-reviewed papers, preprints, project pages, and company demonstrations.
---

# Robotics Paper Digest

Produce an evidence-bounded robotics paper digest rather than a list of titles.

## Workflow

1. Define the date window and research focus. Default to the last 7 days and the profile in [default-profile.json](references/default-profile.json).
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
7. Save recurring reports as `reports/YYYY-MM-DD.md` and update the seen-ID state only after the report is written successfully.

## Evidence Rules

- Prefer the paper PDF/HTML, official proceedings, DOI page, and official project page.
- Mark arXiv-only work as a preprint. Do not infer acceptance from a project page alone.
- Use company blogs only as demonstration evidence and never as proof of an unpublished method or sensor modality.
- Do not infer RGB, depth, LiDAR, hierarchy, autonomy, payload, or real-world success from a video frame or title.
- Quote quantitative results only after locating the corresponding table, figure, caption, or experiment text.
- Phrase search completeness as “within the reviewed public literature,” not as an absolute absence claim.
- If only metadata and abstracts are available, label the output as abstract-level screening.

## Bundled Automation

Use the deterministic scripts for recurring runs:

```bash
python3 scripts/fetch_arxiv.py \
  --profile references/default-profile.json \
  --state ../../data/seen_arxiv_ids.json \
  --output /tmp/robotics-papers.json

python3 scripts/render_digest.py \
  --input /tmp/robotics-papers.json \
  --output ../../reports/$(date +%F).md \
  --state ../../data/seen_arxiv_ids.json \
  --index ../../reports/README.md \
  --allow-extractive-fallback
```

`render_digest.py` uses the OpenAI Responses API when `OPENAI_API_KEY` is present. Never print, commit, or persist that secret. Without a key, allow the extractive fallback only when the user accepts an abstract-level digest; interactive Codex usage should instead summarize the verified primary sources directly.

The repository-level GitHub Actions workflow runs this pipeline every day and commits the resulting report.
