---
name: "experiment-record"
description: "Record or update a Leo Lab experiment after the user has Play-tested a policy and supplied the actual result plus a run, job, checkpoint, W&B, or experiment identifier. Use for requests to compare the tested run with its prior baseline and write the factual result, training parameters, relevant changes, and evidence to docs/experiments/YYYY-MM-DD.md. Do not use to run Play or training, judge the result, or choose the next experiment."
---

# Experiment Record

Create or update one factual experiment entry after a user reports a Play result.

## Preconditions

- Require the user's actual Play result and at least one run, job, checkpoint, W&B, or existing experiment identifier. Without a Play result, do not create or update a record; ask for it.
- If the tested run or checkpoint cannot be identified uniquely, ask one clarification question.
- If the user's Play result clearly conflicts with evidence for the identified run or checkpoint, ask exactly one clarification question, do not write or update a record, and do not resolve the conflict silently.
- Never run training, Play, or simulation to obtain missing evidence.

## Workflow

1. Locate the tested run using read-only project evidence as needed:
   - `logs/cusrl/<experiment>/<run>/`
   - W&B metadata, summary, and output logs
   - `logs/slurm/` and the relevant `scripts/cusrl/*.sbatch`
   - task registry entries and their environment or agent configs
   - git commits and existing `docs/experiments/` entries
2. Extract only parameters needed to identify, reproduce, or understand this training: task, run name, Slurm job, tested checkpoint or W&B run, seed, environment count, resources, training iterations, and—when relevant—resume or teacher checkpoint, dataset, and algorithm.
3. Select the comparison baseline in this order:
   1. the baseline explicitly named by the user;
   2. a parent, baseline, or current-best explicitly recorded in `docs/experiments/`;
   3. the most recent prior run with the same purpose in the same task family.
   If multiple baselines remain reasonable, ask exactly one clarification question and do not choose one silently.
4. Compare the run with the baseline. Include a changed value in the key-changes list only when it is an experiment-relevant parameter or a concrete code/config change that affects behavior, checking task/config and entrypoint, rewards and weights, termination, command ranges, terrain, curriculum, randomization, observations, actions, network structure, teacher/resume/data, PPO and optimization settings, schedules, seed, environment count, resources, and training budget. Omit unchanged settings and unrelated metadata. Keep raw commit hashes, build IDs, timestamps, hostnames, operator metadata, and other provenance out of the key-changes list; place them only in the object or evidence when useful. Never infer a code change from a hash change alone. If historical dirty-worktree evidence cannot be recovered, state that the affected difference cannot be determined from available evidence.
5. Preserve the user's Play report faithfully. Structure or compress it without adding observations, causes, judgments, or conclusions.
6. Write directly to `docs/experiments/YYYY-MM-DD.md`. If the same run already has an EXP entry, update that entry instead of creating a duplicate. Otherwise assign the next `EXP-YYYYMMDD-NN` ID for that date.

## Entry Format

Omit fields with no relevant content. Add as many change and evidence bullets as completeness requires.

```markdown
## EXP-YYYYMMDD-NN：<run name>

- 对象：<task / run / job / tested checkpoint>
- 对照：<previous version or baseline>
- 基本参数：<seed, envs, resources, iterations, and relevant teacher/data/resume>

### 用户 Play 结果

<faithful account of the user's reported behavior>

### 相对上一版本的关键改动

- <each relevant setting or code change>

### 证据

- <run, W&B, config, log, commit, or code path>
```

Keep user-reported behavior separate from facts recovered from project evidence. Do not rate success or failure, infer unreported behavior or causes, recommend changes, select the next experiment, dump full configurations, or include a hardware inventory.
