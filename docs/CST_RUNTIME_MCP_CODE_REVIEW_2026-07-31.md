# CST Runtime / MCP 源码审阅报告

> 审阅日期：2026-07-31
> 本地基线：当前工作树，`HEAD=d62a5d6`
> 审阅方式：只读静态分析；未运行测试、构建、CST、MCP Server 或 Worker
> 首要目标：识别 CST 2022 静默失败风险，并给出最小错误 Gateway 方案

## 0. 结论摘要与证据口径

### 0.1 总体判断

当前仓库已经建立了有价值的双 Python 进程隔离、常驻 Worker、统一工具注册表、工程身份校验、Command Buffer 和部分 CST 安全守卫。MCP 层没有直接导入 `cst_runtime`，这一关键隔离成立。

但当前真实依赖关系不是交接说明中的简单线性结构 `Worker → lib → core`：原子工具通常是 `Worker → API registry → tools → core`，工作流通常是 `Worker → API registry → workflows → lib → core`，而少数 `lib` 函数又直接访问 CST COM 对象。最严重的问题仍是 `_add_vba_history()` 在 COM 调用未抛异常时无条件返回 `success`，这会把 CST 2022 已知的 VBA 运行时错误或语法错误误报成成功。

因此，项目目前可以称为“传输层和分层重构基本完成”，但还不能称为“建模执行结果可靠”。在错误 Gateway 和后置验证落地前，Agent 不应仅凭 `status=success` 宣称实体、材料、边界、端口或参数已经正确写入 CST。

### 0.2 证据标签

| 标签                   | 含义                                             |
| ---------------------- | ------------------------------------------------ |
| **[源码确认]**   | 可由本地或固定版本的公开源码直接证明             |
| **[交接实测]**   | 来自交接材料记录的 CST 2022 实验，本轮未复测     |
| **[合理推断]**   | 由调用链和已知行为推导，尚未用 CST 2022 真机复核 |
| **[待真机验证]** | 必须在隔离的 CST 2022 临时工程中确认             |

### 0.3 外部源码固定版本

