# MCP Exposure

| Module | Function | Status | MCP | Reason |
| ------ | -------- | ------ | --- | ------ |
| array | build_array | Stable | Yes | 复杂阵列构建 |
| boundary | set_all | Stable | Yes | 基础设置 |
| boundary | set_per_face | Stable | Yes | 基础设置 |
| boundary | set_unit_cell | Stable | Yes | 基础设置 |
| cross_process | CrossProcessSweep | Experimental | No | 特定业务逻辑，建议作为example |
| cross_process | quick_cross_sweep | Experimental | No | 特定业务逻辑 |
| farfield | export_grid | Stable | Yes | 数据导出 |
| farfield | export_cut | Stable | Yes | 数据导出 |
| farfield | list_monitors | Stable | Yes | 状态查询 |
| geometry | brick, cylinder, cone, rectangle | Stable | Yes | 基础几何构建 |
| geometry | boolean_* | Stable | Yes | 布尔运算 |
| geometry | delete_* | Stable | Yes | 实体/组件删除 |
| geometry | transform (rotate, mirror, translate) | Stable | Yes | 几何变换 |
| geometry | wcs (activate, deactivate) | Stable | Yes | 坐标系操作 |
| geometry | arc, polygon | Stable | Yes | 复杂几何 |
| materials | define, define_from_mtd | Stable | Yes | 材质创建 |
| materials | list_materials, exists, set_material | Stable | Yes | 材质管理 |
| mesh | settings, acceleration, set_* | Stable | Yes | 网格与加速设置 |
| monitors | set_*, delete_* | Stable | Yes | 监视器与探针管理 |
| optimization | create_study, ask, tell, best | Stable | Yes | 优化器接口 |
| parameters | list_params, get_param, set_param... | Stable | Yes | 参数管理 |
| port | define_waveguide, define_floquet | Stable | Yes | 端口定义 |
| results | get_sparam, list_*, export_all... | Stable | Yes | 结果读取与导出 |
| session | open, close, create_blank, save, quit | Stable | Yes | 工程生命周期管理 |
| session | inspect, list_open, is_locked | Internal | No | 内部辅助功能，MCP 侧可通过专门 tool 整合 |
| solver | start, wait, is_running, stop, rebuild, delete_results, set_freq_range | Stable | Yes | 仿真与求解器控制 |
| sweep | ParameterSweep, quick_sweep, load_lut, interpolate_lut | Stable | Yes | 参数扫描 |
| unit_cells | UnitCellBase | Stable | No | Python开发者扩展用接口 |

