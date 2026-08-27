"""L1/L2 双态长任务生命周期的离线测试。

覆盖冻结计划 v3.3：
- 阶段信标 write/read/grace 判定；
- get_long_run_threshold 配置解析与钳制；
- run_experiment 自动让出（long_run_relinquish）与显式上限传统语义；
- wait-simulation 省缺 timeout_seconds 的自动让出与显式传值旧行为；
- 架构守护：cst_runtime 不依赖 mcp_server。
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from cst_runtime.lib.contracts import success_result


# ── 架构守护 ──


def test_runtime_never_imports_mcp_server() -> None:
    """runtime-cli 必须可脱离 MCP 独立使用：禁止反向依赖。"""
    scripts_root = Path(__file__).resolve().parents[1] / "scripts" / "cst_runtime"
    violations: list[str] = []
    for path in scripts_root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_bytes().decode("utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            for module in names:
                if module == "mcp_server" or module.startswith("mcp_server."):
                    violations.append(f"{path.name}:{node.lineno}:{module}")
    assert violations == []


# ── 阶段信标 ──


@pytest.fixture()
def beacon_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_beacon_write_read_roundtrip(beacon_cwd):
    from cst_runtime.core import phase_beacon as beacon

    assert beacon.write_phase("C:/work/model.cst", beacon.POLLING) is True
    data = beacon.read_phase("C:/work/model.cst")
    assert data["phase"] == beacon.POLLING
    assert data["pid"] > 0
    # 归一化不敏感：同义路径命中同一信标
    assert beacon.read_phase("c:\\WORK\\model.cst")["phase"] == beacon.POLLING


def test_beacon_grace_gate(beacon_cwd):
    from cst_runtime.core import phase_beacon as beacon

    assert beacon.phase_allows_grace("C:/work/model.cst") is False

    beacon.write_phase("C:/work/model.cst", beacon.POLLING)
    assert beacon.phase_allows_grace("C:/work/model.cst") is False

    beacon.write_phase("C:/work/model.cst", beacon.POSTFLIGHT)
    assert beacon.phase_allows_grace("C:/work/model.cst") is True

    beacon.write_phase("C:/work/model.cst", beacon.CLOSING)
    assert beacon.phase_allows_grace("C:/work/model.cst") is True


def test_beacon_stale_entry_is_not_grace(beacon_cwd, monkeypatch):
    from cst_runtime.core import phase_beacon as beacon

    beacon.write_phase("C:/work/model.cst", beacon.CLOSING)
    path = beacon._beacon_path("C:/work/model.cst")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["updated_at"] -= beacon.FRESHNESS_SECONDS + 1.0
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert beacon.phase_allows_grace("C:/work/model.cst") is False


# ── 阈值配置 ──


def test_threshold_default_without_config(beacon_cwd):
    from cst_runtime.core.environment import get_long_run_threshold

    assert get_long_run_threshold() == 600


def test_threshold_reads_config_and_clamps(beacon_cwd):
    from cst_runtime.core.environment import get_long_run_threshold

    (beacon_cwd / ".cst_config.json").write_text(
        json.dumps({"runtime": {"long_run_threshold_seconds": 36000}}),
        encoding="utf-8",
    )
    assert get_long_run_threshold() == 36000

    (beacon_cwd / ".cst_config.json").write_text(
        json.dumps({"runtime": {"long_run_threshold_seconds": 5}}),
        encoding="utf-8",
    )
    assert get_long_run_threshold() == 60

    (beacon_cwd / ".cst_config.json").write_text("not-json", encoding="utf-8")
    assert get_long_run_threshold() == 600


# ── run_experiment 双语义 ──


def _patch_experiments(monkeypatch, *, running_value=True, close_calls=None,
                       list_run_ids=None):
    from cst_runtime.lib import experiments as ex
    from cst_runtime.lib.contracts import error_result

    if close_calls is None:
        close_calls = []
    if list_run_ids is None:
        # 默认：结果节点不存在（error）且树枚举确认缺失 ⇒ 合法空基线
        list_run_ids = lambda *a, **kw: error_result(
            "list_run_ids_failed", "tree path not found: stub"
        )
    monkeypatch.setattr(
        ex, "get_background",
        lambda _p: success_result(farfield_compatible=True, background_type="Normal"),
    )
    monkeypatch.setattr(ex, "list_monitors", lambda _p: success_result(monitors=[]))
    monkeypatch.setattr(
        ex, "list_result_items",
        lambda project_path=None, **kw: success_result(items=[]),
    )
    monkeypatch.setattr(ex, "list_run_ids", list_run_ids)
    monkeypatch.setattr(ex, "capture_solver_log_baseline", lambda _p: {})
    monkeypatch.setattr(
        ex, "read_appended_solver_logs",
        lambda _p, baseline=None: success_result(
            errors=[], error_lines=[], log_files=[], log_tails={}
        ),
    )
    monkeypatch.setattr(ex, "open_project", lambda p: success_result(project_path=p))
    monkeypatch.setattr(ex, "start_simulation_async", lambda p: success_result())
    monkeypatch.setattr(
        ex, "is_simulation_running",
        lambda p: success_result(running=running_value),
    )
    monkeypatch.setattr(
        ex, "close_project",
        lambda p, **kw: (close_calls.append(p), success_result())[1],
    )
    monkeypatch.setattr(ex.time, "sleep", lambda _s: None)
    return ex


def test_run_experiment_auto_relinquish(beacon_cwd, monkeypatch):
    from cst_runtime.core.relinquish import RELINQUISH_ERROR_TYPE  # noqa: F401  存在性
    from cst_runtime.lib import experiments as ex

    close_calls: list = []
    ex = _patch_experiments(monkeypatch, running_value=True, close_calls=close_calls)
    monkeypatch.setattr(ex, "get_long_run_threshold", lambda: 0.5)

    result = ex.run_experiment(
        "C:/work/model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        poll_interval_seconds=0.1,
    )

    assert result["status"] == "error"
    assert result["error_type"] == "long_run_relinquish"
    assert result["terminal"] is True
    assert result["await_user_decision"] is True
    assert result["timeout_class"] == "expected_simulation"
    assert result["solver_left_running"] is True
    assert result["recovery"] and result["next_action"]
    # 让出路径不做任何收尾：工程保持打开、CST 不被触碰
    assert close_calls == []


def test_run_experiment_explicit_timeout_keeps_legacy_cap(beacon_cwd, monkeypatch):
    from cst_runtime.lib import experiments as ex

    close_calls: list = []
    ex = _patch_experiments(monkeypatch, running_value=True, close_calls=close_calls)
    # 显式传值时禁用自动让出：即使阈值更小也不应 relinquish
    monkeypatch.setattr(ex, "get_long_run_threshold", lambda: 0.1)

    result = ex.run_experiment(
        "C:/work/model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        timeout_seconds=0.3,
        poll_interval_seconds=0.1,
    )

    assert result["error_type"] == "pipeline_sim_timeout"
    assert "terminal" not in result
    assert close_calls == ["C:/work/model.cst"]


def test_run_experiment_completed_below_threshold(beacon_cwd, monkeypatch):
    """solver 正常结束仍走原验证链路（stub 使首查即停）。"""
    from cst_runtime.lib import experiments as ex
    from cst_runtime.lib.contracts import error_result, success_result

    ex = _patch_experiments(monkeypatch, running_value=False)
    state = {"post": False}

    def _list_run_ids(*a, **kw):
        # preflight 报节点缺失（合法空基线），postflight 返回本次新 Run ID
        if state["post"]:
            return success_result(run_ids=[7])
        state["post"] = True
        return error_result("list_run_ids_failed", "tree path not found: pre")

    monkeypatch.setattr(ex, "list_run_ids", _list_run_ids)
    monkeypatch.setattr(
        ex, "inspect_1d_result",
        lambda p, path, run_id, **kw: success_result(
            result_path=path, run_id=run_id, point_count=2,
            xdata=[1.0, 2.0], ydata=[{"real": 1.0, "imag": 0.0}, {"real": 0.0, "imag": 1.0}],
        ),
    )

    result = ex.run_experiment(
        "C:/work/model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        poll_interval_seconds=0.1,
    )
    assert result["status"] == "success"
    assert result["run_id"] == 7
    assert result["s11_metric"]["point_count"] == 2


# ── wait-simulation 双语义 ──


class _FakeClock:
    """monotonic 每次调用推进一个步长，避免真实等待。"""

    def __init__(self, step: float = 0.2) -> None:
        self.step = step
        self.value = 0.0

    def monotonic(self) -> float:
        self.value += self.step
        return self.value

    def time(self) -> float:
        return self.value

    def sleep(self, _s: float) -> None:
        self.value += self.step


def _patch_wait_context(monkeypatch, clock):
    from cst_runtime.tools import project as project_module

    monkeypatch.setattr(project_module, "time", clock)
    monkeypatch.setattr(
        project_module, "_sim",
        SimpleNamespace(
            is_simulation_running=lambda path: success_result(
                project_path=path, running=True
            )
        ),
    )
    monkeypatch.setattr(
        project_module, "_sv",
        SimpleNamespace(
            load_log_baseline=lambda path: success_result(baseline={}),
            capture_log_baseline=lambda path: success_result(baseline={"x": 0}),
            read_solver_errors=lambda path, baseline=None, since=None: success_result(
                errors=[], error_lines=[], log_files=[]
            ),
        ),
    )


def test_wait_simulation_auto_relinquish(beacon_cwd, monkeypatch):
    from cst_runtime.tools.project import tool_wait_simulation

    clock = _FakeClock(step=0.2)
    _patch_wait_context(monkeypatch, clock)
    monkeypatch.setattr(
        "cst_runtime.core.environment.get_long_run_threshold", lambda: 0.5
    )

    result = tool_wait_simulation({"project_path": "C:/work/model.cst"})

    assert result["status"] == "error"
    assert result["error_type"] == "long_run_relinquish"
    assert result["terminal"] is True
    assert result["running"] is True
    assert result["source_tool"] == "wait-simulation"


def test_wait_simulation_explicit_timeout_legacy(beacon_cwd, monkeypatch):
    from cst_runtime.tools.project import tool_wait_simulation

    clock = _FakeClock(step=0.2)
    _patch_wait_context(monkeypatch, clock)

    result = tool_wait_simulation(
        {"project_path": "C:/work/model.cst", "timeout_seconds": 0.3}
    )

    assert result["error_type"] == "simulation_wait_timeout"
    assert "terminal" not in result
