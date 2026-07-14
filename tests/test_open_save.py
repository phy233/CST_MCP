import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_SCRIPTS_PATH = PROJECT_ROOT / "skills" / "cst-runtime-cli" / "scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS_PATH))

from cst_runtime.core.proxy import CSTWorkerProxy

def main():
    print("=== 开始现有工程操作测试 ===")
    
    # 1. 指定要操作的文件路径 (使用刚刚建好的 test_hello_cst.cst)
    test_file_path = str(Path(__file__).resolve().parent / "test_hello_cst.cst")
    print(f"\n1. 准备操作工程: {test_file_path}")
    
    # 获取代理实例 (此时会在后台拉起 Python 3.9 环境)
    proxy = CSTWorkerProxy.get_instance()
    
    def call_cst(module_name: str, func_name: str, **kwargs):
        return proxy.call(module_name, func_name, **kwargs)

    # 2. 打开已经存在的工程 (而不是 create_blank_project)
    print("\n2. 正在通过 IPC 打开现有工程 (open_project)...")
    res_open = call_cst("core.session", "open_project", project_path=test_file_path)
    if res_open.get("status") != "success":
        print(f"❌ 打开工程失败: {res_open}")
        return
    print("✅ 工程已成功打开！")
    
    # 3. 对工程做一些修改：比如我们再在刚才的基础上，增加一个空气腔
    print("\n3. 正在往现有工程中追加一个空气腔 (Air Box)...")
    res_box = call_cst(
        "lib.geometry", 
        "brick", 
        project_path=test_file_path,
        name="AirBox",
        component="Metasurface",
        material="Vacuum", 
        x_range=(-10, 10), 
        y_range=(-10, 10), 
        z_range=(1, 10)
    )
    if res_box.get("status") != "success":
        print(f"❌ 绘制空气腔失败: {res_box}")
    else:
        print("✅ 追加空气腔成功！")
        
    print("\n👀 你现在可以在 CST 中看到新加的空气腔 (AirBox)！")
    input("👉 请按【回车键】继续，程序将执行【保存】并【安全退出】...")

    # 4. 保存并安全关闭当前工程
    print("\n4. 正在保存工程并释放锁 (close_project)...")
    res_close = call_cst(
        "core.session", 
        "close_project", 
        project_path=test_file_path, 
        save=True,               # 【关键参数】设置为 True 表示保存工程
        kill_processes=True      # 关闭可能残留的僵尸进程
    )
    if res_close.get("status") == "success":
        print("✅ 工程保存并关闭成功！")
    else:
        print(f"❌ 工程关闭失败: {res_close}")

    # 5. 彻底退出 CST 实例
    print("\n5. 彻底清理 CST 进程驻留 (quit_cst)...")
    call_cst("core.session", "quit_cst", project_path=test_file_path)
    print("✅ CST 进程树已完全清理！测试结束。")

if __name__ == "__main__":
    main()
