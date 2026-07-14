import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 将 skills 下的模块路径拼接到根目录后，加入系统搜索路径
RUNTIME_SCRIPTS_PATH = PROJECT_ROOT / "skills" / "cst-runtime-cli" / "scripts"
sys.path.insert(0, str(RUNTIME_SCRIPTS_PATH))

# 导入我们刚刚写的代理层
from cst_runtime.core.proxy import call_cst, CSTWorkerProxy

def main():
    print("=== [1] 开始通过跨进程代理启动 CST ===")
    test_file_path = str(Path(__file__).resolve().parent / "test_hello_cst.cst")
    
    if Path(test_file_path).exists():
        Path(test_file_path).unlink()

    # 通过 proxy 发送命令给 Python 3.9 Worker
    print("正在唤醒后端的 Python 3.9 环境，并通过它启动 CST，请耐心等待...")
    result = call_cst("core.session", "create_blank_project", project_path=test_file_path)
    
    if result.get("status") == "success":
        print(f"\n🎉 成功！CST 跨进程启动完美通过。")
        print(f"空白项目已创建在: {test_file_path}")
        print("💡 看看你的任务栏，是不是已经出现了 CST 的软件窗口？")
        
        input("\n按【回车键】将自动关闭工程并退出 CST...")
        
        print("\n=== [2] 正在安全清理进程 ===")
        call_cst("core.session", "close_project", project_path=test_file_path, save=False)
        call_cst("core.session", "quit_cst")
        
        # 通知 worker 退出
        CSTWorkerProxy.get_instance().shutdown()
        
        print("CST 进程及 Worker 后端已安全结束！")
    else:
        print(f"\n❌ 连接失败，报错信息如下：\n{result}")
        CSTWorkerProxy.get_instance().shutdown()

if __name__ == "__main__":
    main()