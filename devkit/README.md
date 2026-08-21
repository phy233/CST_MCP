# CST Runtime CLI — 开发包

面向仓库维护者，包含开发参考、生成工具和维护流程。普通 CST 设计任务从根目录 `README.md` 和对应 Skill 进入，不需要先阅读本目录。

---

## 1. 仓库身份

当前仓库按职责维护四个 Skill：

- `cst-mcp`：MCP 调用和工具传输边界；
- `cst-runtime-cli`：Python 3.9 Worker、CLI 与高风险运维；
- `cst-metasurface-design`：超表面设计、仿真与结果验证；
- `cst-runtime-optimization`：逐轮参数优化和停止条件。

工具清单由 Registry 动态生成，不在文档中维护固定数量。

### 绝对禁止

- 禁止在仓库运行 `uv run python -m cst_runtime` 或任何 CST CLI 命令（会产生污染目录）
- 禁止修改 `archive/`、`refs/` 下文件
- 禁止写一次性 Python 脚本绕过 CLI
- 禁止收到修改指令后直接动手——必须先拆解问题、分析影响、给出方案

---

## 2. 快速开始

### 前提条件

- CST Studio Suite 2022（含 `python_cst_libraries`）已安装
- 测试区已初始化（`bootstrap.py` → `health-check --auto-fix`）

### 新增 VBA 工具（手工扩展路径）

```powershell
# 1. 查阅官方文档
start "<CST_INSTALL>\\Online Help\\mergedProjects\\VBA_3D\\index.htm"

# 2. 按 references/tool-development-guide.md 的 6 步流程实现：
#    改函数签名（带默认值的新参数，VBA 模板中 "{param}" 替代硬编码）
#    → 同步 JSON Schema → 在真实 CST 上逐个工具测试（每个工具独立 run）

# 3. 跑合约测试
uv run pytest <repo>\\skills\\cst-runtime-cli\\tests -v

# 4. 注册到 CLI（tools 模块 Registry）
```

### 增强现有工具

```powershell
# 1. 修改函数签名（加带默认值的参数，VBA 模板中 "{param}" 替代硬编码）
# 2. 同步 JSON Schema（新参数声明类型 + 默认值，type 用 number 非 integer）
# 3. 跑合约测试
uv run pytest <repo>\\skills\\cst-runtime-cli\\tests -v
# 4. 默认值向下兼容——新参数默认值 = 旧硬编码值
```

---

## 3. 文件索引

### 参考文档

| 文档                                         | 内容                                                                      |
| -------------------------------------------- | ------------------------------------------------------------------------- |
| `references/vba-official-reference.md`     | VBA 官方对象参考——150+ 对象方法签名/参数类型/枚举值                     |
| `references/cst-official-api-reference.md` | CST Python API 参考（cst.interface / cst.results / cst.units / C 扩展层） |
| `references/tool-development-guide.md`     | 工具开发集成指南——从查文档到 CLI 上线的完整 6 步流程                    |
| `references/lib-usage-guide.md`            | Python `lib` 门面的事实来源、返回契约和使用边界                         |
| `references/pipeline-metadata.md`          | Registry 中 pipeline mode 元数据词汇                                    |
| `../docs/development/testing.md`           | 测试体系全貌——分层测试命令与真机集成门控                                |

### 开发工具

| 工具                              | 内容                                        |
| --------------------------------- | ------------------------------------------- |
| `tools/generate_agent_tools_list.py` | 从统一 Registry 生成 agent 暴露面快照 `tools-list.json` |

---

## 4. 开发路径

| 场景                    | 路径       | 步骤                                                        |
| ----------------------- | ---------- | ----------------------------------------------------------- |
| **新对象/新方法** | 手工扩展   | 查官方文档 → 改函数签名 → 同步 JSON Schema → CST 实测 |
| **现有工具增强**  | 手工修补   | 改`core/*.py` 函数签名 → 同步 JSON Schema → 合约测试    |

### 管道与原子工具的分工

