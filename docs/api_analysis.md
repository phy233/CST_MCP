# CST Python API 行为实验验证报告

基于一系列针对 CST 2022 Python API 的独立行为实验，我们总结了官方接口在同步性、错误反馈、数据通信等方面的真实表现。

## 实验总结

### 1. 哪些 API 是同步的？
- **`add_to_history()` 的 COM 提交阶段**：调用方同步等待 VBA 字符串被送达 CST 的宏执行引擎；其返回值仅表示提交成功，不能用于判断宏是否已经执行完成或执行成功。
- **`execute_vba_code()`**：**是同步的（阻塞执行）**。此方法存在于 `project.schematic` 等对象中，在执行耗时 VBA 时同样阻塞，并且强制要求 VBA 采用 `Public Sub Main()` 结构。

### 2. 哪些 API 是异步提交？
- **`add_to_history()` 的 VBA 执行阶段**：CST 在内部处理已提交的历史命令，Python 端不获得完成通知或执行结果。因此它应理解为“同步提交、异步执行结果”的单向接口，不能以返回 `True` 作为后续依赖操作的完成条件。

### 3. 哪些 API 能反馈执行成功或抛出异常？
- **`execute_vba_code()`**：**能够反馈执行状态**。如果 VBA 存在语法错误或运行时异常，该接口会同步抛出 Python `RuntimeError`，从而被 `try...except` 捕获。
- **部分项目级 API**：例如 `cst_env.open_project()`，传入不存在的路径时会准确抛出 `FileNotFoundError`。

### 4. 哪些 API 永远返回 True（或静默失败）？
- **`add_to_history()`**：无论 VBA 后续执行成功、产生语法错误还是运行时异常，都可能返回 `True` 且不在 Python 端抛出异常；`True` 只代表命令字符串已提交给 CST。
- **`full_history_rebuild()`**：即使历史树（History Tree）中包含了语法错误的块，执行该接口依然返回 `1` (True)，不抛出异常。
- **`project.save()`**：当传入非法路径（如非法盘符）时，不抛出异常，仅静默返回 `None`。

### 5. 哪些错误只能在 CST GUI 中看到？
- 由于 `add_to_history()` 和 `full_history_rebuild()` 会吞噬一切 VBA 错误，这些由历史块产生的错误（通常在 Message Window 显示为红字）**无法通过官方 Python API 捕获**。
- 对 `project`、`modeler` 等对象的属性扫描（如 `get_message`、`log`、`output`、`error` 等）表明，**官方 API 没有暴露任何读取 Message Window 文本的接口**。

### 6. Python 与 VBA 之间目前可用的数据通信方式有哪些？
- **文件 I/O（可行且最可靠）**：VBA 使用 `Scripting.FileSystemObject` 将结果写入本地临时文件，由于执行是同步的，Python 可以在 `add_to_history` 或 `execute_vba_code` 返回后立即读取该文件。
- **返回值（不可行）**：`execute_vba_code` 强制要求入口是 `Public Sub Main()`，不允许使用 `Function Main()`，因此无法直接通过函数返回值获取数据。
- **参数（受限）**：虽然可以通过 VBA `StoreDouble` 写入参数，但 Python 官方对象上没有暴露直接的 `get_parameter` 字典查询接口，读取不便。

### 7. 对于 Runtime 开发者，应如何设计错误处理策略？
基于上述实验事实，建议采用以下错误处理与架构策略：
1. **优先使用 `execute_vba_code()` 执行验证和短代码**：在需要严格感知 VBA 执行状态（抛错）时，应尽量使用 `project.schematic.execute_vba_code` 来包裹 `Public Sub Main()` 执行代码，这可以直接利用 Python 的 `try...except`。
2. **构建“探针文件”机制验证 `add_to_history`**：既然 `add_to_history` 会吞噬异常，若必须通过它修改模型，可在 VBA 代码的末尾添加一行“向特定临时文件写入成功标志”的代码。Python 在该接口返回后检查该文件是否存在，以此判断 VBA 是否因中途抛错而中断。
3. **不要依赖 `full_history_rebuild()` 判断模型健康度**：它不会对内部块的错误做出异常反馈。
4. **防御性 IO**：对于所有文件路径操作（如 `save`），需要开发者自己在 Python 层通过 `os.path` 进行合法性及写权限检查，因为底层 API 可能静默失败。
