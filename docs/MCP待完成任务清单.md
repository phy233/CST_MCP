# MCP 部分待完成任务清单

> **文档目的**: 对比计划文档与当前实现，列出MCP部分所有待完成任务
>
> **参考文档**: `CST_Step5-8_MCP与优化.md`、`CST交互代码实现指南.md`
>
> **当前状态**: 2026年6月16日

---

## 一、总体完成度

| 步骤 | 计划文件 | 完成度 | 状态 |
|------|----------|--------|------|
| Step 5 | `mcp_server/memory/store.py` | 0% | ❌ 完全缺失 |
| Step 6 | `mcp_server/server.py` + `tools/cst_tools.py` | 60% | ⚠️ 部分完成 |
| Step 7 | `mcp_server/tools/optimization_tools.py` | 0% | ❌ 完全缺失 |
| Step 8 | `mcp_server/agents/agent_examples.py` | 0% | ❌ 完全缺失 |

**总体MCP完成度: ~30%**

---

## 二、待完成任务详细列表

### Step 5: 经验记忆系统 (优先级: ★★★★★)

**文件**: `mcp_server/memory/store.py`

这是AI协同优化的核心组件，没有它，AI无法学习和复用历史优化经验。

#### 5.1 需要创建的目录结构

```
mcp_server/
└── memory/
    ├── __init__.py
    └── store.py
```

#### 5.2 需要实现的类和函数

| 类/函数 | 功能 | 行数估计 |
|---------|------|----------|
| `OptimizeCase` | 优化案例数据模型 (dataclass) | ~50行 |
| `OptimizationMemory` | 记忆存储主类 | ~200行 |
| `_row_to_case()` | SQLite行转对象辅助函数 | ~20行 |
| `_safe_json()` | JSON安全解析辅助函数 | ~10行 |

#### 5.3 `OptimizeCase` 字段定义

```python
@dataclass
class OptimizeCase:
    context_id: str               # "s11_opt_circular_ring_10ghz"
    unit_type: str                # "circular_ring"
    freq_ghz: float               # 10.0
    goal_type: str                # "s11_min" | "bw_max" | "phase_range"
    parameters: List[str]         # ["outer_radius_mm", ...]
    init_values: Dict[str, float] # {"outer_radius_mm": 5.0, ...}
    bounds: Dict[str, list]       # {"outer_radius_mm": [3.0, 7.0], ...}
    optimizer_method: str         # "trust_region" | "genetic" | ...
    strategy_notes: str           # AI给出的策略描述
    iterations: int               # 实际迭代次数
    duration_s: float             # 耗时
    final_score: float            # 目标函数终值
    converged: bool               # 是否收敛
    lessons: List[Dict]           # [{"type":"insight","msg":"..."}]
    tags: List[str]               # ["x_band", "single_layer"]
    id: Optional[int] = None
    created_at: Optional[str] = None
```

#### 5.4 `OptimizationMemory` 方法清单

| 方法 | 功能 | 参数 | 返回值 |
|------|------|------|--------|
| `__init__(db_path)` | 初始化，创建SQLite数据库 | db_path: str | None |
| `_init_db()` | 创建表结构（幂等） | 无 | None |
| `save_case(case)` | 保存优化案例 | OptimizeCase | int (case_id) |
| `_try_update_best(...)` | 更新最优参数追踪 | context_id, param_name, param_value, score | None |
| `get_similar_cases(...)` | 检索相似案例 | unit_type, freq_ghz, goal_type, tolerance_ghz, limit | List[OptimizeCase] |
| `get_context_for_llm(...)` | 生成LLM可读上下文 | unit_type, freq_ghz | str (Markdown) |
| `get_consolidated_knowledge()` | 全局经验汇总 | 无 | str (Markdown) |
| `get_stats()` | 记忆库统计 | 无 | Dict |

#### 5.5 SQLite表结构

