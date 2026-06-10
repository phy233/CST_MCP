# MATLAB → Python 功能对齐报告

## 对齐状态总览

| 状态 | MATLAB 函数 | Python 函数 | 文件位置 |
|------|------------|-------------|----------|
| ✅ 完全对齐 | `initializeCSTproj.m` | `open_project()` | `lib/session.py` |
| ✅ 完全对齐 | `quitCSTproj.m` | `close_project()`, `quit_cst()` | `lib/session.py` |
| ✅ 完全对齐 | `getParameterList.m` | `list_params()` | `lib/parameters.py` |
| ✅ 完全对齐 | `settingParameter.m` | `set_param()` | `lib/parameters.py` |
| ✅ 完全对齐 | `ensureParameterExist.m` | `param_exists()` | `lib/parameters.py` |
| ✅ 完全对齐 | `defineBrick.m` | `brick()` | `lib/geometry.py` |
| ✅ 完全对齐 | `defineCylinder.m` | `cylinder()` | `lib/geometry.py` |
| ✅ 完全对齐 | `addObj.m` | `boolean_add()` | `lib/geometry.py` |
| ✅ 完全对齐 | `substractObj.m` | `boolean_subtract()` | `lib/geometry.py` |
| ✅ 完全对齐 | `deleteObj.m` | `delete_entity()` | `lib/geometry.py` |
| ✅ 完全对齐 | `deleteComponent.m` | `delete_component()` | `lib/geometry.py` |
| ✅ 完全对齐 | `rotateObj.m` | `rotate()` | `lib/geometry.py` |
| ✅ 完全对齐 | `translationObj.m` | `translate()` | `lib/geometry.py` |
| ✅ 完全对齐 | `activateWCS.m` | `activate_wcs()`, `deactivate_wcs()` | `lib/geometry.py` |
| ✅ 完全对齐 | `defineArc.m` | `arc()` | `lib/geometry.py` |
| ✅ 完全对齐 | `defineMaterial.m` | `define()` | `lib/materials.py` |
| ✅ 完全对齐 | `check_material_exists.m` | `exists()` | `lib/materials.py` |
| ✅ 完全对齐 | `startCurrentSolver.m` | `start()`, `start_async()` | `lib/solver.py` |
| ✅ 完全对齐 | `updateStructure.m` | `rebuild()` | `lib/solver.py` |
| ✅ 完全对齐 | `deleteResult.m` | `delete_results()` | `lib/solver.py` |
| ✅ 完全对齐 | `setWorkFrequency.m` | `set_frequency_range()` | `lib/solver.py` |
| ✅ 完全对齐 | `smartReadSParameter.m` | `get_sparam()` | `lib/results.py` |
| ✅ 完全对齐 | `getSParamAtFreq.m` | `get_sparam_at_freq()` | `lib/results.py` |
| ✅ 完全对齐 | `listAvailableSParams.m` | `list_sparams()` | `lib/results.py` |
| ✅ 完全对齐 | `setFloquetPort.m` | `define_floquet()` | `lib/port.py` |
| ✅ 完全对齐 | `setUnitBoundary.m` | `set_per_face()`, `set_unit_cell()` | `lib/boundary.py` |
| ✅ 完全对齐 | `arrayModeling.m` | `build_coding_array()` | `lib/array.py` |
| ✅ 完全对齐 | `fastArrayModeling.m` | `fast_array()` | `lib/array.py` |
| ⚠️ 需要用户实现 | `unit_Cyuanhuan.m` 等 | `UnitCellBase` (抽象基类) | `lib/unit_cells.py` |
| ❌ 未实现 | `setFrequencySolver.m` | - | 需要添加 |
| ❌ 未实现 | `setBackground.m` | - | 需要添加 |
| ❌ 未实现 | `crossProcess.m` | - | 需要添加 |
| ❌ 未实现 | `rebuildLUT_Offline.m` | - | 需要添加 |
| ❌ 未实现 | `diffractionPhaseQuant.m` | - | 需要添加 |

## 详细对齐说明

### 1. 会话管理 (`lib/session.py`)

| MATLAB | Python | 差异 |
|--------|--------|------|
| `initializeCSTproj(ProjectAddress)` | `open_project(project_path)` | Python 返回 dict，MATLAB 返回 mws 对象 |
| `quitCSTproj(mws)` | `close_project()`, `quit_cst()` | Python 分离了关闭和退出 |

### 2. 参数操作 (`lib/parameters.py`)

| MATLAB | Python | 差异 |
|--------|--------|------|
| `getParameterList(mws)` | `list_params(project_path)` | Python 返回 dict，MATLAB 返回 cell |
| `settingParameter(mws, name, value)` | `set_param(project_path, name, value)` | 无差异 |
| `ensureParameterExist(mws, name)` | `param_exists(project_path, name)` | 无差异 |

