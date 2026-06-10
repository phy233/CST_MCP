# CST Runtime lib/ 层使用指南

## 概述

`lib/` 层是 CST Runtime 的标准库风格公开 API，提供简洁的函数接口用于 CST 仿真自动化。

## 模块列表

| 模块 | 功能 | 主要函数 |
|------|------|----------|
| `session` | 会话管理 | `open_project`, `close_project`, `inspect` |
| `parameters` | 参数操作 | `list_params`, `get_param`, `set_param` |
| `solver` | 求解器控制 | `start`, `stop`, `is_running`, `rebuild` |
| `results` | 结果读取 | `get_sparam`, `list_items`, `list_runs` |
| `geometry` | 几何建模 | `brick`, `cylinder`, `boolean_subtract` |
| `materials` | 材料管理 | `define`, `define_from_mtd`, `list_materials` |
| `boundary` | 边界条件 | `set_all`, `set_per_face`, `set_unit_cell` |
| `port` | 端口配置 | `define_waveguide`, `define_floquet` |
| `monitors` | 监视器管理 | `set_farfield`, `set_efield`, `set_probe` |
| `farfield` | 远场操作 | `export_grid`, `export_cut`, `list_monitors` |
| `optimization` | 优化 | `create_study`, `ask`, `tell`, `best` |
| `array` | 阵列建模 | `build_coding_array`, `fast_array` |
| `unit_cells` | 单元格基类 | `UnitCellBase` (抽象基类) |
| `mesh` | 网格设置 | `settings`, `acceleration` |

## 快速开始

### 基本使用

```python
from cst_runtime.lib.session import open_project, close_project
from cst_runtime.lib.parameters import list_params, set_param
from cst_runtime.lib.solver import start, wait
from cst_runtime.lib.results import get_sparam

# 打开工程
open_project("C:\\path\\to\\model.cst")

# 读取参数
params = list_params("C:\\path\\to\\model.cst")
print(params)

# 修改参数
set_param("C:\\path\\to\\model.cst", "g", 24.0)

# 运行仿真
start("C:\\path\\to\\model.cst")
wait("C:\\path\\to\\model.cst")

# 读取结果
result = get_sparam("C:\\path\\to\\model.cst", "1D Results\\S-Parameters\\S1,1")
print(result)

# 关闭工程
close_project("C:\\path\\to\\model.cst")
```

### 几何建模

```python
from cst_runtime.lib.geometry import brick, cylinder, boolean_subtract

# 创建长方体
brick("C:\\path\\to\\model.cst",
      component="component1",
      name="patch",
      material="PEC",
      x_range=(-5, 5),
      y_range=(-5, 5),
      z_range=(0, 0.1))

# 创建圆柱
cylinder("C:\\path\\to\\model.cst",
         component="component1",
         name="via",
         material="Copper",
         axis="z",
         center=(0, 0),
         radius=0.5,
         z_range=(0, 1))

# 布尔减
boolean_subtract("C:\\path\\to\\model.cst",
                 target="component1:outer",
                 tool="component1:inner")
```

## 创建自定义单元格类

`unit_cells` 模块提供抽象基类 `UnitCellBase`，用户需要继承并实现 `code_modeling` 方法。

### 步骤

1. 创建新文件（如 `my_unit_cells.py`）
2. 继承 `UnitCellBase`
3. 定义 `name`, `codes`, `params` 属性
4. 实现 `code_modeling` 方法

### 示例

```python
from cst_runtime.lib.unit_cells import UnitCellBase
from cst_runtime.lib.geometry import brick, boolean_add

class MyCrossCell(UnitCellBase):
    """自定义十字单元格"""
    
    name = "my_cross"
    codes = [0, 1, 2, 3]
    params = {
        0: {"arm_length": 3.0, "arm_width": 0.5},
        1: {"arm_length": 3.0, "arm_width": 0.8},
        2: {"arm_length": 3.0, "arm_width": 1.0},
        3: {"arm_length": 3.0, "arm_width": 1.2},
    }

    def code_modeling(self, project_path, code, center, name):
        """创建十字单元格几何"""
        self.validate_code(code)
        p = self.get_params(code)
        
        # 创建水平臂
        brick(project_path, "component1", f"{name}_h", "PEC",
              x_range=(center[0] - p["arm_length"]/2, center[0] + p["arm_length"]/2),
              y_range=(center[1] - p["arm_width"]/2, center[1] + p["arm_width"]/2),
              z_range=(center[2], center[2] + 0.1))
        
        # 创建垂直臂
        brick(project_path, "component1", f"{name}_v", "PEC",
              x_range=(center[0] - p["arm_width"]/2, center[0] + p["arm_width"]/2),
              y_range=(center[1] - p["arm_length"]/2, center[1] + p["arm_length"]/2),
              z_range=(center[2], center[2] + 0.1))
        
        # 布尔加
        boolean_add(project_path, f"component1:{name}_h", f"component1:{name}_v")
```

### 使用自定义单元格

```python
from my_unit_cells import MyCrossCell

# 创建单元格实例
cell = MyCrossCell()

# 创建单元格几何
cell.code_modeling("C:\\path\\to\\model.cst",
                   code=0,
                   center=(0, 0, 0),
                   name="unit_0_0")
```

## 设计原则

1. **解耦设计**: 每个 `lib/` 模块只调用对应的 `core/` 模块
2. **独立导入**: 任何模块都可单独导入使用
3. **统一异常**: 成功返回数据，失败抛异常
4. **简洁签名**: 函数参数简洁，类型注解完整
5. **用户自定义**: 单元格类由用户继承实现

## CST 2022/2026 兼容性

- 大部分功能在 CST 2022 和 2026 中兼容
- 标注 `CST 2026 feature` 的代码可能需要适配
- 建议在 CST 2022 中测试关键功能
