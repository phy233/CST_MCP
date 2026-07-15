# CST_MCP 实施计划

> 生成日期: 2026-05-25
> 目标: MATLAB 功能补全 + MCP Server 搭建 + CST 2022 兼容适配

---

## 目录

1. [CST 2022 vs 2026 兼容性分析](#一cst-2022-vs-2026-兼容性分析)
2. [MATLAB → Python 功能缺口清单](#二matlab--python-功能缺口清单)
3. [现有 CST-Python 交互能力盘点](#三现有-cst-python-交互能力盘点)
4. [标准库风格拆分方案](#四标准库风格拆分方案)
5. [Batch 1: P0 功能补全（阻塞核心流程）](#五batch-1-p0-功能补全)
6. [Batch 2: P1 功能补全（核心流程辅助）](#六batch-2-p1-功能补全)
7. [Batch 3: P2 功能补全（高级功能）](#七batch-3-p2-功能补全)
8. [MCP Server 实施方案](#八mcp-server-实施方案)（含 8.8 非阻塞仿真设计）
9. [CST 2022 兼容适配方案](#九cst-2022-兼容适配方案)
10. [文件变更清单](#十文件变更清单)
11. [测试计划](#十一测试计划)

---

## 一、CST 2022 vs 2026 兼容性分析

### 1.1 关键风险

| 风险 | 严重度 | 说明 | 应对方案 |
|------|--------|------|---------|
| `DesignEnvironment.connect_to_any()` 不存在 | **高** | CST 2022 的 `cst.interface` 可能无此方法 | 添加版本检测 + 回退到 `DesignEnvironment()` |
| `running_design_environments()` 不存在 | **高** | `core/identity.py:85` 使用 | 添加 `hasattr` 守卫 |
| `cst.results` C 扩展不读 2022 格式 | **中** | 文档声明支持 2025/2026 | 需实测，不行则用 VBA 导出替代 |
| Python 3.13 要求 | **中** | CST 2022 自带 Python 3.9/3.10 | 用外部 Python 3.13 + `sys.path` 链接 CST 库 |
| `PBAVersion "2023042623"` | **低** | 硬编码的网格版本时间戳 | 旧版通常向后兼容 |
| `execute_vba_code()` 已移除 | **无** | 项目已用 `add_to_history()` 为主 | 已处理，三级回退链存在 |

### 1.2 需要验证的 API 调用

在 `core/identity.py` 和 `core/environment.py` 中使用了以下可能 2022 不存在的 API：

```python
# core/identity.py:73-101
de.connect_to_any()                    # 可能 2022 无此方法
running_design_environments()          # 可能 2022 无此函数
de.connect(pid)                        # 可能 2022 无此方法

# core/environment.py
de.quiet_mode_enabled()                # 可能 2022 无此方法
de.list_open_projects()                # 可能 2022 无此方法
```

### 1.3 兼容适配策略

在 `core/compat.py`（新建）中封装版本检测和 API 回退：

```python
# core/compat.py
import cst.interface

def detect_cst_version() -> tuple[int, int]:
    """检测 CST 版本，返回 (major, minor)"""
    try:
        de = cst.interface.DesignEnvironment()
        ver = de.version  # e.g. "2026.0.0"
        parts = ver.split(".")
        return int(parts[0]), int(parts[1])
    except Exception:
        return 0, 0

def safe_connect_to_any():
    """兼容 CST 2022/2026 的连接方式"""
    de_cls = cst.interface.DesignEnvironment
    if hasattr(de_cls, "connect_to_any"):
        return de_cls.connect_to_any()
    elif hasattr(de_cls, "connect_to_any_or_new"):
        return de_cls.connect_to_any_or_new()
    else:
        return de_cls()  # CST 2022: 直接构造
```

---

## 二、MATLAB → Python 功能缺口清单

### 2.1 总览

| 状态 | 数量 | 占比 |
|------|------|------|
| 完全覆盖 | 19 | 31% |
| 部分覆盖 | 14 | 23% |
| **未覆盖** | **28** | **46%** |

### 2.2 P0 缺口（阻塞核心流程）

| # | 缺口 | MATLAB 文件 | 影响范围 |
|---|------|------------|---------|
| 1 | ~~WCS 坐标系操作~~ ✅已完成 | `Modeling/activateWCS.m`, `activateWCSGlobal_VBAOnly.m` | 阵列建模、单元放置 |
| 2 | ~~Translate 变换~~ ✅已完成 | `Modeling/translationObj.m` | 复制-平移阵列 |
| 3 | ~~Floquet 端口~~ ✅已完成 | `Simulation/setFloquetPort.m` | 周期边界仿真 |
| 4 | ~~逐面边界设置~~ ✅已完成 | `Simulation/setUnitBoundary.m` | 单元格仿真 |
| 5 | ~~阵列建模框架~~ ✅已完成 | `ArrayProcess/arrayModeling.m`, `fastArrayModeling.m` | 超表面整体建模 |
| 6 | ~~Arc 曲线~~ ✅已完成 | `Modeling/defineArc.m`, `defineArcBlock.m` | C-ring 等曲线结构 |
| 7 | ~~组件删除~~ ✅已完成 | `Modeling/deleteComponent.m` | 组件管理 |

### 2.3 P1 缺口（核心流程辅助）

| # | 缺口 | MATLAB 文件 | 影响范围 |
|---|------|------------|---------|
| 8 | ~~程序化材料定义~~ ✅已完成 | `Modeling/defineMaterial.m` | 动态创建新材料 |
| 9 | ~~结果删除~~ ✅已完成 | `Postprocessing/deleteResult.m` | 重跑仿真前清理 |
| 10 | ~~结构重建~~ ✅已完成 | `AssistFunction/updateStructure.m` | 参数修改后重建 |
| 11 | ~~参数存在检查~~ ✅已完成 | `AssistFunction/ensureParameterExist.m` | 参数校验 |
| 12 | ~~材料存在检查~~ ✅已完成 | `AssistFunction/check_material_exists.m` | 材料校验 |
| 13 | ~~单元格参数化类~~ ✅已完成 | `MetaUnitInfo/unit_Cyuanhuan.m` 等 | 编码→几何映射 |
| 14 | ~~S 参数频率插值~~ ✅已完成 | `Postprocessing/getSParamAtFreq.m` | 精确频率点提取 |

### 2.4 P2 缺口（高级功能）

| # | 缺口 | MATLAB 文件 | 影响范围 |
|---|------|------------|---------|
| 15 | ~~参数扫频 + LUT~~ ✅已完成 | `CodeMataUnitProcess/crossProcess.m` | 自动化扫参 |
| 16 | ~~LUT 离线重建~~ ✅已完成 | `CodeMataUnitProcess/rebuildLUT_Offline.m` | 数据后处理 |
| 17 | CST 导出文件解析 | `Postprocessing/disign_for_manual_export/` | 离线分析 |
| 18 | 相位量化 | `Postprocessing/diffractionPhaseQuant.m` | D2NN 算法 |
| 19 | FD 求解器配置 | `Simulation/setFrequencySolver.m` | 频域求解器 |
| 20 | MNIST 切割板建模 | `ArrayProcess/buildMNIST_Cutout.m` | 特定数据集 |

---

## 三、现有 CST-Python 交互能力盘点

> 结论：`core/` 层已实现完整的双向交互，可独立调用，不依赖 CLI dispatch。

### 3.1 两条独立的 CST API 通道

| API | 用途 | 是否需要 CST 运行 | 典型调用 |
|-----|------|-------------------|---------|
| `cst.interface` (COM) | 实时模型操作（读写参数、控制仿真、查询状态） | **是** — 需要 CST Design Environment 进程 | `project.model3d.RestoreDoubleParameter()` |
| `cst.results` (离线) | 读取仿真结果文件（S 参数、场数据） | **否** — 直接读 `.cst` 文件 | `ProjectFile(path).get_3d().get_result_item()` |

### 3.2 已实现的交互能力

| 能力 | 函数 | 文件:行 | CST API | 可独立调用? |
|------|------|---------|---------|-----------|
| **读取所有参数值** | `list_parameters()` | `core/project.py:66` | `m3d.GetNumberOfParameters()` + `RestoreDoubleParameter()` | ✅ |
| **写入单个参数** | `change_parameter()` | `core/project.py:152` | VBA `StoreDoubleParameter` via `add_to_history()` | ✅ |
| **批量写入参数** | `define_parameters()` | `core/project.py:187` | VBA `StoreParameters` via `add_to_history()` | ✅ |
| **读取 S 参数** | `get_1d_result()` | `core/results.py:209` | `cst.results.get_result_item()` | ✅ |
| **读取 2D 场数据** | `get_2d_result()` | `core/results.py:285` | `cst.results.get_result2d_item()` | ✅ |
| **列出可用结果** | `list_result_items()` | `core/results.py:101` | `cst.results.get_tree_items()` | ✅ |
| **列出仿真 run ID** | `list_run_ids()` | `core/results.py:144` | `cst.results.get_run_ids()` | ✅ |
| **读取 run 对应参数组合** | `get_parameter_combination()` | `core/results.py:179` | `cst.results.get_parameter_combination()` | ✅ |
| **查询求解器运行状态** | `is_simulation_running()` | `core/simulation.py:68` | `project.modeler.is_solver_running()` | ✅ |
| **列出 CST 中打开的工程** | `list_open_projects()` | `core/identity.py:129` | `de.list_open_projects()` | ✅ |
| **列出几何实体** | `list_entities()` | `core/project.py:116` | `project.modeler.get_tree_items()` | ✅ |
| **导出远场数据** | `export_farfield_grid/cut()` | `core/farfield.py` | VBA `ASCIIExport` via `add_to_history()` | ✅ |
| **启动/停止仿真** | `start_simulation()` | `core/simulation.py:16` | `mws.RunSolver()` / `mws.AbortSolver()` | ✅ |
| **打开/关闭 CST 会话** | `open_project()` / `close_project()` | `core/session.py` | `cst.interface.DesignEnvironment` COM | ✅ |
| **环境检测（进程/锁/就绪）** | `inspect()` | `core/session.py:25` | 进程发现 + 锁文件 + COM | ✅ |

### 3.3 COM 返回值机制说明

MATLAB 和 Python 调用 CST COM 方法的对比：

| MATLAB 调用 | Python 等价调用 | 返回值 | 现有 Python 代码是否使用 |
|------------|----------------|--------|------------------------|
| `invoke(mws, 'GetNumberOfParameters')` | `m3d.GetNumberOfParameters()` | int | ✅ `core/project.py:88` |
| `invoke(mws, 'GetParameterName', idx)` | `m3d.GetParameterName(idx)` | str | ✅ `core/project.py:89` |
| `invoke(mws, 'GetParameterNValue', idx)` | `m3d.RestoreDoubleParameter(name)` | float | ✅ `core/project.py:91` |
| `invoke(mws, 'DoesParameterExist', name)` | `m3d.DoesParameterExist(name)` | bool | ❌ 未使用（用 list 遍历替代） |
| `tmp = invoke(mws, 'Material'); invoke(tmp, 'Exists', name)` | `m3d.Material.Exists(name)` | bool | ❌ 未使用 |
| `rt = invoke(mws, 'ResultTree'); invoke(rt, 'DoesTreeItemExist', path)` | `m3d.ResultTree.DoesTreeItemExist(path)` | bool | ❌ 未使用（用 cst.results 替代） |
| `invoke(rt, 'GetFirstChildName', folder)` | `m3d.ResultTree.GetFirstChildName(folder)` | str | ❌ 未使用（用 cst.results 替代） |
| `invoke(rt, 'GetNextItemName', current)` | `m3d.ResultTree.GetNextItemName(current)` | str | ❌ 未使用（用 cst.results 替代） |
| `invoke(rt, 'GetFileFromTreeItem', path)` | `m3d.ResultTree.GetFileFromTreeItem(path)` | str | ❌ 未使用 |
| `invoke(mws, 'Result1DComplex', path)` | `m3d.Result1DComplex(path)` | COM obj | ❌ 未使用（用 cst.results 替代） |
| `invoke(resObj, 'GetArray', 'x')` | `res_obj.GetArray('x')` | array | ❌ 未使用（用 cst.results 替代） |
| `invoke(mws, 'RunSolver')` | `m3d.RunSolver()` | — | ✅ `core/simulation.py` |
| `invoke(mws, 'IsSolverRunning')` | `m3d.is_solver_running()` | bool | ✅ `core/simulation.py:74` |
| `invoke(mws, 'DeleteResults')` | `m3d.DeleteResults()` | — | ❌ 未使用（需补全） |
| `invoke(mws, 'GetSolverType')` | `m3d.GetSolverType()` | str | ❌ 未使用 |

**关键发现：**

1. **Python 的 `cst.interface` 支持与 MATLAB 完全相同的 COM 方法调用** — 语法从 `invoke(mws, 'Method', args)` 变为 `m3d.Method(args)`
2. **子对象链式访问同样支持** — `m3d.Material.Exists(name)`, `m3d.ResultTree.DoesTreeItemExist(path)`, `m3d.Monitor.Create(...)`, `m3d.Mesh.AdaptionLimit(...)` 等
3. **现有 Python 代码只用了少数 COM 返回值调用** — 大部分查询用 `cst.results`（离线文件读取）替代了 COM `ResultTree` 遍历
4. **`cst.results` 方案更优** — 不占 CST 许可证、支持并行读取、无需 CST 运行

**需要补全的 COM 返回值调用（`lib/` 层）：**

| 函数 | COM 调用 | MATLAB 等价 | 用途 |
|------|---------|------------|------|
| `param_exists()` | `m3d.DoesParameterExist(name)` | `ensureParameterExist` | 参数校验 |
| `material_exists()` | `m3d.Material.Exists(name)` | `check_material_exists` | 材料校验 |
| `tree_item_exists()` | `m3d.ResultTree.DoesTreeItemExist(path)` | `smartReadSParameter` 中检查 | 结果路径校验 |
| `list_sparams()` | `m3d.ResultTree.GetFirstChildName()` + `GetNextItemName()` | `listAvailableSParams` | 列出 S 参数 |
| `delete_results()` | `m3d.DeleteResults()` | `deleteResult` | 清除结果 |
| `get_solver_type()` | `m3d.GetSolverType()` | — | 查询求解器类型 |

### 3.4 已实现的双向反馈循环

| 循环 | 流程 | 代码位置 |
|------|------|---------|
| **参数优化** | 读参数 → 写新值 → 重建 → 仿真 → 读结果 → 再调整 | `list_parameters()` → `change_parameter()` → `prepare-experiment` → `get_1d_result()` |
| **仿真轮询** | 启动仿真 → 轮询 `is_simulation_running()` → 完成后读结果 | `start_simulation_async()` → `wait_simulation` (poll loop) → `export_run_results()` |
| **网关守卫** | 写参数 → 标记 dirty → 仿真前检查 → 强制重建 | `gateway.mark_params_dirty()` → `guard_before_simulation()` → 报错要求 close+reopen |

### 3.5 `core/` 层独立调用示例

```python
# 不需要 CLI dispatch、workspace、audit，直接调用 core 函数
from cst_runtime.core.project import list_parameters, change_parameter
from cst_runtime.core.results import get_1d_result
from cst_runtime.core.simulation import start_simulation, is_simulation_running

# 1. 读取当前参数
params = list_parameters("C:\\path\\to\\model.cst")
print(params["parameters"]["g"])  # 当前值

# 2. 修改参数
change_parameter("C:\\path\\to\\model.cst", name="g", value=24.0)

# 3. 读取仿真结果（离线，不需要 CST 运行）
result = get_1d_result("C:\\path\\to\\model.cst",
                        treepath="1D Results\\S-Parameters\\S1,1")
print(result["ydata"][0])  # 第一个频率点的 Re/Im
```

---

## 四、标准库风格拆分方案

> ✅ **状态：已完成 (Commit b3e5eba7等)**

> 目标：将 CST 控制代码拆分为多个独立小文件，每个文件可单独 import 使用，类似 Python 标准库风格。

### 4.1 设计原则

1. **一个文件一个职责** — 每个 `.py` 文件只做一类事
2. **无循环依赖** — 文件间单向依赖，底层不依赖上层
3. **可独立 import** — 任何文件都能 `from cst_runtime.lib.xxx import func` 直接使用
4. **与 CLI 解耦** — 库层不依赖 argparse、workspace、audit

### 4.2 新目录结构：`cst_runtime/lib/`

在现有 `core/` 和 `tools/` 之外新建 `lib/` 目录，作为**面向用户的公开 API 层**：

```
cst_runtime/
├── core/               ← 现有（保留，内部实现层）
│   ├── session.py      ← COM 会话管理
│   ├── project.py      ← 参数/实体操作
│   ├── results.py      ← 结果读取
│   ├── simulation.py   ← 求解器控制
│   ├── modeling.py     ← VBA 建模
│   ├── farfield.py     ← 远场导出
│   ├── gateway.py      ← 安全守卫
│   ├── identity.py     ← 工程身份识别
│   ├── compat.py       ← CST 版本兼容（新建）
│   └── ...
├── tools/              ← 现有（保留，CLI 工具定义层）
├── lib/                ← 【新建】标准库风格公开 API
│   ├── __init__.py     ← 导出所有公共函数
│   ├── session.py      ← 会话：open, close, inspect, quit
│   ├── parameters.py   ← 参数：list, get, set, exists
│   ├── geometry.py     ← 几何：brick, cylinder, arc, boolean, transform, wcs
│   ├── materials.py    ← 材料：define, list, check_exists
│   ├── mesh.py         ← 网格：settings, acceleration
│   ├── boundary.py     ← 边界：per-face, unit-cell, periodic
│   ├── port.py         ← 端口：Floquet, waveguide
│   ├── solver.py       ← 求解器：start, stop, poll, frequency-range
│   ├── monitors.py     ← 监视器：farfield, e-field, field, probe
│   ├── results.py      ← 结果：s-param, 2d-field, run-ids, export
│   ├── farfield.py     ← 远场：grid-export, cut-export, flatness
│   ├── optimization.py ← 优化：optuna-study, doe-probes
│   ├── array.py        ← 阵列建模：coding-array, fast-array
│   └── unit_cells.py   ← 单元格：c-ring, cross, custom
└── cli/                ← 现有（保留，CLI 入口）
```

### 4.3 `lib/` 层设计模式

每个 `lib/*.py` 文件遵循统一模式：

```python
# lib/parameters.py — 参数操作公开 API
"""CST project parameter operations.

Usage:
    from cst_runtime.lib.parameters import list_params, get_param, set_param

    # 读取所有参数
    params = list_params("C:\\path\\to\\model.cst")

    # 读取单个参数
    g = get_param("C:\\path\\to\\model.cst", "g")

    # 设置参数
    set_param("C:\\path\\to\\model.cst", "g", 24.0)
"""
from __future__ import annotations
from typing import Any

# 内部依赖：仅引用 core 层
from ..core.project import list_parameters as _list_parameters
from ..core.project import change_parameter as _change_parameter
from ..core import gateway


def list_params(project_path: str) -> dict[str, float]:
    """列出所有参数及其当前值。

    Args:
        project_path: .cst 文件路径

    Returns:
        {"param_name": value, ...}
    """
    result = _list_parameters(project_path)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Unknown error"))
    return {k: v["value"] for k, v in result["parameters"].items()}


def get_param(project_path: str, name: str) -> float:
    """获取单个参数的当前值。

    Args:
        project_path: .cst 文件路径
        name: 参数名

    Returns:
        参数值
    """
    params = list_params(project_path)
    if name not in params:
        raise KeyError(f"Parameter '{name}' not found. Available: {list(params.keys())}")
    return params[name]


def set_param(project_path: str, name: str, value: float) -> None:
    """设置参数值。修改后需调用 solver.rebuild() 或 close+reopen 生效。

    Args:
        project_path: .cst 文件路径
        name: 参数名
        value: 新值
    """
    result = _change_parameter(project_path, name=name, value=value)
    if result.get("status") == "error":
        raise RuntimeError(result.get("message", "Unknown error"))


def param_exists(project_path: str, name: str) -> bool:
    """检查参数是否存在。"""
    return name in list_params(project_path)
```

### 4.4 各 `lib/` 模块职责与函数清单

#### `lib/session.py` — 会话管理

| 函数 | 签名 | 说明 |
|------|------|------|
| `open_project` | `(path: str) -> None` | 打开 CST 工程 |
| `close_project` | `(path: str, save: bool = False) -> None` | 关闭 CST 工程 |
| `inspect` | `(path: str = "") -> dict` | 检查 CST 环境状态 |
| `quit_cst` | `(path: str) -> None` | 退出 CST 进程 |
| `list_open` | `() -> list[str]` | 列出所有打开的工程路径 |
| `is_locked` | `(path: str) -> bool` | 检查工程是否被锁定 |

#### `lib/parameters.py` — 参数操作

| 函数 | 签名 | 说明 |
|------|------|------|
| `list_params` | `(path: str) -> dict[str, float]` | 列出所有参数 |
| `get_param` | `(path: str, name: str) -> float` | 获取单个参数 |
| `set_param` | `(path: str, name: str, value: float) -> None` | 设置参数 |
| `set_params` | `(path: str, params: dict) -> None` | 批量设置参数 |
| `param_exists` | `(path: str, name: str) -> bool` | 检查参数是否存在（COM: `DoesParameterExist`） |

#### `lib/geometry.py` — 几何建模

| 函数 | 签名 | 说明 |
|------|------|------|
| `brick` | `(path, component, name, xrange, yrange, zrange, material) -> None` | 创建长方体 |
| `cylinder` | `(path, component, name, axis, center, radius, height, material) -> None` | 创建圆柱 |
| `cone` | `(path, ...) -> None` | 创建圆锥 |
| `arc` | `(path, name, center, radius, start_angle, end_angle) -> None` | 创建弧线（新增） |
| `polygon` | `(path, ...) -> None` | 创建多边形 |
| `boolean_add` | `(path, solid1, solid2) -> None` | 布尔加 |
| `boolean_subtract` | `(path, solid1, solid2) -> None` | 布尔减 |
| `boolean_intersect` | `(path, solid1, solid2) -> None` | 布尔交 |
| `delete_entity` | `(path, name) -> None` | 删除实体 |
| `delete_component` | `(path, component) -> None` | 删除组件（新增） |
| `rotate` | `(path, name, center, angle, ...) -> None` | 旋转 |
| `translate` | `(path, name, vector, ...) -> None` | 平移（新增） |
| `mirror` | `(path, name, plane_normal, ...) -> None` | 镜像 |
| `activate_wcs` | `(path, name, origin, normal, uvector) -> None` | 激活局部 WCS（新增） |
| `deactivate_wcs` | `(path) -> None` | 切回全局 WCS（新增） |

#### `lib/materials.py` — 材料管理

| 函数 | 签名 | 说明 |
|------|------|------|
| `define` | `(path, name, epsilon, mue, tan_d, ...) -> None` | 定义材料（新增） |
| `define_from_mtd` | `(path, mtd_path) -> None` | 从 .mtd 文件加载 |
| `list_materials` | `(path) -> list[str]` | 列出可用材料 |
| `exists` | `(path, name) -> bool` | 检查材料是否存在（COM: `Material.Exists`）（新增） |
| `set_material` | `(path, entity, material) -> None` | 修改实体材料 |

#### `lib/boundary.py` — 边界条件

| 函数 | 签名 | 说明 |
|------|------|------|
| `set_all` | `(path, boundary_type) -> None` | 所有面设为同一类型 |
| `set_per_face` | `(path, xmin, xmax, ymin, ymax, zmin, zmax) -> None` | 逐面设置（新增） |
| `set_unit_cell` | `(path, periodic_angle=0) -> None` | 设为单元格边界（新增） |

#### `lib/port.py` — 端口配置

| 函数 | 签名 | 说明 |
|------|------|------|
| `define_waveguide` | `(path, ...) -> None` | 定义波导端口 |
| `define_floquet` | `(path, zmin_modes, zmax_modes, ...) -> None` | 定义 Floquet 端口（新增） |

#### `lib/solver.py` — 求解器控制

| 函数 | 签名 | 说明 |
|------|------|------|
| `set_frequency_range` | `(path, fmin, fmax) -> None` | 设置频率范围 |
| `start` | `(path) -> None` | 启动仿真 |
| `start_async` | `(path) -> None` | 异步启动仿真 |
| `wait` | `(path, timeout=3600, interval=10) -> bool` | 等待仿真完成 |
| `is_running` | `(path) -> bool` | 查询是否在运行 |
| `stop` | `(path) -> None` | 停止仿真 |
| `rebuild` | `(path) -> None` | 重建结构（新增） |
| `delete_results` | `(path) -> None` | 删除所有结果（COM: `DeleteResults`）（新增） |
| `get_solver_type` | `(path) -> str` | 获取求解器类型（COM: `GetSolverType`）（新增） |

#### `lib/monitors.py` — 监视器管理

| 函数 | 签名 | 说明 |
|------|------|------|
| `set_farfield` | `(path, name, ...) -> None` | 设置远场监视器 |
| `set_efield` | `(path, name, ...) -> None` | 设置电场监视器 |
| `set_field` | `(path, name, ...) -> None` | 设置通用场监视器 |
| `set_probe` | `(path, name, ...) -> None` | 设置探针 |
| `delete_probe` | `(path, name) -> None` | 删除探针 |
| `delete_monitor` | `(path, name) -> None` | 删除监视器 |

#### `lib/results.py` — 结果读取

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_sparam` | `(path, treepath, run_id) -> dict` | 读取 S 参数（离线: `cst.results`） |
| `get_sparam_at_freq` | `(path, treepath, freq_ghz) -> dict` | 指定频率插值读取（新增） |
| `get_2d_field` | `(path, treepath) -> dict` | 读取 2D 场数据 |
| `list_items` | `(path, filter) -> list[str]` | 列出可用结果项（离线: `cst.results`） |
| `list_sparams` | `(path) -> list[str]` | 列出 S 参数（COM: `ResultTree.GetFirstChildName` 遍历）（新增） |
| `sparam_exists` | `(path, treepath) -> bool` | 检查 S 参数是否存在（COM: `ResultTree.DoesTreeItemExist`）（新增） |
| `list_runs` | `(path) -> list[int]` | 列出 run ID |
| `get_param_combo` | `(path, run_id) -> dict` | 获取 run 对应参数 |
| `export_all` | `(path, ...) -> dict` | 批量导出结果 |

#### `lib/farfield.py` — 远场操作

| 函数 | 签名 | 说明 |
|------|------|------|
| `export_grid` | `(path, ...) -> dict` | 导出远场网格数据 |
| `export_cut` | `(path, ...) -> dict` | 导出远场切面数据 |
| `list_monitors` | `(path) -> list[str]` | 列出远场监视器 |

#### `lib/optimization.py` — 优化

| 函数 | 签名 | 说明 |
|------|------|------|
| `create_study` | `(path, study_name, params) -> str` | 创建 Optuna 研究 |
| `ask` | `(study_path) -> dict` | 获取下一组参数 |
| `tell` | `(study_path, params, value) -> None` | 回报结果 |
| `best` | `(study_path) -> dict` | 获取最优参数 |

#### `lib/array.py` — 阵列建模（新增）

| 函数 | 签名 | 说明 |
|------|------|------|
| `build_coding_array` | `(path, matrix, unit_type, dx, dy) -> None` | 从编码矩阵建阵列 |
| `fast_array` | `(path, template, positions) -> None` | 模板复制建阵列 |

#### `lib/unit_cells.py` — 单元格类（新增）

| 类 | 说明 |
|----|------|
| `UnitCellBase` | 抽象基类 |
| `CRingCell` | C-ring 开口圆环 |
| `CrossCell` | I-shaped 十字 |

### 4.5 `lib/__init__.py` — 统一导出

```python
"""cst_runtime.lib — CST 控制公开 API

标准库风格，每个模块可独立 import:

    from cst_runtime.lib.parameters import list_params, set_param
    from cst_runtime.lib.geometry import brick, boolean_subtract
    from cst_runtime.lib.results import get_sparam
    from cst_runtime.lib.solver import start, wait, is_running

或统一导入:

    from cst_runtime import lib
    lib.parameters.list_params("C:\\path\\to\\model.cst")
"""
from . import (
    session,
    parameters,
    geometry,
    materials,
    mesh,
    boundary,
    port,
    solver,
    monitors,
    results,
    farfield,
    optimization,
    array,
    unit_cells,
)

__all__ = [
    "session", "parameters", "geometry", "materials", "mesh",
    "boundary", "port", "solver", "monitors", "results",
    "farfield", "optimization", "array", "unit_cells",
]
```

### 4.6 `lib/` 与 `core/`、`tools/` 的关系

```
用户代码 / MCP Server / 脚本
        ↓ import
    lib/*.py          ← 公开 API（简洁函数签名，异常处理，文档）
        ↓ 内部调用
    core/*.py         ← 内部实现（COM 调用，VBA 构造，gateway 守卫）
        ↓
    cst.interface / cst.results  ← CST 官方库

    tools/*.py        ← CLI 工具定义（TOOL_DEFS + handler，给 dispatch 用）
    cli/dispatch.py   ← CLI 入口（argparse，workspace 检查，audit）
```

- `lib/` 调用 `core/`，不调用 `tools/` 或 `cli/`
- `tools/` 调用 `core/`，不调用 `lib/`
- `lib/` 和 `tools/` 是 `core/` 的两种不同前端
- MCP Server 直接调用 `lib/`（而非 `tools/`），获得更干净的函数签名

### 4.7 实验数据库的归属：MCP Server vs 上级项目

**结论：数据库在上级项目实现，不在 MCP server 或 cst_runtime 中。**

```
┌──────────────────────────────────────────────────────────────┐
│  MCP Server (mcp_server/)                                    │
│  只做: 协议转换、参数校验、MCP 层审计                         │
│  记录: "工具 X 被调用，参数 Y，返回 Z"                        │
│  不记录: "这次调参的优化目标是什么、结果好不好"               │
│  审计文件: run_logs/tool_calls.jsonl                          │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│  上级项目 (microwave metasurface) — db/ 模块                 │
│  记录: 实验语义（目标、结论、收敛曲线）                       │
│  表结构:                                                      │
│    experiments(id, task, goal, status, created_at)            │
│    param_sets(exp_id, param_name, param_value, step)          │
│    measurements(exp_id, step, s11_min_db, best_freq, ...)     │
│    decisions(exp_id, step, action, reason)                    │
│  调用方式: 上级项目代码调用 lib/ 获取数据，自己写入 db/       │
└───────────────────────┬──────────────────────────────────────┘
                        │ 调用
┌───────────────────────▼──────────────────────────────────────┐
│  cst_runtime/lib/                                            │
│  只做: CST 操作，返回原始数据                                 │
│  返回: {"status":"success", "parameters":{...}, "ydata":[...]}│
│  不关心: 数据好不好、要不要继续优化                           │
└──────────────────────────────────────────────────────────────┘
```

**职责划分：**

| 信息 | 谁记录 | 存在哪 | 原因 |
|------|--------|--------|------|
| 工具调用记录（谁调了什么） | MCP Server 审计 | `run_logs/tool_calls.jsonl` | 协议层职责 |
| 参数值（g=24.5） | 上级项目 db/ | `experiments.db` | 业务语义 |
| 测量结果（S11=-18.3dB） | 上级项目 db/ | `experiments.db` | 需要与目标关联 |
| 优化决策（"增大 g"） | 上级项目 db/ | `experiments.db` | 领域知识 |
| 收敛曲线 | 上级项目 db/ | `experiments.db` | 实验分析 |

**上级项目调用示例：**

```python
# 上级项目代码（非 cst_runtime）
from cst_runtime.lib.parameters import set_param
from cst_runtime.lib.solver import start, wait
from cst_runtime.lib.results import get_sparam
from db.experiment import ExperimentDB

db = ExperimentDB()
exp_id = db.create_experiment(task="s11_optimization", goal="S11 < -20dB at 10GHz")

for step in range(20):
    # 1. 设置参数
    g = optimizer.ask()
    set_param("C:\\model.cst", "g", g)

    # 2. 仿真
    start("C:\\model.cst")
    wait("C:\\model.cst")

    # 3. 读取结果
    result = get_sparam("C:\\model.cst", "1D Results\\S-Parameters\\S1,1")
    s11_min = min(result["ydata"], key=lambda d: 20*log10(abs(complex(d["real"], d["imag"]))))

    # 4. 记录到数据库（上级项目自己的逻辑）
    db.log_measurement(exp_id, step, param_g=g, s11_db=s11_min["db"], freq_ghz=s11_min["freq"])

    # 5. 优化决策
    optimizer.tell(g, s11_min["db"])
    db.log_decision(exp_id, step, action=f"tried g={g}", result=f"S11={s11_min['db']:.1f}dB")

db.set_status(exp_id, "completed")
```

---

## 五、Batch 1: P0 功能补全

### 5.1 WCS 坐标系操作

**新建文件**: `skills/cst-runtime-cli/scripts/cst_runtime/tools/wcs.py`

**MATLAB 原始逻辑** (`activateWCS.m`):
```matlab
function activateWCS(mws, origin, uvector, normal, name)
    wcs = invoke(mws, 'WCS');
    invoke(wcs, 'ActivateWCS', 'local');
    invoke(wcs, 'SetNormal', normal(1), normal(2), normal(3));
    invoke(wcs, 'SetOrigin', origin(1), origin(2), origin(3));
    invoke(wcs, 'SetUVector', uvector(1), uvector(2), uvector(3));
    invoke(wcs, 'SetName', name);
end
```

**Python 实现要点**:
```python
# tools/wcs.py
TOOL_DEFS = {
    "activate-wcs": {
        "category": "modeling",
        "risk": "write",
        "description": "Activate a local working coordinate system (WCS) for array modeling and unit cell placement.",
        "handler": "tool_activate_wcs",
        "json_schema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "name": {"type": "string", "description": "WCS name"},
                "origin": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
                "normal": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3,
                           "default": [0, 0, 1]},
                "uvector": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3,
                            "default": [1, 0, 0]},
            },
            "required": ["project_path", "name", "origin"],
        },
    },
    "deactivate-wcs": { ... },  # 切回全局坐标系
    "list-wcs": { ... },        # 列出已有 WCS
}

def tool_activate_wcs(args: dict) -> dict:
    vba = f"""
With WCS
    .ActivateWCS "local"
    .SetOrigin {origin[0]}, {origin[1]}, {origin[2]}
    .SetNormal {normal[0]}, {normal[1]}, {normal[2]}
    .SetUVector {uvector[0]}, {uvector[1]}, {uvector[2]}
    .SetName "{name}"
End With
"""
    # 通过 add_to_history 执行
```

### 5.2 Translate 变换

**修改文件**: `skills/cst-runtime-cli/scripts/cst_runtime/core/modeling.py`

**问题**: `transform_shape()` (line 802) 只支持 `mirror` 和 `rotate`，不支持 `translate`。

**MATLAB 原始逻辑** (`translationObj.m`):
```matlab
function translationObj(mws, objname, vector, copy, repeatcount, newcomponent)
    transform = invoke(mws, 'Transform');
    invoke(transform, 'Reset');
    invoke(transform, 'Name', objname);
    invoke(transform, 'Vector', vector(1), vector(2), vector(3));
    invoke(transform, 'MultipleObjects', copy);
    invoke(transform, 'MultipleCopyCount', repeatcount);
    invoke(transform, 'Translate');
    if newcomponent ~= ""
        invoke(transform, 'Destination', newcomponent);
    end
end
```

**修改内容**:

在 `transform_shape()` 的 `_TYPE_MAP` 中添加 translate:

```python
# modeling.py ~line 820
_TYPE_MAP = {
    "mirror": "Mirror",
    "rotate": "Rotate",
    "translate": "Translate",  # 新增
}
```

添加 translate 特有参数处理:

```python
if transform_type == "Translate":
    if vector is None:
        raise ValueError("translate requires 'vector' [x, y, z]")
    vba_lines.append(f'.Vector "{vector[0]}", "{vector[1]}", "{vector[2]}"')
    if destination:
        vba_lines.append(f'.Destination "{destination}"')
```

同时在 `tools/modeling.py` 的 `tool_transform_shape` 的 json_schema 中添加 `vector` 和 `destination` 字段。

### 5.3 Floquet 端口

**新建工具**: 添加到 `tools/modeling.py` 或新建 `tools/ports.py`

**MATLAB 原始逻辑** (`setFloquetPort.m`):
```matlab
function setFloquetPort(mws, zmin_modes, zmax_modes, ref_dist, pol_type)
    port = invoke(mws, 'Port');
    invoke(port, 'Reset');
    invoke(port, 'Floquet');
    invoke(port, 'SetDialogParameter', 'ZminModes', num2str(zmin_modes));
    invoke(port, 'SetDialogParameter', 'ZmaxModes', num2str(zmax_modes));
    invoke(port, 'SetDialogParameter', 'ZminReferenceDistance', num2str(ref_dist));
    invoke(port, 'SetDialogParameter', 'PolarizationType', pol_type);
    invoke(port, 'CreateFloquetPort');
end
```

**新增工具**:
```python
"define-floquet-port": {
    "category": "modeling",
    "risk": "write",
    "description": "Configure Floquet ports for periodic/metasurface unit cell simulation.",
    "handler": "tool_define_floquet_port",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string"},
            "zmin_modes": {"type": "integer", "default": 1},
            "zmax_modes": {"type": "integer", "default": 1},
            "zmin_reference_distance": {"type": "number", "default": 0},
            "zmax_reference_distance": {"type": "number", "default": 0},
            "polarization_type": {"type": "string", "enum": ["linear", "circular"], "default": "linear"},
        },
        "required": ["project_path"],
    },
}
```

### 5.4 逐面边界设置

**修改文件**: `core/modeling.py` 中 `define_boundary()`

**问题**: 现有 `define_boundary()` 对所有面设置同一类型，无法逐面控制。

**MATLAB 原始逻辑** (`setUnitBoundary.m`):
```matlab
function setUnitBoundary(mws, xmin_type, xmax_type, ymin_type, ymax_type, zmin_type, zmax_type)
    boundary = invoke(mws, 'Boundary');
    invoke(boundary, 'Xmin', xmin_type);  % "unit cell"
    invoke(boundary, 'Xmax', xmax_type);
    invoke(boundary, 'Ymin', ymin_type);
    invoke(boundary, 'Ymax', ymax_type);
    invoke(boundary, 'Zmin', zmin_type);  % "open"
    invoke(boundary, 'Zmax', zmax_type);
    invoke(boundary, 'ApplyInAllDirections', False);
    invoke(boundary, 'PeriodicUsePrimitive', False);
end
```

**新增工具**:
```python
"define-boundary-per-face": {
    "category": "project_ops",
    "risk": "write",
    "description": "Set boundary conditions per face for unit cell / periodic simulations.",
    "handler": "tool_define_boundary_per_face",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string"},
            "xmin": {"type": "string", "enum": ["electric", "magnetic", "open", "periodic", "unit cell"],
                     "default": "unit cell"},
            "xmax": {"type": "string", "default": "unit cell"},
            "ymin": {"type": "string", "default": "unit cell"},
            "ymax": {"type": "string", "default": "unit cell"},
            "zmin": {"type": "string", "default": "open"},
            "zmax": {"type": "string", "default": "open"},
            "periodic_angle": {"type": "number", "default": 0},
        },
        "required": ["project_path"],
    },
}
```

### 5.5 Arc 曲线

**新增到**: `tools/modeling.py`

**MATLAB 原始逻辑** (`defineArc.m`):
```matlab
function defineArc(mws, name, center, radius, startangle, endangle, segments)
    curve = invoke(mws, 'Curve');
    invoke(curve, 'Name', name);
    invoke(curve, 'InvokeCurve', 'Arc', ...
        center(1), center(2), center(3), ...
        radius, startangle, endangle, segments);
end
```

**新增工具**:
```python
"define-arc": {
    "category": "modeling",
    "risk": "write",
    "description": "Create an arc curve. Used for C-ring resonators and curved strips.",
    "handler": "tool_define_arc",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string"},
            "name": {"type": "string", "description": "Curve name"},
            "center": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3},
            "radius": {"type": "number"},
            "start_angle": {"type": "number", "description": "Degrees"},
            "end_angle": {"type": "number", "description": "Degrees"},
            "segments": {"type": "integer", "default": 0, "description": "0 = auto"},
            "component": {"type": "string", "default": "component1"},
        },
        "required": ["project_path", "name", "center", "radius", "start_angle", "end_angle"],
    },
}
```

### 5.6 组件删除

**新增到**: `tools/modeling.py`

```python
"delete-component": {
    "category": "modeling",
    "risk": "write",
    "description": "Delete an entire component folder and all solids within it.",
    "handler": "tool_delete_component",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string"},
            "component": {"type": "string", "description": "Component name to delete"},
        },
        "required": ["project_path", "component"],
    },
}
```

VBA:
```vba
Component.Delete "<component>"
```

### 5.7 阵列建模框架

**新建文件**: `skills/cst-runtime-cli/scripts/cst_runtime/tools/array.py`

**MATLAB 原始逻辑** (`arrayModeling.m` 核心):
```matlab
function arrayModeling(mws, codingMatrix, unitCellClass, dxdy, layers)
    [M, N] = size(codingMatrix);
    for layer = 1:layers
        for m = 1:M
            for n = 1:N
                code = codingMatrix(m, n);
                center = [(n-1)*dxdy, (m-1)*dxdy, (layer-1)*layerDist];
                name = sprintf("unit_%d_%d_%d", layer, m, n);
                unitCellClass.codeModeling(mws, code, center, name);
            end
        end
    end
end
```

**新增工具**:
```python
"build-coding-array": {
    "category": "modeling",
    "risk": "write",
    "description": "Build a coding metasurface array from a coding matrix. Places unit cells on a grid.",
    "handler": "tool_build_coding_array",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string"},
            "coding_matrix": {
                "type": "array",
                "items": {"type": "array", "items": {"type": "integer"}},
                "description": "2D matrix of unit cell codes, e.g. [[0,1],[1,0]]",
            },
            "unit_type": {"type": "string", "enum": ["c_ring", "cross", "custom"],
                          "description": "Unit cell geometry type"},
            "dx": {"type": "number", "description": "Unit cell spacing X (mm)"},
            "dy": {"type": "number", "description": "Unit cell spacing Y (mm)"},
            "layer_distance": {"type": "number", "default": 0, "description": "Z offset between layers"},
            "template_name": {"type": "string", "default": "unit",
                              "description": "Template component name for copy-translate"},
        },
        "required": ["project_path", "coding_matrix", "unit_type", "dx", "dy"],
    },
}
```

**fastArrayModeling** 实现策略:
1. 先在原点创建一个模板单元 (`codeModeling`)
2. 用 `Transform.Translate` 复制到所有位置（避免逐个建模，O(N) 次 VBA 调用 → O(1) 次）

---

## 六、Batch 2: P1 功能补全

### 6.1 程序化材料定义

**修改文件**: `tools/modeling.py`

**MATLAB 原始逻辑** (`defineMaterial.m`):
```matlab
function defineMaterial(mws, name, eps_r, mu_r, tan_d, tan_d_freq, transparency)
    material = invoke(mws, 'Material');
    invoke(material, 'Reset');
    invoke(material, 'Name', name);
    invoke(material, 'Epsilon', eps_r);
    invoke(material, 'Mue', mu_r);
    invoke(material, 'TanD', tan_d);
    invoke(material, 'TanDFreq', tan_d_freq);
    invoke(material, 'TanDGiven', 'True');
    invoke(material, 'Transparency', transparency);
    invoke(material, 'Create');
end
```

**新增工具**:
```python
"define-material": {
    "category": "modeling",
    "risk": "write",
    "description": "Create a material with inline properties (epsilon, mu, tan_d).",
    "handler": "tool_define_material",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string"},
            "name": {"type": "string"},
            "epsilon": {"type": "number", "default": 1.0},
            "mue": {"type": "number", "default": 1.0},
            "tan_d": {"type": "number", "default": 0},
            "tan_d_freq": {"type": "number", "default": 0},
            "transparency": {"type": "number", "default": 0},
        },
        "required": ["project_path", "name"],
    },
}
```

### 6.2 结果删除

```python
"delete-results": {
    "category": "simulation",
    "risk": "write",
    "description": "Delete all simulation results. Use before re-running to avoid stale data.",
    "handler": "tool_delete_results",
}
```

VBA: `Solver.DeleteResults`

### 6.3 结构重建

```python
"rebuild-structure": {
    "category": "project_ops",
    "risk": "write",
    "description": "Rebuild geometry from parameter table (RebuildOnParametricChange).",
    "handler": "tool_rebuild_structure",
}
```

VBA: `Application.RebuildOnParametricChange False, False` 或 `Application.Rebuild`

### 6.4 参数/材料存在检查

**修改文件**: `core/project.py` 和 `core/modeling.py`

```python
# project.py 新增
def does_parameter_exist(project, name: str) -> bool:
    count = project.model3d.get_number_of_parameters()
    for i in range(count):
        if project.model3d.get_parameter_name(i) == name:
            return True
    return False

# modeling.py 新增
def does_material_exist(project, name: str) -> bool:
    return project.model3d.material.is_available(name)
```

### 6.5 单元格参数化类

**新建文件**: `skills/cst-runtime-cli/scripts/cst_runtime/modules/unit_cells.py`

```python
from abc import ABC, abstractmethod

class UnitCellBase(ABC):
    """单元格参数化基类"""
    name: str
    codes: list[int]          # 支持的编码值
    params: dict              # 几何参数 LUT

    @abstractmethod
    def code_modeling(self, mws, code: int, center: tuple, name: str):
        """根据编码值创建单元格几何"""
        ...

class CRingCell(UnitCellBase):
    """C-ring (开口圆环) 单元格"""
    name = "c_ring"
    codes = [0, 1, 2, 3]  # 2-bit 编码
    params = {
        0: {"outer_r": 2.0, "gap_angle": 0},
        1: {"outer_r": 2.0, "gap_angle": 30},
        2: {"outer_r": 2.0, "gap_angle": 60},
        3: {"outer_r": 2.0, "gap_angle": 90},
    }

    def code_modeling(self, mws, code, center, name):
        p = self.params[code]
        # VBA: 创建圆环 → 切开口 → 放置到 center
        ...

class CrossCell(UnitCellBase):
    """I-shaped (十字) 单元格"""
    name = "cross"
    ...
```

### 6.6 S 参数频率插值

**修改文件**: `core/results.py`

```python
def get_sparam_at_freq(treepath: str, target_freq_ghz: float, run_id: int = -1) -> dict:
    """获取指定频率处的 S 参数（线性插值）"""
    data = get_1d_result(project_path, treepath, run_id)
    freqs = [d["frequency"] for d in data["ydata"]]
    reals = [d["real"] for d in data["ydata"]]
    imags = [d["imag"] for d in data["ydata"]]

    # 线性插值
    import numpy as np
    re_interp = np.interp(target_freq_ghz, freqs, reals)
    im_interp = np.interp(target_freq_ghz, freqs, imags)
    mag = np.sqrt(re_interp**2 + im_interp**2)
    phase = np.arctan2(im_interp, re_interp)

    return {
        "status": "success",
        "frequency_ghz": target_freq_ghz,
        "real": float(re_interp),
        "imag": float(im_interp),
        "magnitude": float(mag),
        "magnitude_db": float(20 * np.log10(max(mag, 1e-30))),
        "phase_rad": float(phase),
        "phase_deg": float(np.degrees(phase)),
    }
```

---

## 七、Batch 3: P2 功能补全

### 7.1 参数扫频 + LUT 构建

**新建文件**: `tools/sweep.py`

```python
"parameter-sweep": {
    "category": "simulation",
    "risk": "long-running",
    "description": "Run a 2D parameter sweep and build a lookup table (LUT) of S-parameters.",
    "handler": "tool_parameter_sweep",
    "json_schema": {
        "type": "object",
        "properties": {
            "project_path": {"type": "string"},
            "param1_name": {"type": "string"},
            "param1_values": {"type": "array", "items": {"type": "number"}},
            "param2_name": {"type": "string"},
            "param2_values": {"type": "array", "items": {"type": "number"}},
            "result_treepath": {"type": "string", "default": "1D Results\\S-Parameters\\S1,1"},
            "target_freq_ghz": {"type": "number"},
            "output_path": {"type": "string", "description": "LUT output .npz file path"},
        },
        "required": ["project_path", "param1_name", "param1_values", "output_path"],
    },
}
```

实现: 遍历 (param1, param2) 组合 → prepare-experiment → run-experiment → 提取 S 参数 → 存入 .npz

### 7.2 FD 求解器配置

```python
"define-fd-solver": {
    "category": "simulation",
    "risk": "write",
    "description": "Configure frequency domain solver with stimulation port and mode.",
    "handler": "tool_define_fd_solver",
}
```

VBA:
```vba
With FDSolver
    .Stimulation "1", "1"
    .SetAccuracy "1e-6"
    .Start
End With
```

---

## 八、MCP Server 实施方案

### 8.1 文件结构

```
CST_MCP/
├── mcp_server/
│   ├── __init__.py
│   ├── server.py          ← FastMCP 入口
│   ├── adapter.py         ← TOOL_DEFS → MCP tool 自动转换
│   └── config.py          ← 配置
├── skills/cst-runtime-cli/scripts/cst_runtime/  ← 现有代码（零修改）
└── pyproject.toml         ← 新增 mcp 依赖
```

### 8.2 `pyproject.toml` 变更

在项目根目录新建或修改 `pyproject.toml`:

```toml
[project]
name = "cst-mcp"
version = "1.0.0"
requires-python = ">=3.13"
dependencies = [
    "mcp[cli]>=1.20",
]

[project.scripts]
cst-mcp = "mcp_server.server:main"
```

### 8.3 `mcp_server/adapter.py` — 自动注册核心

两种注册策略可选（推荐策略 A）：

**策略 A：从 `lib/` 层注册（推荐）**

直接调用 `lib/` 层的公开函数，获得简洁的参数签名和异常处理：

```python
"""adapter.py — 从 cst_runtime.lib 注册 MCP tools"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any

# 将 cst_runtime 加入 sys.path
_CRT_SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "cst-runtime-cli" / "scripts"
if str(_CRT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_CRT_SCRIPTS))

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError


def _wrap(fn, name: str, description: str, risk: str = "read"):
    """将 lib 函数包装为 MCP tool handler"""
    import inspect
    sig = inspect.signature(fn)

    async def handler(**kwargs) -> str:
        try:
            result = fn(**kwargs)
            if isinstance(result, dict) and result.get("status") == "error":
                raise ToolError(result.get("message", "Unknown error"))
            return json.dumps(result, ensure_ascii=False, indent=2, default=str)
            if not isinstance(result, str):
                return json.dumps(result, ensure_ascii=False, indent=2, default=str)
            return result
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"[{type(e).__name__}] {e}")

    handler.__name__ = name.replace("-", "_")
    risk_tag = {"read": "[READ]", "write": "[WRITE]", "session": "[SESSION]"}.get(risk, f"[{risk.upper()}]")
    handler.__doc__ = f"{risk_tag} {description}"
    return handler


def register_all_tools(mcp: FastMCP) -> int:
    """从 cst_runtime.lib 自动注册所有工具到 MCP server"""
    from cst_runtime.lib import (
        session, parameters, geometry, materials, solver,
        results, farfield, boundary, port, monitors,
    )

    # 工具定义: (lib_module, func_name, mcp_tool_name, description, risk)
    TOOL_SPECS = [
        # session
        (session, "open_project", "open-project", "Open a CST project", "session"),
        (session, "close_project", "close-project", "Close a CST project", "session"),
        (session, "inspect", "inspect-session", "Inspect CST environment state", "read"),
        (session, "list_open", "list-open-projects", "List all open CST projects", "read"),
        # parameters
        (parameters, "list_params", "list-parameters", "List all parameters with values", "read"),
        (parameters, "get_param", "get-parameter", "Get a single parameter value", "read"),
        (parameters, "set_param", "set-parameter", "Set a parameter value", "write"),
        (parameters, "param_exists", "parameter-exists", "Check if a parameter exists", "read"),
        # geometry
        (geometry, "brick", "define-brick", "Create a brick solid", "write"),
        (geometry, "cylinder", "define-cylinder", "Create a cylinder solid", "write"),
        (geometry, "boolean_add", "boolean-add", "Boolean add two solids", "write"),
        (geometry, "boolean_subtract", "boolean-subtract", "Boolean subtract", "write"),
        (geometry, "delete_entity", "delete-entity", "Delete a solid entity", "write"),
        (geometry, "delete_component", "delete-component", "Delete entire component folder", "write"),
        (geometry, "translate", "translate-shape", "Translate (move) a solid", "write"),
        (geometry, "rotate", "rotate-shape", "Rotate a solid", "write"),
        (geometry, "activate_wcs", "activate-wcs", "Activate local WCS", "write"),
        (geometry, "deactivate_wcs", "deactivate-wcs", "Switch back to global WCS", "write"),
        # materials
        (materials, "define", "define-material", "Create material with inline properties", "write"),
        (materials, "define_from_mtd", "define-material-from-mtd", "Load material from .mtd file", "write"),
        (materials, "list_materials", "list-materials", "List available materials", "read"),
        # solver
        (solver, "set_frequency_range", "define-frequency-range", "Set solver frequency range", "write"),
        (solver, "start", "start-simulation", "Start solver (blocking)", "session"),
        (solver, "start_async", "start-simulation-async", "Start solver (non-blocking)", "session"),
        (solver, "wait", "wait-simulation", "Wait for solver to finish", "session"),
        (solver, "is_running", "is-simulation-running", "Check if solver is running", "read"),
        (solver, "stop", "stop-simulation", "Stop the solver", "session"),
        (solver, "rebuild", "rebuild-structure", "Rebuild geometry from parameters", "write"),
        (solver, "delete_results", "delete-results", "Delete all simulation results", "write"),
        # results
        (results, "get_sparam", "get-1d-result", "Read S-parameter data", "read"),
        (results, "get_sparam_at_freq", "get-sparam-at-freq", "Read S-param at specific frequency", "read"),
        (results, "get_2d_field", "get-2d-result", "Read 2D field data", "read"),
        (results, "list_items", "list-result-items", "List available result items", "read"),
        (results, "list_runs", "list-run-ids", "List simulation run IDs", "read"),
        (results, "export_all", "export-run-results", "Export all results for a run", "read"),
        # farfield
        (farfield, "export_grid", "export-farfield-grid", "Export farfield grid data", "read"),
        (farfield, "export_cut", "export-farfield-cut", "Export farfield cut data", "read"),
        (farfield, "list_monitors", "inspect-farfield-monitors", "List farfield monitors", "read"),
        # boundary
        (boundary, "set_all", "define-boundary", "Set all faces to same boundary type", "write"),
        (boundary, "set_per_face", "define-boundary-per-face", "Set boundary per face", "write"),
        (boundary, "set_unit_cell", "define-unit-cell-boundary", "Set unit cell boundary", "write"),
        # port
        (port, "define_floquet", "define-floquet-port", "Define Floquet port", "write"),
        # monitors
        (monitors, "set_farfield", "set-farfield-monitor", "Set farfield monitor", "write"),
        (monitors, "set_efield", "set-efield-monitor", "Set E-field monitor", "write"),
        (monitors, "set_probe", "set-probe", "Set a probe", "write"),
        (monitors, "delete_probe", "delete-probe", "Delete a probe", "write"),
    ]

    registered = 0
    for mod, func_name, mcp_name, desc, risk in TOOL_SPECS:
        fn = getattr(mod, func_name, None)
        if fn is None:
            continue
        tool_fn = _wrap(fn, mcp_name, desc, risk)
        mcp.tool(name=mcp_name, description=tool_fn.__doc__)(tool_fn)
        registered += 1

    return registered
```

**策略 B：从 `tools/` 层注册（兼容现有 113+ 工具）**

如果 `lib/` 层尚未实现，可先用 `tools/` 层的 TOOL_DEFS 自动注册。代码见下方折叠块：

<details>
<summary>策略 B 代码（点击展开）</summary>

```python
def register_all_tools_from_cli(mcp: FastMCP) -> int:
    """从 cst_runtime.tools TOOL_DEFS 自动注册（兼容模式）"""
    from cst_runtime.tools import all_defs
    from cst_runtime.cli.dispatch import _HANDLER_MAP

    registered = 0
    for name, defn in sorted(all_defs().items()):
        handler_key = defn.get("handler", "")
        handler_fn = _HANDLER_MAP.get(handler_key)
        if handler_fn is None:
            continue

        risk = defn.get("risk", "read")
        category = defn.get("category", "")
        desc = defn.get("description", "")
        risk_tag = {"read": "[READ]", "write": "[WRITE]", "session": "[SESSION]",
                     "long-running": "[LONG-RUNNING]"}.get(risk, f"[{risk.upper()}]")
        description = f"{risk_tag} {desc}\nCategory: {category}"

        def make_handler(fn, tool_name):
            def handler(**kwargs) -> str:
                from cst_runtime.cli.dispatch import _invoke_tool
                result = _invoke_tool(tool_name, dict(kwargs))
                if result.get("status") == "error":
                    raise ToolError(f"[{result.get('error_type','')}] {result.get('message','')}")
                return json.dumps(result, ensure_ascii=False, indent=2, default=str)
            handler.__name__ = tool_name.replace("-", "_")
            handler.__doc__ = description
            return handler

        mcp.tool(name=name, description=description)(make_handler(handler_fn, name))
        registered += 1

    return registered
```

</details>

### 8.4 `mcp_server/server.py` — 入口

```python
"""server.py — CST Runtime MCP Server"""
from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from .adapter import register_all_tools

mcp = FastMCP(
    "cst-runtime",
    instructions=(
        "CST Studio Suite automation server. "
        "113+ tools for electromagnetic simulation: modeling, solver control, "
        "results extraction, farfield analysis, optimization. "
        "Tools tagged with [WRITE] modify CST projects; [READ] tools are safe. "
        "Always run 'health-check' first. "
        "Use 'prepare-experiment' + 'run-experiment' pipeline for parametric sweeps."
    ),
)

_COUNT = register_all_tools(mcp)


def main():
    import sys
    print(f"CST Runtime MCP Server: {_COUNT} tools registered", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

### 8.5 `mcp_server/__init__.py`

```python
"""CST Runtime MCP Server"""
```

### 8.6 运行方式

```bash
# 直接运行 (stdio)
uv run python -m mcp_server

# MCP Inspector 调试
uv run mcp dev mcp_server/server.py

# 安装到 Claude Desktop (可选)
uv run mcp install mcp_server/server.py --name "CST Runtime"
```

### 8.7 MCP Resources / Prompts 说明

**MCP Resources** = 让 LLM 读取的数据源（类似 GET 请求）。例如 `cst://workspace/status` 返回工作区状态。当前工具的 `health-check` 和 `usage-guide` 已覆盖此功能，**不需要单独实现**。

**MCP Prompts** = 预设的提示词模板。例如 "帮我做超表面单元扫参" 展开为完整的操作步骤指导。可后续添加，**当前阶段不需要**。

### 8.8 长时间仿真：非阻塞工具设计（方案 A）

CST 仿真耗时 1 分钟到数小时不等，MCP 工具调用默认超时 60-120 秒。阻塞式工具必然超时。

**方案：拆分为非阻塞工具，Agent 自己编排轮询循环。**

#### 8.8.1 问题

```
CST 仿真耗时:
  简单结构:   1-5 分钟
  复杂结构:   30 分钟 - 2 小时
  大型阵列:   数小时

MCP 工具调用超时:
  默认:       60-120 秒
  Agent 会话: 几分钟到几十分钟

结论: 单个阻塞式 MCP tool 调用必然超时
```

#### 8.8.2 现有代码基础

`core/simulation.py` 已有非阻塞模式：

| 函数 | 行为 | 返回 |
|------|------|------|
| `start_simulation(mode="async")` | 启动求解器，**立即返回** | `{status: "success"}` |
| `is_simulation_running()` | 查询状态，**立即返回** | `{running: true/false}` |
| `start_simulation(mode="blocking")` | 阻塞直到完成 | ⚠️ 不适合 MCP |

`cli/pipelines/impl.py` 中的 `run-experiment` 流水线已使用异步模式：

```
start_simulation_async → wait_simulation(poll loop) → close modeler → export results
```

#### 8.8.3 MCP 工具拆分方案

**不暴露阻塞工具，只暴露非阻塞工具：**

| MCP Tool | 对应 lib 函数 | 行为 | 耗时 |
|----------|-------------|------|------|
| `start-simulation` | `solver.start_async()` | 启动仿真，立即返回 | < 1s |
| `sim-status` | `solver.is_running()` | 查询是否在运行 | < 0.1s |
| `get-1d-result` | `results.get_sparam()` | 读取 S 参数（离线） | < 1s |
| `optuna-ask` | `optimization.ask()` | 获取下一组参数 | < 0.1s |
| `optuna-tell` | `optimization.tell()` | 回报结果 | < 0.1s |
| `optuna-best` | `optimization.best()` | 获取最优参数 | < 0.1s |

**不暴露的函数（Agent 自己实现逻辑）：**

| 函数 | 原因 |
|------|------|
| `solver.wait()` | 阻塞式轮询，Agent 自己用 `sim-status` 轮询 |

#### 8.8.4 Agent 编排的优化循环

```
Agent 通过 MCP 调用的完整序列:

  1. optuna-ask        → {g: 24.5, patch_w: 8.2}        [0.1s]
  2. set-parameter     → g = 24.5                         [0.1s]
  3. set-parameter     → patch_w = 8.2                    [0.1s]
  4. start-simulation  → {status: "success"}              [0.5s]
  ┌── Agent 自己等待 30 秒（或做其他推理） ──────────────┐
  │ 5. sim-status      → {running: true}                 [0.1s]  │
  │    Agent: 继续等待...                                    │
  │ 6. sim-status      → {running: true}                 [0.1s]  │
  │    Agent: 继续等待...                                    │
  │ 7. sim-status      → {running: false}                [0.1s]  │
  └─────────────────────────────────────────────────────────────┘
  8. get-1d-result     → {ydata: [...], s11_min: -18.3}  [0.5s]
  9. optuna-tell       → trial #5, value = -18.3         [0.1s]
  10. optuna-best      → {best: -22.1, params: {g: 23.0}} [0.1s]
  ┄┄ Agent 分析: "S11=-18.3dB，未达目标 -20dB，继续" ┄┄
  11. 回到步骤 1，重复
```

每步都是毫秒级返回，**永不超时**。

#### 8.8.5 Agent 等待策略

Agent 在轮询间隔可以做以下事情：

```python
# Agent 内部推理逻辑（不是 MCP tool，是 LLM 的思维过程）

# 策略 1: 简单等待
start_simulation("C:\\model.cst")
time.sleep(30)  # Agent 可以通知用户"仿真中，请等待"
status = sim_status("C:\\model.cst")

# 策略 2: 带超时的轮询
for i in range(60):  # 最多等 60 次 × 30 秒 = 30 分钟
    time.sleep(30)
    if not sim_status("C:\\model.cst")["running"]:
        break
    # Agent 可以在此期间:
    # - 向用户报告进度
    # - 分析之前的仿真日志
    # - 准备下一步的参数策略

# 策略 3: 并行优化（多结构同时仿真）
# 如果有多个 CST 工程，Agent 可以:
start_simulation("C:\\model_v1.cst")
start_simulation("C:\\model_v2.cst")
# 然后交替检查两个工程的状态
```

#### 8.8.6 为什么不引入端口监听/Webhook

| 方案 | 优点 | 缺点 | 推荐 |
|------|------|------|------|
| **A. 非阻塞工具 + Agent 轮询** | 简单、现有代码支持、Agent 可做其他事 | Agent 需要自己编排循环 | ✅ 首选 |
| B. MCP Progress Reporting | 一个工具搞定 | 阻塞 Agent、无法做其他事 | 可选 |
| C. 端口监听/Webhook | 完全异步 | 需要额外服务、安全风险、部署复杂 | ❌ |

端口监听**不需要**，因为：
1. MCP stdio 传输不存在 HTTP 连接超时问题
2. Agent 可以在轮询间隔做其他推理
3. 增加了安全风险和部署复杂度
4. 现有 `start_simulation_async` + `is_simulation_running` 已经解决了核心问题

#### 8.8.7 lib/solver.py 中的工具注册

```python
# lib/solver.py
def start_async(path: str) -> dict:
    """启动仿真，立即返回。"""
    result = _start_simulation(path, mode="async")
    return {"status": "success", "message": "simulation started"}

def is_running(path: str) -> bool:
    """查询仿真是否在运行。"""
    result = _is_simulation_running(path)
    return result.get("running", False)

def wait(path: str, timeout: int = 3600, interval: int = 10) -> dict:
    """轮询等待完成。仅供内部使用，不暴露为 MCP tool。"""
    ...
```

```python
# adapter.py — 注册时排除 wait
TOOL_SPECS = [
    (solver, "start_async", "start-simulation", "Start solver, return immediately", "session"),
    (solver, "is_running",  "sim-status",       "Check if solver is running",       "read"),
    (solver, "stop",        "stop-simulation",   "Stop the solver",                  "session"),
    (solver, "delete_results", "delete-results", "Delete all results",               "write"),
    (solver, "get_solver_type", "get-solver-type", "Get solver type",                "read"),
    # wait 不注册为 MCP tool
]
```

---

## 九、CST 2022 兼容适配方案

### 9.1 新建 `core/compat.py`

```python
"""core/compat.py — CST 2022/2026 版本兼容层"""
from __future__ import annotations
import warnings
from typing import Any

_CST_MAJOR = 0
_CST_MINOR = 0
_detected = False


def detect_version() -> tuple[int, int]:
    """检测已连接的 CST 版本"""
    global _CST_MAJOR, _CST_MINOR, _detected
    if _detected:
        return _CST_MAJOR, _CST_MINOR
    try:
        import cst.interface
        de = cst.interface.DesignEnvironment()
        ver = getattr(de, "version", "0.0.0")
        parts = ver.split(".")
        _CST_MAJOR = int(parts[0])
        _CST_MINOR = int(parts[1]) if len(parts) > 1 else 0
    except Exception:
        pass
    _detected = True
    return _CST_MAJOR, _CST_MINOR


def is_2022_or_later() -> bool:
    major, _ = detect_version()
    return major >= 2022


def is_2026_or_later() -> bool:
    major, minor = detect_version()
    return major >= 2026


def safe_connect_to_any():
    """兼容 CST 2022/2026 的 DesignEnvironment 连接"""
    import cst.interface
    de_cls = cst.interface.DesignEnvironment

    if hasattr(de_cls, "connect_to_any"):
        try:
            return de_cls.connect_to_any()
        except Exception:
            pass

    if hasattr(de_cls, "connect_to_any_or_new"):
        try:
            return de_cls.connect_to_any_or_new()
        except Exception:
            pass

    # CST 2022 回退: 直接构造
    return de_cls()


def safe_running_design_environments() -> list[int]:
    """兼容 CST 2022/2026 的进程列表"""
    import cst.interface
    if hasattr(cst.interface, "running_design_environments"):
        try:
            return cst.interface.running_design_environments()
        except Exception:
            pass
    return []


def safe_list_open_projects(de) -> list[str]:
    """兼容 CST 2022/2026 的项目列表"""
    if hasattr(de, "list_open_projects"):
        try:
            return de.list_open_projects()
        except Exception:
            pass
    return []


def safe_quiet_mode(de):
    """兼容 CST 2022/2026 的静默模式"""
    if hasattr(de, "quiet_mode_enabled"):
        try:
            return de.quiet_mode_enabled()
        except Exception:
            pass
    # CST 2022 回退: 无静默模式支持
    class _NoOp:
        def __enter__(self): return self
        def __exit__(self, *a): pass
    return _NoOp()
```

### 9.2 修改 `core/identity.py`

将 `DesignEnvironment.connect_to_any()` 替换为 `compat.safe_connect_to_any()`:
```python
# identity.py
from . import compat

# 原: de = cst.interface.DesignEnvironment.connect_to_any()
# 改: de = compat.safe_connect_to_any()
```

### 9.3 修改 `core/__init__.py`

在安装路径搜索中添加 CST 2022:
```python
_CST_SEARCH_PATHS = [
    r"C:\Program Files\CST Studio Suite 2026\AMD64\python_cst_libraries",
    r"C:\Program Files\CST Studio Suite 2025\AMD64\python_cst_libraries",
    r"C:\Program Files\CST Studio Suite 2022\AMD64\python_cst_libraries",  # 新增
    r"C:\Program Files (x86)\CST Studio Suite 2026\AMD64\python_cst_libraries",
    r"C:\Program Files (x86)\CST Studio Suite 2022\AMD64\python_cst_libraries",  # 新增
]
```

### 9.4 `health-check` 增加版本检测

在 `tools/workspace.py` 的 `tool_health_check` 中添加:
```python
from ..core import compat
major, minor = compat.detect_version()
if major < 2022:
    result["warnings"] = result.get("warnings", [])
    result["warnings"].append(f"CST version {major}.{minor} may not be fully supported")
if major < 2026:
    result["compat_notes"] = "Running in CST 2022 compatibility mode"
```

---

## 十、文件变更清单

### 10.1 新建文件

| 文件 | 说明 | Batch |
|------|------|-------|
| **lib/ 层（标准库风格公开 API）** | | |
| `cst_runtime/lib/__init__.py` | 统一导出所有 lib 模块 | Batch 1 |
| `cst_runtime/lib/session.py` | 会话管理 API | Batch 1 |
| `cst_runtime/lib/parameters.py` | 参数操作 API | Batch 1 |
| `cst_runtime/lib/geometry.py` | 几何建模 API | Batch 1 |
| `cst_runtime/lib/materials.py` | 材料管理 API | Batch 2 |
| `cst_runtime/lib/mesh.py` | 网格设置 API | Batch 2 |
| `cst_runtime/lib/boundary.py` | 边界条件 API | Batch 1 |
| `cst_runtime/lib/port.py` | 端口配置 API | Batch 1 |
| `cst_runtime/lib/solver.py` | 求解器控制 API | Batch 1 |
| `cst_runtime/lib/monitors.py` | 监视器管理 API | Batch 1 |
| `cst_runtime/lib/results.py` | 结果读取 API | Batch 1 |
| `cst_runtime/lib/farfield.py` | 远场操作 API | Batch 1 |
| `cst_runtime/lib/optimization.py` | 优化 API | Batch 3 |
| `cst_runtime/lib/array.py` | 阵列建模 API | Batch 1 |
| `cst_runtime/lib/unit_cells.py` | 单元格参数化类 | Batch 2 |
| **MCP Server** | | |
| `mcp_server/__init__.py` | MCP server 包 | MCP |
| `mcp_server/server.py` | FastMCP 入口 | MCP |
| `mcp_server/adapter.py` | lib → MCP tool 自动注册 | MCP |
| `mcp_server/config.py` | MCP 配置 | MCP |
| **兼容层** | | |
| `cst_runtime/core/compat.py` | CST 版本兼容层 | 兼容 |
| **其他** | | |
| `docs/implementation-plan.md` | 本文档 | — |
| `pyproject.toml` (根目录) | MCP server 依赖 | MCP |

### 10.2 修改文件

| 文件 | 修改内容 | Batch |
|------|---------|-------|
| `core/modeling.py` | transform_shape 添加 translate；新增 define_arc, delete_component | Batch 1 |
| `core/project.py` | 新增 does_parameter_exist | Batch 2 |
| `core/results.py` | 新增 get_sparam_at_freq | Batch 2 |
| `core/__init__.py` | 添加 CST 2022 搜索路径 | 兼容 |
| `core/identity.py` | 使用 compat 层替换直接 API 调用 | 兼容 |
| `tools/modeling.py` | 新增 TOOL_DEFS（作为 lib 层的 CLI 前端） | Batch 1+2 |
| `tools/simulation.py` | 新增 delete-results, rebuild-structure | Batch 2 |
| `tools/__init__.py` | 注册新模块的 TOOL_DEFS | Batch 1+2+3 |
| `tools/workspace.py` | health-check 增加版本检测 | 兼容 |

---

## 十一、测试计划

### 11.1 MCP Server 测试

| 测试项 | 方法 | 判定标准 |
|--------|------|---------|
| 工具注册数量 | `mcp dev` 启动后检查 | ≥ 113 个工具 |
| 工具描述格式 | 检查 description 含 [READ]/[WRITE] 标签 | 所有工具均有标签 |
| 参数 schema | 调用 `list-tools` 检查 inputSchema | 与 TOOL_DEFS json_schema 一致 |
| 只读工具调用 | 调用 `health-check`, `list-tools` | 返回 JSON，无异常 |
| 写工具错误处理 | 未初始化工作区时调用 `change-parameter` | ToolError 含明确提示 |
| stdio 通信 | MCP Inspector 连接测试 | 双向通信正常 |

### 11.2 新增工具测试

| 测试项 | 方法 | 判定标准 |
|--------|------|---------|
| activate-wcs | 调用后检查 VBA 历史 | WCS 命令写入正确 |
| translate 变换 | 创建 brick → translate → 检查位置 | 位置偏移正确 |
| define-floquet-port | 调用后检查端口设置 | Floquet 端口存在 |
| define-arc | 创建 arc 曲线 | 曲线在 CST 中可见 |
| delete-component | 创建组件 → 删除 → 检查 | 组件不存在 |
| define-material | 定义 eps_r=10 材料 | 材料属性正确 |
| delete-results | 有结果时调用 | 结果被清除 |
| rebuild-structure | 修改参数后调用 | 几何更新 |

### 11.3 CST 2022 兼容测试

| 测试项 | 方法 | 判定标准 |
|--------|------|---------|
| 版本检测 | 调用 `compat.detect_version()` | 返回 (2022, x) |
| 连接方式 | 调用 `safe_connect_to_any()` | 成功连接 CST 2022 |
| 进程列表 | 调用 `safe_running_design_environments()` | 不抛异常 |
| 安装路径 | `health-check` 找到 CST 2022 | 路径正确 |
| VBA 兼容 | 建模 + 仿真全流程 | PBAVersion 不报错 |
| results 兼容 | 读取 S 参数 | 数据正确 |

### 11.4 集成测试

| 测试项 | 方法 | 判定标准 |
|--------|------|---------|
| MCP → 工具 → CST 全链路 | 通过 MCP 调用 inspect-project | 返回项目参数列表 |
| 阵列建模 | coding_matrix 2×2 → build-coding-array | CST 中 4 个单元存在 |
| 参数扫频 | 2×2 参数空间 → parameter-sweep | LUT .npz 文件生成 |
| 端到端仿真 | prepare-experiment → run-experiment → get-1d-result | S 参数数据正确 |
