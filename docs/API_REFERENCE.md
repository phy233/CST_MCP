# API Reference & Inventory

> **统一契约说明（优先于下方旧版逐函数 Raises 描述）**：所有 `cst_runtime.lib` 公开函数现在返回可 JSON 序列化的 `OperationResult`。默认情况下业务失败返回 `{status: "error", error_type, message}`；只有 Python 调用者显式执行 `raise_for_error()` 或 `unwrap()` 时才抛出 `CSTOperationError`。下方尚未重新生成的 `Raises: RuntimeError` 条目仅描述旧行为，不再代表当前公开契约。

## `array` Module

### Function: `build_array`
- **Description**: 构建复杂阵列，通过回调函数构建。自动开启并管理 Command Buffer 的生命周期。
- **Arguments**: 
  - `project_path : str`
  - `unit_builder : ModelBuilder`
  - `elements : Sequence[ArrayElement]`
  - `summary : str = "Build Array"`
- **Returns**: `dict[str, Any]` (包含 "status" 和执行信息)
- **Raises**: None
- **Typical Usage**: 根据元素列表构建参数化阵列。
- **Example**: `build_array("project.cst", my_unit_builder, elements)`
- **Status**: Stable
- **MCP Exposure**: Yes

## `boundary` Module

### Function: `set_all`
- **Description**: Set all faces to same boundary type.
- **Arguments**:
  - `project_path : str`
  - `boundary_type : str = "expanded open"`
- **Returns**: `None`
- **Raises**: `RuntimeError` If boundary cannot be set
- **Typical Usage**: 设置所有边界条件。
- **Example**: `set_all("project.cst", "expanded open")`
- **Status**: Stable
- **MCP Exposure**: Yes

### Function: `set_per_face`
- **Description**: Set boundary conditions per face for unit cell / periodic simulations.
- **Arguments**:
  - `project_path : str`
  - `xmin : str = "unit cell"`
  - `xmax : str = "unit cell"`
  - `ymin : str = "unit cell"`
  - `ymax : str = "unit cell"`
  - `zmin : str = "open"`
  - `zmax : str = "open"`
  - `periodic_angle : float = 0`
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Typical Usage**: 周期性结构边界条件设置。
- **Status**: Stable
- **MCP Exposure**: Yes
- **Review Required**: 在 `lib` 层暴露了 VBA 拼接，过于底层，应移入 `core`。

### Function: `set_unit_cell`
- **Description**: Set unit cell boundary for periodic simulation.
- **Arguments**:
  - `project_path : str`
  - `periodic_angle : float = 0`
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes

## `cross_process` Module

### Class: `CrossProcessSweep`
- **Description**: Parameter sweep for cross-shaped unit cells.
- **Arguments**: `project_path`, `lx_range`, `ly1_range`, `target_freq_ghz`, `y_polarization_path`, `x_polarization_path`
- **Returns**: `SweepResult`
- **Status**: Experimental
- **MCP Exposure**: No
- **Review Required**: 属于上层特定业务逻辑，可作为 Example 存在，不应作为通用库的 lib API。

### Function: `quick_cross_sweep`
- **Description**: Quick parameter sweep for cross-shaped unit cells.
- **Arguments**: `project_path`, `lx_range`, `ly1_range`, `target_freq_ghz`, `output_dir`
- **Returns**: `SweepResult`
- **Status**: Experimental
- **MCP Exposure**: No

## `farfield` Module

### Function: `export_grid`
- **Description**: Export farfield grid data.
- **Arguments**: `project_path`, `farfield_name`, `export_dir`, `quantity`, `theta_step_deg`, `phi_step_deg`, `run_id`
- **Returns**: `dict[str, Any]`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes

### Function: `export_cut`
- **Description**: Export farfield cut data.
- **Arguments**: `project_path`, `tree_path`, `export_dir`
- **Returns**: `dict[str, Any]`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes
- **Review Required**: 暴露了 VBA 拼接细节，建议移至 core。

### Function: `list_monitors`
- **Description**: List farfield monitors.
- **Arguments**: `project_path`
- **Returns**: `list[str]`
- **Status**: Stable
- **MCP Exposure**: Yes

## `geometry` Module

### Function: `brick`
- **Description**: 创建一个长方体。
- **Arguments**: `project_path`, `component`, `name`, `material`, `x_range`, `y_range`, `z_range`
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes

### Function: `cylinder`
- **Description**: 创建一个圆柱体。
- **Arguments**: `project_path`, `component`, `name`, `material`, `axis`, `center`, `radius`, `z_range`, `inner_radius`
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes

### Function: `cone`
- **Description**: 创建一个圆锥体。
- **Arguments**: `project_path`, `component`, `name`, `material`, `axis`, `center`, `bottom_radius`, `top_radius`, `z_range`
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes

### Function: `rectangle`
- **Description**: 创建矩形曲线(2D)。
- **Arguments**: `project_path`, `curve`, `name`, `x_range`, `y_range`
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes

### Function: `boolean_add`, `boolean_subtract`, `boolean_intersect`
- **Description**: 布尔运算。
- **Arguments**: `project_path`, `shape1`/`target`, `shape2`/`tool`
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes

### Function: `delete_entity`
- **Description**: 删除一个实体。
- **Arguments**: `project_path`, `name`, `component`
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes

### Function: `delete_component`
- **Description**: 删除整个 Component。
- **Arguments**: `project_path`, `component`
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes
- **Review Required**: 直接拼接了 VBA。应移至 core 实现。

### Function: `rotate`, `mirror`
- **Description**: 几何变换。
- **Arguments**: 几何变换相关参数。
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes

