# CST MCP 测试指南

本项目把测试分为离线单元测试和真实 CST 集成测试。两者使用同一套 Pytest 收集规则，
但只有显式提供 `--run-cst` 时才允许启动 CST。

## 离线测试

在仓库根目录运行：

```powershell
python -m pytest -q
```

普通测试会收集真机用例，但将其标记为跳过。该命令不得打开 CST，也不要求许可证。

离线测试可以使用替身，但用途仅限以下几类：

- Worker 退出、超时、编码错误和响应 ID 不匹配；
- COM 或 VBA 错误注入；
- CST 版本兼容路由；
- Buffer 失败状态机和多工程身份冲突；
- 结果序列化、数据转换和 API 外壳。

真实 CST 成功路径不能使用 `monkeypatch`、`mocker`、`MagicMock` 或
`unittest.mock`。`test_cst_test_policy.py` 会自动检查这一规则。

## 真实 CST 测试

真机测试由根 Python 3.12 测试进程通过一个 `CSTWorkerProxy` 调用 Python 3.9
Runtime。CST 2022 Python 库和 Worker 解释器必须已经在 `.cst_config.json` 中配置，
也可以用 `CST_WORKER_PYTHON` 覆盖 Worker 路径。

运行命令：

```powershell
python -m pytest -q -s --run-cst -m cst_integration
```

真机测试禁止使用 pytest-xdist 或其他并行方式。执行前必须关闭用户自己的 CST 工程；
如果测试发现任何已打开工程，会立即拒绝运行，不会接管或关闭用户工程。

默认基准工程是：

```text
skills/cst-runtime-cli/tests/refs/ref_0/ref_0.cst
```

如需使用其他基准工程，可设置：

```powershell
$env:CST_TEST_PROJECT = "D:\path\to\disposable-source.cst"
```

环境变量指向的文件仍然只作为只读源。测试会复制 `.cst` 和同名伴随目录，并在副本上
执行全部操作。

## 唯一工程生命周期

整批真机测试遵循固定生命周期：

1. 启动唯一 Python 3.9 Worker。
2. 调用 `list-open-projects`，确认没有已有工程。
3. 计算源工程摘要并复制到 Pytest 临时目录。
4. 只打开这个工程副本，确认可见工程列表中只有该路径。
5. 所有用例串行复用同一个 Worker 和工程。
6. 测试结束时停止仍在运行的求解器，清理登记资源。
7. 使用 `save=False`、`kill_processes=False` 关闭测试工程并等待锁释放。
8. 确认没有打开工程，关闭 Worker，复核源工程摘要并删除临时目录。

测试不会执行全局 CST 进程清理，也不会终止与测试工程无关的用户进程。

## 建模和清理契约

可删除对象必须在同一个用例中完成：

1. 创建前查询目标不存在；
2. 调用真实 Worker 工具创建；
3. 查询 CST 实体树确认对象存在；
4. 调用公开删除工具；
5. 再次查询确认对象消失。

每个用例还有一个唯一名称前缀和资源登记表。如果断言中途失败，夹具会在 `finally`
阶段删除已登记资源。清理失败会污染共享工程，因此测试会停止后续真机用例。

材料等没有公开删除工具的工程设置放在测试末段，并通过最终不保存关闭隔离副本回滚；
测试不得使用隐藏 VBA 绕过受控工具。

## 求解器、参数和结果

- 求解器只使用异步启动，轮询到 `running=True` 后立即在 `finally` 中强制停止，
  再确认 `running=False`；不会等待完整仿真。
- 参数测试只在已有参数上写入两个值并逐次回读，最后恢复原值；不会运行真正的参数扫描。
- 空结果读取测试使用 `xfail(strict=True)` 等待统一的 `no_result` 或
  `result_not_found` 错误。当前接口一旦正确实现会产生严格 XPASS，提示删除 xfail。

## 故障处理

真机工具返回错误后，测试不会立即重试写操作。夹具会先查询实体、求解器或工程状态，
再决定是否执行登记的清理动作。如果工程关闭、锁释放或资源清理无法确认，临时目录会保留
用于诊断，并把整个真机会话标记为失败。
