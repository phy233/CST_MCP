# CST Runtime Lib API Reference

## 1. 概述与 API 冻结评估

根据完整 Meta Surface (超表面) CST 自动化工作流的执行逻辑，如果一个用户完全不了解内部实现，他/她仅需要调用部分稳定、高层抽象的 API 即可完成全自动化的建模、设置、仿真和后处理。这些被验证为稳定的核心 API 建议进行**冻结**（即参数固定、函数名固定、返回值固定、文档固定）。

### 推荐的完整自动化工作流与可冻结 API：
1. **工程管理**: `session.create_blank_project` 或 `session.open_project` 创建/打开工程。
2. **材料定义**: `materials.define` 设置使用的介质。
3. **参数控制**: `parameters.set_param` 定义全局变量。
4. **几何建模**: 
   - 基础形状：`geometry.brick`, `geometry.cylinder`, `geometry.boolean_add`, `geometry.boolean_subtract`。
   - 高级阵列：`array.build_array` 结合 `unit_cells.UnitCellBase` 实现复杂阵列与多态单元。
5. **边界条件**: `boundary.set_unit_cell` 快速生成超表面常用的周期边界。
6. **激励端口**: `port.define_floquet` 配置 Floquet 周期端口。
7. **求解与网格**: `solver.set_frequency_range`, `mesh.settings`。
8. **监视器**: `monitors.set_farfield`, `monitors.set_efield` 设置求解目标。
9. **仿真执行**: `solver.start` (或结合 `solver.wait`)，若需要扫描可直接使用 `sweep.ParameterSweep`。
10. **结果提取**: `results.get_sparam` 提取 S 参数，`farfield.export_grid` 导出远场增益。
11. **退出**: `session.close_project`。

---

## 2. API 详情

### 2.1 模块: `session`
管理 CST 工程的生命周期。

*   **`open_project`** / **`create_blank_project`**
    *   **输入**: `project_path` (str)
    *   **返回值**: `dict[str, Any]` (状态字典)
    *   **功能描述**: 打开现有工程或创建空白工程。
    *   **调用示例**: `session.open_project("C:\\model.cst")`
    *   **底层Core API**: `core.session.open_project`, `core.session.create_blank_project`
*   **`close_project`**
    *   **输入**: `project_path` (str), `save` (bool, 默认 False)
    *   **返回值**: `dict[str, Any]`
    *   **功能描述**: 关闭工程，可选择是否保存。
    *   **调用示例**: `session.close_project("C:\\model.cst", save=True)`
    *   **底层Core API**: `core.session.close_project`
*   **`inspect`** / **`list_open`** / **`is_locked`** / **`quit_cst`** / **`save_project`**
    *   **功能描述**: 提供工程状态检查、已打开工程列表、工程是否卡死锁定以及强制退出等功能。`is_locked` 与 `wait_project_unlocked` 使用同一规则，递归检查 `.cst` 工程伴生目录中的 `*.lok`，不检查不存在的 `项目名.cst.lock`。
    *   **底层Core API**: `core.session.inspect`, `core.identity.list_open_projects`, `core.project.save_project` 等。

### 2.2 模块: `parameters`
全局参数控制。

*   **`list_params`**
    *   **输入**: `project_path` (str)
    *   **返回值**: `dict[str, float]`
    *   **功能描述**: 获取所有全局参数及其值。
    *   **底层Core API**: `core.project.list_parameters`
*   **`get_param`** / **`set_param`** / **`set_params`** / **`param_exists`**
    *   **输入**: `project_path`, `name` (str), `value` (float) 等
    *   **返回值**: `float` 或 `None` 或 `bool`
    *   **功能描述**: 获取或修改指定的全局参数。修改后需调用 `solver.rebuild()`。
    *   **调用示例**: `parameters.set_param("C:\\model.cst", "lx", 5.0)`
    *   **底层Core API**: `core.project.change_parameter`, `core.project.define_parameters`

### 2.3 模块: `geometry`
CST 几何实体创建与布尔运算。