| 角色     | 说明               | 例子                                                            |
| -------- | ------------------ | --------------------------------------------------------------- |
| 管道执行 | 编排好的原子调用链 | `inspect-project`、`prepare-experiment`、`run-experiment` |
| 灵活编排 | 单个原子工具       | `set-farfield-monitor`、`change-material`                   |

原则：管道尽可组合，不是黑箱。

---

## 5. 关键规则

### 设计方法

涉及新功能或修改时，先回答四个问题：

1. **输入输出边界是什么？** 函数的输入从哪来、输出被谁消费
2. **根因在哪个层？** CST COM 行为 / 管道编排 / CLI 注册——不跨层补丁
3. **一次性还是需要灵活性？** 管道覆盖 80% 标准路径，原子工具留给 20% 非标
4. **网上有没有已实现的？** 不要重复造轮

### 实测驱动

遇到 CST 行为不确定时，写最小 Python 脚本直连 COM 查事实：

- `project.modeler.add_to_history("name","VBA")` 执行建模/仿真
- `get_result_item(treepath, run_id=N)` 读 N 号 run 的原始数据
- `get_parameter_combination(run_id)` 获取历史参数

### 常见 CST 陷阱

| 问题                         | 原因                        | 处理                           |
| ---------------------------- | --------------------------- | ------------------------------ |
| run_id 0 是别名              | 永远指向当前结果            | 导出时跳过                     |
| 远场每轮覆盖                 | 新仿真覆盖旧远场            | 每轮 export-run-results        |
| 远场导出后不可 save          | CST 进入错误状态            | close(save=False)              |
| modeler/results session 分离 | 不同 session 不同状态       | 仿真后关 modeler，再开 results |
| S11 不是 dB                  | ydata 是复数                | `20*log10(hypot(real,imag))` |
| modeler 未被废弃             | `add_to_history` 仍是入口 | 用`add_to_history`           |
| model3d 不是建模接口         | 只是历史记录开关            | 建模仍用 modeler               |

### VBA 拼装规则

| 参数类型 | Python 传入          | VBA 输出     | 引号             |
| -------- | -------------------- | ------------ | ---------------- |
| str      | `"brick1"`         | `"brick1"` | 加               |
| float    | `10.0`             | `10.0`     | 不加             |
| int      | `5`                | `5`        | 不加             |
| bool     | `True`             | `True`     | 不加             |
| enum     | `FieldType.EFIELD` | `"Efield"` | 加（`.value`） |

### 时序约定

- modeler session 与 results session 独立，禁止混用
- 仿真后先关 modeler，再 results 侧 reopen 刷新
- 远场导出放流程最后，导出后 `close(save=False)`
- `close_project()` 默认 `kill_processes=False`；需要退出关联 DE 时显式传入 `kill_processes=True`
- `change-parameter` 改参后必须 save → close → reopen → 仿真才能生效

---

## 6. Schema 规则

- 参数类型 `number`（非 `integer`），布尔用 `"boolean"`
- `default` 字段必填（保证 agent 知道可选参数的存在）
- `description` 描述功能而非实现
- 未知字段会被拒绝——Schema 是工具对外契约，改动必须同步合约测试

---

## 7. 结构

```
devkit/
├── README.md
├── references/
│   ├── vba-official-reference.md
│   ├── cst-official-api-reference.md
│   ├── lib-usage-guide.md
│   ├── pipeline-metadata.md
│   └── tool-development-guide.md
└── tools/
    └── generate_agent_tools_list.py
```

---

## 8. 外部资源

| 资源              | URL                                                           |
| ----------------- | ------------------------------------------------------------- |
| CST 内建 VBA 文档 | `<CST_INSTALL>\Online Help\mergedProjects\VBA_3D\index.htm` |
| CST 官方社区      | `3dswym.3dexperience.3ds.com/`                              |
| EDAboard CST      | `edaboard.com/forums/cst-microwave.242/`                    |
| CST VBA 在线镜像  | `mweda.com/cst/cst2013/`                                    |
