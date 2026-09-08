# 故障判断与恢复

## 先处理终止信号

在普通错误或超时处理之前检查 `terminal` 和 `await_user_decision`。任一为 `true` 时，立即停止本回合对该任务的所有后续 CST 调用，包括状态查询、轮询、重试和重新启动求解。

- `long_run_relinquish`：Runtime 达到长任务分界后让出等待，CST 求解可能仍在后台运行；这不是求解失败证据。
- 带 `terminal=true` 的传输超时：同样停止，不能按普通传输错误继续检查副作用。
- 报告 `project_path`、`error_type`、`timeout_class`、`solver_left_running` 和返回的 `recovery`；未返回的信息标为未知。只在用户决定恢复后，按该次返回的恢复序列继续。

以下故障流程仅用于未触发上述终止分支的调用。

## 写操作失败

- `validation_error`：尚未提交 CST，修正输入后可以重新调用；
- `vba_runtime_error`：CST 已执行到明确错误，检查可能留下的部分副作用；
- `vba_compile_or_host_error`：无法确定 VBA 是否执行，查看 History 和实体后再决定；
- transport/worker timeout 或退出：请求可能已经到达 Worker/CST，禁止直接重发；
- `recording_status=incomplete`：业务操作可能成功，但快照或日志不完整，应补做状态检查并保留问题说明。

## 求解器失败

- 同步启动返回 `solver_run_failed` 时读取附带的 CST 日志错误；
- `wait-simulation` 返回 `solver_stopped_with_error` 时检查等待期间新增日志；
- 求解停止但无新 Run ID 时，不宣称成功，检查结果树、缓存、参数是否生效和实际求解日志；
- 不通过重复发送 start 命令修复未知状态。

## 工程锁与 Session

- `.lok` 未释放时不复制、覆盖或重新打开工程；
- 多个打开工程且目标不唯一时停止；
- 不关闭或终止用户已有 Design Environment；
- 关闭失败后保留 PID、工程路径、锁状态和错误文本，不用进程名批量杀 CST。

## History 不确定性

根据当前快照与 operation 的 expected-before/after 判断：

- 与 before 相同：`not_applied`，用户确认后才允许重试；
- 与 after 相同：`applied`，跳过；
- 两者都不同：`ambiguous`，禁止自动重试，使用 `reconcile-history-operation` 记录人工结论。

需要回退或切换分支时，从物理检查点创建隔离副本并生成 restore plan，不在当前工程上调用未验证的私有 History 写接口。
