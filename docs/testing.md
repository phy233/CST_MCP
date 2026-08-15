# CST MCP 测试指南

本项目把测试分为离线单元测试和真实 CST 集成测试。两者使用同一套 Pytest 收集规则，
但只有显式提供 `--run-cst` 时才允许启动 CST；求解器类用例还需要二次显式开关
`--run-cst-solver`。

## 分层与命令

| 层级 | 内容 | 命令 | 典型耗时 |
|---|---|---|---|
| 默认（离线全量） | 纯单元 + 子进程 CLI + Worker 代理（均不启动 CST） | `python -m pytest -q` | ~45s |
| 快速通道（纯单元） | 不含子进程与 Worker 代理 | `python -m pytest -q -m "not subprocess and not worker_proxy"` | ~6s |
| 子进程 CLI | `subprocess` 标记：`cli/test_*.py`、`test_cli_remaining.py`、`test_cli_hygiene.py` | `python -m pytest -q -m subprocess` | ~35s |
| Worker 代理 | `worker_proxy` 标记：`mcp_server/tests` 中拉起 py39 Worker 的用例 | `python -m pytest -q -m worker_proxy` | ~10s |
| 真机集成（非求解器） | `cst_integration` 标记 | `python -m pytest -q -s --run-cst -m cst_integration` | ~7 分钟 |
| 真机求解器 | `cst_solver` 标记（真机子集） | `python -m pytest -q -s --run-cst --run-cst-solver -m cst_solver` | 另加 ~2 分钟 |
| 真机全量 | 上述两者合并 | `python -m pytest -q -s --run-cst --run-cst-solver -m cst_integration` | ~9 分钟 |

标记在 `pyproject.toml [tool.pytest.ini_options] markers` 中统一声明；门控与跳过逻辑
只存在于根 `conftest.py`。默认命令会收集真机用例但全部跳过，绝不打开 CST、不要求许可证。

- `--run-cst`：运行真机集成测试，但跳过 `cst_solver` 用例。
- `--run-cst --run-cst-solver`：全量运行（含短暂启停求解器的用例）。
- 分析最慢用例：`python -m pytest -q --durations=10`。

## 离线测试

离线测试可以使用替身，但用途仅限以下几类：

- Worker 退出、超时、编码错误和响应 ID 不匹配；
- COM 或 VBA 错误注入；
- CST 版本兼容路由（`core/compatibility/*` 的版本化 VBA 与错误路径）；
- Buffer 失败状态机和多工程身份冲突；
- 结果序列化、数据转换和 API 外壳。

真实 CST 成功路径不能使用 `monkeypatch`、`mocker`、`MagicMock` 或
`unittest.mock`。`test_cst_test_policy.py` 会自动检查这一规则，并禁止
真机模块使用装饰器级 `xfail`（会吞掉传输超时）。

`worker_proxy` 用例会启动 `CSTWorkerProxy`（Python 3.9 Worker 子进程）。找不到
Worker 解释器（`CST_WORKER_PYTHON` 环境变量或 `~/miniconda3/envs/cst39/python.exe`）
时自动跳过，不会让默认运行失败。

## 测试卫生

- `helpers.run_cli` 与 conftest 的 `run_cli_json` 夹具使用**会话级临时 cwd**，
  CLI 子进程的任何工作区/参数捕获文件都落在临时目录并在会话结束时删除，
  不会向仓库根写入 `.cst_runtime` 状态。`test_cli_hygiene.py` 会验证这一点。
- 仓库根下的 `.cst_runtime/workspace.json` 属于真实运行环境标记，测试不会创建或删除它。
- 历史遗留的损坏 ACL 目录（`.pytest_cache`、`.pytest_basetemp`、`.pytest_bt_py`、
  已删除的 `mcp_server/tests/manual/__pycache__`）无法在测试进程内删除。
  如遇到 `PytestCacheWarning: could not create cache path`，请在**管理员
  PowerShell** 中执行一次：
  ```powershell
  cd D:\My_Program\Python\CST_MCP
  takeown /F .pytest_cache /R /D Y; icacls .pytest_cache /reset /T /C
  Remove-Item -Recurse -Force .pytest_cache, .pytest_basetemp, .pytest_bt_py
  ```
- 当前没有 CI 配置；分层命令即本地验收流程。

## 真实 CST 测试

真机测试由根 Python 测试进程（venv 为 Python 3.14，`requires-python >= 3.12`）
通过一个 `CSTWorkerProxy` 调用 Python 3.9 Runtime（conda `cst39` 环境）。
CST 2022 Python 库与 Worker 解释器已在 `.cst_config.json` 配置，
也可用 `CST_WORKER_PYTHON` 覆盖 Worker 路径。

默认基准工程是：

```text
skills/cst-runtime-cli/tests/refs/ref_0/ref_0.cst
```

