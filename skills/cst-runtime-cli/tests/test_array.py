import sys
import os
import shutil

project_root = r"D:\My_Program\Python\CST_MCP\skills\cst-runtime-cli\scripts"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import cst.interface
from cst_runtime.lib.session import create_blank_project, save_project
from cst_runtime.lib.geometry import brick, boolean_add
from cst_runtime.lib.array import build_array, ArrayElement, BuildResult
from cst_runtime.core.utils import abs_project_path

def build_cross(project_path: str, element: ArrayElement) -> BuildResult:
    code = element.code or 1
    # 利用 code 来确保模板名称唯一，防止被 CST 重命名
    arm_h = f"arm_h_{code}"
    arm_v = f"arm_v_{code}"
    
    # 模拟不同的 code 生成不同尺寸的实体
    length = 5.0 if code == 1 else 7.0
    
    brick(project_path,
          component="metasurface", name=arm_h, material="PEC",
          x_range=(-length, length), y_range=(-1, 1), z_range=(0, 0.5))
    brick(project_path,
          component="metasurface", name=arm_v, material="PEC",
          x_range=(-1, 1), y_range=(-length, length), z_range=(0, 0.5))
    
    boolean_add(project_path, f"metasurface:{arm_h}", f"metasurface:{arm_v}")
    
    return BuildResult(
        component="metasurface",
        reference_names=[arm_h]
    )

def main():
    print("=== Phase 3: Array Workflow Test ===")
    
    project_name = os.path.join(project_root, "test_array.cst")
    target_cst = abs_project_path(project_name)
    target_dir = target_cst[:-4]  # 移除 .cst 获取同名文件夹
    
    if os.path.exists(target_cst):
        print(f"[*] 删除已存在的工程文件: {target_cst}")
        try:
            if os.path.isfile(target_cst):
                os.remove(target_cst)
            else:
                shutil.rmtree(target_cst)
        except Exception as e:
            print(f"无法删除旧的工程文件: {e}")
            
    if os.path.exists(target_dir):
        print(f"[*] 删除已存在的工程数据目录: {target_dir}")
        try:
            shutil.rmtree(target_dir)
        except Exception as e:
            print(f"无法删除旧的工程目录: {e}")

    print("0. Creating blank project...")
    res = create_blank_project(project_name)
    if res.get("status") != "success":
        print(f"FAILED to create project: {res}")
        return
    pp = res["project_path"]
        
    input(f"\n[*] CST 已经启动并创建了工程 '{pp}'。\n[*] 请检查 CST 窗口是否可见，然后按回车生成并发送 Batch 宏...")
    
    elements = []
    for x in range(3):
        for y in range(3):
            # 交替使用 code=1 和 code=2
            code = 1 if (x + y) % 2 == 0 else 2
            elements.append(ArrayElement(x=x * 15.0, y=y * 15.0, z=0.0, code=code))
            
    print(f"\n[*] 开始拼装 {len(elements)} 个十字阵列的 VBA 缓冲，并发送执行...")
    
    res = build_array(
        project_path=pp,
        unit_builder=build_cross,
        elements=elements,
        summary="Build 3x3 Mixed Array"
    )
    
    print("\n[*] Batch Flush 结果:", res)
    if res.get("status") == "error":
        print("\n[!] 发生错误！请检查 CST 的 Message Window (信息窗口) 中的 VBA 报错。")
        
    input("\n[*] 阵列执行完毕。请观察 CST 模型与历史树，按回车键保存工程并退出...")
        
    save_project(pp)

if __name__ == "__main__":
    main()
