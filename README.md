# Yuxin Agent Skills

这个仓库集中维护我个人使用的 Codex/Agent skills。每个 skill 都是独立、可安装、可验证的目录；后续新增 skill 统一放在 `skills/<skill-name>/` 下。

## Skills

| Skill | 用途 | 目录 |
| --- | --- | --- |
| `experiment-record` | 根据真实 Play 结果与 run/checkpoint 证据记录 Leo Lab 实验 | [`skills/experiment-record`](skills/experiment-record) |
| `robotics-paper-digest` | 抓取、筛选并总结最新机器人论文，支持每日自动生成中文简报 | [`skills/robotics-paper-digest`](skills/robotics-paper-digest) |

## 安装

安装单个 skill：

```bash
cp -R skills/experiment-record ~/.codex/skills/
cp -R skills/robotics-paper-digest ~/.codex/skills/
```

也可以通过支持 GitHub 路径的 skill installer 安装指定子目录。

## 机器人论文日报

仓库中的 [GitHub Actions 工作流](.github/workflows/daily-robotics-papers.yml) 每天北京时间 08:30 执行：

1. 从 arXiv `cs.RO` 抓取最近 7 天的新论文，API 限流时自动降级到官方 RSS 当日批次；
2. 按人形、腿式运动、操作、强化学习、感知、sim-to-real 和安全等研究兴趣排序；
3. 去重并生成 `reports/YYYY-MM-DD.md`；
4. 自动更新 `data/seen_arxiv_ids.json` 和报告索引；
5. 将新日报提交回仓库。

要启用高质量中文总结，在仓库 `Settings → Secrets and variables → Actions` 中添加：

- Secret `OPENAI_API_KEY`：用于调用 Responses API；
- Variable `OPENAI_MODEL`（可选）：默认使用 `gpt-5-mini`。

没有 API key 时，工作流仍会生成基于标题、摘要和关键词的证据型简报，但不会把抽取结果伪装成模型分析。

也可以在 Actions 页面手动运行 `Daily robotics paper digest`，并临时调整回溯天数和论文数量。

## 本地运行

```bash
python3 skills/robotics-paper-digest/scripts/fetch_arxiv.py \
  --profile skills/robotics-paper-digest/references/default-profile.json \
  --state data/seen_arxiv_ids.json \
  --output .cache/papers.json

OPENAI_API_KEY=... python3 skills/robotics-paper-digest/scripts/render_digest.py \
  --input .cache/papers.json \
  --output reports/$(date +%F).md \
  --state data/seen_arxiv_ids.json \
  --index reports/README.md
```

## 新增个人 Skill

1. 目录名与 frontmatter 中的 `name` 使用小写连字符格式；
2. 每个 skill 至少包含 `SKILL.md`；
3. 推荐提供 `agents/openai.yaml`；
4. 重复、确定性的步骤放到 `scripts/`；详细领域知识放到 `references/`；
5. 提交前运行 `quick_validate.py skills/<skill-name>`，并实际执行新增脚本的代表性测试。
