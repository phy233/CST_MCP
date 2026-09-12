# 优化任务与记录

## 任务卡

任务开始时按实际信息填写。下面是待确认示例，不构成执行授权；其中动作、范围和预算均需与用户已有授权核对，确认后再将 `approval_status` 记录为 `approved`：

```json
{
  "task_id": "task_metasurface_phase_001",
  "source_project": "D:/models/baseline.cst",
  "working_project": "D:/runs/run_001/projects/working.cst",
  "objective": {
    "description": "10 GHz 同极化反射相位接近 90 度",
    "direction": "minimize",
    "spec": {
      "type": "phase_at_freq",
      "result_path": "SZmax(1),Zmax(1)",
      "freq": 10,
      "target_deg": 90
    }
  },
  "parameters": [
    {"name": "patch_w", "min": 2.0, "max": 4.0, "unit": "mm"}
  ],
  "constraints": ["gap >= 0.2 mm"],
  "budget": {"max_trials": 20, "no_improvement_trials": 4},
  "roles": {
    "user_owned_decisions": ["objective", "parameters", "hard_bounds", "budget", "final_selection"],
    "agent_suggestions": ["candidate_order", "sampler", "early_stop"]
  },
  "approved_actions": ["change-parameter", "rebuild-model", "save-project", "run-experiment", "export-sparameter", "tell-study"],
  "automation_scope": "只在已确认的变量、硬范围、预算和停止条件内连续执行",
  "approval_status": "proposed"
}
```

此例假设从 Zmax 的模式 1 入射，并以同一端口、同一模式的反射相位为目标。CST 2022 Online Help 的 `mergedProjects/EXP_HF/examplesoverview/fss__simulation_of_resonator_array.htm` 将 `SZmax(1),Zmax(1)` 定义为该通道的同极化反射；`SZmin(1),Zmax(1)` 是跨端口透射通道。执行前根据实际结果树、入射侧、模式极化和参考面替换路径，不把示例当成通用配置。

字段应反映实际工具能力，不要求创建新的固定 Schema 文件。`objective.spec` 直接对应 `run-probe-phase`/`run-optimization-step` 的 `objective` 参数；需要复合指标时使用 expression 类型，沙箱内可用 `phase_deg(path,f)`、`amp_db(path,f)`、`wrap(x)` 与 `s11_db/s11_freq/min/max/len/abs`。自由文本的 `formula` 字段仅供人阅读，不能被执行；凡是进入 trial 循环的目标必须给出可执行的 spec。`approval_status` 未达到 `approved` 时，只能完善任务卡和提出建议，不能启动探针、仿真或优化。

## 每个 trial 必须记录

- trial 编号和时间；
- 工程副本、operation 和 interaction ID；普通成功调用不要求 before/after snapshot，只有恢复或 ambiguous 时才关联；
- 请求参数和接口成功/错误状态；接口成功时不要求重复读回参数；
- 求解状态、Run ID 和耗时；
- 结果树路径或导出文件；
- 目标公式、目标值和约束结果；
- `completed`、`failed`、`rejected` 或 `unvalidated`；
- 错误和用户决定；
- 建议、批准和实际执行状态，避免把 `proposed` 写成 `approved` 或 `executed`。

使用现有 task/run 的 `stages/`、`logs/`、interaction journal、History journal 和 Agent notes，不另建第二套 `trials.jsonl`。若当前工具已经生成 study 数据库或导出文件，记录其路径而不是复制内容。

收到终止信号时，本 trial 暂记 `unvalidated`，附上工具返回的求解器状态和待恢复原因；后台求解尚未确认结束时，不据此记为求解失败或提交有效目标值。

## 工作笔记分类建议

- `plan`：优化目标、变量和预算；
- `decision`：选择候选、调整范围或更换 sampler；
- `user_confirmation`：用户确认高成本仿真或策略变化；
- `milestone`：基线、最佳点、停止结论；
- `reconciliation`：中断后确认 operation 是否生效。

工作笔记还应区分 `user_decision`、`agent_suggestion`、`approved_action` 和 `executed_fact`，使最终报告能够说明哪些是用户决定、哪些只是 Agent 建议、哪些已经由工具执行。

## 数据保留

- 不覆盖旧 run 的工程、结果或导出；
- 失败和拒绝 trial 保留原因，避免以后重复；
- 多个结果比较前确认工程版本、Run ID、模式映射和频率网格一致；
- 当前仓库未实现代理模型训练，不生成虚假的 dataset/model version 或模型卡。

最终交付以 trial 表、授权范围内的候选排序、约束满足情况、失败/未验证项和仍需用户决定的问题为主，不把局部最佳称为全局最优设计。
