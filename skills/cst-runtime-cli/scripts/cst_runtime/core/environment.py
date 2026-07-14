from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
import json
import re

from .errors import error_response


# 扫描常见的 CST Studio Suite 安装路径，按优先级顺序排列
_COMMON_CST_PATHS = [
    r"C:\Program Files\CST Studio Suite 2026\AMD64\python_cst_libraries",
    r"C:\Program Files (x86)\CST Studio Suite 2026\AMD64\python_cst_libraries",
    r"D:\Program Files (x86)\CST Studio Suite 2022\AMD64\python_cst_libraries",
    r"D:\Program Files\CST Studio Suite 2022\AMD64\python_cst_libraries"
]

def load_cst_config(workspace_root: str = "") -> dict[str, Any]:
    """
    读取项目配置文件。如果不存在则创建一个带默认值的。
    """
    # 确定配置文件的绝对路径
    if workspace_root:
        config_path = Path(workspace_root).resolve() / ".cst_config.json"
    else:
        config_path = Path.cwd().resolve() / ".cst_config.json"
        
    # 定义你设想的分类字典结构（默认配置）
    default_config = {
        "project": {
            "cst_path": r"D:\Program Files\CST Studio Suite 2022\AMD64\python_cst_libraries",
            "description": "项目运行所依赖的 CST 接口路径"
        }
    }
    # 如果文件不存在，我们就抛出警告并创建一个
    if not config_path.exists():
        import warnings
        warnings.warn(f"未找到配置文件，已在 {config_path} 创建默认配置。请确认 CST 路径是否正确。")
        # 把字典写入文件，indent=4 表示漂亮地缩进换行
        config_path.write_text(json.dumps(default_config, indent=4), encoding="utf-8")
        return default_config
        
    # 如果文件存在，读取它并转为 Python 字典
    content = config_path.read_text(encoding="utf-8")
    return json.loads(content)


def extract_cst_version_from_path(cst_path: str) -> str:
    """
    从绝对路径中提取 CST 的版本年份（例如返回 "2022"）。
    如果提取失败，返回 "Unknown"。
    """
    # re.search 会在字符串中寻找符合规律的片段
    match = re.search(r"CST Studio Suite (\d{4})", cst_path)
    if match:
        # group(1) 就是我们刚才用括号 () 括起来的那 4 个数字
        return match.group(1) 
    return "Unknown"


def _probe_path(path_str: str) -> dict[str, Any]:
    """探测指定路径是否是一个合法的 CST Python 接口库。

    该函数会进行“鸭子类型校验”，不仅检查文件夹是否存在，还会检查
    内部是否包含 'cst' 包、'interface' 模块以及 'results.py' 文件。

    Args:
        path_str (str): 待检查的本地绝对路径。

    Returns:
        dict[str, Any]: 包含探测结果的字典，包括 'exists', 'has_interface' 等布尔标志。
    """
    # 转为 Path 对象并解析为绝对路径
    p = Path(path_str).expanduser().resolve()
    # 初始化结果字典，包含路径信息和检查结果
    result: dict[str, Any] = {
        "path": str(p),
        "exists": p.is_dir(),
        "has_interface": False,
        "has_results": False,
        "files_accessible": False,
    }
    if p.is_dir():
        cst_pkg = p / "cst"
        # 严格检查 cst 包是否存在 interface 和 results.py 文件
        result["has_interface"] = (cst_pkg / "interface").is_dir() if cst_pkg.is_dir() else False
        result["has_results"] = (cst_pkg / "results.py").is_file() if cst_pkg.is_dir() else False
        # 检查目录是否可访问（尝试列出文件）
        try:
            next(p.iterdir())
            result["files_accessible"] = True
        except PermissionError:
            pass
    return result

