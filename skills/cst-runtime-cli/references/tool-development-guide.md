# CST Runtime CLI — 工具开发集成指南

面向 agent 或开发者。覆盖从查阅 VBA 文档到 CLI 上线的完整流程（手工扩展路径；TOML 代码生成器已移除，其输入定义从未入库）。

---

## 目录

1. [前置知识](#1-前置知识)
2. [开发流程总览](#2-开发流程总览)
3. [Step 1: 查阅 VBA 对象文档](#3-step-1-查阅-vba-对象文档)
4. [Step 2: 实现工具函数](#4-step-2-实现工具函数)
5. [Step 3: 注册 TOOL_DEFS 与 JSON Schema](#5-step-3-注册-tool_defs-与-json-schema)
6. [Step 4: 在真实 CST 上测试](#6-step-4-在真实-cst-上测试)
7. [Step 5: 验证暴露面与治理标记](#7-step-5-验证暴露面与治理标记)
8. [Step 6: 上线归档](#8-step-6-上线归档)
9. [测试脚本模板](#9-测试脚本模板)
10. [常见问题](#10-常见问题)

---

## 1. 前置知识

### 两个入口点

| 入口 | 方式 | 用途 |
|------|------|------|
| 直接 COM | `project.modeler.StoreDoubleParameter("w", 10)` | 参数读写、查询、仿真控制 |
| VBA 字符串 | `project.modeler.add_to_history("名称", "VBA 代码")` | 建模、端口、监视器、求解器配置 |

### 三个文档来源

| 来源 | 位置 | 内容 |
|------|------|------|
| **VBA_3D HTML**（官方） | `<CST_INSTALL>\Online Help\mergedProjects\VBA_3D\` | 150+ 对象的完整方法签名、参数类型、枚举值 |
| **官方 API 参考** | `devkit/references/vba-official-reference.md`、`cst-official-api-reference.md` | 整理好的 VBA/CST Python API 速查 |
| **cst_runtime 源码** | `scripts/cst_runtime/tools/*.py`、`core/*.py` | 生产环境验证过的 VBA 拼装模式 |

### 架构层次

```
VBA_3D HTML 方法签名 → tools/<domain>.py（TOOL_DEFS + handler 函数）
                                   ↓
                    cst_runtime.api.registry（统一 Registry，动态清册）
                                   ↓
                    CLI dispatch / MCP（仅 exposure=agent 的工具暴露）
```

---

## 2. 开发流程总览

```
查阅 VBA_3D HTML → 实现 handler + TOOL_DEFS → 离线合约测试 → 部署到测试区 → CST 实测
                                                                    ↓
                                                        PASS? → 注册/验证暴露面 → 提交
                                                                    ↓
                                                        FAIL? → 修实现 → 重跑
```

**核心原则：**
- 只加优化流程相关方法，不全量照抄官方文档
- 非核心参数加默认值，不暴露给 agent
- 方法名和枚举值必须和 VBA_3D HTML 一致
- 工具不直接 import `core` 之外的跨层模块；`lib` 是唯一稳定公开 API

---

## 3. Step 1: 查阅 VBA 对象文档

### 3.1 离线 HTML（推荐）

用浏览器直接打开，不需启动 CST（以 CST 2022 安装路径为例）：

```
# 对象索引（50+ 子目录入口）
<CST_INSTALL>\Online Help\mergedProjects\VBA_3D\index.htm

# 对象树总览
<CST_INSTALL>\Online Help\mergedProjects\VBA_3D\special_vbaobjects\special_vbaobjects_vbaobjects.htm

# 基本实体
<CST_INSTALL>\Online Help\mergedProjects\VBA_3D\common_vbabasicsolids\

# 导入导出
<CST_INSTALL>\Online Help\mergedProjects\VBA_3D\common_vbaimpexp\

# 后处理
<CST_INSTALL>\Online Help\mergedProjects\VBA_3D\special_vbapostproc\

# 求解器
<CST_INSTALL>\Online Help\mergedProjects\VBA_3D\special_vbasolver\
```

### 3.2 核对清单

对每个 VBA 对象逐个核对：
- [ ] 方法名是否与 HTML 文档一致
- [ ] 参数类型是否正确（str / float / int / bool / enum）
- [ ] 枚举值是否完整且值正确
- [ ] 哪些方法是优化流程核心需要的
- [ ] 哪些方法可以加默认值

### 3.3 在线镜像（备用）

CST 2013 版对象树，与新版基本兼容：
- `http://www.mweda.com/cst/cst2013/mergedProjects/VBA_Help_MWS/special_vbaobjects/special_vbaobjects_vbaobjects.htm`

---

## 4. Step 2: 实现工具函数

### 4.1 文件位置

按域选择或新建 `scripts/cst_runtime/tools/<domain>.py`（如 `modeling.py`、`simulation.py`、`em_setup.py`）。

### 4.2 handler 函数约定

- 签名统一为 `def tool_xxx(args: dict) -> dict`，由原子层把校验后的参数透传。
- 参数模板中 `{param}` 占位符替代硬编码值，例如：

```python
def tool_define_monitor(args: dict) -> dict:
    return _ms.define_monitor(
        name=str(args.get("name", "")),
        field_type=str(args.get("field_type", "Efield")),
        freq=float(args.get("freq", 10.0)),
    )
```

### 4.3 VBA 拼装规则

| 参数类型 | Python 传入 | VBA 输出 | 引号 |
| -------- | ----------- | -------- | ---- |
| str      | `"brick1"` | `"brick1"` | 加 |
| float    | `10.0`    | `10.0`   | 不加 |
| int      | `5`       | `5`      | 不加 |
| bool     | `True`    | `True`   | 不加 |
| enum     | `FieldType.EFIELD` | `"Efield"` | 加（`.value`） |

### 4.4 关键规则

| 规则 | 说明 |
|------|------|
| 返回值 | 必须是可 JSON 序列化的 `OperationResult` 字典（`{status, message, ...}`），零异常控制流 |
| 守卫 | 改参未重建、跨 session 混用等已知陷阱由守卫层拦截，工具层不做手工判断 |
| 默认值 | 新参数默认值 = 旧硬编码值，保证向后兼容 |
| 版本差异 | CST 2022 不支持的调用走 `core/compatibility/` 探测，返回 `unsupported_feature`，不得静默降级 |

---

## 5. Step 3: 注册 TOOL_DEFS 与 JSON Schema

在域模块底部定义 `TOOL_DEFS` 并调用注册（模式见 `tools/modeling.py`）：

```python
TOOL_DEFS = {
    "define-monitor": {
        "category": "em_setup",
        "risk": "write",
        "description": "定义场监视器；CST 2022 仅支持单频。",
        "handler": "tool_define_monitor",
        "json_schema": {
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "minLength": 1},
                "name": {"type": "string", "minLength": 1},
                "field_type": {
                    "type": "string",
                    "enum": ["Efield", "Hfield", "Farfield"],
                    "default": "Efield",
                },
                "freq": {"type": "number", "default": 10.0},
            },
            "required": ["project_path", "name"],
        },
    },
}

from . import _register_tool_defs
_register_tool_defs(TOOL_DEFS)
```

### Schema 规则

- 参数类型用 `number`（非 `integer`），布尔用 `"boolean"`
- `default` 字段必填（保证 agent 知道可选参数的存在）
- `description` 描述功能而非实现
- 未知字段默认拒绝（`additionalProperties: false`），避免拼错参数被静默忽略
- handler 名必须能在 `api/atomic.py` 的 handler map 中解析，否则 `build_tools` 直接报错

---

## 6. Step 4: 在真实 CST 上测试

### 测试体系

分层测试命令与门控见 [docs/testing.md](../../docs/testing.md)：

| 层 | 触发时机 | 命令 |
|----|---------|------|
| **离线单元测试** | 每次改代码后 | `.venv\Scripts\python.exe -m pytest -q -m "not subprocess and not worker_proxy"` |
| **真机集成测试** | 涉及真实 CST 行为时 | `.venv\Scripts\python.exe -m pytest -q -s --run-cst -m "cst_integration and not cst_solver"` |

真机成功路径禁止 mock；`test_cst_test_policy.py` 自动检查这一规则。

### 新工具验证（额外层）

新工具上线前，在测试区对真实 CST 逐工具验证。**每个工具一个独立 run**，路径遵循标准结构：

```
<test_workspace>\
  refs\ref_0\ref_0.cst                 ← 基准工程（只读）
  tasks\task_test_xxx\
    runs\
      run_001\
        projects\working.cst            ← 测试工程（save=True）
        summary.md                       ← 记录操作和结果
      run_002\...
```

测试脚本模板见 [§9](#9-测试脚本模板)。

---

## 7. Step 5: 验证暴露面与治理标记

- **暴露面**：CLI 不等于 MCP。`exposure` 为 `agent` 的工具才会注册到 MCP；未经审核的能力保持 `cli_only` 或 `experimental`（策略见 `docs/MCP_EXPOSURE.md`）。
- **治理标记**：`risk` 决定 `readOnlyHint` / `destructiveHint`（read / write / filesystem-write / session / long-running 等）。
- **动态清册自检**：

```powershell
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'skills/cst-runtime-cli/scripts'); from cst_runtime.api import describe_tools; ts=describe_tools(); print(len(ts)); print([t['name'] for t in ts if t['name']=='define-monitor'])"
```

- **快照**：需要 agent 暴露面快照时运行 `uv run python devkit/tools/generate_agent_tools_list.py`（产出 `tools-list.json`，不入 git）。

---

## 8. Step 6: 上线归档

```powershell
# 1. 跑合约测试（默认全量不启动 CST）
.venv\Scripts\python.exe -m pytest -q

# 2. 同步到 agent 安装目录
Copy-Item -LiteralPath "skills\cst-runtime-cli\scripts\cst_runtime\" -Destination "$env:USERPROFILE\.config\opencode\skills\cst-runtime-cli\scripts\cst_runtime\" -Recurse -Force
Copy-Item -LiteralPath "skills\cst-runtime-cli\SKILL.md" -Destination "$env:USERPROFILE\.config\opencode\skills\cst-runtime-cli\SKILL.md" -Force
Copy-Item -LiteralPath "skills\cst-runtime-cli\scripts\bootstrap.py" -Destination "$env:USERPROFILE\.config\opencode\skills\cst-runtime-cli\scripts\bootstrap.py" -Force
```

---

## 9. 测试脚本模板

```python
"""每个工具一个独立 run，保存供人工查验。"""
import shutil, sys
from pathlib import Path

TEST_DIR = Path(r"<test_workspace>")
sys.path.insert(0, str(TEST_DIR / ".cst_runtime"))

from cst_runtime.core.session import open_project, close_project, get_attached_project

REF0 = TEST_DIR / "refs" / "ref_0" / "ref_0.cst"
TASK = TEST_DIR / "tasks" / "task_test_xxx"


def new_run(name: str) -> Path:
    """创建新 run 目录，复制 ref_0 → working.cst。"""
    run_id = len(results) + 1
    run_dir = TASK / "runs" / f"run_{run_id:03d}"
    proj_dir = run_dir / "projects"
    proj_dir.mkdir(parents=True, exist_ok=True)
    dst = proj_dir / "working.cst"
    shutil.copy2(REF0, dst)
    comp_src = REF0.with_suffix("")
    comp_dst = dst.with_suffix("")
    if comp_src.is_dir():
        shutil.copytree(comp_src, comp_dst, dirs_exist_ok=True)
    return dst


def summary(run_dir: Path, content: str):
    (run_dir / "summary.md").write_text(content, encoding="utf-8")


results = []


def do(run_name, desc, import_line, call_fn):
    dst = new_run(run_name)
    run_dir = dst.parent.parent
    proj_path = str(dst)
    try:
        open_project(proj_path)
        prj = get_attached_project(proj_path)
        exec(import_line, globals())
        call_fn(prj)
        close_project(proj_path, save=True, kill_processes=True)
        summary(run_dir, f"# {run_name}\n\n**Status**: PASS\n**Op**: {desc}")
        results.append((True, run_name, ""))
    except Exception as e:
        results.append((False, run_name, str(e)))
        try: close_project(proj_path, save=False, kill_processes=True)
        except: pass
        summary(run_dir, f"# {run_name}\n\n**Status**: FAIL\n**Error**: {e}")


# ── 在此定义要测试的工具 ──
TESTS = [
    (
        "Monitor (farfield)",                           # 测试名
        "define_monitor: farfield (f=12), freq=12.0",   # 操作描述
        "from cst_runtime.tools.em_setup import tool_define_monitor",  # import
        lambda prj: tool_define_monitor({               # 调用
            "project_path": str(prj),
            "name": "farfield (f=12)",
            "field_type": "Farfield",
            "freq": 12.0,
        }),
    ),
]


def main():
    for name, desc, imp, fn in TESTS:
        do(name, desc, imp, fn)
    total = len(results)
    passed = sum(1 for ok, _, _ in results if ok)
    print(f"\nResults: {passed}/{total} passed")
    if passed == total:
        print(f"All passed! See: {TASK / 'runs'}")


if __name__ == "__main__":
    main()
```

---

## 10. 常见问题

**Q: VBA_3D HTML 与现有代码不一致怎么办？**
以 VBA_3D HTML 为准。如果既有方法名在现有代码中使用但不在 HTML 里（如 `.ResetBackground`），说明是旧版 API，实测通过则保留。

**Q: 手工 VBA 风格不一但都通过测试？**
都有效。差异通常是 `With/End With` vs 直接前缀风格，或 bool/数字加不加引号。CST COM 都接受。

**Q: 测试区能不能直接在 ref_0 上跑？**
不能。必须复制到 `tasks/task_xxx/runs/run_xxx/projects/working.cst`。测试完 `save=True` 保留供人工查验。

**Q: 怎么人工查验测试结果？**
用 CST GUI 打开 `working.cst`，检查 History List 中是否有对应操作记录。

**Q: 真机测试什么时候跑？**
修改涉及真实 CST 行为（COM/VBA/结果树）后才跑 `--run-cst` 分层；纯离线改动不需要。

**Q: 现有的 core/lib 函数要不要迁移到新模块？**
不需要。已验证的手工实现保持原样，新对象直接在域模块新增 TOOL_DEFS + handler。
