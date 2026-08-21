# CST 官方 Python API (`cst.interface`) 分析与排雷指南

在开发 `cst_runtime` 框架期间，我们对官方的 `cst.interface` 包（特别是 `add_to_history` 方法）进行了深度的内省测试与行为实验。本日志记录了官方 API 的部分隐藏特性与设计缺陷，为后续的异常处理和架构设计提供依据。

## 1. `project.modeler.add_to_history` 的行为缺陷

### 实验现象
当我们通过 Python COM 接口向 CST 提交 VBA 宏指令时，可能遇到三种典型情况：
1. **完全正确的 VBA**：宏执行成功，生成对应几何体。
2. **存在逻辑错误的 VBA**：例如使用 `.Material "不存在的材料"`，宏符合 VBA 语法，但 CST 内部计算或校验失败，并在 CST 的 Message Window 中飘红报错。
3. **完全的语法垃圾**：例如提交 `Solid.DoSomethingCrazy "what is this"`，完全不符合语法规范。

在上述**所有情况**下，`project.modeler.add_to_history("Name", vba_script)` 均**返回了 `True`，且未在 Python 端抛出任何异常**。

### 结论与隐患
- 官方的 `add_to_history` 是一个**“同步提交、异步执行结果”**的单向接口：Python 同步等待字符串送达 CST 宏执行引擎，但不会获得 VBA 的完成通知或执行结果。
- `True` 仅仅代表“字符串已成功送达 CST 宏执行引擎”，**绝不代表 VBA 已执行完成或执行成功**。
- 这导致了一个严重隐患：Python 脚本会误以为指令执行成功（如 Batch Flush 显示 success），继续往后执行，而实际上 CST 内部模型已经崩溃或卡死。

## 2. API 对象的底层类型与隐藏接口 (Introspection)

通过对 `cst.interface` 导出的对象进行 `dir()` 与 `inspect` 分析，得到如下信息：

### `project` 对象
- **Type**: `<class '_cst_interface.Project'>`
- 代表当前的 CST MWS 工程实例。

### `project.modeler` 对象
- **Type**: `<class '_cst_interface.RemoteObject'>`
- 本质上是 CST COM 接口的一个极简代理包装器。
- 过滤掉内置魔术方法后，一共暴露了 **12个公有方法**：
  - 常规控制流：`abort_solver`, `add_to_history`, `full_history_rebuild`, `get_active_solver_name`, `is_solver_running`, `pause_solver`, `resume_solver`, `run_solver`, `start_solver`
  - **隐藏的内部方法**（下划线开头）：
    - `_GetHistory`：返回 `<class '_cst_interface.RemoteObjectMethod'>`
    - `_ResizeHistory`
    - `_TryToUndoNTimes`

### 缺失的关键能力
我们在公有与私有属性中检索了 `error`, `log`, `message`, `output` 等关键字，**未发现任何可以直接读取 CST Message Window 日志或获取最后一次错误的端点**。

## 3. 其他官方 API 行为结论（行为实验实测）

- **`execute_vba_code()`**：**同步阻塞执行**，存在于 `project.schematic` 等对象；强制要求 VBA 采用 `Public Sub Main()` 结构（不允许 `Function Main()` 返回值）。VBA 存在语法错误或运行时异常时，会同步抛出 Python `RuntimeError`，可被 `try...except` 捕获。适合执行需要严格感知执行状态的验证与短代码。
- **`cst_env.open_project()`**：传入不存在的路径时会准确抛出 `FileNotFoundError`。
- **`full_history_rebuild()`**：即使 History Tree 中包含语法错误的块，依然返回 `1` (True)，不抛出异常，**不能作为模型健康度的判据**。
- **`project.save()`**：传入非法路径（如非法盘符）时不抛异常，仅静默返回 `None`——所有文件路径操作都需要在 Python 层自行做合法性与写权限校验（防御性 IO）。

## 4. Python 与 VBA 之间的数据通信实测

- **文件 I/O（可行且最可靠）**：VBA 使用 `Scripting.FileSystemObject` 将结果写入本地临时文件；由于提交是同步的，Python 可在 `add_to_history` / `execute_vba_code` 返回后立即读取。
- **函数返回值（不可行）**：`execute_vba_code` 强制入口为 `Public Sub Main()`，无法通过 `Function Main()` 返回值取数。
- **参数（受限）**：VBA 可用 `StoreDouble` 写入参数，但官方 Python 对象没有暴露直接的参数字典查询接口，读取不便。

## 5. 框架错误处理策略落地

既然无法指望 `add_to_history` 自带异常捕获，框架层必须引入“后置校验（Post-validation）”机制来保证运行时的鲁棒性：

1. **方案 A（历史树校验）**：
   既然 `add_to_history` 会在 CST 的 History Tree 中生成一个具有特定 `Name` 的节点。如果是语法或严重逻辑错误导致执行中止，该节点通常会被丢弃或标记为错误。我们可以尝试封装官方意外暴露的隐藏方法 `_GetHistory`，在 Flush 后检索指定的 History Name 是否真正落盘成功。
2. **方案 B（文件系统嗅探）**：
   解析工程同名目录下的日志文件（如 Log 文件夹内的 txt），动态嗅探 Error 关键字。
3. **方案 C（实体存在性校验）**：
   通过生成一段查询 VBA，将模型树内的实体列表输出到本地临时文件，Python 读取文件确认目标对象（如 `component:name`）是否被真实创建。
4. **方案 D（探针文件验证 `add_to_history`）**：
   在 VBA 代码末尾追加“向特定临时文件写入成功标志”的探针代码，Python 在接口返回后检查该文件是否存在，以此判断 VBA 是否中途抛错中断。
5. **优先使用 `execute_vba_code()` 执行验证和短代码**：
   需要严格感知 VBA 执行状态（抛错）时，尽量使用 `project.schematic.execute_vba_code` 包裹 `Public Sub Main()`，直接利用 Python 的 `try...except`。
6. **不要依赖 `full_history_rebuild()` 判断模型健康度**：它不会对内部块的错误做出异常反馈。

---

*记录时间：2026-07-16（行为实验部分合并自 docs/api_analysis.md，2026-07-31）*
*相关 Commit: e113955 及之前*
