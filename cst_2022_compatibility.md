# CST 2022 兼容性问题记录

## 1. 参数获取接口不兼容 (`project.model3d`)

**受影响的功能：**
- `list-parameters` 工具 (核心函数: `cst_runtime.core.project.list_parameters`)
- `get-parameter` 工具 (依赖 `list_parameters`)
- `parameter-exists` 工具 (依赖 `list_parameters`，但目前异常被静默吞没)

**现象与原因：**
CST 2022 的 COM 接口中 `project` 对象未暴露 `model3d` 属性（该属性为 CST 2023+ 引入）。因此在调用 `project.model3d` 时会引发 COM AttributeError/Exception，导致无法调用 `GetNumberOfParameters` 和 `RestoreDoubleParameter`。

**当前状态的规避路线：**
参数写入操作 (`change_parameter`, `define_parameters`) 目前使用的是纯 VBA 宏执行路径 (`_single_vba`) 传递 `StoreDoubleParameter`，这避开了新版 COM 属性的依赖，因而在 CST 2022 下依然可以正常工作。

**后续解决思路：**
需要查阅 CST 2022 的 VBA/COM 手册，寻找替代的 COM 属性（如 `project.modeler` 是否包含对应接口），或将参数读取操作也降级为通过 `_single_vba` 配合临时文件/标准输出来完成。

---
## 2. Python 版本限制 (`cst.interface` 版本检查)

**受影响的功能：**
- 所有需要导入 `cst.interface` 的测试和核心逻辑代码。

**现象与原因：**
在使用高于 3.9 的 Python 版本（例如当前工作区 `uv` 默认或指定的 Python 3.12/3.14 环境）跑 `pytest` 时，`cst` 库初始化代码 (`cst\__init__.py:7`) 会抛出异常：`ImportError: The cst package supports only Python 3.6/3.7/3.8/3.9`。
这意味着 CST 2022 官方附带的 Python 包硬编码了对旧版 Python 的依赖。

**影响与风险：**
- 本项目的 `pyproject.toml` 要求 `requires-python = ">=3.12"`，但直接导入 `cst.interface` 却要求 `<=` 3.9，导致在原生测试环境（如 `uv run pytest`）中无法执行包含 CST 导入的模块测试（`skills/cst-runtime-cli/tests/test_array.py` 等均引发 Collection Error）。
- 亟需统一运行环境的 Python 版本，或屏蔽掉 `cst` 库的强制版本检测。

---
## 3. MCP 适配器层单元测试损坏

**受影响的功能：**
- `tests/test_mcp_server.py` 中的单元测试。

**现象与原因：**
因为此前我们重构了 `mcp_server/adapter.py`，去除了 `TOOL_SPECS` 等旧的硬编码定义，导致该测试文件大量报错（报 `ImportError: cannot import name 'TOOL_SPECS' from 'mcp_server.adapter'` 及 `AttributeError`）。共有 13 个测试因架构演进而失败，需要后续同步重构测试代码。

---
## 4. Python 语法兼容性冲突 (Python 3.9 vs Python 3.12+)

**受影响的功能：**
- 几乎整个项目，特别是使用了新式类型注解和 f-string 的模块（如 `cli/test_capture_3d_view.py` 和 `render/svg_page.py`）。

**现象与原因：**
当我们强行切换到兼容 CST 2022 的 **Python 3.9** 环境（`conda cst39`）运行测试时，暴露出该项目的代码大量使用了较新的 Python 语法特性，这些特性在 Python 3.9 中不受支持，导致直接抛出 `SyntaxError` 和 `TypeError`：
1. **类型提示冲突：** `input_text: str | None = None` (使用了 Python 3.10 引入的 `|` 联合类型写法，若未在文件顶部声明 `from __future__ import annotations` 则在 3.9 下报错)。
2. **嵌套 F-String 冲突：** `f'{f'<span...>{...}</span>' ... }'` (使用了 Python 3.12 引入的允许嵌套相同引号的 f-string 特性，在 3.9 下报 `SyntaxError: f-string: expecting '}'`)。

**影响与风险：**
- 这是一个**相互死锁的兼容性矛盾**：CST 2022 强制要求运行在 `<=` Python 3.9 环境；但 MCP Server 和 CLI 项目代码大量使用了 `>=` Python 3.10 (甚至 3.12) 的语法糖。
- 前期之所以能通过代理 (`proxy`) 跑通，是因为 proxy 把 Python 3.12 环境（用于启动 MCP）与底层的 Python 3.9 环境（用于通过 COM 通信调用 CST）隔离开来了。
- 要彻底排查 lib 层函数，我们无法直接把包含高版本语法的代码扔进 Python 3.9 环境里裸跑。

---
## 5. lib/core 层的实际 CST COM API 兼容性 (CST 2022)

在隔离掉测试库中的 Python 3.10+ 语法冲突后，我们在 `cst39` 下成功执行了 `core` 和 `lib` 层纯净的 52 个单元测试。这证明了 `lib` 层的**VBA代码生成、参数拼装、数据验证等纯逻辑代码完全兼容 Python 3.9**。

但结合对源码调用的深层溯源分析，发现在 `lib` 层部分读取操作下发给 CST 时，会有一部分致命的 **COM API 缺失异常**，因为这部分高阶功能依赖了 CST 2023+ 引入的新型 Python 接口对象 `project.model3d`：

1. **`list_parameters` (参数读取)**
   - **位置**: `core/project.py:72` (`m3d = project.model3d`)
   - **影响**: 由于 2022 版本下 `project` 对象并没有 `.model3d`，调用直接抛出 `AttributeError`，并引发 `get_parameter` 与 `parameter_exists` 的连锁雪崩。
2. **`discover_farfield_monitors` (远场监视器探索)**
   - **位置**: `core/farfield.py:392` (`for item in project.model3d.get_tree_items():`)
   - **影响**: 报错导致远场列表读取失败。作为对比，老版本中通常使用 `project.modeler.get_tree_items()` (`core/project.py:122` 就仍旧使用了这种兼容写法)。
3. **`export_farfield_grid` (远场标量网格读取)**
   - **位置**: `core/farfield.py:296` (`calculator = project.model3d.FarfieldCalculator`) 以及 `302` 行 (`project.model3d.SelectTreeItem(...)`)
   - **影响**: 读取天线远场方向图（Gain, Directivity）的底层计算器对象无法被获取，导致直接通过 Python 对象抽取远场网格的功能在 CST 2022 中完全瘫痪。
4. **色图获取 `colormap`**
   - **位置**: `core/results.py:540` (`m3d2.get_tree_items(filter="colormap")`)
   - **影响**: 色图树节点抓取失败，功能降级。

**总结结论：** 
只要 `lib` 的函数实现是 **封装为纯 VBA 字符串并通过 `project.modeler.add_to_history("ExecuteVBA", code)` 宏下发执行的**，它就 **完全兼容 CST 2022**（如建模 `brick`、材质 `materials`、布尔运算、扫参等各种执行类动作）。

但凡涉及到 **“绕过 VBA，直接调用 CST 新版 Python COM 对象的属性去访问内存数据”**（如拿参数列表对象、拿远场数据计算器 `FarfieldCalculator`），就会在 2022 环境下崩溃。这在 `project.model3d` 对象上表现得最突出。

---
*待后续发现的其他兼容性问题将持续补充至本文档...*
