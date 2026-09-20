# 模板建立与批量建模

批量建模的主流程是：**先建立若干种几何样板，再复制样板并平移到目标位置**。每种样板只准备一次，批量阶段使用 `copy-template` 复制已有样板，不逐位置重新执行样板的几何创建、布尔运算等步骤。

`build-array` 将复制和平移命令合并为一次 History 提交。`units` 登记样板，`elements` 指定样板代号和相对位移；它不选择拓扑、不自动建立材料和参数，也不保存工程。只在已授权的工程、数量和参数范围内调用。

## 选择模板

模板能力未知时调用 `list-unit-builders {}`，以当前 Worker 返回的 `builder_id`、`parameters_schema` 和 `example_parameters` 为准。以下两个 ID 是 `build-array` 中 `units` 的 `builder_id` 取值，不是独立 MCP 工具。

| 规范 ID | 方法名称与适用情况 | 源实体处理 |
| --- | --- | --- |
| `copy-template` | **复制已有样板**：引用已经建好的单元，可含多个实体，逐位置复制和平移 | 始终保留源实体；零位移直接复用源实体 |
| `create-brick-template` | **创建方块样板后复制**：每个 code 只创建一次方块样板，随后逐位置复制和平移 | 本次创建参考方块；存在零位移则保留，否则复制完成后删除临时参考方块 |

ID 统一采用“动作-对象”：`copy-template` 表明复制样板，`create-brick-template` 表明先创建方块样板。两者只在样板来源和源实体保留策略上不同，逐位置布置都使用复制和平移。

`copy-template` 的所有实体必须在同一工程、同一 component 内。只填写最终实体的短名称，例如 `patch`，不能填写 `cell:patch`。材料、布尔运算及单元内部相对位置沿用源单元；不同参数变体应先分别建好，再分别使用一个 code。此模板不导入另一个工程，不替换源实体参数，不复制端口、边界或监视器。

Python 的 `registry.register(...)` 只影响当前 Python 进程。自定义 builder 必须通过 `cst_runtime.unit_builders` entry point 部署到 Worker，再重启 MCP；仅编写一个脚本或在另一个进程注册，并不会使 MCP 能调用它。扩展 builder 只能使用可缓冲的建模操作，不能自行 flush、保存、运行求解或直接执行未缓冲的写操作。

## 建立与调用顺序

1. 沿用已授权的绝对 `project_path`、单位、材料、尺寸范围、数量和保存策略；工程与 CST 对象命名使用 ASCII。
2. 在建模前设置单位、参数、材料、component。复杂单元用原子建模工具完成，再将最终实体登记为 `copy-template`；简单方块可由 `create-brick-template` 在本次批量调用中准备一次样板。
3. 将模板定义放入 `units`，每个 code 对应一种模板；将所有目标位移放入 `elements`。坐标不是单元中心，`create-brick-template` 的 `origin` 是最小角点。按当前建模坐标系解释位移；默认全局坐标系，不要在未说明的局部 WCS 下调用。
4. 调用一次 `build-array`，读取终止信号、状态和失败详情。成功后按任务约定调用 `save-project`。修改被几何引用的参数后，先 `rebuild-model` 再 `save-project`。

同一 code 的完全重复位移会被拒绝；不同 code 不得使用相同参考实体名称。参数表达式保留给 CST 求值，工具不证明不同表达式所指的位置一定不同。数值尺寸必须为正，表达式尺寸的有效性由 CST 判断。`code="0"` 是普通模板代号；空位置应从 `elements` 中省略。

同一工程的批次须串行执行。普通成功调用无需逐实体回查；只读取完成状态并继续。请求不是幂等操作，重复发送会再次建模；工具不会预先查询既有实体以防重名，调用方应使用本次任务的唯一命名。

## 创建方块样板后复制示例

先在目标工程创建 `array` component，随后调用 `build-array`：

```json
{
  "project_path": "D:/CST_Work/batch_demo.cst",
  "summary": "Build Patch Array",
  "units": {
    "A": {
      "builder_id": "create-brick-template",
      "parameters": {
        "component": "array",
        "name": "cell_A",
        "material": "PEC",
        "origin": [-1, -1, 0],
        "size": [2, 2, 0.1]
      }
    }
  },
  "elements": [
    {"code": "A", "x": 0, "y": 0, "z": 0},
    {"code": "A", "x": 5, "y": 0, "z": 0}
  ]
}
```

上例只创建一次方块样板，零位移复用该样板，另一个位置复制并平移，最终形成两个单元。若已经定义 `w`、`t`、`p` 等 CST 参数，可使用 `origin=["-w/2", "-w/2", 0]`、`size=["w", "w", "t"]` 和 `x="p"`。

## 复制已有样板示例

假设 `cell_template` component 内已建好 `patch` 和 `substrate`，用以下请求复用源单元并新增两个完整副本：

```json
{
  "project_path": "D:/CST_Work/batch_demo.cst",
  "summary": "Repeat Existing Cell",
  "units": {
    "A": {
      "builder_id": "copy-template",
      "parameters": {
        "component": "cell_template",
        "reference_names": ["patch", "substrate"]
      }
    }
  },
  "elements": [
    {"code": "A", "x": 0, "y": 0, "z": 0},
    {"code": "A", "x": 5, "y": 0, "z": 0},
    {"code": "A", "x": 10, "y": 0, "z": 0}
  ]
}
```

成功返回 `instances_planned=3`、`instances_created=2`、`instances_reused=1`。实例表示完整单元，不是实体数量；上例新增四个实体。如果不写零位移，源单元仍然保留，但不计入请求实例。复制实体由 CST 自动命名；需要对副本进行后续定点编辑而名称未知时，再按需使用 `list-entities`。

## 失败和恢复

- 输入错误在开始批次前拒绝；错误信息指出未知 builder、拼错字段、缺失字段、重复位置或重名模板。
- 编排阶段失败会丢弃未提交缓冲区；执行阶段失败保留底层 `failure`、错误阶段与终止标志。成功数量保持为零，计划数量单独报告，不能据此声称 CST 中没有部分新增实体。
- 进入 CST 提交后，失败批次被冻结，只保留诊断脚本。后续追加和重复 flush 会被拒绝；先核查实际副作用，再调用同一 MCP Worker 的 `discard-array-batch`，只传入对应 `project_path`。它只清除命令缓存，不撤销已经执行的几何。另起 CLI 进程无法清除原 Worker 的内存缓存；Python 同进程调用可使用 `cst_runtime.lib.batch.discard`。
- 返回 `terminal=true` 或 `await_user_decision=true` 时遵循主 Skill 的终止规则，不能继续查询或恢复。
- `reference_objects` 是编排时的参考名称，不是最终全部副本的实体清单；临时参考方块可能已被按计划删除。

CLI 可先运行 `args-template --tool build-array --output <args.json>`。生成的文件现在包含完整的方块模板与两个位移示例；修改工程路径、模板和布置后，通过 `build-array --args-file <args.json>` 调用。JSON 请求文件可以复用，但应先确认目标工程及命名不会重复；它不是跨工程几何导入文件。