```sql
-- 优化案例表
CREATE TABLE IF NOT EXISTS optimize_cases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    context_id      TEXT NOT NULL,
    unit_type       TEXT NOT NULL,
    freq_ghz        REAL NOT NULL,
    goal_type       TEXT NOT NULL,
    parameters      TEXT,           -- JSON数组
    init_values     TEXT,           -- JSON对象
    bounds          TEXT,           -- JSON对象
    optimizer_method TEXT,
    strategy_notes  TEXT,
    iterations      INTEGER,
    duration_s      REAL,
    final_score     REAL,
    converged       INTEGER DEFAULT 0,
    lessons         TEXT,           -- JSON数组
    tags            TEXT,           -- JSON数组
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 最优参数追踪表
CREATE TABLE IF NOT EXISTS best_params (
    context_id      TEXT NOT NULL,
    param_name      TEXT NOT NULL,
    param_value     REAL NOT NULL,
    score           REAL NOT NULL,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (context_id, param_name)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_cases_unit_freq
ON optimize_cases(unit_type, freq_ghz);
```

#### 5.6 依赖关系

- **前置依赖**: 无（纯Python标准库）
- **后续依赖**: Step 7 的 optimization_tools.py

#### 5.7 验证标准

```bash
# 1. 导入测试
python -c "from mcp_server.memory.store import OptimizationMemory, OptimizeCase"

# 2. 功能测试
python -c "
from mcp_server.memory.store import OptimizationMemory, OptimizeCase
mem = OptimizationMemory(':memory:')
case = OptimizeCase(
    context_id='test', unit_type='circular_ring',
    freq_ghz=10.0, goal_type='s11_min',
    parameters=['outer_radius_mm'], init_values={'outer_radius_mm': 5.0},
    bounds={'outer_radius_mm': [3.0, 7.0]}, optimizer_method='trust_region',
    strategy_notes='test', iterations=10, duration_s=100.0,
    final_score=-20.0, converged=True, lessons=[], tags=[]
)
cid = mem.save_case(case)
print(f'Saved case ID: {cid}')
ctx = mem.get_context_for_llm('circular_ring', 10.0)
print(f'Context length: {len(ctx)} chars')
"
```

---

### Step 6 补充: 训练 MCP 工具 (优先级: ★★★)

**文件**: `mcp_server/tools/training_tools.py`

#### 6.1 需要创建的目录结构

```
mcp_server/
└── tools/
    ├── __init__.py
    └── training_tools.py
```

#### 6.2 需要实现的工具

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `cst_start_training` | 启动模型训练 | config_json: str |
| `cst_check_training_status` | 检查训练状态 | task_id: str |
| `cst_get_training_metrics` | 获取训练指标 | task_id: str |
| `cst_stop_training` | 停止训练 | task_id: str |

#### 6.3 实现说明

这些工具需要与现有的`generative_model`项目集成：

```python
# 需要导入的模块
from generative_model.train import start_training
from generative_model.config import TrainingConfig
```

#### 6.4 依赖关系

- **前置依赖**: 需要了解`generative_model`项目的训练接口
- **后续依赖**: 无

#### 6.5 验证标准

```bash
python -c "from mcp_server.tools.training_tools import cst_start_training"
```

---

### Step 7: AI 协同优化工具 (优先级: ★★★★★)

**文件**: `mcp_server/tools/optimization_tools.py`

这是AI Agent进行智能优化的核心工具集。

#### 7.1 需要实现的工具

| 工具名 | 功能 | 风险级别 |
|--------|------|----------|
| `cst_query_optimization_memory` | 查询历史优化案例 | READ |
| `cst_record_optimization_case` | 保存优化案例 | WRITE |
| `cst_recommend_strategy` | 推荐优化策略 | READ |
| `cst_get_optimization_knowledge` | 获取全局经验汇总 | READ |

#### 7.2 工具详细规格

##### `cst_query_optimization_memory`

```python
@mcp.tool()
def cst_query_optimization_memory(
    unit_type: str,
    freq_ghz: float,
    goal_type: str = ""
) -> str:
    """
    查询历史优化案例，获取经验参考。
    
    AI在开始优化前必须调用此工具！
    历史经验会帮助AI选择优化器、设定参数范围和初始值。
    
    Args:
        unit_type: 单元类型 ("circular_ring" | "rectangular_patch")
        freq_ghz: 工作频率
        goal_type: 目标类型 ("s11_min" | "bw_max" | "phase_range")
    
    Returns:
        JSON格式:
        {
            "status": "success" | "no_history" | "error",
            "count": int,
            "context": "Markdown格式的历史经验文本"
        }
    """
```

