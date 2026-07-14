import sys
import time
from pathlib import Path

# 设置环境路径以加载 proxy
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_SCRIPTS_PATH = PROJECT_ROOT / "skills" / "cst-runtime-cli" / "scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS_PATH))

from cst_runtime.core.proxy import call_cst, CSTWorkerProxy

def main():
    print("=== 开始几何建模直接指令测试 ===")
    
    # 1. 准备项目路径
    test_file_path = str(Path(__file__).resolve().parent / "test_metasurface.cst")
    if Path(test_file_path).exists():
        Path(test_file_path).unlink()

    # 2. 创建空白项目
    print("1. 正在启动 CST 并创建项目...")
    res = call_cst("core.session", "create_blank_project", project_path=test_file_path)
    if res.get("status") != "success":
        print(f"❌ 项目创建失败: {res}")
        return

    try:
        # 3. 画一个介质基板 (用默认的 Vacuum 替代，因为真实材料可能需要先加载)
        print("2. 正在绘制基板 (Substrate)...")
        res = call_cst(
            "lib.geometry", "brick",
            project_path=test_file_path,
            component="Metasurface",
            name="Substrate",
            material="Vacuum",
            x_range=(-5.0, 5.0),
            y_range=(-5.0, 5.0),
            z_range=(0.0, 1.0)
        )
        if res.get("status") != "success":
            print(f"❌ 绘制基板失败: {res}")

        # 4. 画一个顶部金属圆柱贴片 (用 PEC)
        print("3. 正在绘制顶部谐振器 (Resonator)...")
        res = call_cst(
            "lib.geometry", "cylinder",
            project_path=test_file_path,
            component="Metasurface",
            name="Resonator",
            material="PEC",
            axis="z",
            center=(0.0, 0.0),
            radius=3.0,
            z_range=(1.0, 1.05)
        )
        if res.get("status") != "success":
            print(f"❌ 绘制圆柱失败: {res}")

        print("\n🎉 建模完成！")
        
        # 5. 为了让你能看清楚建好的模型，我们保存并暂停一下
        call_cst("core.session", "save_project", project_path=test_file_path)
        input("👀 请去 CST 软件里看看画出来的 'Metasurface' 组件，看完后按【回车键】关闭退出...")

    finally:
        # 6. 安全退出
        print("\n正在清理环境...")
        call_cst("core.session", "close_project", project_path=test_file_path, save=False)
        call_cst("core.session", "quit_cst")
        CSTWorkerProxy.get_instance().shutdown()
        print("清理完毕，测试结束。")

if __name__ == "__main__":
    main()