def _scan_registry() -> list[dict[str, Any]]:
    """扫描 Windows 注册表寻找 CST 安装信息。

    通过读取 HKEY_LOCAL_MACHINE\\SOFTWARE\\CST AG\\CST Studio Suite，
    遍历所有版本号并提取 'Installation Directory'。
    这是在 Windows 环境下最稳定、推荐的探测方式。

    Returns:
        list[dict[str, Any]]: 包含所有从注册表中发现并校验通过的 CST 路径字典列表。
    """
    found: list[dict[str, Any]] = []
    try:
        import winreg
        # 打开注册表键以查找 CST Studio Suite 安装信息
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\CST AG\CST Studio Suite")
        i = 0
        while True:
            try:
                # 枚举注册表子键（版本号）
                version = winreg.EnumKey(key, i)
                vk = winreg.OpenKey(key, version)
                try:
                    # 查询安装目录值
                    install_dir, _ = winreg.QueryValueEx(vk, "Installation Directory")
                    py_lib = Path(install_dir) / "AMD64" / "python_cst_libraries"
                    if py_lib.is_dir():
                        # 如果路径存在，调用 _probe_path 检查其有效性，并记录来源信息
                        info = _probe_path(str(py_lib))
                        info["source"] = f"registry:CST Studio Suite {version}"
                        found.append(info)
                except FileNotFoundError:
                    pass
                winreg.CloseKey(vk)
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except (FileNotFoundError, ImportError):
        pass
    return found

def _scan_cst_named_dirs() -> list[dict[str, Any]]:
    """兜底策略：在常见的 Program Files 目录下进行通配符扫描。

    遍历如 C 盘和 D 盘的 Program Files 目录，寻找名称中包含
    'CST Studio Suite' 的文件夹，以应对注册表记录损坏的情况。

    Returns:
        list[dict[str, Any]]: 包含所有从目录扫描中发现的合法 CST 路径列表。
    """
    found: list[dict[str, Any]] = []
    search_roots = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        r"D:\Program Files",
        r"D:\Program Files (x86)",
    ]
    for root in search_roots:
        root_p = Path(root)
        if not root_p.is_dir():
            continue
        try:
            for child in root_p.iterdir():
                # 如果子目录是文件夹且名称包含 "CST Studio Suite"，则进一步检查其 Python 库路径
                if child.is_dir() and "CST Studio Suite" in child.name:
                    py_lib = child / "AMD64" / "python_cst_libraries"
                    if py_lib.is_dir():
                        info = _probe_path(str(py_lib))
                        info["source"] = f"named_dir:{child.name}"
                        found.append(info)
        except PermissionError:
            continue
    return found


def scan_cst_installations() -> dict[str, Any]:
    """环境探测总控：聚合所有探测手段的结果。

    依次执行静态路径检查、目录扫描、注册表扫描，并将结果合并。
    该函数仅负责“数据收集”，不负责判断最终使用哪一个版本。

    Returns:
        dict[str, Any]: 包含状态、找到的安装数量、详细安装列表以及当前激活路径的聚合字典。
    """
    found: list[dict[str, Any]] = []

    # 第一步：扫描常见的 CST Studio Suite 安装路径
    for raw_path in _COMMON_CST_PATHS:
        info = _probe_path(raw_path)
        info["source"] = "common_path"
        if info["exists"]:
            found.append(info)

    # 第二步：扫描命名的 CST Studio Suite 文件夹
    found.extend(_scan_cst_named_dirs())

    # 第三步：扫描 Windows 注册表以查找 CST Studio Suite 安装路径
    found.extend(_scan_registry())

    # 读取当前 pyproject.toml 中配置的 active CST 路径
    active_path = _read_active_cst_path()
    
    # 返回扫描结果，包括找到的安装路径数量、详细信息以及当前活动路径的有效性
    return {
        "status": "success",
        "found_count": len(found),
        "installations": found,
        "active_path": active_path,
        "active_valid": bool(active_path and Path(active_path).is_dir()),
    }


def _read_active_cst_path() -> str | None:
    """读取项目中当前已激活的 CST 路径。

    解析当前工作目录下的 pyproject.toml 文件，提取 `[tool.uv.sources]`
    中 `cst-studio-suite-link` 的 path 字段。

    Returns:
        str | None: 如果存在已配置的路径，则返回该绝对路径字符串；否则返回 None。
    """
    try:
        pyproject = Path.cwd().resolve() / "pyproject.toml"
        if not pyproject.exists():
            pyproject = Path(__file__).resolve().parents[3] / "pyproject.toml"
        if not pyproject.exists():
            return None
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        source = data.get("tool", {}).get("uv", {}).get("sources", {}).get("cst-studio-suite-link", {})
        if isinstance(source, dict):
            return source.get("path")
    except Exception:
        pass
    return None