##### `cst_record_optimization_case`

```python
@mcp.tool()
def cst_record_optimization_case(
    context_id: str,
    unit_type: str,
    freq_ghz: float,
    goal_type: str,
    parameters_json: str,      # JSON数组: ["outer_radius_mm", ...]
    init_values_json: str,     # JSON对象: {"outer_radius_mm": 5.0, ...}
    bounds_json: str,          # JSON对象: {"outer_radius_mm": [3.0, 7.0], ...}
    optimizer_method: str,
    strategy_notes: str,
    iterations: int,
    duration_s: float,
    final_score: float,
    converged: bool,
    lessons_json: str = "[]",  # JSON数组: [{"type":"insight","msg":"..."}]
    tags_json: str = "[]"      # JSON数组: ["x_band", "single_layer"]
) -> str:
    """
    记录一次优化案例到经验记忆库。
    
    每次CST优化完成后必须调用此工具！
    记录成功经验，也记录失败教训——两者都是宝贵的。
    
    Returns:
        JSON格式: {"status": "saved", "case_id": int}
    """
```

##### `cst_recommend_strategy`

```python
@mcp.tool()
def cst_recommend_strategy(
    unit_type: str,
    freq_ghz: float,
    goal_type: str,
    available_parameters_json: str  # JSON数组
) -> str:
    """
    基于历史经验推荐优化策略。
    
    AI在制定优化计划时应调用此工具获取数据驱动的建议。
    
    Returns:
        JSON格式:
        {
            "status": "success",
            "recommendations": {
                "recommended_optimizer": "trust_region",
                "optimizers_ranked": ["trust_region", "genetic", ...],
                "suggested_init": {"outer_radius_mm": 5.0, ...},
                "fastest_case": {...},
                "domain_tips": [...]
            }
        }
    """
```

##### `cst_get_optimization_knowledge`

```python
@mcp.tool()
def cst_get_optimization_knowledge() -> str:
    """
    获取全局归纳的优化经验知识。
    
    AI可以调用此工具建立整体直觉：
    哪个优化器在哪个场景下好用？最常优化的参数是什么？
    
    Returns:
        JSON格式:
        {
            "status": "success",
            "stats": {"total_cases": int, "avg_duration_seconds": float},
            "knowledge": "Markdown格式的全局经验汇总"
        }
    """
```

#### 7.3 依赖关系

- **前置依赖**: Step 5 (memory/store.py)
- **后续依赖**: Step 8 (agent_examples.py)

#### 7.4 验证标准

```bash
# 导入测试
python -c "from mcp_server.tools.optimization_tools import cst_query_optimization_memory"

# 功能测试（需要先实现Step 5）
python -c "
from mcp_server.memory.store import OptimizationMemory
from mcp_server.tools.optimization_tools import cst_query_optimization_memory
result = cst_query_optimization_memory('circular_ring', 10.0)
print(result)
"
```

---

### Step 8: Agent 调用示例 (优先级: ★★★★)

**文件**: `mcp_server/agents/agent_examples.py`

#### 8.1 需要创建的目录结构

```
mcp_server/
└── agents/
    ├── __init__.py
    └── agent_examples.py
```

#### 8.2 需要实现的示例函数

| 函数名 | 功能 | 运行命令 |
|--------|------|----------|
| `example_manual_lut_generation()` | 手动LUT生成示例 | `python -m mcp_server.agents.agent_examples lut` |
| `example_ai_assisted_optimization()` | AI辅助优化示例 | `python -m mcp_server.agents.agent_examples optimization` |
| `example_full_pipeline()` | 全流程概念演示 | `python -m mcp_server.agents.agent_examples full` |

#### 8.3 示例内容要求

##### `example_manual_lut_generation()`