### 3. 几何建模 (`lib/geometry.py`)

| MATLAB | Python | 差异 |
|--------|--------|------|
| `defineBrick(mws, name, comp, center, x, y, z, mat)` | `brick(path, comp, name, mat, x_range, y_range, z_range)` | Python 使用范围而非中心+尺寸 |
| `defineCylinder(mws, comp, name, mat, outR, inR, h, dir, center)` | `cylinder(path, comp, name, mat, axis, center, radius, z_range)` | Python 参数更清晰 |
| `translationObj(mws, obj, x, y, z, iscopy, repeat, newname)` | `translate(path, name, vector, multiple, repeat, dest)` | Python 使用 tuple |
| `rotateObj(mws, comp, name, center, angle, iscopy)` | `rotate(path, name, center, angle, multiple)` | 无差异 |
| `activateWCS(mws, normal, origin, uvector, activate)` | `activate_wcs()`, `deactivate_wcs()` | Python 分离了激活和停用 |
| `defineArc(mws, orient, center, start, theta, comp, name)` | `arc(path, name, center, radius, start_angle, end_angle)` | Python 使用半径和角度范围 |

### 4. 材料管理 (`lib/materials.py`)

| MATLAB | Python | 差异 |
|--------|--------|------|
| `defineMaterial(mws, name, eps, mu, tand, freq, trans)` | `define(path, name, epsilon, mue, tan_d, tan_d_freq, transparency)` | 无差异 |
| `check_material_exists(mws, name)` | `exists(path, name)` | Python 使用列表遍历，MATLAB 使用 COM |

### 5. 求解器控制 (`lib/solver.py`)

| MATLAB | Python | 差异 |
|--------|--------|------|
| `startCurrentSolver(mws)` | `start()`, `start_async()` | Python 支持阻塞和非阻塞 |
| `updateStructure(mws, isfull)` | `rebuild()` | Python 简化了参数 |
| `deleteResult(mws)` | `delete_results()` | 无差异 |
| `setWorkFrequency(mws, freq)` | `set_frequency_range(path, fmin, fmax)` | 无差异 |

### 6. 结果读取 (`lib/results.py`)

| MATLAB | Python | 差异 |
|--------|--------|------|
| `smartReadSParameter(mws, name)` | `get_sparam(path, treepath)` | Python 使用 cst.results 离线读取 |
| `getSParamAtFreq(freq, re, im, target)` | `get_sparam_at_freq(path, treepath, freq)` | Python 自动读取数据 |
| `listAvailableSParams(mws)` | `list_sparams(path)` | 无差异 |

### 7. 边界条件 (`lib/boundary.py`)

| MATLAB | Python | 差异 |
|--------|--------|------|
| `setUnitBoundary(mws)` | `set_unit_cell()`, `set_per_face()` | Python 支持自定义边界 |

### 8. 端口配置 (`lib/port.py`)

| MATLAB | Python | 差异 |
|--------|--------|------|
| `setFloquetPort(mws, zmin, zmax, circular)` | `define_floquet(path, zmin_modes, zmax_modes, ...)` | Python 参数更丰富 |

### 9. 阵列建模 (`lib/array.py`)

| MATLAB | Python | 差异 |
|--------|--------|------|
| `arrayModeling(mws, params, matrix, layer)` | `build_coding_array(path, matrix, unit_type, dx, dy)` | Python 简化了参数 |
| `fastArrayModeling(mws, template, positions)` | `fast_array(path, template, positions)` | 无差异 |

### 10. 单元格类 (`lib/unit_cells.py`)

| MATLAB | Python | 差异 |
|--------|--------|------|
| `unit_Cyuanhuan.m`, `unit_gongzixing.m` 等 | `UnitCellBase` (抽象基类) | Python 需要用户继承实现 |

## 未实现功能

### P2 优先级（高级功能）

1. **`setFrequencySolver.m`** - 频域求解器配置
   - 需要在 `lib/solver.py` 中添加 `set_fd_solver()` 函数

2. **`setBackground.m`** - 背景材料设置
   - 需要在 `lib/boundary.py` 或新建 `lib/background.py` 中添加

3. **`crossProcess.m`** - 参数扫频 + LUT
   - 需要在 `lib/optimization.py` 中添加

4. **`rebuildLUT_Offline.m`** - LUT 离线重建
   - 需要在 `lib/optimization.py` 中添加

5. **`diffractionPhaseQuant.m`** - 相位量化
   - 需要在 `lib/results.py` 或新建 `lib/analysis.py` 中添加

## 建议

1. **已完成**: 核心功能（会话、参数、几何、材料、求解器、结果、边界、端口、阵列）已完全对齐
2. **待完善**: 高级功能（频域求解器、背景设置、参数扫频）需要补充
3. **用户自定义**: 单元格类需要用户继承 `UnitCellBase` 实现