def _write_pyproject_cst_path(cst_path: str, pyproject_path: str = "") -> dict[str, Any]:
    """将目标 CST 路径写入 pyproject.toml 进行依赖注入。

    使用字符串操作（而非可能会丢失格式的 toml 解析器）安全地向
    pyproject.toml 注入或更新 `cst-studio-suite-link`，并确保
    它被添加到了 `dependencies` 列表中。

    Args:
        cst_path (str): 想要注入的 CST Python 库绝对路径。
        pyproject_path (str, optional): 指定的 pyproject.toml 路径。默认为空。

    Returns:
        dict[str, Any]: 写入结果状态。
    """
    if pyproject_path:
        pyproject = Path(pyproject_path).resolve()
    else:
        pyproject = Path.cwd().resolve() / "pyproject.toml"
        if not pyproject.exists():
            pyproject = Path(__file__).resolve().parents[3] / "pyproject.toml"
    if not pyproject.exists():
        return error_response("pyproject_not_found", "No pyproject.toml found in workspace or repo root")

    original = pyproject.read_text(encoding="utf-8")

    toml_path = cst_path.replace("\\", "\\\\")
    entry = f'cst-studio-suite-link = {{ path = "{toml_path}", editable = true }}'

    # 1. 更新 [tool.uv.sources] 中的路径
    entry_start = "cst-studio-suite-link = {"
    idx = original.find(entry_start)
    if idx >= 0:
        line_end = original.find("\n", idx)
        if line_end == -1:
            line_end = len(original)
        new_content = original[:idx] + entry + original[line_end:]
    else:
        heading = "[tool.uv.sources]"
        hidx = original.find(heading)
        if hidx >= 0:
            insert_at = original.find("\n", hidx) + 1
            new_content = original[:insert_at] + entry + "\n" + original[insert_at:]
        else:
            uv_heading = "[tool.uv]"
            uvidx = original.find(uv_heading)
            if uvidx >= 0:
                insert_at = original.find("\n", uvidx) + 1
                new_content = original[:insert_at] + f"\n{heading}\n" + entry + "\n" + original[insert_at:]
            else:
                new_content = original.rstrip() + f"\n\n{uv_heading}\n\n{heading}\n" + entry + "\n"

    if new_content == original:
        return error_response("pyproject_update_failed", "Failed to modify pyproject.toml; check file format")

    # 2. 确保 cst-studio-suite-link 在 [project.dependencies] 中
    dep_name = "cst-studio-suite-link"
    deps_start = "dependencies = ["
    ds = new_content.find(deps_start)
    if ds >= 0:
        de = new_content.find("]", ds)
        if de >= 0 and f'"{dep_name}"' not in new_content[ds:de]:
            body = new_content[ds:de].rstrip()
            needs_comma = body.endswith('"')
            prefix = f',\n    "{dep_name}",' if needs_comma else f'\n    "{dep_name}",'
            new_content = new_content[:de] + prefix + new_content[de:]

    pyproject.write_text(new_content, encoding="utf-8")
    return {"status": "success", "cst_path": cst_path, "updated_file": str(pyproject)}


def auto_register_cst(workspace_root: str = "") -> dict[str, Any]:
    """自动探测并注册 CST 环境。

    高层封装函数。它会调用底层的 scan_cst_installations 进行扫描，
    如果发现系统中存在可用的 CST 且当前项目尚未配置，
    则静默地将第一个合法路径写入 pyproject.toml 中。

    Args:
        workspace_root (str, optional): 工作区根目录。默认为当前目录。

    Returns:
        dict[str, Any]: 注册结果状态字典。
    """
    scan = scan_cst_installations()
    if not scan["found_count"]:
        return {"status": "success", "cst_registered": False, "reason": "no_cst_found"}

    valid = [inst for inst in scan["installations"] if inst["has_interface"] and inst["has_results"]]
    if not valid:
        return {"status": "success", "cst_registered": False, "reason": "cst_incomplete"}

    target = valid[0]["path"]
    pyproj = Path(workspace_root).resolve() / "pyproject.toml" if workspace_root else Path.cwd().resolve() / "pyproject.toml"
    if not pyproj.exists():
        return {"status": "success", "cst_registered": False, "reason": "no_pyproject"}

    # Already configured with the same path?
    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        data = tomllib.loads(pyproj.read_text(encoding="utf-8"))
        existing = data.get("tool", {}).get("uv", {}).get("sources", {}).get("cst-studio-suite-link", {})
        if isinstance(existing, dict) and existing.get("path") == target:
            return {"status": "success", "cst_registered": True, "already_configured": True}
    except Exception:
        pass

    write_result = _write_pyproject_cst_path(target, str(pyproj))
    write_result["cst_registered"] = write_result.get("status") == "success"
    return write_result


