# CST Runtime 2022 人工兼容冒烟测试

本文只用于人工操作。自动化测试不得启动、连接或控制 CST。

## 1. 测试前准备

1. 关闭重要的正式工程，并保存当前工作。
2. 新建专用目录，例如 `D:\CST_Runtime_Compatibility_Test`。
3. 测试工程固定使用 `D:\CST_Runtime_Compatibility_Test\smoke_2022.cst`，不要指向正式工程。
4. 如果需要远场结果，再复制一份已有结果的非正式工程为 `D:\CST_Runtime_Compatibility_Test\farfield_2022.cst`。最多使用这两个工程。
5. 记录 CST 的完整版本号：在 CST 的“帮助 → 关于”中查看，并保存截图。

每次调用后先检查返回值：

- `status` 应为 `success`；
- `compatibility.profile` 应为 `cst2022`；
- 失败时若功能确实不存在，应看到 `error_type=unsupported_feature` 和 `phase=compatibility`，不能显示假成功；
- CST Message Window 不应出现 VBA 编译错误或“对象不支持此属性/方法”。

## 2. 建议执行顺序

以下名称是 Runtime 函数名。可以从当前 MCP 工具入口逐项调用，也可以用项目现有 Worker/CLI 调用同名操作。每一步都等待完成后再继续。

### A. 会话与单位

1. 调用 `create_blank_project` 创建 `smoke_2022.cst`。
2. 调用 `list_open_projects`，确认只需活动工程回退时也能列出该路径。
3. 调用 `define_units`，所有参数保持默认值。
4. 在 CST 的 Units 对话框确认长度 `mm`、频率 `GHz`、时间 `ns`、温度单位已经应用。
5. 检查返回结果中的 `compatibility.not_applied`，应明确列出 CST 2022 无独立设置入口的电学单位。
6. 再调用一次 `define_units`，把 `voltage` 改成 `mV`；预期返回 `unsupported_feature`，并且 History 中不新增单位节点。

### B. 背景、基本几何和参数

1. 调用 `define_background(background_type="Normal")`。
2. 调用 `set_background_with_space`，使用默认空间值。
3. 创建一个参数，例如长度参数 `L=10`，再调用 `list_parameters`。
4. 确认返回中包含参数名和数值/表达式；若 Python 参数对象不可用，返回仍应通过即时 VBA 得到结果。
5. 创建一个 Brick 和一个 Cylinder，确认模型树出现实体且没有 VBA 错误。

### C. 曲线、WCS、多边形和变换

1. 调用 `activate_wcs`，原点设为 `(0, 0, 2)`，随后调用 `deactivate_wcs`。
2. 调用 `arc`，圆心 Z 坐标使用非零值，例如 `(0, 0, 2)`；确认圆弧位于 Z=2，且操作后原工作坐标系已恢复。
3. 调用 `polygon` 创建三角形或矩形拉伸实体，例如顶点 `[(0,0), (5,0), (0,5)]`、`z_range=(0,1)`。
4. 确认最终得到实体，临时二维曲线已清理，History 中没有把 `Polygon3D` 当实体生成器。
5. 对实体依次调用 `translate`、`rotate`、`mirror`。
6. `translate(destination="")` 应成功；再用非空 `destination` 调用一次，预期返回 `unsupported_feature` 且不修改模型。

### D. 边界和端口

1. 调用 `set_per_face`，X/Y 面使用 `unit cell`，Z 面使用 `open`，周期角可先设为 `0`。
2. 在 Boundary 对话框确认采用恒定周期角设置，没有 VBA 方法错误。
3. 调用 `define_waveguide`，先使用 `face="zmax"` 且不传宽高；确认端口范围来自结构包围盒。
4. 再传入较小的 `width`、`height`，确认端口仍居中且范围改变。
5. Floquet 测试前确认工程使用频域求解器和单元边界；调用 `define_floquet`，先令 Zmin/Zmax 各 2 个线极化模式。
6. 在 Floquet 端口对话框确认 Zmin/Zmax 各包含 `TE(0,0)`、`TM(0,0)`，参考面距离与输入一致。

### E. 监视器、网格和求解器

1. 调用 `set_farfield_monitor(start_freq=8, end_freq=12, step=1)`；预期旧版样本数为 5。
2. 调用 `set_efield_monitor` 使用同一频率范围。
3. 再用 `start_freq=8, end_freq=12, step=0.3` 调用监视器；预期在提交前返回验证错误，因为范围不能被步长整除。
4. 调用 `define_mesh` 使用默认参数；打开 Mesh Properties，确认每波长线数、最小步数、比例限制和网格平衡值已应用。
5. 调用 `define_solver` 使用默认参数；确认求解器设置中阻抗、激励、缓存、自适应等旧版选项正确。
6. 调用 `set_solver_acceleration` 使用默认参数，确认线程数、分布式计算、MPI 和硬件加速项可读取。
7. 调用 `set_mesh_fpbavoid_nonreg_unite`；预期直接返回 `unsupported_feature`，CST History 不应出现该命令。

### F. 保存、重开和公共查询

1. 保存工程并调用 `close_project(save=True)`。
2. 确认工程文件锁释放，再调用 `open_project` 重开同一工程。
3. 调用 `get_solver_type`，确认返回实际求解器类型。
4. 对一个已知存在和一个不存在的结果树路径分别调用 `result_item_exists`，确认返回 `true`/`false`。
5. 调用 `delete_results`；确认不要求 `model3d`，结果被删除且结构保留。
6. 调用 `list_result_items(filter_type="all")`。若当前 2022 结果库没有全量枚举能力，预期为 `unsupported_feature`，提示改用 `0D/1D` 或 `colormap`。
7. 调用 `get_2d_result`。CST 2022 不支持时，预期保留 `error_type=unsupported_feature` 和 `phase=compatibility`。

### G. 远场（仅在已有结果时执行）

不要为了本项重复创建多个工程。优先使用前述工程的一次小型仿真结果；没有结果时，才使用准备好的 `farfield_2022.cst` 副本。

1. 确认结果树中已存在 `Farfields\farfield (f=...)` 节点。
2. 调用 `export_farfield_grid`，依次测试 `Gain`、`Directivity`、`Realized Gain` 中至少一种。
3. 预期返回的 `source` 为 `FarfieldPlot`，输出 JSON 的 `sample_count` 与 theta×phi 网格数一致。
4. 检查峰值角度、波束轴向值和网格方向是否合理。
5. 对一个已有 Farfield Cut 调用 `export_farfield_cut`，确认基础 `ASCIIExport` 能产生非空 JSON。

## 3. 失败时请回传的信息

出现失败时先停止后续步骤，不要在正式工程重试。请提供：

1. 失败步骤和完整调用参数；
2. Runtime 返回的完整 JSON；
3. CST 完整版本号；
4. CST Message Window 中第一条 VBA 编译/运行错误全文；
5. History 树中失败节点的名称和生成脚本（如果节点存在）；
6. 能说明端口、WCS、网格或结果树状态的截图；
7. 是否在失败前保存过测试工程。

测试结束后关闭测试工程。保留测试目录便于复现，确认不再需要后再人工删除。
