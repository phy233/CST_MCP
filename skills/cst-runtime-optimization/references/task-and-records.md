# 优化任务与记录

## 任务卡

任务开始时记录：

```json
{
  "task_id": "task_metasurface_phase_001",
  "source_project": "D:/models/baseline.cst",
  "working_project": "D:/runs/run_001/projects/working.cst",
  "objective": {
    "description": "10 GHz 同极化反射相位接近 90 度",
    "direction": "minimize",
    "formula": "abs(wrapped_phase_deg - 90)"
  },
  "parameters": [
    {"name": "patch_w", "min": 2.0, "max": 4.0, "unit": "mm"}
  ],
  "constraints": ["gap >= 0.2 mm"],
  "budget": {"max_trials": 20, "no_improvement_trials": 4}
}
```

字段应反映实际工具能力，不要求创建新的固定 Schema 文件。

## 每个 trial 必须记录

- trial 编号和时间；
- 工程副本、before/after snapshot 或 operation；
- 请求参数和读回参数；
- 求解状态、Run ID 和耗时；
- 结果树路径或导出文件；
- 目标公式、目标值和约束结果；
- `completed`、`failed`、`rejected` 或 `unvalidated`；
- interaction ID、错误和用户决定。

使用现有 task/run 的 `stages/`、`logs/`、interaction journal、History journal 和 Agent notes，不另建第二套 `trials.jsonl`。若当前工具已经生成 study 数据库或导出文件，记录其路径而不是复制内容。

## 工作笔记分类建议

- `plan`：优化目标、变量和预算；
- `decision`：选择候选、调整范围或更换 sampler；
- `user_confirmation`：用户确认高成本仿真或策略变化；
- `milestone`：基线、最佳点、停止结论；
- `reconciliation`：中断后确认 operation 是否生效。

## 数据保留

- 不覆盖旧 run 的工程、结果或导出；
- 失败和拒绝 trial 保留原因，避免以后重复；
- 多个结果比较前确认工程版本、Run ID、模式映射和频率网格一致；
- 当前仓库未实现代理模型训练，不生成虚假的 dataset/model version 或模型卡。