def install_cst_libraries(cst_path: str = "", dry_run: bool = False) -> dict[str, Any]:
    """安装/绑定 CST Studio Suite Python 库。

    这是环境配置的主入口点。它会优先读取本地的 .cst_config.json 配置文件
    来确定用户期望的版本。然后校验该路径，修改 pyproject.toml，并执行冒烟测试。

    Args:
        cst_path (str, optional): 手动覆盖的目标路径。默认为空。
        dry_run (bool, optional): 是否仅进行模拟测试而不修改文件。默认为 False。

    Returns:
        dict[str, Any]: 包含配置、修改记录和导入测试结果的详细报告。
    """
    scan_result = scan_cst_installations()

    if cst_path:
        target_path = cst_path
        probe = _probe_path(target_path)
        if not probe["exists"]:
            return {
                **error_response("path_not_found", f"CST Python library path does not exist: {target_path}"),
                "scan": scan_result,
            }
    else:
        # 1. 尝试读取配置文件
        config = load_cst_config()
        preferred_path = config.get("project", {}).get("cst_path", "")
        
        # 2. 提取出有效的安装列表 (has_interface 和 has_results 均为 True)
        valid_installations = [inst for inst in scan_result["installations"] if inst["has_interface"] and inst["has_results"]]
        
        if not valid_installations:
            return {
                **error_response(
                    "cst_not_found",
                    "系统中未检测到任何有效的 CST Python 库。请检查安装或配置文件。",
                ),
                "scan": scan_result,
            }
            
        # 3. 如果配置文件有路径，按照你的思路进行严格匹配校验
        if preferred_path:
            # 看看我们配置里的路径，在不在系统真实扫描出来的 valid 列表里
            matched_inst = next((inst for inst in valid_installations if inst["path"] == preferred_path), None)
            
            if matched_inst:
                target_path = matched_inst["path"]
                # 这里就是你提到的：日志里顺便打印出版本号
                version = extract_cst_version_from_path(target_path)
                print(f"[INFO] 根据配置文件，锁定 CST 版本: {version}")
            else:
                return {
                    **error_response(
                        "cst_config_mismatch",
                        f"配置文件指定的 CST 路径不存在或无效: {preferred_path}",
                    ),
                    "scan": scan_result,
                }
        else:
            # 4. 如果没写配置（兜底），才退化到拿第一个，但这次报错不再写死 2026
            target_path = valid_installations[0]["path"]
            version = extract_cst_version_from_path(target_path)
            print(f"[WARN] 未指定 CST 路径配置，自动降级选择发现的首个有效版本: {version}")

    if dry_run:
        return {
            "status": "success",
            "dry_run": True,
            "target_path": target_path,
            "active_path_matches": target_path == scan_result.get("active_path"),
            "scan": scan_result,
        }

    if target_path == scan_result.get("active_path"):
        verify = _verify_cst_imports(target_path)
        return {
            "status": "success",
            "cst_path": target_path,
            "already_configured": True,
            "pyproject_updated": False,
            "import_verification": verify,
            "scan": scan_result,
        }

    write_result = _write_pyproject_cst_path(target_path)
    if write_result.get("status") == "error":
        return {**write_result, "scan": scan_result}

    verify = _verify_cst_imports(target_path)
    return {
        "status": "success",
        "cst_path": target_path,
        "already_configured": False,
        "pyproject_updated": True,
        "import_verification": verify,
        "scan": scan_result,
    }


def _verify_cst_imports(cst_path: str) -> dict[str, Any]:
    """执行冒烟测试：验证指定路径下的 CST 库是否能被 Python 成功导入。

    将给定的 cst_path 临时插入到 sys.path 的最前端，然后尝试
    `__import__` 核心模块。只要不抛出异常，即视为可用。

    Args:
        cst_path (str): 要测试的 CST Python 库绝对路径。

    Returns:
        dict[str, Any]: 各个子模块导入结果的状态字典。
    """
    results: dict[str, Any] = {}
    sp = str(Path(cst_path).resolve())
    if sp not in sys.path:
        sys.path.insert(0, sp)
    for mod in ("cst", "cst.interface", "cst.results"):
        try:
            __import__(mod)
            results[mod] = "success"
        except Exception as exc:
            results[mod] = f"error: {exc}"
    return results