### Function: `translate`
- **Description**: 平移。
- **Arguments**: `project_path`, `name`, `vector`, `multiple_objects`, `repetitions`, `destination`
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes
- **Review Required**: 注释提及这是 fallback VBA，应由 _transform_shape 支持并移出 VBA。

### Function: `activate_wcs`, `deactivate_wcs`
- **Description**: WCS 控制。
- **Arguments**: ...
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes
- **Review Required**: 暴露了 VBA 拼接，应移至 core。

### Function: `arc`, `polygon`
- **Description**: 曲线与多边形创建。
- **Returns**: `None`
- **Status**: Stable
- **MCP Exposure**: Yes
- **Review Required**: 直接暴露了 VBA 拼接，应移入 core 层。

## `materials` Module

### Function: `define`
- **Description**: Create a material.
- **Arguments**: `project_path`, `name`, `epsilon`, `mue`, `tan_d`, `tan_d_freq`, `transparency`
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes
- **Review Required**: 直接拼接了 VBA。

### Function: `define_from_mtd`
- **Description**: Load material from .mtd file.
- **Arguments**: `project_path`, `material_name`
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes

### Function: `list_materials`, `exists`, `set_material`
- **Description**: 材质相关辅助功能。
- **Returns**: `list[str]`, `bool`, `None`
- **Status**: Stable
- **MCP Exposure**: Yes
- **Review Required**: `set_material` 的参数 `entity` 使用 `component:name` 格式，与 `geometry.delete_entity` 分离传递 `name` 和 `component` 的格式不一致。

## `mesh` Module

### Function: `settings`, `acceleration`, `set_fpbavoid_nonreg_unite`, `set_minimum_step_number`
- **Description**: Mesh and Solver acceleration setup.
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes

## `monitors` Module

### Function: `set_farfield`, `set_efield`, `set_field`, `set_probe`, `delete_probe`, `delete_monitor`
- **Description**: Monitors and Probes.
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes

## `optimization` Module

### Function: `create_study`, `ask`, `tell`, `best`
- **Description**: Optuna based optimization.
- **Returns**: `None` / `dict[str, Any]`
- **Status**: Stable
- **MCP Exposure**: Yes

## `parameters` Module

### Function: `list_params`, `get_param`, `set_param`, `set_params`, `param_exists`
- **Description**: 项目参数管理。
- **Returns**: `dict`, `float`, `None`, `bool`
- **Status**: Stable
- **MCP Exposure**: Yes

## `port` Module

### Function: `define_waveguide`, `define_floquet`
- **Description**: 端口定义。
- **Returns**: `None`
- **Raises**: `RuntimeError`
- **Status**: Stable
- **MCP Exposure**: Yes
- **Review Required**: 包含 VBA 拼接，应交由 core。

## `results` Module

### Function: `get_sparam`, `get_sparam_at_freq`, `get_2d_field`, `list_items`, `list_sparams`, `sparam_exists`, `list_runs`, `get_param_combo`, `export_all`
- **Description**: 获取仿真结果及数据导出。
- **Returns**: Various (`dict`, `list`, `bool`)
- **Status**: Stable
- **MCP Exposure**: Yes

## `session` Module

### Function: `open_project`, `create_blank_project`, `close_project`, `inspect`, `save_project`, `quit_cst`, `list_open`, `is_locked`
- **Description**: CST 生命周期和工程管理。
- **Returns**: `dict[str, Any]` 或 `bool` 或 `list`
- **Status**: Stable
- **MCP Exposure**: Yes (部分如 `is_locked`, `inspect` 可作为 Internal 辅助)

## `solver` Module

### Function: `set_frequency_range`, `start`, `start_async`, `wait`, `is_running`, `stop`, `rebuild`, `delete_results`, `get_solver_type`
- **Description**: 求解器管理。
- **Returns**: `None` 或 `bool`
- **Status**: Stable
- **MCP Exposure**: Yes
- **Review Required**: `set_frequency_range` 和 `rebuild` 中暴露了 VBA，应移至 core。

## `sweep` Module
- **Description**: ParameterSweep and quick_sweep.
- **Status**: Stable
- **MCP Exposure**: Yes

## `unit_cells` Module
- **Description**: `UnitCellBase` abstract class.
- **Status**: Stable
- **MCP Exposure**: No (面向 Python 开发者扩展用的接口)

---

# API 审查（API Freeze Audit）及一致性检查

### 命名一致性
- `delete_entity`, `delete_component`, `delete_monitor`, `delete_probe`, `delete_results` 命名基本一致，使用了 `delete_` 前缀。

### 参数命名一致性
- `project_path` 在各模块中保持了一致使用。
- `name`, `component` 的使用存在轻微不一致。如 `geometry.delete_entity` 接受 `name` 和可选的 `component`，而 `materials.set_material` 直接接受拼接的 `entity` 字符串 (`component:name`)。

### 返回值一致性
- **存在严重不一致**：部分 API 返回 `dict` 包含状态码（如 `session.open_project`），部分返回 `None` 并在失败时抛出 `RuntimeError`（如 `geometry.brick`），部分返回特定类型如 `float`（`get_param`）或 `list`（`list_materials`）。
- **建议**：既然 `lib` 是公共 API，应统一返回行为：要么全用 Exceptions 来处理错误并返回实际结果，要么全返回统一定义的 `Result` 对象/字典。当前推荐全面转向 `None` 或原生类型 + Exception 风格，更符合 Python 库设计。

### 存在过于底层的 API
- 大量 `lib` API（如 `geometry.translate`, `geometry.arc`, `materials.define`, `boundary.set_per_face`, `port.define_floquet`）直接在模块内进行 VBA 字符串拼接然后调用 `_add_to_history`。
- 这违反了 `lib -> core -> COM` 架构，`lib` 应该仅负责接口签名和组合，具体的 VBA 生成应该是 `core` 的职责。