```python
def example_manual_lut_generation():
    """
    手动生成LUT（研究员直接写脚本）。
    
    展示不通过MCP，直接作为Python库调用的方式。
    
    流程:
    1. 创建单元: MetaUnitBase.create("circular_ring", freq_ghz=10.0)
    2. 创建任务管理器: TaskManager("tasks")
    3. 创建任务: task_mgr.create_task(...)
    4. 创建运行: task_mgr.create_run(...)
    5. 生成LUT: LUTPipeline.run(...)
    """
```

##### `example_ai_assisted_optimization()`

```python
def example_ai_assisted_optimization():
    """
    AI Agent辅助优化的完整流程。
    
    模拟AI Agent调用MCP工具的完整过程:
    
    Step 1: AI检索历史经验
        - 调用 cst_query_optimization_memory()
        - 获取相似案例的上下文
    
    Step 2: AI分析 + 推荐策略
        - 基于历史案例分析
        - 生成优化策略JSON
    
    Step 3: AI执行CST优化
        - 调用 cst_open_project()
        - 调用 cst_set_parameter() (多次)
        - 调用 cst_start_simulation()
        - 调用 cst_wait_simulation()
    
    Step 4: AI保存经验
        - 调用 cst_record_optimization_case()
        - 包含成功经验和失败教训
    """
```

##### `example_full_pipeline()`

```python
def example_full_pipeline():
    """
    全流程管线：从单元设计到训练完成。
    
    Phase 1: 单元设计与CST扫参
        - 定义单元类型
        - CST开工程 → 建单元 → 扫参 → 提取S21
        - 保存LUT
    
    Phase 2: 模型训练
        - 训练脚本加载LUT
        - MetasurfaceCorrector用LUT校正理想相位
        - 训练生成模型
    
    Phase 3: 验证
        - 训练好的相位 → ArraySimPipeline
        - CST全阵列仿真 → 提取近场
        - 仿真近场 vs 期望图像 → 误差分析
    
    Phase 4: 闭环优化（AI参与）
        - 如果误差太大 → AI分析原因
        - 建议调整LUT密度或相位量化位数
        - 重新生成LUT → 重新训练
        - 保存优化经验到OptimizationMemory
    """
```

#### 8.4 依赖关系

- **前置依赖**: Step 5, Step 7
- **后续依赖**: 无

#### 8.5 验证标准

```bash
# 运行示例
python -m mcp_server.agents.agent_examples lut
python -m mcp_server.agents.agent_examples optimization
python -m mcp_server.agents.agent_examples full
```

---

### 补充: MCP CLI 入口 (优先级: ★★)

**文件**: `mcp_server/cli.py`

#### 需要实现的功能