*   **`brick`** / **`cylinder`** / **`cone`** / **`rectangle`** / **`polygon`** / **`arc`**
    *   **输入**: `project_path`, `component`, `name`, `material`, 尺寸坐标等 (如 `x_range`, `center` 等)。
    *   **返回值**: `None`
    *   **功能描述**: 创建基础 3D 实体或 2D 曲线。
    *   **调用示例**: `geometry.brick("C:\\m.cst", "comp1", "patch", "PEC", (-5,5), (-5,5), (0,0.1))`
    *   **未来拓展可能**: `polygon` 和 `arc` 目前依赖直接注入 VBA，未来可拓展相应的 Python `core` 接口。
    *   **底层Core API**: `core.modeling.define_brick`, `core.modeling.define_cylinder` 等。
*   **`boolean_add`** / **`boolean_subtract`** / **`boolean_intersect`**
    *   **输入**: `project_path`, `shape1`/`target`, `shape2`/`tool` (str)
    *   **返回值**: `None`
    *   **功能描述**: 进行形状的布尔运算。
    *   **底层Core API**: `core.modeling.boolean_add`, `core.modeling.boolean_subtract` 等。
*   **`translate`** / **`rotate`** / **`mirror`**
    *   **输入**: `project_path`, `name`, 位移/角度/法向量等。
    *   **返回值**: `None`
    *   **功能描述**: 平移、旋转或镜像实体。
    *   **未来拓展可能**: `translate` 目前通过硬编码的 VBA 代码实现，未来将拓展 `transform_shape` 核心 API 来原生支持 translate (CST 2026 feature)。
*   **`delete_entity`** / **`delete_component`** / **`activate_wcs`** / **`deactivate_wcs`**
    *   **功能描述**: 删除实体/组件，管理局部坐标系。未来 `delete_component`, `activate_wcs` 均可能从直接使用 VBA 拓展为原生 `core` 调用。

### 2.4 模块: `materials`
材料属性定义与赋值。

*   **`define`**
    *   **输入**: `project_path`, `name`, `epsilon`, `mue`, `tan_d` 等。
    *   **返回值**: `None`
    *   **功能描述**: 创建自定义材料。
    *   **底层Core API**: 依赖直接注入 VBA (`core.modeling.add_to_history`)。未来有拓展专门 `core` 接口的可能。
*   **`define_from_mtd`**
    *   **输入**: `project_path`, `material_name`
    *   **返回值**: `None`
    *   **功能描述**: 从 .mtd 库加载材料。
    *   **底层Core API**: `core.modeling.define_material_from_mtd`
*   **`list_materials`** / **`exists`** / **`set_material`**
    *   **功能描述**: 列出、检查与修改实体的材料。
    *   **未来拓展可能**: `exists` 会在 CST 2026 后使用原生的 `Material.Exists()`，目前依靠回溯树列表实现。

### 2.5 模块: `boundary` 与 `port`
物理边界与激励端口配置。

*   **`boundary.set_all`** / **`boundary.set_per_face`** / **`boundary.set_unit_cell`**
    *   **功能描述**: 设置边界条件，`set_unit_cell` 会自动将四周设为 "unit cell"，Z轴设为 "open"。
    *   **调用示例**: `boundary.set_unit_cell("C:\\m.cst", periodic_angle=0)`
    *   **底层Core API**: `core.modeling.define_boundary`
*   **`port.define_waveguide`** / **`port.define_floquet`**
    *   **输入**: `project_path`, `port_number`, `face` 或 Floquet 模式数量与极化类型等。
    *   **返回值**: `None`
    *   **功能描述**: 设置波导端口和 Floquet 端口。
    *   **未来拓展可能**: `define_floquet` 目前依赖 VBA，对于 CST 2022 的兼容性未来可能需要通过抽象层拓展优化。

### 2.6 模块: `mesh` 与 `monitors`
网格设置与物理量监视器。

*   **`mesh.settings`** / **`mesh.acceleration`**
    *   **功能描述**: 设置网格密度参数以及求解器加速(硬件/并行)选项。
    *   **底层Core API**: `core.modeling.define_mesh`, `core.simulation.set_solver_acceleration`
