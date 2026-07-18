# Workflow Reference

这是一个基于 `lib` 接口的标准自动建模工作流推荐指南。

## 1. Session 管理 (工程启停)
创建一个新工程，或打开现有工程。
- `session.create_blank_project(path)`
- `session.open_project(path)`

## 2. Parameter 初始化
设置全局变量与参数。
- `parameters.set_params(path, dict_params)`

## 3. Materials 定义
定义结构所需要的材料。
- `materials.define(path, ...)`
- `materials.define_from_mtd(path, ...)`

## 4. Geometry 构建与变换
构建 3D/2D 模型实体，进行变换。
- 基本形体: `geometry.brick(path, ...)` / `cylinder` / `cone`
- 局部坐标系: `geometry.activate_wcs(path, ...)`
- 布尔运算: `geometry.boolean_add`, `geometry.boolean_subtract`
- 变换: `geometry.translate`, `geometry.rotate`, `geometry.mirror`
- 材质赋予: `materials.set_material(path, ...)`

## 5. Array 构建 (可选)
如果需要创建大量周期或非周期阵列。
- `array.build_array(path, unit_builder, elements)`

## 6. Boundary & Port 设置
设置仿真边界和激励端口。
- `boundary.set_all(path, ...)` 或 `boundary.set_unit_cell(path, ...)`
- `port.define_waveguide(path, ...)` 或 `port.define_floquet(path, ...)`

## 7. Monitors 设置
添加场监视器和探针。
- `monitors.set_farfield(path, ...)`
- `monitors.set_efield(path, ...)`
- `monitors.set_probe(path, ...)`

## 8. Mesh & Solver 配置
设置网格精度与求解器，并定义求解频率。
- `mesh.settings(path, ...)`
- `solver.set_frequency_range(path, ...)`
- `mesh.acceleration(path, ...)`

## 9. Simulation & Results
开始仿真，等待完成并获取结果。
- `solver.start(path)` 阻塞运行, 或 `solver.start_async` + `solver.wait(path)`
- `results.get_sparam(path, ...)`
- `farfield.export_grid(path, ...)`

## 10. 保存与清理
保存结果并关闭 CST。
- `session.save_project(path)`
- `session.close_project(path)`
- `session.quit_cst(path)`