```python
"""
MCP Server 备选CLI入口

用法:
    python -m mcp_server.cli list-tools        # 列出所有MCP工具
    python -m mcp_server.cli describe-tool <name>  # 描述单个工具
    python -m mcp_server.cli run               # 启动MCP服务器
"""

import argparse
from .adapter import list_available_tools

def cmd_list_tools():
    """列出所有可用的MCP工具"""
    tools = list_available_tools()
    for tool in tools:
        print(f"  {tool['name']:<30} [{tool['risk']}] {tool['description']}")

def cmd_describe_tool(name):
    """描述单个工具的详细信息"""
    tools = list_available_tools()
    for tool in tools:
        if tool['name'] == name:
            print(f"Name: {tool['name']}")
            print(f"Module: {tool['module']}")
            print(f"Function: {tool['function']}")
            print(f"Risk: {tool['risk']}")
            print(f"Description: {tool['description']}")
            return
    print(f"Tool not found: {name}")

def main():
    parser = argparse.ArgumentParser(prog="mcp-server-cli")
    sub = parser.add_subparsers(dest="command")
    
    sub.add_parser("list-tools", help="列出所有MCP工具")
    p_desc = sub.add_parser("describe-tool", help="描述单个工具")
    p_desc.add_argument("name", help="工具名称")
    sub.add_parser("run", help="启动MCP服务器")
    
    args = parser.parse_args()
    
    if args.command == "list-tools":
        cmd_list_tools()
    elif args.command == "describe-tool":
        cmd_describe_tool(args.name)
    elif args.command == "run":
        from .server import main
        main()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

---

## 三、实施顺序建议

### 阶段 1: 核心基础设施 (1-2天)

```
1. 创建 mcp_server/memory/__init__.py
2. 实现 mcp_server/memory/store.py (Step 5)
3. 测试 memory 模块
```

### 阶段 2: 优化工具 (1天)

```
4. 创建 mcp_server/tools/__init__.py
5. 实现 mcp_server/tools/optimization_tools.py (Step 7)
6. 测试 optimization 工具
```

### 阶段 3: 示例和文档 (1天)

```
7. 创建 mcp_server/agents/__init__.py
8. 实现 mcp_server/agents/agent_examples.py (Step 8)
9. 运行示例验证
```

### 阶段 4: 可选增强 (可推迟)

```
10. 实现 mcp_server/tools/training_tools.py (Step 6 补充)
11. 实现 mcp_server/cli.py (CLI入口)
```

---

## 四、快速开始指南

### 4.1 创建目录结构

```powershell
# 在项目根目录执行
mkdir mcp_server\memory -Force
mkdir mcp_server\tools -Force
mkdir mcp_server\agents -Force
```

### 4.2 创建 __init__.py 文件

```powershell
# 创建空的 __init__.py
New-Item -ItemType File -Path "mcp_server\memory\__init__.py" -Force
New-Item -ItemType File -Path "mcp_server\tools\__init__.py" -Force
New-Item -ItemType File -Path "mcp_server\agents\__init__.py" -Force
```

### 4.3 复制计划代码

从 `CST_Step5-8_MCP与优化.md` 中复制以下代码：

1. Step 5 的完整代码 → `mcp_server/memory/store.py`
2. Step 7 的完整代码 → `mcp_server/tools/optimization_tools.py`
3. Step 8 的完整代码 → `mcp_server/agents/agent_examples.py`

### 4.4 验证安装

```powershell
# 测试导入
python -c "from mcp_server.memory.store import OptimizationMemory; print('Memory OK')"
python -c "from mcp_server.tools.optimization_tools import cst_query_optimization_memory; print('Tools OK')"
python -c "from mcp_server.agents.agent_examples import example_manual_lut_generation; print('Agents OK')"
```

---

## 五、与现有架构的集成

### 5.1 当前架构

```
mcp_server/
├── server.py          # FastMCP入口
├── adapter.py         # 自动注册cst_runtime.lib函数
├── config.py          # 配置管理
└── __main__.py        # 启动入口
```

### 5.2 计划架构

```
mcp_server/
├── server.py          # FastMCP入口 (保留)
├── adapter.py         # 自动注册cst_runtime.lib函数 (保留)
├── config.py          # 配置管理 (保留)
├── __main__.py        # 启动入口 (保留)
├── cli.py             # CLI入口 (新增)
├── memory/            # 经验记忆系统 (新增)
│   ├── __init__.py
│   └── store.py
├── tools/             # 专用工具 (新增)
│   ├── __init__.py
│   ├── cst_tools.py   # 可选: 手动定义的CST工具
│   ├── training_tools.py
│   └── optimization_tools.py
└── agents/            # Agent示例 (新增)
    ├── __init__.py
    └── agent_examples.py
```

### 5.3 集成方式

在 `mcp_server/server.py` 中添加新工具的导入：

```python
def create_mcp_server():
    # ... 现有代码 ...
    
    # 注册cst_runtime.lib的工具
    from .adapter import register_all_tools
    count = register_all_tools(mcp)
    
    # 注册优化工具 (新增)
    from .tools import optimization_tools  # noqa: F401
    
    # 注册训练工具 (新增，可选)
    # from .tools import training_tools  # noqa: F401
    
    print(f"CST Runtime MCP Server: {count} tools registered", file=sys.stderr)
    
    return mcp