*   **`monitors.set_farfield`** / **`monitors.set_efield`** / **`monitors.set_probe`**
    *   **输入**: 频率范围 (`start_freq`, `end_freq`, `step`) 以及子空间大小。
    *   **返回值**: `None`
    *   **功能描述**: 在指定频段设置电场或远场监视器。
    *   **调用示例**: `monitors.set_farfield("C:\\m.cst", 8, 12, 0.5)`
    *   **底层Core API**: `core.modeling.set_farfield_monitor` 等。

### 2.7 模块: `solver`
仿真引擎控制。

*   **`set_frequency_range`** / **`start`** / **`start_async`** / **`wait`** / **`stop`** / **`rebuild`**
    *   **输入**: 工程路径与所需频率/超时时间等。
    *   **功能描述**: 结构重建、求解器频率设置、阻塞/非阻塞启动、等待完成与强制停止。
    *   **底层Core API**: `core.simulation.start_simulation` 等。

### 2.8 模块: `results` 与 `farfield`
后处理与结果提取。

*   **`results.get_sparam`** / **`results.get_sparam_at_freq`**
    *   **输入**: `project_path`, `treepath` (例如 `"1D Results\\S-Parameters\\S1,1"`), `freq_ghz`
    *   **返回值**: `dict[str, Any]` (包含提取到的频率、幅值、相位等)
    *   **功能描述**: 读取特定的 S 参数或插值到特定频率。
    *   **底层Core API**: `core.results.get_1d_result`
*   **`results.get_2d_field`** / **`results.export_all`**
    *   **功能描述**: 提取二维场或批量导出所有 Run 的结果。
*   **`farfield.export_grid`** / **`farfield.export_cut`**
    *   **功能描述**: 导出远场网格或切片数据到文本。
    *   **未来拓展可能**: `export_cut` 目前是一个依赖 VBA 的简化版实现，未来将拓展以直接调用 core 层的远场处理。

### 2.9 模块: `sweep` 与 `cross_process`
自动化参数扫描与后处理逻辑。

*   **Class `ParameterSweep`**
    *   **参数**: `project_path`, `parameters`, `ranges`, `target_freq_ghz` 等。
    *   **方法**: `run(output_dir)`
    *   **返回值**: `SweepResult`
    *   **功能描述**: 建立一个自动化参数扫描，通过指定扫描参数范围，自动提取每个步骤下的 S 参数生成查询表 (LUT)。
*   **`quick_sweep`**
    *   **功能描述**: `ParameterSweep` 的快捷包装函数。
*   **Class `CrossProcessSweep`** / **`quick_cross_sweep`**
    *   **功能描述**: 专为十字型单元设计的双极化 S 参数提取自动化扫描。底层包裹 `ParameterSweep`。

### 2.10 模块: `optimization`
使用 Optuna 与 CST 联合优化。

*   **`create_study`** / **`ask`** / **`tell`** / **`best`**
    *   **输入**: `storage_path`, `study_name`, 变量定义字典等。
    *   **返回值**: `dict`
    *   **功能描述**: 构建优化循环。使用 `ask` 从优化器获取下一步参数，代入 CST 仿真后，通过 `tell` 返回指标进行下一次迭代。
    *   **底层Core API**: `core.optimizer.create_study` 等。

### 2.11 模块: `array` 与 `unit_cells`
复杂阵列的高级建模模式。

*   **Class `UnitCellBase`**
    *   **功能描述**: 抽象基类。用户应继承它并实现 `code_modeling` 来定义自己特有超表面单元类型的具体几何构建逻辑。
*   **Class `ArrayElement`** 与 **Class `BuildResult`**
    *   **功能描述**: 用于定义空间中的单一阵列单元位置及状态回调的数据类。
    *   **未来拓展可能**: `ArrayElement` 的 `code` 属性被设计为 `Any`，未来有拓展传递包括旋转(rotation)和材料(material)等多维度数据的可能。
*   **`build_array`**
    *   **输入**: `project_path`, `unit_builder` (回调函数), `elements` (阵列排列清单)
    *   **返回值**: `dict[str, Any]`
    *   **功能描述**: 自动化地执行复杂的阵列批量建模。通过组装 `elements`，它只需运行一次单元建模，接着自动进行大量的平移拷贝，极大降低建模时间和通信开销。
    *   **底层Core API**: `core.modeling.begin_batch`, `core.modeling.flush_batch` 等。
