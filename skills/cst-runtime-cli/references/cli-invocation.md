# Runtime CLI 调用约定

## 入口

```powershell
& $env:CST_WORKER_PYTHON -m cst_runtime list-tools
& $env:CST_WORKER_PYTHON -m cst_runtime describe-tool --tool <工具名>
```

工具参数和行为以当前 Registry 返回为准，不从旧文档猜测。

## 参数

- 标量且已由 `describe-tool` 确认支持时可使用 CLI flag；
- 数组、对象和复杂参数必须使用 `--args-file`；
- `args-template --tool <工具名>` 生成临时模板，编辑后再调用；
- 所有工程路径使用绝对 `.cst` 路径；
- 不向命令添加 Schema 未声明字段。

## 返回值

每次读取 stdout JSON：

- `status=success`：充分相信 CST 已成功执行该工具对应的 VBA，不再查询实体、参数或配置证明执行成功；结果导出等文件产物和异步求解结果仍按工具承诺取得；
- `status=error`：读取 `error_type`、`message`、`error` 和 `context`；
- transport/worker timeout：操作可能已经提交，先检查实际状态，不直接重复；
- 输出不是合法 JSON：按 Worker/CLI 故障处理，不从控制台杂项推断业务结果。

## 审计

生产任务使用 task/run 目录。`--args-file`、阶段输出、工具调用和结果文件应保存在对应 run 中；不要在仓库根目录散落临时参数文件。设计意图和用户确认使用 Agent note，工具请求和返回由 interaction journal 记录。
