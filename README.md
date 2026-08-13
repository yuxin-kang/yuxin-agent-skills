# Yuxin Agent Skills

个人 Agent Skills 集合。

## Skills

- `experiment-record`：记录 Leo Lab 实验结果和运行证据。
- `robotics-paper-digest`：抓取、筛选并总结最新机器人论文。

## 本地论文日报

默认检索最近 3 天：

```bash
python3 robotics-paper-digest/scripts/run_local_digest.py
```

指定其他天数：

```bash
python3 robotics-paper-digest/scripts/run_local_digest.py --lookback-days 7
```

安装每天 08:30 的本地定时任务：

```bash
python3 robotics-paper-digest/scripts/install_local_schedule.py
```

日报、去重状态和日志只保存在本地的 `.local-output/` 和 `.local-data/`，不会上传到 GitHub。