- `bbl21/cst-runtime-cli`：公开 `master` 的固定提交 [`7eac82190845083396889a7ae96ed22c2118a892`](https://github.com/bbl21/cst-runtime-cli/tree/7eac82190845083396889a7ae96ed22c2118a892)，提交时间 2026-06-24。
- HERMES `cst-python-api`：公开 `main` 的固定提交 [`72b0e13f56a57749f640191abe2239a4e222a53b`](https://src.koda.cnrs.fr/hermes/cst-python-api/-/tree/72b0e13f56a57749f640191abe2239a4e222a53b)，提交时间 2026-06-29。
- 本报告只做源码与架构比较。由于本地没有 `upstream/master` 跟踪引用，不伪造逐提交共同祖先或精确增删统计。

## 1. 当前仓库真实架构图

```mermaid
flowchart TD
    A["Agent / MCP Client"] --> B["mcp_server.server<br/>Python 3.12+"]
    B --> C["CSTWorkerProxy<br/>同步请求锁、超时、重启"]
    C -->|"JSONL / stdin / stdout"| D["cst_runtime.worker<br/>Python 3.9 常驻进程"]
    D --> E["API registry<br/>统一公开名和 Schema"]
    E --> F["动态发现的 tools handlers"]
    E --> G["显式注册的 workflows"]
    F --> H["core"]
    G --> I["lib 公开工作流 API"]
    I --> H
    I -. "少数越层 COM 访问" .-> J["CST project / modeler / model3d"]
    H --> J
    J --> K["cst.interface / cst.results / COM / VBA"]
    K --> L["CST Studio Suite 2022+"]
    F -. "个别反向调用" .-> M["cli.pipelines"]
```

### 1.1 已成立的架构约束

- **[源码确认]** `mcp_server/server.py:7-8` 只导入本层 `config` 和 `proxy`；`tests/test_mcp_server.py:42-57` 也以 AST 检查 MCP 层不得导入 `cst_runtime`。
- **[源码确认]** `mcp_server/proxy.py:66-77` 使用指定解释器启动 `python -m cst_runtime.worker`，通信为 UTF-8 JSONL，且 `shell=False`。
- **[源码确认]** `mcp_server/proxy.py:145-175` 用重入锁串行化请求，以 UUID 校验响应；超时后终止 Worker，避免迟到响应污染下一次调用。
- **[源码确认]** `cst_runtime/worker.py:36-67` 只接受 `ping`、`describe_tools`、`call_tool` 三类白名单动作，不允许客户端指定任意模块和函数。
- **[源码确认]** `cst_runtime/api/registry.py:268-294` 将原子工具和三个工作流合并为统一操作/工具视图。

### 1.2 与交接说明不同的当前事实

- **[源码确认]** 工具清单不是 MCP 侧静态维护。`api/atomic.py:27-39` 会导入受控模块并扫描全部 `tool_*` 可调用对象，`server.py:21-22` 又在服务器创建时通过 Worker 动态读取描述。
- **[源码确认]** 动态发现是“限定模块白名单内的动态发现”，不是对整个 `lib` 任意扫描；安全性明显好于旧 Adapter，但仍应在文档中准确表述。
- **[源码确认]** 当前 `tools-list.json` 含 117 个条目；README 写 113 个，`skills/cst-mcp/SKILL.md` 写“不复制 114 个工具”，`INSTALL.md` 仍写 20 个工具，四者不一致。
- **[源码确认]** Worker 仍会在 `worker.py:25-33` 修改自身 `sys.path` 以加载 CST 库；真正被移除的是 MCP 进程直接修改路径并导入 Runtime 的旧方式。

## 2. 问题清单（按严重程度）

### P0：建模 History 的“成功”可能是假成功

**证据：**

- **[源码确认]** `core/modeling.py:13-45` 调用 `project.modeler.add_to_history(...)` 后，只要 Python 没收到异常，就直接返回 `status=success`；没有检查返回值、状态文件或模型后置条件。
- **[交接实测]** CST 2022 中，不存在材料和明显 VBA 语法错误仍可能让 `add_to_history` 返回 `True`，错误只出现在 Message Window。
- **[源码确认]** `core/modeling.py:15-17` 在批处理模式下甚至尚未提交 CST 就返回 `success`，该状态实际只代表“已加入内存缓冲区”。

**影响：** Agent 可能在模型未创建、只创建一部分或 History 含错误时继续保存、仿真和导出，最终得到错误但表面完整的结果链。

**建议：** 第一优先级引入批次级错误 Gateway；把“已缓冲、已提交、VBA 报告成功、后置验证通过”拆成不同状态，不再复用一个 `success`。

### P0：Command Buffer 在提交前被弹出，失败后命令丢失

- **[源码确认]** `core/buffer.py:53-58` 的 `pop_batch()` 先从全局字典删除缓冲区。
- **[源码确认]** `core/modeling.py:65-77` 随后才把脚本提交给 CST。
- **[合理推断]** 若 attach、COM 提交、Worker 或 CST 在两者之间失败，内存中的原始批次无法重试或诊断；当前返回中也没有批次脚本摘要、哈希或 `operation_id`。

**建议：** 将 flush 改为 `peek → submit/verify → commit_remove`；失败时保留或显式归档批次，成功后才删除。VBA 状态文件应按“整个 flush”创建一次，不能按阵列单元创建。

### P1：CST 2022 仍有直接 `model3d` 访问和错误吞噬

- **[源码确认]** `core/project.py:67-114` 的参数枚举必须经过 `get_model3d()`，CST 2022 无此对象时直接失败。
- **[源码确认]** `lib/solver.py:139-177` 直接调用 `project.model3d.DeleteResults()` 和 `GetSolverType()`，绕过兼容层。
- **[源码确认]** `lib/results.py:141-158` 直接调用 `project.model3d.ResultTree...`，任何异常都被转成 `False`；“接口不支持”“COM 故障”和“结果不存在”无法区分。
- **[源码确认]** `lib/materials.py:84-109` 直接访问 `project.modeler.get_tree_items()`，异常时返回空列表；`exists()` 又会把异常当成“不存在”。

**影响：** 兼容故障可能被误解释为业务上的对象不存在，导致 Agent 重复创建、错误分支或破坏已有对象。

**建议：** 所有 COM 查询下沉到 `core/compatibility`，返回结构化的 `unsupported_feature` 或 `cst_query_error`；公开 `lib` 不直接持有/访问项目 COM 对象。

### P1：兼容层的能力检测可能被 RemoteObject 代理误导

- **[源码确认]** `compatibility/base.py:7-11`、`parameters.py:7-12`、`farfield.py:8-23` 主要依靠 `hasattr()`。
- **[源码确认]** `base.py:10` 硬编码“requires CST 2023+”，但本仓库没有官方版本矩阵或固定实测记录证明精确起始版本。
- **[源码确认]** `tree.py:13-26` 的新版路径没有捕获调用失败并尝试旧版路径；只在旧版 `filter` 参数触发 `TypeError` 时回退。
- **[合理推断]** 动态 RemoteObject 可能让属性存在性检测通过，但真正调用仍失败。

**建议：** 使用“安全、只读、可重复”的能力探针，并分别记录 `attribute_missing`、`call_unsupported`、`call_failed`；版本文本改为“当前运行时未提供该能力”，精确版本仅作为经验证的元数据。

### P1：错误契约在各层之间不统一

- **[源码确认]** `core/errors.py:11-26` 采用 `{status, error_type, message}` 字典。
- **[源码确认]** 多数 `lib` 包装器又把错误字典转换为普通 `RuntimeError`；部分布尔查询把错误吞成 `False`。
- **[源码确认]** `api/registry.py:307-323` 只保留异常类名和字符串，阶段、CST 原始信息、回滚和恢复建议都丢失。
- **[源码确认]** `worker.py:60-66` 对注册表外溢异常返回完整 Python traceback；这既可能暴露本机路径，也不符合面向 Agent 的稳定错误接口。
- **[源码确认]** Proxy 的启动、IPC、退出和超时错误抛 `CSTTransportError`，`server.py:40-52` 未把它标准化成与业务错误相同的信封。

**建议：** 引入单一错误信封，并让 `validation/transport/worker/submission/execution/verification/rollback` 成为稳定阶段；Worker traceback 仅写受控诊断日志，不默认返回 MCP 客户端。

### P1：远场即时 VBA 的最终 fallback 再次产生假成功

- **[源码确认]** `core/farfield.py:161-201` 优先尝试 `schematic.execute_vba_code` 和新版私有入口，这些异常至少可被捕获。
- **[源码确认]** `core/farfield.py:203-210` 最后回退到 `modeler.add_to_history` 后无条件返回成功，重新引入同一静默失败问题。
- **[交接实测]** `schematic.execute_vba_code` 在 CST 2022 会对语法或运行时错误抛出 `RuntimeError`，但它不写建模 History，不能替代常规参数化建模。

**建议：** 保留即时 VBA 与 History 两条语义明确的路径；History fallback 必须进入统一 Gateway，不能伪装成与 `execute_vba_code` 等价的可靠执行。

### P2：实际依赖方向仍存在越层和反向依赖

- **[源码确认]** `tools/simulation.py:72-81` 从 `tools` 反向导入 `cli.pipelines.impl`。
- **[源码确认]** `tools/__init__.py:27-47` 为构建工具对象导入 `cst_runtime.cli.dispatch._tool_governance`。
- **[源码确认]** 多数原子 `tools` 直接调用 `core`，工作流则通过 `lib`；因此 `lib` 并不是所有公开入口的唯一稳定 API。
- **[源码确认]** `lib/materials.py`、`lib/solver.py`、`lib/results.py` 存在直接 COM 访问。

**建议：** 固定依赖为 `transport adapters → application API/registry → workflows/tools adapters → lib services → core drivers`。CLI 治理逻辑应上移到协议无关 API 层，避免 tools 依赖 CLI。

### P2：仿真状态语义仍可能过度乐观

- **[源码确认]** `core/simulation.py:17-40` 在 `run_solver()` 返回后直接写“simulation completed”，没有读取求解器终态、错误码或结果存在性。
- **[源码确认]** `start_solver()` 返回后直接写“simulation started”；轮询只读取 `is_solver_running()`，不能区分“成功结束”和“启动后立刻失败”。
- **[源码确认]** `lib/solver.py:95-107` 在状态查询报错时返回 `False`，调用者可能把查询失败误认成“仿真已结束”。

**建议：** 轮询结果至少区分 `running/completed/failed/unknown/query_error`，并用预期结果树或求解器日志作为完成后验证。

### P2：原始 VBA 工具扩大了 Agent 风险面

- **[源码确认]** `tools/modeling.py:44-45,2086` 暴露通用 `add_to_history` 工具。
- **[合理推断]** 即使 Schema 将其标记为写操作，Agent 仍可提交未经过业务校验的任意 VBA；现有静默成功会进一步放大风险。

**建议：** 默认不向普通 Agent 工作流暴露，或标记为高风险专家工具；要求显式启用、工程副本和 `strict` 验证。

### P3：文档、版本和工具数量已经漂移

- **[源码确认]** 根 `pyproject.toml:23-24` 指向不存在或错误归属的 `bbl21/cst-mcp`，当前远程实际是 `phy233/CST_MCP`。
- **[源码确认]** README 要求 CST 2026/Python 3.13+，INSTALL 要求 CST 2022+/MCP Python 3.12+/Worker 3.9。
- **[源码确认]** README clone 示例仍指向 `anomalyco/cst-runtime-cli`。
- **[源码确认]** `INSTALL.md` 描述 FastMCP、20 个工具、`cst_worker.py` 和 `conda run`，当前源码实际使用低层 `mcp.server.Server`、117 条已导出清单、`cst_runtime.worker` 和直接解释器路径。
- **[源码确认]** `docs/implementation-plan.md` 和 `docs/MCP待完成任务清单.md` 仍大量描述已删除 Adapter，容易误导维护者。

## 3. 当前错误处理调用链

```mermaid
sequenceDiagram
    participant CST
    participant Core
    participant LibTool as lib/tools
    participant Registry
    participant Worker
    participant Proxy
    participant MCP

    Core->>CST: COM / add_to_history / solver
    alt Python 收到异常
        CST-->>Core: Exception
        Core-->>LibTool: status=error
    else CST 吞掉 VBA 错误
        CST-->>Core: True 或正常返回
        Core-->>LibTool: status=success（可能是假成功）
    end
    LibTool-->>Registry: 字典、RuntimeError 或 False
    Registry-->>Worker: 字典；异常被压缩为类名和 message
    Worker-->>Proxy: JSONL 响应；外溢异常可能含 traceback
    Proxy-->>MCP: 业务字典，或抛 CSTTransportError
```

### 3.1 当前存在的三类“成功”被混在一起

1. 已加入 Command Buffer，尚未接触 CST。
2. COM/History 提交没有向 Python 抛异常。
3. 业务目标真实成立。

当前多数建模 API 把前两类都写成 `status=success`，但系统真正需要的是第三类。建议以后明确使用：

```json
{
  "ok": true,
  "submission": "accepted",
  "execution": "reported_ok",
  "verification": "passed"
}
```

若尚未验证，则必须写 `verification: "not_run"`，而不是省略后仍由上层推断成功。

## 4. CST 2022 中可能静默失败或误判的 API 清单

| 入口                                            | 本地位置                     | 目的                     | 当前错误可见性                | CST 2022 判断                              | 迁移建议              |
| ----------------------------------------------- | ---------------------------- | ------------------------ | ----------------------------- | ------------------------------------------ | --------------------- |
| `modeler.add_to_history`                      | `core/modeling.py:32`      | 绝大多数建模/设置        | 仅 Python/COM 异常            | **[交接实测]** VBA 错误可能返回 True | P0，统一 Gateway      |
| 缓冲追加                                        | `core/modeling.py:15-17`   | 批量 VBA                 | 尚未执行却返回成功            | **[源码确认]**                       | 改为`buffered` 状态 |
| 批量 flush                                      | `core/modeling.py:65-77`   | 合并 History 节点        | 弹出后提交，无后置验证        | **[合理推断]** 失败会丢批次          | peek/commit 两阶段    |
| 原始 VBA Tool                                   | `tools/modeling.py:2086`   | 任意 History VBA         | 继承假成功                    | **[合理推断]** 高风险                | 默认隐藏或 strict     |
| 即时 VBA                                        | `core/farfield.py:161-201` | GUI/查询/导出            | `execute_vba_code` 异常可见 | **[交接实测]** 2022 较可靠           | 保留独立语义          |
| 即时 VBA fallback                               | `core/farfield.py:203-210` | 无即时入口时回退         | 无条件成功                    | **[源码确认]**                       | 进入 Gateway          |
| 参数枚举                                        | `core/project.py:67-114`   | 读取全部参数             | `model3d` 缺失时报错        | **[交接实测]** 2022 不支持           | 借鉴旧 COM 参数 API   |
| 参数写入                                        | `core/project.py:153-181`  | `StoreDoubleParameter` | History 假成功；无读回        | **[源码确认]**                       | 写后读回验证          |
| 材料枚举                                        | `lib/materials.py:84-109`  | 树读取                   | 异常变空列表                  | **[源码确认]**                       | 兼容层 + 明确错误     |
| 结果存在性                                      | `lib/results.py:141-158`   | `ResultTree` 查询      | 异常变 False                  | **[源码确认]**                       | 不支持与不存在分离    |
| 删除结果/求解器类型                             | `lib/solver.py:139-177`    | 直接`model3d`          | 普通 RuntimeError             | **[交接实测]** 2022 不兼容           | 下沉兼容层            |
| `run_solver`                                  | `core/simulation.py:17-40` | 阻塞仿真                 | 仅 COM 异常                   | **[待真机验证]**                     | 终态和结果验证        |
| `start_solver` + polling                      | `core/simulation.py:43-88` | 非阻塞仿真               | running 布尔值                | **[合理推断]** 不能证明成功结束      | 多状态模型            |
| `full_history_rebuild`                        | 运行时代码中未找到           | 重建 History             | 当前无正式入口                | **[交接实测]** True 也不可靠         | 不作为成功判据        |
| `_GetHistory/_TryToUndoNTimes/_ResizeHistory` | 仅文档引用，无运行时接入     | 诊断/回滚                | 私有且未文档化                | **[待真机验证]**                     | 仅实验，不进生产      |

## 5. 三方源码级比较

| 维度                  | 当前 Fork                                    | `bbl21/cst-runtime-cli` 固定提交       | HERMES CST Python API 固定提交                                |
| --------------------- | -------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------- |
| 主要目标              | Agent/MCP + Runtime + CLI                    | CST 2026 CLI/Agent 工具链                | Windows 下直接 Python COM API                                 |
| Python                | MCP ≥3.12；Worker 3.9                       | README 指向现代 Python/CST 2026          | `setup.py` 为 Python ≥3.6                                  |
| CST 版本              | 重点兼容 2022，同时保留新版 API              | README 明示 CST 2026                     | 当前 README 支持 CST 2026；旧版本建议 v0.1.2                  |
| 进程模型              | 高低版本常驻 Worker，JSONL                   | 单进程 CLI/包，无 Worker                 | 调用进程直接 pywin32 COM                                      |
| Session               | core 集中管理并追踪工程身份                  | core session，面向 CLI                   | `CST_MicrowaveStudio` 构造时连接/打开，显式 save/close/quit |
| MCP                   | 低层 MCP Server + 动态描述                   | 无 MCP Server                            | 无 MCP                                                        |
| API 分层              | MCP/API/tools/workflows/lib/core，但仍有越层 | cli/tools/core 为主，无 lib/API registry | 大类直接包裹同一 MWS COM 对象                                 |
| VBA 生成              | core 为主，部分 lib 生成                     | 多数在 core，仍有分散入口                | 每个业务类内拼接 VBA                                          |
| History               | 中央`_add_vba_history` + Buffer            | 多处`add_to_history`                   | 各方法直接`MWS.AddToHistory`                                |
| 建模错误判断          | 当前只捕获 Python/COM 异常                   | 同样主要捕获异常                         | 检查`AddToHistory` 返回值是否为 True                        |
| `On Error`/临时文件 | 无                                           | 无                                       | 未发现                                                        |
| 执行后验证            | 保存、导出等少数路径有验证                   | 导出文件等少数路径有验证                 | 结果读取会检查树/COM 异常；建模基本无后置验证                 |
| 旧版参数读取          | 尚未完成                                     | 依赖新版实现                             | `DoesParameterExist`、`GetParameter*` 等旧 COM 方法       |
| 结果读取              | `cst.results` + GUI/VBA fallback           | `cst.results` + GUI/VBA                | 直接 Resulttree COM，捕获`com_error`                        |
| 测试策略              | 纯逻辑、架构、Worker 和真机脚本并存          | CLI/合约/真机参考工程                    | unittest 与真实 CST 工程；README 承认部分需人工观察           |
| 许可证                | MIT                                          | MIT                                      | MPL-2.0，复制源码需遵守文件级要求                             |

### 5.1 当前 Fork 相对上游的关键演化

- **[源码确认]** 上游固定提交的源码树没有 `mcp_server`、`worker.py`、`lib`、`api/registry.py` 或 `core/compatibility/`。
- **[源码确认]** 上游 `core/modeling.py` 除中央入口外仍有多处直接 `add_to_history`；当前 Fork 已显著集中化。
- **[源码确认]** 上游 `core/farfield.py` 已有即时 VBA/fallback 设计，当前 Fork 基本继承它并增加兼容层，但 fallback 的假成功也被继承。
- **[源码确认]** 当前 Fork 的 Worker/API/兼容层是实质性架构新增，不应为了追随上游或旧测试退回 Adapter 直连模式。

## 6. HERMES 错误处理调用链核验

### 6.1 建模函数的真实判断方式

以 Brick 为例，HERMES [`Shape.py:125-135`](https://src.koda.cnrs.fr/hermes/cst-python-api/-/blob/72b0e13f56a57749f640191abe2239a4e222a53b/cst_python_api/Shape.py#L125-135) 执行：

```python
result = self.__MWS.AddToHistory("define brick: " + name, vba)
if result != True:
    raise RuntimeError(...)
```

Boolean、Component、Material、Solver 和 Transform 也重复相同模式。例如 [`Boolean.py:66-75`](https://src.koda.cnrs.fr/hermes/cst-python-api/-/blob/72b0e13f56a57749f640191abe2239a4e222a53b/cst_python_api/Boolean.py#L66-75) 与 [`Component.py:49-58`](https://src.koda.cnrs.fr/hermes/cst-python-api/-/blob/72b0e13f56a57749f640191abe2239a4e222a53b/cst_python_api/Component.py#L49-58)。

结论：

- **[源码确认]** 文档中的“VBA 未成功执行时抛 RuntimeError”实际等价于“`AddToHistory` 返回值不是 True 时抛异常”。
- **[交接实测 + 合理推断]** 既然 CST 2022 对错误 VBA 仍可能返回 True，HERMES 这一判断在该版本同样可能静默失败。
- **[待真机验证]** 要最终确认，应在 CST 2022 上用 HERMES v0.1.2/当前版本分别测试不存在材料、`Err.Raise` 和语法错误；本轮按用户要求没有运行测试。

### 6.2 HERMES 中真正更可靠的部分

- **[源码确认]** 结果读取直接捕获 pywin32 `com_error` 并附带 CST 错误文本，例如 [`Results.py:146-192`](https://src.koda.cnrs.fr/hermes/cst-python-api/-/blob/72b0e13f56a57749f640191abe2239a4e222a53b/cst_python_api/Results.py#L146-192)。这比只检查布尔返回值更可靠，但只覆盖 COM 确实抛异常的查询。
- **[源码确认]** 参数 API 使用 `DoesParameterExist`、`StoreDoubleParameter`、`StoreParameter`、`GetParameter*` 等旧 COM 方法，见 [`Parameter.py`](https://src.koda.cnrs.fr/hermes/cst-python-api/-/blob/72b0e13f56a57749f640191abe2239a4e222a53b/cst_python_api/Parameter.py)。这为 CST 2022 参数 fallback 提供了明确方向。
- **[源码确认]** 会话使用 `CSTStudio.Application`、`Active3D`、`OpenFile/NewMWS`、`SaveAs/Quit`，见 [`CST_MicrowaveStudio.py`](https://src.koda.cnrs.fr/hermes/cst-python-api/-/blob/72b0e13f56a57749f640191abe2239a4e222a53b/cst_python_api/CST_MicrowaveStudio.py)。它适合参考旧 COM 能力，不适合整体替换当前双进程架构。

## 7. 可直接借鉴与不建议照搬

### 7.1 可借鉴，但应重新实现

1. HERMES 参数存在性和读取方法名，可作为 `compatibility/parameters.py` 的 CST 2022 fallback 候选。
2. HERMES Resulttree 的 `DoesTreeItemExist`、`GetResultIDsFromTreeItem`、`GetResultFromTreeItem` 调用，可作为旧版结果查询探针候选。
3. HERMES 对端口、几何范围、参数类型的发送前校验思路，可迁入统一 validation 层。
4. 当前 Fork 的 Proxy 超时后重启 Worker、请求 ID 校验和串行请求锁应保留。
5. 当前 Fork 的工程身份校验、脏参数标记、远场保存守卫和结果文件存在性验证应纳入新错误信封。

这里的“借鉴”是重新编写兼容当前架构的实现，不复制 HERMES 源文件。HERMES 使用 MPL-2.0；若直接复制或修改其源码，应单独进行许可证审查并保留相应声明。

### 7.2 不建议照搬

- 每个业务类自己拼 VBA、直接调用 `AddToHistory`。
- 把 `result == True` 当作执行成功。
- 在主 Python 进程直接使用 pywin32 COM，破坏 3.12/3.9 隔离。
- 将所有异常吞成 `False` 或空列表。
- 依赖版本字符串散布分支，或把 `hasattr` 当成完整能力证明。
- 把私有 `_GetHistory/_TryToUndoNTimes/_ResizeHistory` 直接接入生产路径。
- 为兼容旧文档或旧测试恢复已经删除的 Adapter。

## 8. 最小错误 Gateway 设计

### 8.1 放置位置与内部接口

建议新增内部模块 `core/execution.py`，由 `core/modeling._add_vba_history()` 独占调用。第一阶段不改变公开 `lib` 函数签名。

```python
def execute_history(
    project_path,
    history_name,
    vba_lines,
    project=None,
    verification=None,
    verification_level="basic",
    operation_id=None,
):
    """提交一个 History 块，并返回结构化执行结果。"""
```

该签名使用 Python 3.9 可接受的普通默认值；实现中的类型标注应继续避免 `X | None` 等 3.10+ 语法。

### 8.2 状态机

```mermaid
stateDiagram-v2
    [*] --> Validating
    Validating --> Rejected: 参数或能力不满足
    Validating --> Prepared: 创建 operation_id 与 PENDING 状态文件
    Prepared --> Submitted: COM 接受 History
    Prepared --> SubmissionFailed: COM 抛异常
    Submitted --> RuntimeFailed: 状态文件为 ERROR
    Submitted --> HostOrCompileFailed: 状态仍为 PENDING 或内容损坏
    Submitted --> ReportedOK: 状态文件为 OK
    ReportedOK --> Verified: 后置条件通过
    ReportedOK --> VerificationFailed: 后置条件失败
    VerificationFailed --> RollbackAttempted: 仅显式启用且能力已验证
    Verified --> [*]
```

### 8.3 状态文件方案

1. 使用 `uuid.uuid4().hex` 生成 `operation_id`，按项目规范化路径建立隔离命名；不得使用共享固定文件名。
2. Python 在提交前创建并关闭状态文件，初始内容为 `PENDING`。Windows 上必须先关闭句柄，CST/VBA 才能写入。
3. VBA 外层使用 `On Error GoTo`；成功写 `OK`，运行时错误写 `ERROR`、编号、来源、描述和行号，然后重新 `Err.Raise`，保留 CST Message Window 行为。
4. COM 返回后解析文件：`OK`、`ERROR`、仍为 `PENDING`、残缺/未知内容四类。`PENDING` 不能声称成功，应归类为 `vba_compile_or_host_error`。
5. 路径进入 VBA 前统一执行双引号转义；换行、非 ASCII 路径、UNC 路径和超长路径分别测试。
6. 正常与已确认失败路径在 `finally` 清理；Worker 崩溃留下的文件由启动时 janitor 按年龄清理，避免删除仍可能被 CST 写入的活跃文件。
7. Command Buffer 只在 `flush` 时包一次状态侧信道；单个阵列单元只记录在批次内，不创建独立文件。

### 8.4 统一错误信封

```json
{
  "ok": false,
  "status": "error",
  "error": {
    "type": "vba_runtime_error",
    "code": 1004,
    "message": "Material does not exist.",
    "source": "Brick.Create",
    "line": 120,
    "feature": "geometry.brick",
    "phase": "execution",
    "retryable": false,
    "next_action": "先创建材料或改用现有材料",
    "rollback": {"attempted": false, "status": "not_attempted"}
  },
  "context": {
    "project_path": "...",
    "history_label": "...",
    "operation_id": "...",
    "submission": "accepted",
    "execution": "reported_error",
    "verification": "not_run"
  }
}
```

稳定错误类型至少包括：`validation_error`、`unsupported_feature`、`transport_error`、`worker_error`、`cst_submission_error`、`vba_runtime_error`、`vba_compile_or_host_error`、`verification_failed`、`rollback_failed`、`runtime_error`。

### 8.5 后置验证等级

| 等级       | 行为                             | 建议用途                                        |
| ---------- | -------------------------------- | ----------------------------------------------- |
| `none`   | 只做提交和 VBA 状态解析          | 仅兼容或诊断场景，不对 Agent 默认开放           |
| `basic`  | 对高价值结果做一次廉价验证       | 默认：实体存在、文件非空、参数读回、solver 状态 |
| `strict` | 批次汇总、数量/属性/结果格式验证 | 高风险 Agent 写操作、发布前工作流               |

阵列构建应在整个 flush 后验证关键实体或数量，不能逐单元查询。保存工程已有 `file_mtime_verified`，但当前即使它为 `False` 仍返回 `status=success`；新 Gateway 应把验证失败提升为明确错误或至少 `verification=failed`。

## 9. 事务、History 与回滚判断

- **[源码确认]** 当前 Buffer 只保证“多段 VBA 合并为一个提交”，不提供数据库式原子性、隔离性或回滚。
- **[合理推断]** 一个 History 节点不等于一个事务；VBA 在中途失败前执行的命令可能已经改变模型。
- **[待真机验证]** `_TryToUndoNTimes(1)` 是否能完整撤销材料、实体、参数、监视器、边界和求解器设置，当前没有证据。
- **[源码确认]** 私有 History 方法只出现在参考文档和分析文档中，运行时代码尚未接入，这是正确的保守状态。

建议策略：

1. 第一阶段不自动 Undo，只报告 `rollback.not_attempted` 和工程状态“不确定”。
2. `_GetHistory` 先作为只读实验，用于保存前后快照和诊断证据，不能作为 VBA 成功的唯一判据。
3. `_TryToUndoNTimes` 只在复制的临时工程、单个明确 History 节点上验证；未覆盖全部对象类型前不进入默认路径。
4. `_ResizeHistory` 不接入 Runtime。
5. 删除结果、大批量几何变更和不可逆设置优先采用工程副本/保存点；不要以私有 Undo 代替备份。
6. Worker 超时后不得立即重放写请求。先重新连接并验证 `operation_id` 对应的后置状态，避免重复创建。

## 10. 分阶段修改计划与第一阶段文件/函数

### 阶段 0：只读实验与契约冻结

- 在临时工程验证 `PENDING/OK/ERROR` 状态侧信道、语法错误、`Err.Raise`、不存在材料和路径转义。
- 只读探测 `_GetHistory`；不调用 Undo/Resize。
- 冻结错误信封、验证等级和 operation_id 语义。

### 阶段 1：最小 Gateway（首个代码阶段）

建议只修改以下核心范围，保持公开 `lib` API 不变：

- `core/errors.py`：增加稳定错误类型、信封构造与内部异常到信封的映射。
- 新建 `core/execution.py`：VBA 包装、唯一状态文件、解析、清理和 operation_id。
- `core/modeling.py`：让 `_add_vba_history()` 与 `flush_batch()` 调用 Gateway；缓冲追加返回 `submission=buffered`。
- `core/buffer.py`：增加 peek/commit 或等价两阶段 flush，失败时不静默丢失批次。

### 阶段 2：兼容层和后置验证

- 用旧 COM 参数 API补齐 CST 2022 参数读取。
- 将 `lib` 中直接 `model3d/modeler` 访问迁入 core compatibility。
- 为实体、参数、保存、导出和仿真添加按等级执行的验证器。

### 阶段 3：跨进程错误一致化

- Registry、Worker、Proxy 和 MCP 统一传递错误信封。
- traceback 改为服务端诊断信息，客户端只收到稳定字段。
- transport timeout、worker crash 和 CST 执行错误使用不同 phase/type。

### 阶段 4：受控回滚研究

- 在工程副本上验证 History 快照和一次 Undo 的实际边界。
- 仅在证据充分时增加 opt-in rollback；默认仍以工程副本为高风险保护。

## 11. 需要新增或重写的测试设计

> 本报告只提出测试设计，本轮没有运行任何测试。

### 11.1 不启动 CST 的单元测试

- VBA 字符串、双引号、Windows/UNC/中文路径转义。
- 状态解析：`PENDING`、`OK`、完整 `ERROR`、残缺、未知、空文件。
- 唯一 operation_id、并发项目不串文件、正常/异常清理、陈旧文件 janitor。
- Fake modeler：COM 抛异常、返回 True 但文件为 ERROR、返回 True 但仍 PENDING、OK。
- Buffer：失败保留、成功删除、discard 幂等、空批次、同项目重复 begin、不同项目隔离。
- 错误信封 JSON 可序列化，所有层保持 `type/phase/context`。
- Fake RemoteObject：`hasattr=True` 但调用失败时能回退或返回明确 unsupported。
- `False`、空列表与查询错误不再混淆。

### 11.2 Worker/MCP 合约测试

- 业务错误、Worker 内部错误、JSON 错误、响应 ID 不匹配、超时和进程退出分别映射。
- MCP 返回不包含本机 traceback 和敏感绝对路径。
- 动态工具清单只发现白名单模块，并与版本化清单一致。
- 写请求超时后不会自动重放；重连后要求状态核验。

### 11.3 CST 2022 手工集成矩阵

1. 正常 Brick。
2. 不存在材料。
3. 显式 `Err.Raise`。
4. 非法对象运行时错误。
5. VBA 语法/编译错误。
6. 一个批次中前半成功、后半失败。
7. 参数写入并读回。
8. solver 正常结束、启动失败、查询失败。
9. `_GetHistory` 前后快照。
10. 在工程副本上验证一次 Undo；记录实体树、参数、History、材料和监视器差异。

### 11.4 已知测试状态更正

交接材料提到 `tests/test_mcp_server.py` 仍依赖 `TOOL_SPECS`。当前源码 `tests/test_mcp_server.py:20-31` 已改为通过 Proxy 读取 Runtime 工具清单，`42-57` 也验证 MCP 不直接导入 Runtime；因此该历史问题已经解决，不应恢复旧 Adapter。后续需要改的是错误信封和 Gateway 合约，而不是工具注册架构。

## 12. 建议的独立 Commit 列表

1. `文档(review): 固化 CST 2022 错误模型与实验矩阵`
2. `重构(errors): 定义跨层结构化错误信封`
3. `功能(execution): 增加批次级 VBA 状态侧信道`
4. `修复(buffer): 提交成功后再释放命令缓冲区`
5. `功能(verification): 增加建模与参数基础后置验证`
6. `修复(compat): 补齐 CST 2022 参数与树查询 fallback`
7. `重构(lib): 移除公开 API 层直接 COM 访问`
8. `修复(transport): 区分 Worker、超时与 CST 执行错误`
9. `测试(runtime): 覆盖 Gateway、Buffer 与错误信封`
10. `测试(cst2022): 记录真机错误和 History 行为`
11. `文档(repo): 统一版本、仓库地址、工具数量与安装说明`

每个提交应控制在单一主题，避免一次大规模删除或重写。私有 Undo 实验与正式接入必须分成不同提交，且正式接入要以真机证据为前置条件。

## 13. 文档与发布一致性整改清单

| 项目            | 当前冲突                                                             | 建议唯一事实源                                 |
| --------------- | -------------------------------------------------------------------- | ---------------------------------------------- |
| 仓库地址        | `bbl21/cst-mcp`、`anomalyco/cst-runtime-cli`、`phy233/CST_MCP` | 根 pyproject 指向当前 Fork；上游单列           |
| MCP 实现        | INSTALL 写 FastMCP，源码是低层`mcp.server.Server`                  | `mcp_server/server.py`                       |
| Worker 启动     | INSTALL 写`conda run ... cst_worker.py`                            | `config.py` + `proxy.py` 的解释器路径      |
| Worker 模块     | INSTALL 写独立脚本                                                   | `python -m cst_runtime.worker`               |
| 工具数量        | 20、113、114、117 四种                                               | 生成并版本化工具清单；文档避免硬编码或自动同步 |
| CST/Python 版本 | README 与 INSTALL 冲突                                               | 根 pyproject + runtime pyproject +兼容矩阵     |
| 工具注册        | 交接称静态，当前是白名单模块动态发现                                 | `api/atomic.py` + registry                   |
| Adapter         | 旧计划仍描述已删除实现                                               | 标记历史设计或移入 archive                     |

当前工作树还包含用户未提交的文档修改、三个删除文件和新增 `skills/cst-mcp/`。这些内容不属于本报告的代码缺陷修复，本轮没有改动、恢复、暂存或删除它们。后续提交本报告时应单独暂存本文件，避免把其他未提交内容意外混入。

## 14. 最终优先级

1. 先验证并实现最小错误 Gateway。
2. 修复 Buffer 的提交前弹出和假成功语义。
3. 补齐 CST 2022 参数/树/结果兼容层，消除 `lib` 直接 COM。
4. 统一 Worker、Proxy、MCP 的错误信封。
5. 再研究 `_GetHistory` 和 opt-in Undo。
6. 最后处理工具扩展、详细日志和更高层 Agent Workflow。

在 1–4 完成前，不建议扩大原始 VBA 工具的使用范围，也不建议把更多新功能建立在当前 `status=success` 语义之上。