```

---

## 六、测试策略

### 6.1 单元测试

创建 `tests/test_memory.py`:

```python
import pytest
from mcp_server.memory.store import OptimizationMemory, OptimizeCase

class TestOptimizationMemory:
    def test_init_db(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        mem = OptimizationMemory(db_path)
        assert mem.db_path == db_path
    
    def test_save_and_retrieve(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        mem = OptimizationMemory(db_path)
        
        case = OptimizeCase(
            context_id="test",
            unit_type="circular_ring",
            freq_ghz=10.0,
            goal_type="s11_min",
            parameters=["outer_radius_mm"],
            init_values={"outer_radius_mm": 5.0},
            bounds={"outer_radius_mm": [3.0, 7.0]},
            optimizer_method="trust_region",
            strategy_notes="test",
            iterations=10,
            duration_s=100.0,
            final_score=-20.0,
            converged=True,
            lessons=[],
            tags=[]
        )
        
        case_id = mem.save_case(case)
        assert case_id > 0
        
        cases = mem.get_similar_cases("circular_ring", 10.0)
        assert len(cases) == 1
        assert cases[0].context_id == "test"
```

### 6.2 集成测试

创建 `tests/test_optimization_tools.py`:

```python
import pytest
from mcp_server.tools.optimization_tools import (
    cst_query_optimization_memory,
    cst_record_optimization_case
)

class TestOptimizationTools:
    def test_query_empty(self):
        result = cst_query_optimization_memory("circular_ring", 10.0)
        assert "no_history" in result
    
    def test_record_and_query(self):
        # 先记录一个案例
        result = cst_record_optimization_case(
            context_id="test_001",
            unit_type="circular_ring",
            freq_ghz=10.0,
            goal_type="s11_min",
            parameters_json='["outer_radius_mm"]',
            init_values_json='{"outer_radius_mm": 5.0}',
            bounds_json='{"outer_radius_mm": [3.0, 7.0]}',
            optimizer_method="trust_region",
            strategy_notes="test",
            iterations=10,
            duration_s=100.0,
            final_score=-20.0,
            converged=True
        )
        assert "saved" in result
        
        # 再查询
        result = cst_query_optimization_memory("circular_ring", 10.0)
        assert "success" in result
        assert "案例" in result
```

---

## 七、常见问题

### Q1: 为什么不直接使用adapter.py的自动注册？

**A**: adapter.py适合注册cst_runtime.lib的通用函数，但优化记忆系统是本项目特有的功能，需要手动定义工具以确保：
1. 参数格式符合AI Agent的使用习惯
2. 返回值包含足够的上下文信息
3. 工具描述清晰指导AI的使用流程

### Q2: memory模块可以用其他数据库替代SQLite吗？

**A**: 可以，但SQLite是最佳选择：
- Python标准库自带，零依赖
- 单文件数据库，便于备份和分享
- 足够支持单用户的优化经验存储

### Q3: 这些工具需要连接真实CST吗？

**A**: 
- memory模块: 不需要，纯数据存储
- optimization_tools: 不需要，只调用memory
- agent_examples: 大部分不需要，只有实际仿真部分需要

---

## 八、完成后的验证清单

- [ ] `python -c "from mcp_server.memory.store import OptimizationMemory"` 不报错
- [ ] `OptimizationMemory` 能创建SQLite数据库
- [ ] `save_case()` 返回有效的case_id
- [ ] `get_context_for_llm()` 返回格式化的Markdown文本
- [ ] `python -m mcp_server.agents.agent_examples optimization` 能运行
- [ ] MCP Server启动后能看到优化工具 (`cst_query_optimization_memory` 等)
- [ ] 所有单元测试通过: `pytest tests/test_memory.py -v`

---

## 九、参考资料

- **计划文档**: `CST_Step5-8_MCP与优化.md` (Step 5-8 完整代码)
- **架构文档**: `CST交互代码实现指南.md` (总架构设计)
- **对比分析**: `CST_MCP与CLI对比分析.md` (MCP vs CLI 选择)
- **Python学习**: `CST_Python学习要点.md` (SQLite、dataclass等概念)

---

*文档生成时间: 2026-06-16*
