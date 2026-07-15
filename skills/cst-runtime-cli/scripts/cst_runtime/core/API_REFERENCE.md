# CST Runtime — Core API Reference

> **Auto-generated from source code** · `cst_runtime.core` · Last updated: 2026-07-15
>
> 本文档基于 `core/` 目录下全部 22 个模块的源码分析生成，不包含任何猜测内容。

---

## 目录

- [架构概览](#架构概览)
- [调用关系图](#调用关系图)
- [稳定性标注说明](#稳定性标注说明)
- [模块 API 详解](#模块-api-详解)
  - [errors.py — 标准响应构造](#errspy--标准响应构造)
  - [gateway.py — 安全守卫层](#gatewaypy--安全守卫层)
  - [identity.py — 项目身份识别](#identitypy--项目身份识别)
  - [session.py — 会话生命周期](#sessionpy--会话生命周期)
  - [project.py — 项目操作](#projectpy--项目操作)
  - [project_info.py — 离线元数据读取](#project_infopy--离线元数据读取)
  - [process.py — 进程管理](#processpy--进程管理)
  - [workspace.py — 工作区管理](#workspacepy--工作区管理)
  - [modeling.py — 建模操作](#modelingpy--建模操作)
  - [simulation.py — 仿真控制](#simulationpy--仿真控制)
  - [results.py — 结果提取](#resultspy--结果提取)
  - [farfield.py — 远场分析](#farfieldpy--远场分析)
  - [optimizer.py — Optuna 优化引擎](#optimizerpy--optuna-优化引擎)
  - [objective.py — 目标函数评估](#objectivepy--目标函数评估)
  - [doe.py — 实验设计](#doepy--实验设计)
  - [environment.py — 环境探测与配置](#environmentpy--环境探测与配置)
  - [compat.py — 版本兼容层](#compatpy--版本兼容层)
  - [proxy.py — 子进程 IPC 代理](#proxypy--子进程-ipc-代理)
  - [audit.py — 审计与运行记录](#auditpy--审计与运行记录)
  - [evidence.py — 证据快照](#evidencepy--证据快照)
  - [utils.py — 通用工具函数](#utilspy--通用工具函数)
  - [\_\_init\_\_.py — CST 路径自动探测](#__init__py--cst-路径自动探测)
- [跨模块依赖矩阵](#跨模块依赖矩阵)

---

## 架构概览

`core/` 是 CST Runtime 的 **引擎层**，采用 **纯函数式架构**（无 OOP 状态管理类）。
所有函数返回 `dict[str, Any]`，遵循统一的 `{"status": "success"|"error", ...}` 响应格式。

```
cst_runtime/
├── core/          ← 引擎层（本文档）：业务逻辑、COM 调用、安全守卫
├── lib/           ← 公开 API 门面层：对 core/ 的用户友好封装
└── tools/         ← 接口/模式层：MCP 工具定义（声明式 JSON schema）
```

---

## 调用关系图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        tools/ (接口层)                              │
│  声明式 TOOL_DEFS 字典 + handler 映射                                │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│  │simulation│ modeling │ project  │ results  │ farfield │ ...      │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘          │
│       │          │          │          │          │                 │
│       ▼          ▼          ▼          ▼          ▼                 │
│   core.simulation core.modeling core.project core.results core.ff  │
│   (仅 optimization.py, doe.py 直接 import core)                    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        lib/ (公开 API 门面层)                       │
│  每个模块是 core/ 函数的用户友好封装                                  │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│  │ session  │parameters│ geometry │ solver   │ results  │ ...      │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┘          │
│       │          │          │          │          │                 │
│       ▼          ▼          ▼          ▼          ▼                 │
│   core.session core.project core.modeling core.simulation core.res │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        core/ (引擎层)                               │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ gateway.py  ← 所有 COM 操作的安全守卫入口                      │   │
│  │ identity.py ← 项目身份识别 / DE 进程绑定                      │   │
│  │ session.py  ← 会话生命周期 (open/close/quit)                  │   │
│  │ project.py  ← 参数 / 实体 / 保存                              │   │
│  │ process.py  ← 进程发现 / 清理                                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ modeling.py  ← 几何建模 / 材料 / 端口 / 网格                   │   │
│  │ simulation.py ← 仿真启动 / 停止 / 求解器配置                   │   │
│  │ results.py   ← 1D/2D 结果提取 / 导出                         │   │
│  │ farfield.py  ← 远场数据导出 / 方向图                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ optimizer.py ← Optuna 优化 (create/ask/tell)                  │   │
│  │ objective.py ← 目标函数评估 (S11/增益/带宽)                    │   │
│  │ doe.py       ← 实验设计 (DOE)                                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ environment.py ← CST 安装探测 / 环境配置                       │   │
│  │ workspace.py   ← 工作区初始化 / 任务管理 / 运行目录            │   │
│  │ compat.py      ← CST 2022/2026 版本兼容                      │   │
│  │ proxy.py       ← 子进程 IPC (conda cst39)                     │   │
│  │ audit.py       ← 运行阶段记录                                 │   │
│  │ evidence.py    ← 项目状态快照 / 对比                           │   │
│  │ utils.py       ← 通用工具                                     │   │
│  │ errors.py      ← 标准响应格式                                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**依赖方向:**

```
tools/ ──────→ core/ ←────── lib/
                 │
    （tools/ 和 lib/ 是平行兄弟层，互不依赖）
```

- `lib/` → `core/`：系统性依赖（门面封装）
- `tools/` → `core/`：部分依赖（仅 `optimization.py`, `doe.py` 直接 import core）
- `core/` 内部各模块之间有细粒度依赖（见 [跨模块依赖矩阵](#跨模块依赖矩阵)）

---

## 稳定性标注说明

| 标记 | 含义 |
|------|------|
| 🟢 **稳定** | 公开 API，由 `lib/` 门面层封装，适合外部调用 |
| 🟡 **内部稳定** | 核心内部模块间调用的稳定接口，API 签名较固定 |
| 🔴 **内部实现** | 内部实现细节，不建议直接调用，可能随版本变更 |

---

## 模块 API 详解

---

### errors.py — 标准响应构造

> **模块**: `cst_runtime.core.errors`
> **依赖**: 无（仅 `typing`）
> **稳定性**: 🟢 稳定

所有 `core/` 模块的标准返回格式构造器。

#### `error_response` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `error_response(error_type: str, message: str, **extra: Any) -> dict[str, Any]` |
| **参数** | `error_type` — 错误类型标识符 (如 `"project_not_found"`) |
| | `message` — 人类可读的错误描述 |
| | `**extra` — 任意附加键值对，合并到返回字典 |
| **返回值** | `{"status": "error", "error_type": ..., "message": ..., **extra}` |
| **功能** | 构造标准化错误响应字典 |

```python
from cst_runtime.core.errors import error_response

result = error_response(
    "project_not_found",
    "Cannot find project file",
    project_path="C:/models/test.cst"
)
# => {"status": "error", "error_type": "project_not_found",
#     "message": "Cannot find project file", "project_path": "C:/models/test.cst"}
```

#### `success_response` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `success_response(**payload: Any) -> dict[str, Any]` |
| **参数** | `**payload` — 任意键值对作为响应负载 |
| **返回值** | `{"status": "success", **payload}` |
| **功能** | 构造标准化成功响应字典 |

```python
from cst_runtime.core.errors import success_response

result = success_response(project_path="C:/models/test.cst", saved=True)
# => {"status": "success", "project_path": "C:/models/test.cst", "saved": True}
```

---

### gateway.py — 安全守卫层

> **模块**: `cst_runtime.core.gateway`
> **依赖**: `core.errors`
> **稳定性**: 🟡 内部稳定（`lib/` 层不直接暴露，但被 `core/` 内广泛使用）

所有 COM 操作必须经过 gateway 守卫。维护每个已打开项目的轻量状态注册表，强制执行 CST 特定的安全规则。

#### Public Classes

##### `CstTrapError(Exception)` 🟡

| 项 | 说明 |
|---|---|
| **构造器** | `__init__(self, trap_name: str, message: str, suggestion: str = "")` |
| **属性** | `trap_name: str` — 陷阱名称标识 |
| | `suggestion: str` — 解决建议 |
| **功能** | CST 特定的运行时陷阱异常 |

```python
raise CstTrapError("T2", "Parameters dirty", suggestion="Run rebuild first")
```

##### `ProjectState` (dataclass) 🔴

| 项 | 说明 |
|---|---|
| **字段** | `path: str` — 项目路径 |
| | `session_type: str = "unknown"` — `"modeler"` \| `"results"` |
| | `stage: str = "clean"` — `"clean"` \| `"params_dirty"` \| `"farfield_exported"` \| `"closed"` |
| | `params_changed: list[str] = None` — 本会话中已更改的参数名列表 |
| **功能** | 每项目状态注册条目，跟踪会话类型和阶段 |

> ⚠️ **内部实现**：此数据类由 gateway 内部使用，不建议外部直接实例化。

#### Public Functions

##### `validate_project_path` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `validate_project_path(project_path: str) -> str` |
| **参数** | `project_path` — 项目文件路径 |
| **返回值** | 规范化后的路径字符串 |
| **异常** | `ValueError` — 路径不以 `.cst` 或 `.prj` 结尾时 |
| **功能** | [T10] 验证项目路径指向 `.cst` / `.prj` 文件 |

##### `on_session_open` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `on_session_open(project_path: str, session_type: str) -> None` |
| **功能** | [T5/T9/T12] 在注册表中注册新会话。若已有活跃会话则发出警告。清除 dirty 标记 |

##### `on_session_close` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `on_session_close(project_path: str) -> None` |
| **功能** | 从注册表移除项目状态，清除磁盘上的 dirty 标记 |

##### `guard_cross_session` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `guard_cross_session(project_path: str, expected_type: str) -> dict[str, Any] | None` |
| **返回值** | 冲突时返回 `error_response`；安全时返回 `None` |
| **功能** | [T5] 检测会话类型冲突（如 modeler 和 results 同时打开） |

##### `mark_params_dirty` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `mark_params_dirty(project_path: str, param_name: str = "", param_value: Any = None) -> None` |
| **功能** | [T2] 标记项目阶段为 `"params_dirty"`，写入 `.cst_params_dirty` 磁盘标记文件 |

##### `guard_before_simulation` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `guard_before_simulation(project_path: str) -> dict[str, Any] | None` |
| **返回值** | 参数已更改但未重建模型时返回 `error_response`；安全时返回 `None` |
| **功能** | [T2] 仿真前安全检查：确保已更改的参数被重建 |

##### `clear_dirty` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `clear_dirty(project_path: str) -> None` |
| **功能** | 将阶段从 `"params_dirty"` 重置为 `"clean"` |

##### `mark_farfield_exported` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `mark_farfield_exported(project_path: str) -> None` |
| **功能** | 远场导出后标记阶段为 `"farfield_exported"`。阻止后续保存操作以防项目损坏 |

##### `guard_before_close_save` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `guard_before_close_save(project_path: str, requested_save: bool) -> tuple[bool, str]` |
| **返回值** | `(actual_save, warning_message)` |
| **功能** | [T3] 若远场已导出，强制 `save=False` 以防止项目损坏 |

##### `compute_db` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `compute_db(ydata: list[dict[str, float]]) -> list[float]` |
| **参数** | `ydata` — 复数 S 参数 y 数据列表，每项为 `{"real": float, "imag": float}` |
| **返回值** | dB 值列表 |
| **功能** | [T4] 将复数 S 参数转换为 dB 值 (`20*log10(|z|)`) |

```python
from cst_runtime.core.gateway import compute_db

db_values = compute_db([{"real": 0.1, "imag": -0.05}])
```

##### `guard_farfield_quantity` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `guard_farfield_quantity(quantity: str) -> dict[str, Any] | None` |
| **功能** | [T8] 验证远场量类型。有效值：`"Realized Gain"`, `"Gain"`, `"Directivity"` |

##### `annotate_change_param_result` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `annotate_change_param_result(result: dict[str, Any], project_path: str = "", param_name: str = "") -> dict[str, Any]` |
| **功能** | [T13] 为参数更改结果添加警告注释（模型几何未重新生成） |

##### `guard_result_filter` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `guard_result_filter(filter_type: str) -> dict[str, Any] | None` |
| **功能** | [T14] 验证结果过滤类型。有效值：`"0D/1D"`, `"colormap"`, `"all"` |

##### `guard_close_save_order` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `guard_close_save_order(project: Any, save: bool) -> None` |
| **功能** | [T15] 确保保存操作在关闭之前执行 |

---

### identity.py — 项目身份识别

> **模块**: `cst_runtime.core.identity`
> **依赖**: `core.errors`
> **稳定性**: 🟡 内部稳定

负责项目路径规范化、DE（Design Environment）进程发现与绑定。

#### `normalize_project_path` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `normalize_project_path(path: str) -> str` |
| **返回值** | 规范化的绝对路径（大小写规范化） |
| **功能** | 对项目路径进行 `normcase + abspath + expanduser` 处理 |

```python
from cst_runtime.core.identity import normalize_project_path

path = normalize_project_path("~/models/Test.cst")
# => "c:\\users\\username\\models\\test.cst"
```

#### `project_path_from_args` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `project_path_from_args(args: dict[str, Any]) -> str` |
| **参数** | `args` — 依次检查键 `project_path`, `fullpath`, `working_project` |
| **返回值** | 项目路径字符串 |
| **异常** | `ValueError` — 所有键都不存在时 |
| **功能** | 从参数字典中提取项目路径 |

#### `infer_run_dir_from_project` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `infer_run_dir_from_project(project_path: str) -> Path | None` |
| **功能** | 若项目位于 `projects/` 子目录内，推断并返回运行目录（祖父目录） |

#### `find_lock_files` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `find_lock_files(project_path: str) -> list[Path]` |
| **返回值** | 排序后的 `.lok` 锁文件路径列表 |
| **功能** | 递归搜索项目伴生目录中的锁文件 |

#### `wait_project_unlocked` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `wait_project_unlocked(project_path: str, timeout_seconds: float = 10.0, poll_interval_seconds: float = 0.5) -> dict[str, Any]` |
| **返回值** | 成功时包含 `waited_seconds`；超时时包含 `lock_files` 列表 |
| **功能** | 轮询等待锁文件清除，直到超时 |

#### `list_open_projects` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `list_open_projects() -> dict[str, Any]` |
| **返回值** | `{"status": "success", "open_projects": [...], "count": N, "design_environment_count": N, "failures": [...]}` |
| **功能** | 连接所有运行中的 CST DE，列出所有已打开的项目 |

```python
from cst_runtime.core.identity import list_open_projects

result = list_open_projects()
for p in result["open_projects"]:
    print(p)
```

#### `attach_expected_project` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `attach_expected_project(project_path: str) -> tuple[Any | None, dict[str, Any]]` |
| **返回值** | `(project_object, status_dict)` — 失败时 project 为 `None` |
| **功能** | 在所有运行中的 DE 中搜索匹配的项目，确保其为活跃项目。返回 COM 项目对象和状态信息 |

#### `verify_project_identity` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `verify_project_identity(project_path: str) -> dict[str, Any]` |
| **功能** | `attach_expected_project` 的薄封装，仅返回状态字典 |

---

### session.py — 会话生命周期

> **模块**: `cst_runtime.core.session`
> **依赖**: `core.gateway`, `core.process`, `core.identity`, `core.errors`, `core.utils`
> **稳定性**: 🟢 稳定

管理 CST 项目的打开、关闭、退出等会话操作。

#### 模块级状态

- `_OPENED_PROJECTS: dict[str, Any]` — 已打开项目的内存缓存（按规范化路径索引）

#### `get_attached_project` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `get_attached_project(project_path: str) -> dict[str, Any] | None` |
| **功能** | 从内存缓存中查找已打开的项目对象 |

#### `inspect` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `inspect(project_path: str = "") -> dict[str, Any]` |
| **功能** | 委托给 `process.inspect_cst_environment()` 获取诊断信息 |

```python
from cst_runtime.core.session import inspect

status = inspect("C:/models/antenna.cst")
print(status["readiness"])  # "clear" | "blocked" | "attention_required"
```

#### `create_blank_project` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `create_blank_project(project_path: str) -> dict[str, Any]` |
| **参数** | `project_path` — 新项目的文件路径 |
| **返回值** | `{"status": "success", "project_path": ..., "session_action": "create"}` |
| **功能** | 在指定路径创建一个新的空白 CST MWS 项目。若文件已存在则返回错误 |

```python
from cst_runtime.core.session import create_blank_project

result = create_blank_project("C:/models/new_antenna.cst")
```

#### `open_project` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `open_project(project_path: str) -> dict[str, Any]` |
| **返回值** | `{"status": "success", "already_open": bool, "session_action": "open", "post_inspect": {...}}` |
| **功能** | 打开已有 CST 项目。检查文件存在性，尝试绑定到已运行的 DE，否则通过新 DE 打开。缓存到 `_OPENED_PROJECTS` |

```python
from cst_runtime.core.session import open_project

result = open_project("C:/models/antenna.cst")
if result["status"] == "success":
    print("Project opened successfully")
```

#### `reattach_project` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `reattach_project(project_path: str) -> dict[str, Any]` |
| **功能** | 验证项目身份并重新附加，返回 `session_action: "reattach"` |

#### `close_project` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `close_project(project_path: str, save: bool = False, wait_unlock: bool = True, timeout_seconds: float = 30.0, poll_interval_seconds: float = 0.5, kill_processes: bool = True) -> dict[str, Any]` |
| **返回值** | 包含 `close_result`, `unlock_result`, `kill_result`, `orphan_result`, `post_inspect` 的复合字典 |
| **功能** | 安全关闭运行中的 CST 项目。可选保存（受 gateway T3 远场导出陷阱保护），等待锁文件清除，终止 DE 进程，清理孤儿进程 |

```python
from cst_runtime.core.session import close_project

result = close_project("C:/models/antenna.cst", save=True)
```

#### `quit_cst` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `quit_cst(project_path: str = "", dry_run: bool = False, settle_seconds: float = 0.5) -> dict[str, Any]` |
| **返回值** | `{"status": ..., "session_action": "quit", "pre_inspect": {...}, "cleanup_result": {...}, "post_inspect": {...}}` |
| **功能** | 完全退出 CST 应用程序，清理所有后台子进程 |

---

### project.py — 项目操作

> **模块**: `cst_runtime.core.project`
> **依赖**: `core.errors`, `core.gateway`, `core.identity`, `core.utils`
> **稳定性**: 🟢 稳定

项目级操作：保存、参数管理、实体列举。

#### `save_project` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `save_project(project_path: str) -> dict[str, Any]` |
| **返回值** | `{"status": "success", "project_path": ..., "file_mtime_verified": bool}` |
| **功能** | 保存项目并验证文件修改时间是否更新（轮询最多 1s） |

```python
from cst_runtime.core.project import save_project

result = save_project("C:/models/antenna.cst")
print(result["file_mtime_verified"])  # True
```

#### `list_parameters` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `list_parameters(project_path: str) -> dict[str, Any]` |
| **返回值** | `{"status": "success", "parameters": {name: {value, description, category}}, "count": N}` |
| **功能** | 读取 CST 模型的所有设计参数。自动推断参数类别（geometry/material/solver/mesh/frequency） |

```python
from cst_runtime.core.project import list_parameters

result = list_parameters("C:/models/antenna.cst")
for name, info in result["parameters"].items():
    print(f"{name} = {info['value']} ({info['category']})")
```

#### `list_entities` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `list_entities(project_path: str, component: str = "") -> dict[str, Any]` |
| **参数** | `component` — 可选的组件名过滤器 |
| **返回值** | `{"status": "success", "entities": [{component, name}], "count": N, "tree_paths": [...]}` |
| **功能** | 列出 CST 3D 模型中的所有实体（固体） |

#### `change_parameter` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `change_parameter(project_path: str, name: str = "", value: float | int | str | None = None, **aliases: Any) -> dict[str, Any]` |
| **参数** | `name` / `parameter` / `para_name` — 参数名（支持别名） |
| | `value` — 新值 |
| **返回值** | `{"status": "success", "changed": {name: value}}` |
| **功能** | 通过注入 `StoreDoubleParameter` VBA 命令更改单个参数。通知 gateway 标记 dirty |

```python
from cst_runtime.core.project import change_parameter

result = change_parameter("C:/models/antenna.cst", name="patch_length", value=15.5)
```

#### `define_parameters` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `define_parameters(project_path: str, names: list[str], values: list[str]) -> dict[str, Any]` |
| **功能** | 批量定义多个参数。`names` 和 `values` 长度必须一致 |

---

### project_info.py — 离线元数据读取

> **模块**: `cst_runtime.core.project_info`
> **依赖**: `core.errors`, `core.utils`
> **稳定性**: 🟢 稳定

无需启动 DE 进程即可读取 `.cst` 文件的元数据。

#### `read_project_info` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `read_project_info(project_path: str) -> dict[str, Any]` |
| **返回值** | `{"status": "success", "entities": [...], "entities_count": N, "solver_name": str, "min_frequency": ..., "max_frequency": ..., "frequency_unit": str, "cst_version": str}` |
| **功能** | 使用 C 扩展 `_cst_interface.cst_project_info_reader` 离线读取项目元数据 |

```python
from cst_runtime.core.project_info import read_project_info

info = read_project_info("C:/models/antenna.cst")
print(f"Solver: {info['solver_name']}, Freq: {info['min_frequency']}-{info['max_frequency']} {info['frequency_unit']}")
```

---

### process.py — 进程管理

> **模块**: `cst_runtime.core.process`
> **依赖**: `core.identity`, `core.workspace`, `core.errors`
> **稳定性**: 🟡 内部稳定

CST 进程的发现、诊断和清理。

#### 模块级常量

- `CST_FORCE_KILL_PROCESS_ALLOWLIST: list[str]` — 允许强制终止的 CST 进程名列表。从 `cst_process_allowlist.json` 加载，默认值：`["cstd", "CST DESIGN ENVIRONMENT_AMD64", "CSTDCMainController_AMD64", "CSTDCSolverServer_AMD64"]`

#### `stop_process` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `stop_process(pid: int, name: str) -> dict[str, Any]` |
| **功能** | 通过 PowerShell `Stop-Process -Force` 终止单个进程 |

#### `cleanup_orphan_processes` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `cleanup_orphan_processes(settle_seconds: float = 0.5) -> dict[str, Any]` |
| **返回值** | `{"status": "success", "orphan_found": N, "orphan_killed": N, "killed": [...]}` |
| **功能** | 发现并终止所有没有打开项目的孤儿 CST DE 进程 |

#### `inspect_cst_environment` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `inspect_cst_environment(project_path: str = "") -> dict[str, Any]` |
| **返回值** | `{"status": "success", "readiness": "clear"|"blocked"|"attention_required", "processes": [...], "lock_files": [...], "open_projects_status": {...}, "project_identity_status": {...}, "safe_to_copy_or_reopen": bool, "cleanup_required": bool, "next_steps": [...]}` |
| **功能** | 完整诊断快照：CST 进程、锁文件、已打开项目、项目身份验证 |

```python
from cst_runtime.core.process import inspect_cst_environment

diag = inspect_cst_environment("C:/models/antenna.cst")
if diag["readiness"] == "clear":
    print("Environment is ready")
```

#### `cleanup_cst_processes` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `cleanup_cst_processes(project_path: str = "", dry_run: bool = False, settle_seconds: float = 0.5) -> dict[str, Any]` |
| **功能** | 终止所有白名单内的 CST 进程，验证锁文件已清除 |

---

### workspace.py — 工作区管理

> **模块**: `cst_runtime.core.workspace`
> **依赖**: `core.errors`
> **稳定性**: 🟢 稳定（工作区和任务管理部分）/ 🔴 内部（工具函数）

工作区初始化、任务/运行管理、文件操作。

#### 模块级常量

```python
WORKSPACE_META_DIR = ".cst_runtime"
WORKSPACE_META_FILE = "workspace.json"
WORKSPACE_SCHEMA_VERSION = 1
```

#### `now_iso` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `now_iso() -> str` |
| **功能** | 返回当前时间的 ISO 8601 字符串（含时区） |

#### `skill_root` / `scripts_root` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `skill_root() -> Path` / `scripts_root() -> Path` |
| **功能** | 返回技能根目录 / 脚本根目录（基于文件相对路径推断） |

#### `find_workspace_marker` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `find_workspace_marker(start: Path | None = None) -> Path | None` |
| **功能** | 从 `start` 向上遍历目录树查找 `.cst_runtime/workspace.json` 标记文件 |

#### `resolve_workspace_root` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `resolve_workspace_root(explicit_workspace: str = "") -> tuple[Path, str, bool]` |
| **返回值** | `(root_path, source_string, is_initialized)` |
| **功能** | 按优先级解析工作区根目录：(1) 显式参数 → (2) `CST_WORKSPACE` 环境变量 → (3) 祖先标记搜索 → (4) cwd 回退 |

#### `workspace_status` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `workspace_status(explicit_workspace: str = "") -> dict[str, Any]` |
| **功能** | 返回工作区状态描述（根路径、来源、是否已初始化、子目录存在性） |

#### `init_workspace` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `init_workspace(workspace: str = "") -> dict[str, Any]` |
| **返回值** | `{"status": "success", "workspace_root": ..., "already_initialized": bool}` |
| **功能** | 初始化工作区：创建 `tasks/`, `refs/`, `docs/`, `.cst_runtime/workspace.json`，可选生成 `pyproject.toml` 模板。幂等操作 |

```python
from cst_runtime.core.workspace import init_workspace

result = init_workspace("C:/projects/my_antenna")
```

#### `safe_task_id` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `safe_task_id(task_id: str) -> str` |
| **功能** | 验证任务 ID 格式（仅允许 `[a-zA-Z0-9_-]`），非法时抛出 `ValueError` |

#### `init_task` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `init_task(*, workspace: str = "", task_id: str, source_project: str, goal: str = "", title: str = "", force: bool = False) -> dict[str, Any]` |
| **返回值** | `{"status": "success", "task_id": ..., "task_path": ..., "source_project": ...}` |
| **功能** | 创建新任务目录 `tasks/<task_id>/`，含 `task.json` 清单和 `runs/` 子目录 |

#### `prepare_new_run` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `prepare_new_run(task_path: str, source_project: str = "", goal: str = "", target_metric: str = "", objective: str = "", frequency_start_ghz: float | None = None, frequency_end_ghz: float | None = None, allow_interactive: bool = True, save_project_after_simulation: bool = True) -> dict[str, Any]` |
| **返回值** | `{"status": "success", "run_id": ..., "working_project": ...}` |
| **功能** | 创建完整的运行工作空间：`run_NNN/` 含 `projects/`, `exports/`, `logs/`, `stages/`, `analysis/` 子目录，复制源项目为 `working.cst` |

#### `get_run_context` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `get_run_context(task_path: str, run_id: str = "") -> dict[str, Any]` |
| **返回值** | `{"status": "success", "run_id": ..., "config": {...}, "run_status": {...}}` |
| **功能** | 加载并返回现有运行的完整上下文 |

#### `load_json_file` / `write_json_file` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `load_json_file(file_path: Path) -> dict[str, Any]` |
| | `write_json_file(file_path: Path, payload: dict[str, Any]) -> None` |
| **功能** | JSON 文件读写工具 |

#### `find_next_run_index` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `find_next_run_index(runs_dir: Path) -> int` |
| **功能** | 扫描 `run_NNN` 目录返回下一个索引值 |

#### `resolve_run_dir` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `resolve_run_dir(task_path: str, run_id: str = "") -> tuple[Path, str, Path]` |
| **返回值** | `(task_dir, resolved_run_id, run_dir)` |
| **功能** | 从任务路径和可选 run_id 解析运行目录 |

#### `copy_project_artifacts` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `copy_project_artifacts(source_project: Path, working_project: Path) -> Path | None` |
| **功能** | 复制 `.cst`/`.prj` 文件及其伴生目录。若源文件有 `.lok` 锁文件则抛出 `RuntimeError` |

#### `render_initial_summary` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `render_initial_summary(*, task_id, run_id, created_at, goal, target_metric, objective, frequency_start_ghz, frequency_end_ghz, source_project, working_project) -> str` |
| **功能** | 渲染新运行的 Markdown 摘要文档 |

#### `marker_path` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `marker_path(workspace_root: Path) -> Path` |
| **功能** | 返回 `workspace_root / ".cst_runtime" / "workspace.json"` |

---

### modeling.py — 建模操作

> **模块**: `cst_runtime.core.modeling`
> **依赖**: `core.errors`, `core.identity`, `core.utils`, `core.session`（懒加载）
> **稳定性**: 🟢 稳定
> **说明**: 所有建模函数通过 VBA 历史列表操作 CST 模型。所有函数均返回 `dict[str, Any]`。

#### 模块级常量

```python
_BUILTIN_MATERIALS = frozenset({
    "PEC", "Vacuum", "Copper", "Gold", "Aluminum", "Brass", "Bronze",
    "Silver", "Steel", "Nickel", "Iron", "Tin", "Zinc", "Lead",
})
```

#### 几何基元

##### `define_brick` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `define_brick(project_path: str, name: str, component: str, material: str, x_min: float|str, x_max: float|str, y_min: float|str, y_max: float|str, z_min: float|str, z_max: float|str) -> dict[str, Any]` |
| **功能** | 通过 VBA 历史创建长方体固体 |

```python
from cst_runtime.core.modeling import define_brick

result = define_brick(
    "C:/models/antenna.cst",
    name="substrate", component="component1", material="FR4",
    x_min=-30, x_max=30, y_min=-30, y_max=30, z_min=0, z_max=1.6
)
```

##### `define_cylinder` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `define_cylinder(project_path, name, component, material, outer_radius, inner_radius, axis, range_min=None, range_max=None, z_min=None, z_max=None, center1=0.0, center2=0.0, x_center=None, y_center=None, segments=0) -> dict` |
| **功能** | 创建圆柱体。支持轴向参数别名（`z_min`/`z_max` → `range_min`/`range_max`） |

##### `define_cone` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `define_cone(project_path, name, component, material, bottom_radius, top_radius, axis, range_min=None, range_max=None, z_min=None, z_max=None, center1=0.0, center2=0.0, x_center=None, y_center=None, segments=0) -> dict` |
| **功能** | 创建圆锥/截锥体 |

##### `define_rectangle` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `define_rectangle(project_path, name, curve, x_min, x_max, y_min, y_max) -> dict` |
| **功能** | 创建 2D 矩形曲线 |

##### `define_polygon_3d` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `define_polygon_3d(project_path, name, curve, points: list[list]) -> dict` |
| **功能** | 从 `[x,y,z]` 点列表创建 3D 多边形曲线 |

##### `define_analytical_curve` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `define_analytical_curve(project_path, name, curve, law_x, law_y, law_z, param_start, param_end) -> dict` |
| **功能** | 从 X/Y/Z 参数方程创建分析曲线 |

#### 拉伸与扫掠

##### `define_extrude_curve` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `define_extrude_curve(project_path, name, component, material, curve, thickness, twist_angle=0.0, taper_angle=0.0, delete_profile=True) -> dict` |
| **功能** | 将曲线轮廓拉伸为固体 |

##### `create_loft_sweep` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `create_loft_sweep(project_path, name, component, material, x_min1, x_max1, y_min1, y_max1, z1, x_min2, x_max2, y_min2, y_max2, z2, tangency=0, minimize_twist=True) -> dict` |
| **功能** | 在两个矩形截面之间创建放样体 |

##### `create_hollow_sweep` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `create_hollow_sweep(project_path, name, component, material, x_min1, ..., z2, wall_thickness=2.0, tangency=0, minimize_twist=True) -> dict` |
| **功能** | 创建中空（壁厚）放样体（外放样减内放样） |

##### `define_loft` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `define_loft(project_path, name, component, material, tangency=0, minimize_twist=True) -> dict` |
| **功能** | 低级 API：从预先拾取的面创建放样 |

#### 布尔运算

| 函数 | 签名 | 功能 |
|------|------|------|
| `boolean_subtract` 🟢 | `(project_path, target, tool) -> dict` | `Solid.Subtract target - tool` |
| `boolean_add` 🟢 | `(project_path, shape1, shape2) -> dict` | `Solid.Add shape1 + shape2` |
| `boolean_intersect` 🟢 | `(project_path, shape1, shape2) -> dict` | `Solid.Intersect shape1 & shape2` |
| `boolean_insert` 🟢 | `(project_path, shape1, shape2) -> dict` | `Solid.Insert shape1 ← shape2` |

#### 实体管理

| 函数 | 签名 | 功能 |
|------|------|------|
| `delete_entity` 🟢 | `(project_path, component, name) -> dict` | 删除固体实体 |
| `create_component` 🟢 | `(project_path, component_name) -> dict` | 创建新组件组 |
| `change_material` 🟢 | `(project_path, shape_name, material) -> dict` | 更改形状材料 |
| `rename_entity` 🟢 | `(project_path, old_name, new_name) -> dict` | 重命名固体实体 |
| `set_entity_color` 🟢 | `(project_path, shape_name, use_individual_color=True, r=192, g=192, b=192) -> dict` | 设置形状个别颜色 |

#### 材料

##### `define_material_from_mtd` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `define_material_from_mtd(project_path: str, material_name: str) -> dict[str, Any]` |
| **功能** | 从技能 `references/Materials/` 目录加载 `.mtd` 材料定义文件 |

#### 求解器与仿真设置

| 函数 | 签名（简化） | 功能 |
|------|-------------|------|
| `define_frequency_range` 🟢 | `(project_path, start_freq, end_freq)` | 设置求解器频率范围 |
| `change_frequency_range` 🟢 | `(project_path, min_frequency, max_frequency)` | 更改频率范围（字符串参数） |
| `change_solver_type` 🟢 | `(project_path, solver_type)` | 更改求解器类型 |
| `define_background` 🟢 | `(project_path, background_type="Normal")` | 设置背景材料类型 |
| `define_boundary` 🟢 | `(project_path, face_type="expanded open", symmetry_type="none")` | 设置 6 面边界条件 + 对称 |
| `define_mesh` 🟢 | `(project_path, steps_per_wave_near=5, ..., use_gpu=True)` | 定义六面体网格设置（含 PBA 和边缘细化） |
| `define_solver` 🟢 | `(project_path, stimulation_port="All", ..., use_sensitivity=False)` | 配置时域 S 参数求解器 |
| `define_units` 🟢 | `(project_path, length="mm", frequency="GHz", ...)` | 设置各物理量单位 |

#### 端口与监视器

| 函数 | 签名（简化） | 功能 |
|------|-------------|------|
| `define_port` 🟢 | `(project_path, port_number, x_min, ..., orientation)` | 定义波导端口 |
| `define_monitor` 🟢 | `(project_path, start_freq, end_freq, step)` | 定义远场频率监视器 |
| `set_farfield_monitor` 🟢 | `(project_path, start_freq, end_freq, step=1, subvolume_..., enable_nearfield=True)` | 配置远场监视器（含子体积和近场计算） |
| `set_efield_monitor` 🟢 | `(project_path, start_freq, end_freq, step=1, dimension="Volume", ...)` | 配置 E 场体积/表面监视器 |
| `set_field_monitor` 🟢 | `(project_path, field_type, start_frequency, end_frequency, num_samples)` | 通用场监视器（E/H） |
| `set_probe` 🟢 | `(project_path, field_type, x_pos, y_pos, z_pos)` | 放置场探针 |
| `delete_probe_by_id` 🟢 | `(project_path, probe_id)` | 按 ID 删除探针 |
| `delete_monitor` 🟢 | `(project_path, monitor_name)` | 删除命名监视器 |

#### 变换

| 函数 | 签名（简化） | 功能 |
|------|-------------|------|
| `transform_shape` 🟢 | `(project_path, shape_name, transform_type, center_x="0", ..., repetitions=1, destination="")` | 镜像或旋转形状 |
| `transform_curve` 🟢 | `(project_path, curve_name, center_..., plane_normal_..., ...)` | 镜像曲线 |

#### 背景与后处理

| 函数 | 签名（简化） | 功能 |
|------|-------------|------|
| `set_background_with_space` 🟢 | `(project_path, x_min_space=30, ..., z_max_space=100)` | 设置模型周围的背景填充 |
| `set_farfield_plot_cuts` 🟢 | `(project_path, lateral_cuts=None, polar_cuts=None)` | 配置远场绘图切面 |
| `show_bounding_box` 🟢 | `(project_path)` | 启用 3D 绘图中的包围盒显示 |
| `activate_post_process_operation` 🟢 | `(project_path, operation, enable=True)` | 激活/停用 1D 后处理操作 |

#### 网格组

##### `create_mesh_group` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `create_mesh_group(project_path, group_name, items: list[str]) -> dict` |
| **功能** | 创建网格细化组并添加固体项 |

#### 复合几何

##### `create_horn_segment` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `create_horn_segment(project_path, segment_id, bottom_radius, top_radius, z_min, z_max) -> dict` |
| **功能** | 创建空心锥形喇叭段（外锥减内锥，壁厚 = 5） |

#### 导出

| 函数 | 签名（简化） | 功能 |
|------|-------------|------|
| `export_e_field` 🟢 | `(project_path, frequency, file_path)` | ASCII 导出 E 场结果 |
| `export_surface_current` 🟢 | `(project_path, frequency, file_path)` | ASCII 导出表面电流 |
| `export_voltage` 🟢 | `(project_path, voltage_index, file_path)` | ASCII 导出电压监视器结果 |

#### 历史与拾取

| 函数 | 签名 | 功能 | 稳定性 |
|------|------|------|--------|
| `add_to_history` | `(project_path, command, history_name="")` | 通过 CST 历史列表执行任意 VBA 命令 | 🟢 |
| `pick_face` | `(project_path, component, name, face_id)` | 按 ID 拾取面（用于后续操作如放样） | 🟡 |

#### 3D 可视化

##### `capture_3d_view` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `capture_3d_view(project_path="", output_dir="", filename_prefix="view", view_type="preset", preset_name="Isometric", azimuth=45.0, elevation=30.0, zoom=1.0, return_image_data=False) -> dict` |
| **参数** | `view_type` — `"preset"` 或 `"custom"` |
| | `preset_name` — `Front`, `Back`, `Top`, `Bottom`, `Left`, `Right`, `Isometric` |
| | `return_image_data` — 若 `True`，返回 base64 编码的图像数据 |
| **返回值** | 包含 PNG 路径和 JSON 元数据的字典 |
| **功能** | 捕获 CST 模型的 3D 视图为 1920×1080 PNG + JSON 元数据 |

---

### simulation.py — 仿真控制

> **模块**: `cst_runtime.core.simulation`
> **依赖**: `core.gateway`, `core.errors`, `core.identity`, `core.utils`
> **稳定性**: 🟢 稳定

仿真生命周期操作：启动、停止、暂停、配置。

#### `start_simulation` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `start_simulation(project_path: str) -> dict[str, Any]` |
| **功能** | 同步运行求解器（阻塞直到完成）。经过 `gateway.guard_before_simulation` 安全检查 |

```python
from cst_runtime.core.simulation import start_simulation

result = start_simulation("C:/models/antenna.cst")
```

#### `start_simulation_async` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `start_simulation_async(project_path: str) -> dict[str, Any]` |
| **功能** | 异步启动求解器（立即返回） |

#### `is_simulation_running` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `is_simulation_running(project_path: str) -> dict[str, Any]` |
| **返回值** | `{"running": bool}` |
| **功能** | 查询求解器是否仍在运行 |

#### `stop_simulation` / `pause_simulation` / `resume_simulation` 🟢

| 签名 | 功能 |
|------|------|
| `stop_simulation(project_path) -> dict` | 中止运行中的仿真 |
| `pause_simulation(project_path) -> dict` | 暂停运行中的仿真 |
| `resume_simulation(project_path) -> dict` | 恢复已暂停的仿真 |

#### `set_solver_acceleration` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `set_solver_acceleration(project_path, use_parallelization=True, max_threads=1024, max_cpu_devices=2, remote_calc=False, use_distributed=False, max_distributed_ports=64, distribute_matrix=True, mpi_parallel=False, auto_mpi=False, hardware_accel=True, max_gpus=4) -> dict` |
| **功能** | 通过 VBA 配置求解器加速（并行化、GPU、MPI、分布式计算） |

#### `set_fdsolver_extrude_open_bc` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `set_fdsolver_extrude_open_bc(project_path, enable=True) -> dict` |
| **功能** | 设置 `FDSolver.ExtrudeOpenBC` 开/关 |

#### `set_mesh_fpbavoid_nonreg_unite` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `set_mesh_fpbavoid_nonreg_unite(project_path, enable=True) -> dict` |
| **功能** | 设置 `Mesh.FPBAAvoidNonRegUnite` 开/关 |

#### `set_mesh_minimum_step_number` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `set_mesh_minimum_step_number(project_path, num_steps=5) -> dict` |
| **功能** | 设置 `Mesh.MinimumStepNumber` |

---

### results.py — 结果提取

> **模块**: `cst_runtime.core.results`
> **依赖**: `core.errors`, `core.utils`, `core.farfield`（条件导入）, `render.dashboard`（条件导入）
> **稳定性**: 🟢 稳定

CST 仿真结果的读取、导出和可视化。

#### `get_version_info` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `get_version_info() -> dict[str, Any]` |
| **功能** | 通过 `cst.results` 获取 CST 版本信息 |

#### `open_project` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `open_project(project_path: str, allow_interactive: bool = False, subproject_treepath: str = "") -> dict[str, Any]` |
| **功能** | 打开 CST 项目用于结果读取（非 GUI 会话） |

> ⚠️ 注意：这是结果模块的 `open_project`，与 `session.open_project` 不同。

#### `list_subprojects` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `list_subprojects(project_path: str, allow_interactive: bool = False) -> dict[str, Any]` |
| **功能** | 列出 CST 项目内的所有子项目 |

#### `list_result_items` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `list_result_items(project_path, module_type="3d", filter_type="0D/1D", allow_interactive=False, subproject_treepath="") -> dict` |
| **参数** | `filter_type` — `"0D/1D"`, `"all"`, 或 `"colormap"` |
| **返回值** | 包含 treepath 字符串列表 |
| **功能** | 列出项目中的可用结果项（树节点） |

```python
from cst_runtime.core.results import list_result_items

items = list_result_items("C:/models/antenna.cst", filter_type="0D/1D")
for tp in items["items"]:
    print(tp)
```

#### `list_run_ids` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `list_run_ids(project_path, treepath="", module_type="3d", allow_interactive=False, subproject_treepath="", skip_nonparametric=False, max_mesh_passes_only=True) -> dict` |
| **功能** | 列出运行 ID（参数扫描/网格通道标识符） |

#### `get_parameter_combination` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `get_parameter_combination(project_path, run_id: int, module_type="3d", allow_interactive=False, subproject_treepath="") -> dict` |
| **功能** | 获取特定 run_id 关联的参数组合 |

#### `get_1d_result` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `get_1d_result(project_path, treepath, module_type="3d", run_id=0, load_impedances=True, export_path="", allow_interactive=False, subproject_treepath="") -> dict` |
| **功能** | 提取 1D 结果数据（x/y 数组）并导出为 `.json` 文件 |

```python
from cst_runtime.core.results import get_1d_result

result = get_1d_result("C:/models/antenna.cst", "1D Results\\S-Parameters\\S1,1")
```

#### `get_2d_result` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `get_2d_result(project_path, treepath, module_type="3d", export_path="", allow_interactive=False, subproject_treepath="", include_data=False) -> dict` |
| **功能** | 提取 2D 结果数据（色图/网格）并导出为 `.json` 文件 |

#### `plot_project_result` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `plot_project_result(project_path, treepath, module_type="3d", run_id=0, ..., result_kind="auto", intermediate_json="") -> dict` |
| **功能** | 导出结果（自动检测 1D/2D）并渲染为交互式 HTML 绘图 |

#### `export_run_results` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `export_run_results(project_path, farfield_names=None, farfield_plot_mode="Realized Gain", farfield_theta_step=2.0, farfield_phi_step=2.0, run_id=None) -> dict` |
| **功能** | 批量导出 S 参数、2D 色图和远场网格。自动发现远场监视器 |

#### `generate_report` / `plot_exported_file` 🟢

| 签名 | 功能 |
|------|------|
| `generate_report(data_dir="", output_html="", page_title="", modules="", split=False)` | 从已导出的数据文件创建 HTML 报告 |
| `plot_exported_file(file_path="", output_html="", page_title="")` | 从单个导出 JSON 文件创建 HTML 绘图 |

---

### farfield.py — 远场分析

> **模块**: `cst_runtime.core.farfield`
> **依赖**: `core.process`, `core.gateway`, `core.errors`, `core.session`, `core.utils`, `analysis.farfield`
> **稳定性**: 🟢 稳定

远场数据导出与方向图分析。

#### `discover_farfield_monitors` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `discover_farfield_monitors(project_path: str) -> dict[str, Any]` |
| **返回值** | `{"farfield_names": [...], "count": int}` |
| **功能** | 打开 CST GUI 会话，扫描结果树中的远场监视器节点 |

```python
from cst_runtime.core.farfield import discover_farfield_monitors

result = discover_farfield_monitors("C:/models/antenna.cst")
print(result["farfield_names"])  # ["farfield (f=5.8)"]
```

#### `export_farfield_grid` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `export_farfield_grid(project_path, farfield_name, export_dir, quantity="Realized Gain", theta_step_deg=1.0, phi_step_deg=2.0, theta_min_deg=None, theta_max_deg=None, phi_min_deg=None, phi_max_deg=None, run_id=None, fresh_session=False, selection_tree_path="1D Results\\S-Parameters") -> dict` |
| **参数** | `quantity` — `"Realized Gain"`, `"Gain"`, 或 `"Directivity"` |
| **返回值** | 包含 `output_file`, peak, boresight 指标 |
| **功能** | 通过 CST GUI 中的 `FarfieldCalculator` 导出全球（或部分）远场网格。在 θ×φ 网格上评估增益/方向性，输出 JSON |

```python
from cst_runtime.core.farfield import export_farfield_grid

result = export_farfield_grid(
    "C:/models/antenna.cst",
    farfield_name="farfield (f=5.8)",
    export_dir="C:/models/exports/",
    quantity="Realized Gain",
    theta_step_deg=2.0,
    phi_step_deg=2.0,
)
```

#### `export_farfield_cut` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `export_farfield_cut(project_path, tree_path, export_dir, fresh_session=False) -> dict` |
| **参数** | `tree_path` — 必须以 `"Farfields\\Farfield Cuts\\"` 开头 |
| **返回值** | JSON 输出文件路径 |
| **功能** | 通过 VBA ASCII 导出远场切面（1D 切片），解析角度、主 dB、副 dB、轴比 |

---

### optimizer.py — Optuna 优化引擎

> **模块**: `cst_runtime.core.optimizer`
> **依赖**: `optuna`（外部库）
> **稳定性**: 🟢 稳定
> **说明**: 自包含模块，基于 Optuna 框架的 Ask/Tell 优化接口

#### `create_study` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `create_study(storage_path, study_name, parameters: str|dict, direction="minimize", directions=None, value_names=None, constraints=None, sampler="tpe", n_startup_trials=10) -> dict` |
| **参数** | `sampler` — `"tpe"`, `"cma-es"`, `"random"` |
| | `direction` — `"minimize"` 或 `"maximize"` |
| | `directions` — 多目标时的方向列表 |
| **功能** | 创建 Optuna 研究（SQLite 存储），支持单目标/多目标、约束优化 |

```python
from cst_runtime.core.optimizer import create_study

result = create_study(
    storage_path="C:/opt/study.db",
    study_name="antenna_opt",
    parameters={"R": {"low": 5.0, "high": 20.0}, "L": {"low": 10.0, "high": 30.0}},
    direction="minimize",
    sampler="tpe",
)
```

#### `ask_study` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `ask_study(storage_path, study_name) -> dict` |
| **返回值** | `{"trial_number": int, "params": {...}}` |
| **功能** | 向 Optuna 研究请求下一组参数建议 |

```python
from cst_runtime.core.optimizer import ask_study

suggestion = ask_study("C:/opt/study.db", "antenna_opt")
print(f"Trial #{suggestion['trial_number']}: {suggestion['params']}")
```

#### `tell_study` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `tell_study(storage_path, study_name, trial_number, value=None, values=None, constraints=None, state="complete") -> dict` |
| **功能** | 向研究报告目标值。支持约束 |

#### `best_study` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `best_study(storage_path, study_name) -> dict` |
| **功能** | 获取最佳试验。单目标返回 `best_value`/`best_params`；多目标返回 `best_values` 列表 |

#### `param_importances` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `param_importances(storage_path, study_name) -> dict` |
| **返回值** | `{"importances": {name: float}, "top_param": str}` |
| **功能** | 计算参数重要性排名（需要 scikit-learn） |

#### `add_trials` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `add_trials(storage_path, study_name, trials: list[dict]) -> dict` |
| **参数** | `trials` — 每个字典含 `{"params": {...}, "values": [...], "constraints": [...]}` |
| **功能** | 将预计算的试验注入研究（如手动网格扫描结果） |

#### `switch_sampler` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `switch_sampler(storage_path, study_name, new_sampler) -> dict` |
| **功能** | 切换采样器（tpe/cma-es/random）。删除并重建研究，迁移现有试验 |

> ⚠️ 破坏性操作：会删除并重建研究。

#### `terminate_check` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `terminate_check(storage_path, study_name) -> dict` |
| **返回值** | `{"should_terminate": bool}` |
| **功能** | 使用 `optuna.terminator.Terminator` 检查是否应终止优化 |

---

### objective.py — 目标函数评估

> **模块**: `cst_runtime.core.objective`
> **依赖**: 无（自包含）
> **稳定性**: 🟢 稳定

#### 内置目标类型注册表

| 类型 | 方向 | 说明 |
|------|------|------|
| `"s11_min_db"` | minimize | 提取最小 S11（dB） |
| `"s11_at_freq"` | minimize | 在指定频率处提取 S11（参数：`freq`） |
| `"gain_max"` | maximize | 从远场数据提取峰值增益 |
| `"bandwidth"` | maximize | 计算低于阈值的带宽（参数：`below_db`） |
| `"expression"` | — | 自定义表达式评估 |

#### `compute_objective` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `compute_objective(objective_spec: dict, run_output: dict) -> dict[str, Any]` |
| **参数** | `objective_spec` — 含 `type` 键的目标规格字典 |
| | `run_output` — 仿真运行的输出数据 |
| **返回值** | `{"value": float, "type": str, "direction": str, "details": ...}` |
| **功能** | 主入口：根据注册的评估器或表达式评估器分发计算 |

```python
from cst_runtime.core.objective import compute_objective

result = compute_objective(
    {"type": "s11_min_db"},
    {"s11_data": [...]}
)
print(f"Objective value: {result['value']} dB")
```

---

### doe.py — 实验设计

> **模块**: `cst_runtime.core.doe`
> **依赖**: 无（自包含）
> **稳定性**: 🟢 稳定

#### `design_probes` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `design_probes(parameters: dict[str, dict], max_probes: int = 12, include_center: bool = True) -> dict[str, Any]` |
| **参数** | `parameters` — `{name: {"min": float, "max": float}}` |
| **返回值** | `{"probes": [...], "n_probes": int, "design": str, "low": {...}, "high": {...}}` |
| **功能** | 生成 DOE 探测集。k≤4 参数：全因子 2^k；k>4：分数因子 2^(k-1) + 折叠 |

```python
from cst_runtime.core.doe import design_probes

result = design_probes(
    parameters={"R": {"min": 5, "max": 20}, "L": {"min": 10, "max": 30}},
    max_probes=12,
)
for probe in result["probes"]:
    print(probe)
```

#### `analyze_probes` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `analyze_probes(parameters: list[str], probes: list[dict]) -> dict[str, Any]` |
| **参数** | `probes` — 每个字典含参数值和 `"value"` 键（目标值） |
| **返回值** | `{"main_effects": {...}, "main_effects_normalized": {...}, "interactions": {"A×B": float}, "top_params": [...]}` |
| **功能** | 分析 DOE 探测结果：计算主效应（对比法）和双因素交互作用 |

---

### environment.py — 环境探测与配置

> **模块**: `cst_runtime.core.environment`
> **依赖**: `core.errors`, `core.workspace`（懒加载）
> **稳定性**: 🟢 稳定

CST 安装探测、配置和系统健康检查。

#### `load_cst_config` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `load_cst_config(workspace_root: str = "") -> dict[str, Any]` |
| **功能** | 读取 `.cst_config.json` 配置文件。若不存在则创建默认配置 |

#### `extract_cst_version_from_path` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `extract_cst_version_from_path(cst_path: str) -> str` |
| **功能** | 从路径中提取 CST 版本年份（如 `"2022"`），失败返回 `"Unknown"` |

#### `scan_cst_installations` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `scan_cst_installations() -> dict[str, Any]` |
| **返回值** | `{status, found_count, installations: list, active_path, active_valid}` |
| **功能** | 环境探测总控：聚合静态路径检查、目录扫描和注册表扫描 |

```python
from cst_runtime.core.environment import scan_cst_installations

result = scan_cst_installations()
for inst in result["installations"]:
    print(f"CST {inst['version']} at {inst['path']}")
```

#### `auto_register_cst` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `auto_register_cst(workspace_root: str = "") -> dict[str, Any]` |
| **返回值** | `{status, cst_registered, ...}` |
| **功能** | 自动探测 CST 安装并写入 `pyproject.toml` 配置 |

#### `install_cst_libraries` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `install_cst_libraries(cst_path: str = "", dry_run: bool = False) -> dict[str, Any]` |
| **返回值** | `{status, cst_path, pyproject_updated, import_verification, scan}` |
| **功能** | 安装/绑定 CST Python 库。验证路径、修改 `pyproject.toml`、运行冒烟测试 |

#### `health_check` 🟢

| 项 | 说明 |
|---|---|
| **签名** | `health_check(workspace: str = "", auto_fix: bool = True) -> dict[str, Any]` |
| **返回值** | `{status, overall: "pass"|"degraded"|"blocked", remaining_issues, user_instructions, phases, fixes_applied, workspace, platform}` |
| **功能** | 全面系统诊断：(1) 工作区 + 平台检查，(2) CST 环境检查，(3) 集成检查 |

```python
from cst_runtime.core.environment import health_check

report = health_check(auto_fix=True)
print(f"Overall: {report['overall']}")
if report["remaining_issues"]:
    for issue in report["remaining_issues"]:
        print(f"  ⚠ {issue}")
```

---

### compat.py — 版本兼容层

> **模块**: `cst_runtime.core.compat`
> **依赖**: 无（仅 stdlib）
> **稳定性**: 🟡 内部稳定

CST 2022/2026 版本差异的安全封装。

#### `detect_version` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `detect_version() -> tuple[int, int]` |
| **返回值** | `(major, minor)` 版本号；无法检测时返回 `(0, 0)` |
| **功能** | 检测已连接的 CST 版本。结果缓存到模块全局变量 |

#### `is_2022_or_later` / `is_2026_or_later` 🟡

| 签名 | 功能 |
|------|------|
| `is_2022_or_later() -> bool` | CST 版本 ≥ 2022 |
| `is_2026_or_later() -> bool` | CST 版本 ≥ 2026 |

#### `safe_connect_to_any` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `safe_connect_to_any() -> DesignEnvironment` |
| **功能** | 版本兼容的 DE 连接。依次尝试：`connect_to_any()` (2026) → `connect_to_any_or_new()` (2025) → `DesignEnvironment()` (2022) |
| **异常** | `RuntimeError` — 所有方法失败时 |

#### `safe_running_design_environments` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `safe_running_design_environments() -> list[int]` |
| **功能** | 获取运行中的 CST DE 进程 ID 列表。不可用时返回空列表 |

#### `safe_list_open_projects` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `safe_list_open_projects(de) -> list[str]` |
| **功能** | 版本兼容的已打开项目列表获取 |

#### `safe_quiet_mode` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `safe_quiet_mode(de) -> ContextManager` |
| **功能** | 版本兼容的静默模式。不支持时返回 no-op 上下文管理器 |

#### `safe_get_version` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `safe_get_version(de) -> str` |
| **返回值** | 版本字符串（如 `"2026.0.0"`）或 `"unknown"` |

---

### proxy.py — 子进程 IPC 代理

> **模块**: `cst_runtime.core.proxy`
> **依赖**: 无（仅 stdlib）
> **稳定性**: 🔴 内部实现

通过 JSON-over-stdin/stdout IPC 管理在 conda `cst39` 环境中运行的 `cst_worker.py` 子进程。

#### `CSTWorkerProxy` (Class) 🔴

| 项 | 说明 |
|---|---|
| **类型** | 线程安全单例 |
| **构造器** | `__init__(self)` — 初始化子进程、响应队列、读取线程 |
| **方法** | |
| `get_instance(cls)` | 类方法。线程安全的单例获取器 |
| `call(self, module_name, func_name, **kwargs) -> dict` | 发送 JSON RPC 请求到工作子进程。超时 60 秒。工作进程死亡时自动重启 |
| `shutdown(self)` | 关闭工作进程（等待 3s，不响应则强制终止） |

#### `call_cst` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `call_cst(module_name: str, func_name: str, **kwargs) -> dict[str, Any]` |
| **功能** | 便捷封装：获取单例 `CSTWorkerProxy` 并调用 `proxy.call(...)` |

> ⚠️ **内部实现**：此模块是跨进程 CST API 调用的底层传输机制，不建议直接使用。

---

### audit.py — 审计与运行记录

> **模块**: `cst_runtime.core.audit`
> **依赖**: `core.errors`, `core.workspace`
> **稳定性**: 🟡 内部稳定

运行阶段的审计记录和状态追踪。

#### `parse_json_object_arg` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `parse_json_object_arg(value: Any, field_name: str) -> dict[str, Any]` |
| **功能** | 将 None / 空字符串 / dict / JSON 字符串 解析为 dict |

#### `safe_stage_filename` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `safe_stage_filename(stage: str) -> str` |
| **功能** | 将阶段名清理为安全文件名 |

#### `json_default` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `json_default(value: Any) -> Any` |
| **功能** | 自定义 JSON 序列化默认函数（Path → str，其他 → repr） |

#### `record_run_stage` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `record_run_stage(task_path, stage, run_id="", status="completed", message="", details_json=""|dict, update_status=True) -> dict` |
| **功能** | 记录运行阶段：写入 `stages/` JSON，追加 `logs/production_chain.md`，可选更新 `status.json` |

#### `update_run_status` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `update_run_status(task_path, run_id="", status="", stage="", best_result_json=""|dict, output_files_json=""|dict, error_json=""|dict, extra_json=""|dict, mark_completed=False) -> dict` |
| **功能** | 更新运行的 `status.json`：合并最佳结果、输出文件、错误、额外字段 |

#### `append_tool_call` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `append_tool_call(*, run_dir, adapter, tool_name, tool_args, result) -> dict[str, str]` |
| **功能** | 追加工具调用审计记录到 `logs/tool_calls.jsonl` |

---

### evidence.py — 证据快照

> **模块**: `cst_runtime.core.evidence`
> **依赖**: `core.errors`, `core.project`
> **稳定性**: 🟡 内部稳定

项目状态的快照捕获与对比分析。

#### `capture_snapshot` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `capture_snapshot(project_path="", capture_types=None, output_dir="", stage_name="") -> dict` |
| **参数** | `capture_types` — 支持 `"parameters"`, `"entities"`, `"file_info"` |
| **功能** | 捕获 CST 项目当前状态的证据快照，输出 JSON 文件 |

#### `compare_snapshots` 🟡

| 项 | 说明 |
|---|---|
| **签名** | `compare_snapshots(before_file="", after_file="", output_html="") -> dict` |
| **功能** | 对比两个快照 JSON 文件（before/after），生成带样式的 HTML 证据报告 |

---

### utils.py — 通用工具函数

> **模块**: `cst_runtime.core.utils`
> **依赖**: `core.identity`（懒加载）
> **稳定性**: 🔴 内部实现

#### `abs_project_path` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `abs_project_path(project_path: str) -> str` |
| **功能** | 规范化项目路径（绝对路径 + 确保 `.cst` 后缀） |

#### `safe_log_db` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `safe_log_db(value: float) -> float` |
| **功能** | 计算 `20 * log10(|value|)`，下限 `1e-15` 避免 log(0) |

#### `serialize_value` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `serialize_value(value: Any) -> Any` |
| **功能** | 递归序列化为 JSON 兼容值（complex → dict, numpy → list） |

#### `parse_list_arg` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `parse_list_arg(value: Any) -> list[str]` |
| **功能** | 解析可能为 list / JSON 字符串 / 逗号分隔字符串 的参数 |

#### `project_path_from_args` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `project_path_from_args(args: dict) -> str` |
| **功能** | 从参数字典提取项目路径并验证 `.cst` 后缀 |

#### `run_id_from_args` 🔴

| 项 | 说明 |
|---|---|
| **签名** | `run_id_from_args(args: dict, default: int = 0) -> int` |
| **功能** | 从参数字典提取 run_id，回退到 `max(run_ids)` |

---

### \_\_init\_\_.py — CST 路径自动探测

> **模块**: `cst_runtime.core`
> **依赖**: 无
> **稳定性**: 🔴 内部实现

#### 模块级行为（无公开类/函数）

导入时自动执行以下操作：

1. **pyproject.toml 解析**：读取 `[tool.uv.sources.cst-studio-suite-link].path`，将路径加入 `sys.path`
2. **动态扫描**：扫描 `C:\Program Files` 和 `C:\Program Files (x86)` 中名为 `CST Studio Suite *` 的目录
3. **硬编码回退**：使用预定义的 `_CST_SEARCH_PATHS` 列表
4. **警告过滤**：抑制全局 `DeprecationWarning`

#### 模块级常量

```python
_CST_SEARCH_PATHS: list[str] = [
    r"C:\Program Files\CST Studio Suite 2026\AMD64\python_cst_libraries",
    r"C:\Program Files\CST Studio Suite 2025\AMD64\python_cst_libraries",
    r"C:\Program Files\CST Studio Suite 2022\AMD64\python_cst_libraries",
    # ...
]
```

---

## 跨模块依赖矩阵

| 模块 | 依赖的 core 模块 |
|------|-----------------|
| `__init__` | —（仅 stdlib） |
| `errors` | — |
| `utils` | `identity`（懒加载） |
| `compat` | — |
| `proxy` | — |
| `gateway` | `errors` |
| `identity` | `errors` |
| `process` | `identity`, `workspace`, `errors` |
| `session` | `gateway`, `process`, `identity`, `errors`, `utils` |
| `project` | `errors`, `gateway`, `identity`, `utils` |
| `project_info` | `errors`, `utils` |
| `workspace` | `errors` |
| `modeling` | `errors`, `identity`, `utils`, `session`（懒加载） |
| `simulation` | `gateway`, `errors`, `identity`, `utils` |
| `results` | `errors`, `utils`, `farfield`（条件）, `render.dashboard`（条件） |
| `farfield` | `process`, `gateway`, `errors`, `session`, `utils`, `analysis.farfield` |
| `optimizer` | —（自包含，使用 optuna） |
| `objective` | — |
| `doe` | — |
| `environment` | `errors`, `workspace`（懒加载） |
| `audit` | `errors`, `workspace` |
| `evidence` | `errors`, `project` |

---

> **注意**：本文档仅记录 `core/` 目录中源码实际存在的公开接口。
> 如需用户友好的调用方式，请使用 `lib/` 门面层的封装 API。