该工程连同其 `Model/`、`Result/` 伴随目录已完整纳入 git（`.gitattributes`
禁止对其做任何 EOL 转换），新 clone 即可复现真机套件。如需其他基准工程：

```powershell
$env:CST_TEST_PROJECT = "D:\path\to\disposable-source.cst"
```

环境变量指向的文件仍然只作为只读源。测试会复制 `.cst` 和同名伴随目录，并在副本上
执行全部操作。

### 真机测试文件与覆盖

| 文件 | 数量 | 覆盖 |
|---|---|---|
| `test_cst_integration.py` | 15 | 唯一工程、brick/cylinder/boolean-add、截图、build-array×2、材料缺失错误、1D/2D 结果错误、参数组合、**求解器启停（cst_solver）**、**求解器 pause/resume/stop（cst_solver）**、材料定义验收、参数读写恢复 |
| `test_cst_session.py` | 7 | inspect / verify-identity / wait-unlocked / save 落盘 / reattach / infer-run-dir / is-running |
| `test_cst_modeling.py` | 14 | cone、polygon+extrude、boolean subtract/intersect/insert、transform mirror/rotate/destination 拒收、rename、颜色+换材料、解析曲线、loft/hollow/horn 扫掠 |
| `test_cst_results.py` | 10 | version、结果枚举、run-ids、S 参数/场结果、subprojects、open-results、导出缺失路径结构化错误 |
| `test_cst_setup.py` | 18 | units/background/boundary/unit-cell/plane-wave、mesh/solver/FD 求解器、监视器生命周期、组件与网格组、Floquet、批量参数（末段回滚） |

文件按字母序执行，`test_cst_setup.py` 天然排最后；无公开删除工具的状态类
设置集中在其中，靠会话末段 `save=False` 回滚。`test_cst_integration.py` 的两个
求解器用例必须排在参数写入用例之前：`change-parameter` 会登记 `params_dirty`，
之后任何 `start-simulation-async` 都会被 T2 守卫拒绝。

共享断言与实体树工具在 `cst_helpers.py`（`entity_keys`、`assert_error_response`、
`prepare_interactive_result_read` 等）。

### 唯一工程生命周期

1. 启动唯一 Python 3.9 Worker。
2. 调用 `list-open-projects`，确认没有已有工程。
3. 计算源工程摘要并复制到 Pytest 临时目录。
4. 通过正式的 `cst-session-open` 打开工程副本；等待期间持续发现本次新建的 DE，
   使用 Windows 窗口 API 恢复并显示其主窗口，不允许后台静默运行。
5. 确认只有一个新 DE、一个可见且未最小化的主窗口，以及唯一的工程路径。
6. 所有用例串行复用同一个 Worker 和工程。
7. 测试结束时停止仍在运行的求解器，确认 `running=False` 后再清理登记资源。
8. 使用 `save=False`、`kill_processes=False` 关闭测试工程并等待锁释放。
9. 确认没有打开工程，关闭 Worker，复核源工程摘要并删除临时目录。

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

材料、单位、边界、组件、网格组等没有公开删除工具的工程设置放在测试末段，并通过
最终不保存关闭隔离副本回滚；测试不得使用隐藏 VBA 绕过受控工具。

## 求解器、参数和结果

- 求解器只使用异步启动，轮询到 `running=True` 后立即（或在 pause/resume 验证后）
  在 `finally` 中强制停止，再确认 `running=False`；不会等待完整仿真。
- 参数测试只在已有参数上写入两个值并逐次回读，最后恢复原值；不会运行真正的参数扫描。
- 结果读取前先保存隔离工程，并设置 `allow_interactive=True`。这是 CST 2022 官方接口在工程
  同时由 Studio Suite 打开时读取最近保存状态的必要条件。
- 空 1D 结果测试只对一个精确的旧错误类型执行条件式 `xfail`，并先验证错误消息确实指向
  缺失结果。参数组合测试验证 Run ID 0 能解析为真实或最新结果编号；CST 2022 未公开的
  2D 提取能力则验证精确的 `unsupported_feature` 兼容性错误，不伪装成空结果。
  传输超时、Worker 退出、工程打开失败等无关错误不能被 `xfail` 吞掉。
- 截图测试会检查 PNG 文件签名、IHDR 尺寸和 JSON 元数据；仅有“文件存在且非空”不算通过。

## 故障处理

真机工具返回错误后，测试不会立即重试写操作。夹具会先查询实体、求解器或工程状态，
再决定是否执行登记的清理动作。如果工程关闭、锁释放或资源清理无法确认，临时目录会保留
用于诊断，并把整个真机会话标记为失败。

如果 `cst-session-open` 已经启动 DE，但主窗口仍不可见，测试会在输出中记录已观察到的 PID、
窗口标题和窗口句柄，并在失败清理中只终止本次测试新建的 PID。官方启动参数 `--hide` 不得
出现在真机 fixture 中。