def health_check(workspace: str = "", auto_fix: bool = True) -> dict[str, Any]:
    """执行全盘系统体检，输出诊断报告。

    对当前的 Python 环境、包管理器 uv、工作区目录结构、
    以及 CST 库的绑定状态进行全方位的诊断 (Phases 1-3)。
    
    Args:
        workspace (str, optional): 指定的工作区目录。
        auto_fix (bool, optional): 是否尝试自动修复发现的问题。默认为 True。

    Returns:
        dict[str, Any]: 结构化的体检报告，包含 overall 状态和 remaining_issues。
    """
    from . import workspace as ws_mod
    import platform

    skill_root = ws_mod.skill_root()
    scripts_root = ws_mod.scripts_root()
    ws_info = ws_mod.workspace_status(workspace)

    def _r(name: str, status: str, **kw: Any) -> dict[str, Any]:
        return {"name": name, "status": status, **kw}

    phases: dict[str, Any] = {}
    fixes_applied: list[str] = []

    # ── Phase 1: Workspace + Platform ──
    ws_checks: list[dict[str, Any]] = []

    # 1a. Python version
    py_ok = sys.version_info >= (3, 12)
    ws_checks.append(_r("python_version", "pass" if py_ok else "error",
        version=sys.version, required=">=3.12",
        user_action="Install Python 3.12+" if not py_ok else ""))

    # 1b. uv
    uv_path = shutil.which("uv")
    ws_checks.append(_r("uv", "pass" if uv_path else "warning",
        path=uv_path, user_action="Install uv from https://astral.sh/uv" if not uv_path else ""))

    # 1c. Workspace
    ws_ok = ws_info["workspace_initialized"]
    ws_fixed = False
    if not ws_ok and auto_fix:
        try:
            fix = ws_mod.init_workspace(workspace)
            if fix.get("status") == "success":
                ws_fixed = True
                fixes_applied.append("workspace: initialized workspace")
                ws_info = ws_mod.workspace_status(workspace)
                ws_ok = True
        except Exception:
            pass
    ws_checks.append(_r("workspace", "pass" if ws_ok else "error",
        root=ws_info.get("workspace_root"), marker=ws_info.get("workspace_marker"),
        auto_fixed=ws_fixed,
        user_action="Run init-workspace --workspace <path>" if not ws_ok and not auto_fix else ""))

    # 1d. Skill package
    pkg_ok = (scripts_root / "cst_runtime").exists()
    ws_checks.append(_r("skill_package", "pass" if pkg_ok else "error",
        skill_root=str(skill_root), scripts_root=str(scripts_root)))

    # 1e. stdin
    stdin_info = {"isatty": False, "readable": False}
    for attr in ("isatty", "readable"):
        try:
            stdin_info[attr] = getattr(sys.stdin, attr)()
        except Exception:
            pass
    ws_checks.append(_r("stdin", "success", **stdin_info))

    # 1f. encoding
    ws_checks.append(_r("encoding", "success",
        stdout_encoding=getattr(sys.stdout, "encoding", None),
        stderr_encoding=getattr(sys.stderr, "encoding", None),
        filesystem_encoding=sys.getfilesystemencoding()))

    # 1g. cst_runtime package deployment
    _ws_root = Path(str(ws_info.get("workspace_root", ""))) if ws_info.get("workspace_root") else None
    rt_dir = (_ws_root / ".cst_runtime") if _ws_root else None
    rt_deployed = bool(rt_dir and (rt_dir / "cst_runtime").is_dir())
    rt_importable = False
    if rt_deployed:
        try:
            __import__("cst_runtime")
            rt_importable = True
        except Exception:
            pass
    ws_checks.append(_r("cst_runtime_package", "pass" if rt_importable else "error",
        deployed=rt_deployed, importable=rt_importable,
        path=str(rt_dir) if rt_dir else "",
        user_action="" if rt_importable else "Run bootstrap.py or uv pip install -e .cst_runtime/"))

    ws_status = "pass"
    for c in ws_checks:
        if c["status"] == "error":
            ws_status = "error"
            break
        if c["status"] == "warning":
            ws_status = "degraded"
    phases["workspace"] = {"status": ws_status, "checks": ws_checks, "auto_fixed": ws_fixed}

    # ── Phase 2: CST Environment ──
    cst_checks: list[dict[str, Any]] = []

    # 2a. pyproject CST path dependency
    ws_root = Path(str(ws_info.get("workspace_root", "")))
    pyproject_path = ws_root / "pyproject.toml"
    cst_link_path = None
    if pyproject_path.exists():
        try:
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            src = tomllib.loads(pyproject_path.read_text(encoding="utf-8")).get("tool", {}).get("uv", {}).get("sources", {}).get("cst-studio-suite-link", {})
            if isinstance(src, dict):
                cst_link_path = src.get("path")
        except Exception:
            pass
    cst_link_ok = bool(cst_link_path and Path(str(cst_link_path)).is_dir())
    cst_checks.append(_r("pyproject_cst_path", "pass" if cst_link_ok else "info",
        path=cst_link_path))

    # 2b. CST installation scan
    scan = scan_cst_installations()
    cst_found = scan["found_count"] > 0
    cst_valid = any(inst["has_interface"] and inst["has_results"] for inst in scan["installations"])
    cst_configured = scan["active_valid"]

    cst_fixed = False
    if not cst_configured and cst_valid and auto_fix:
        try:
            install_result = install_cst_libraries()
            if install_result.get("status") == "success":
                cst_fixed = True
                fixes_applied.append(f"cst: configured {install_result.get('cst_path', '')}")
                scan = scan_cst_installations()
                cst_configured = True
        except Exception:
            pass

    if not cst_found:
        cst_status, cst_msg = "error", "No CST Studio Suite installation detected"
    elif not cst_valid:
        cst_status, cst_msg = "error", "CST found but Python libraries incomplete"
    elif not cst_configured:
        cst_status, cst_msg = "warning", "CST libraries found but not configured"
    else:
        cst_status, cst_msg = "pass", f"CST libraries at {scan['active_path']}"
    cst_checks.append(_r("cst_libraries", cst_status, message=cst_msg, auto_fixed=cst_fixed))

    # 2c. Import checks
    for mod_name in ("cst_runtime", "cst.interface", "cst.results"):
        try:
            __import__(mod_name)
            cst_checks.append(_r(f"import:{mod_name}", "pass"))
        except Exception as exc:
            cst_checks.append(_r(f"import:{mod_name}", "error", message=str(exc)))

    cst_status_agg = "pass"
    for c in cst_checks:
        if c["status"] == "error":
            cst_status_agg = "error"
            break
        if c["status"] == "warning":
            cst_status_agg = "degraded"
    phases["cst"] = {"status": cst_status_agg, "checks": cst_checks, "auto_fixed": cst_fixed}

    # ── Phase 3: Integration (diagnostic only) ──
    venv_ok = (ws_root / ".venv").is_dir()
    cst_runtime_ok = rt_importable
    status_checks_ok = all(c["status"] != "error" for c in ws_checks + cst_checks)
    integration_status = "pass" if (venv_ok and cst_runtime_ok) else "degraded" if status_checks_ok else "skipped"
    integration_msg = []
    if not venv_ok:
        integration_msg.append("no .venv (run bootstrap.py to deploy)")
    if not cst_runtime_ok:
        integration_msg.append("cst_runtime not importable (run bootstrap.py to deploy)")
    phases["integration"] = {
        "status": integration_status,
        "check": {"venv": venv_ok, "cst_runtime_importable": cst_runtime_ok},
        "message": "; ".join(integration_msg) if integration_msg else "ready",
    }

    # ── Overall readiness ──
    has_error = any(p.get("status") == "error" for p in phases.values())
    has_warning = any(p.get("status") in ("degraded", "warning") for p in phases.values())
    overall = "blocked" if has_error else ("degraded" if has_warning else "pass")

    # ── remaining_issues + user_instructions ──
    remaining_issues: list[dict[str, str]] = []
    for phase_name, phase_data in phases.items():
        for c in phase_data.get("checks", []):
            if c.get("status") not in ("pass", "success"):
                remaining_issues.append({
                    "phase": phase_name,
                    "name": c["name"],
                    "status": c["status"],
                    "detail": c.get("message", c.get("user_action", c.get("status", ""))),
                })

    _instructions_by_status: dict[str, str] = {
        "blocked": "Fix the issues listed in remaining_issues before proceeding.",
        "degraded": "System is usable but has non-blocking issues. See remaining_issues.",
        "pass": "All checks passed. System is ready.",
    }

    return {
        "status": "success",
        "overall": overall,
        "remaining_issues": remaining_issues,
        "user_instructions": _instructions_by_status.get(overall, "Unknown system status."),
        "phases": phases,
        "fixes_applied": fixes_applied,
        "workspace": {
            "root": ws_info.get("workspace_root"),
            "initialized": ws_info["workspace_initialized"],
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
    }
