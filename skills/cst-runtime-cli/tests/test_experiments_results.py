"""run-experiment 的通用结果完成性验证。"""
from __future__ import annotations

from cst_runtime.lib.contracts import error_result, success_result


def _patch_experiment_pipeline(monkeypatch, *, background=None, monitors=None,
                               diagnostics=None, close=None):
    """打桩 run_experiment 的求解链路与预检依赖。"""
    from cst_runtime.lib import experiments

    monkeypatch.setattr(
        experiments,
        "get_background",
        lambda _path: success_result(
            farfield_compatible=True, background_type="Normal"
        ) if background is None else background,
    )
    monkeypatch.setattr(
        experiments,
        "list_monitors",
        lambda _path: success_result(monitors=[]),
    )
    if monitors is not None:
        monkeypatch.setattr(
            experiments,
            "list_monitors",
            lambda _path: success_result(monitors=monitors),
        )
    monkeypatch.setattr(
        experiments,
        "list_result_items",
        lambda project_path=None, **kwargs: success_result(items=[]),
    )
    monkeypatch.setattr(
        experiments,
        "capture_solver_log_baseline",
        lambda _path: {},
    )
    monkeypatch.setattr(
        experiments,
        "read_appended_solver_logs",
        lambda _path, baseline=None: (
            success_result(errors=[], error_lines=[], log_files=[], log_tails={})
            if diagnostics is None else diagnostics
        ),
    )
    monkeypatch.setattr(experiments, "open_project", lambda _path: success_result(project_path="model.cst"))
    monkeypatch.setattr(experiments, "start_simulation_async", lambda _path: success_result())
    monkeypatch.setattr(experiments, "is_simulation_running", lambda _path: success_result(running=False))
    if close is None:
        close = lambda *_args, **_kwargs: success_result()
    monkeypatch.setattr(experiments, "close_project", close)
    return experiments


def test_run_experiment_requires_completion_paths() -> None:
    from cst_runtime.lib.experiments import run_experiment

    result = run_experiment("model.cst", [])

    assert result["error_type"] == "completion_result_paths_missing"


def test_run_id_queries_enable_interactive_result_access(monkeypatch) -> None:
    from cst_runtime.lib import experiments
    from cst_runtime.lib.contracts import success_result

    captured = {}

    def fake_list_run_ids(**arguments):
        captured.update(arguments)
        return success_result(run_ids=[])

    monkeypatch.setattr(experiments, "list_run_ids", fake_list_run_ids)

    result = experiments._run_ids_for_path("model.cst", "1D Results\\S-Parameters\\S1,1")

    assert result["status"] == "success"
    assert captured["allow_interactive"] is True


def test_run_experiment_uses_common_new_run_and_nonempty_results(monkeypatch) -> None:
    from cst_runtime.lib import experiments

    paths = [
        "1D Results\\S-Parameters\\S1,1",
        "1D Results\\S-Parameters\\SZmin(1),Zmax(1)",
    ]
    calls = {path: 0 for path in paths}
    inspect_calls = []
    _patch_experiment_pipeline(monkeypatch)

    def list_ids(_project_path, result_path):
        calls[result_path] += 1
        return success_result(run_ids=[1] if calls[result_path] == 1 else [1, 7])

    monkeypatch.setattr(experiments, "_run_ids_for_path", list_ids)

    def inspect_result(_project, path, run_id, *, allow_interactive=False):
        inspect_calls.append(
            {
                "path": path,
                "run_id": run_id,
                "allow_interactive": allow_interactive,
            }
        )
        return success_result(
            result_path=path,
            run_id=run_id,
            point_count=1,
            xdata=[10.0],
            ydata=[{"real": 0.1, "imag": 0.0}],
        )

    monkeypatch.setattr(experiments, "inspect_1d_result", inspect_result)

    result = experiments.run_experiment(
        "model.cst",
        paths,
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result["status"] == "success"
    assert result["run_id"] == 7
    assert len(result["result_metrics"]) == 2
    assert result["s11_metric"]["result_path"].endswith("S1,1")
    assert "exported" not in result
    assert result["cst_errors"] == []
    assert result["preflight_warnings"] == []
    assert all(item["allow_interactive"] is True for item in inspect_calls)


def test_run_experiment_rejects_cached_run_ids(monkeypatch) -> None:
    from cst_runtime.lib import experiments

    _patch_experiment_pipeline(monkeypatch)
    monkeypatch.setattr(
        experiments,
        "_run_ids_for_path",
        lambda *_args: success_result(run_ids=[0]),
    )

    result = experiments.run_experiment(
        "model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result["error_type"] == "solver_did_not_create_new_run"
    assert result["solver_log_tails"] == {}


def test_run_experiment_preflight_rejects_incompatible_background(monkeypatch) -> None:
    from cst_runtime.lib import experiments

    close_calls = []

    def record_close(*_args, **_kwargs):
        close_calls.append(True)
        return success_result()

    _patch_experiment_pipeline(
        monkeypatch,
        background=success_result(
            background_type="pec",
            farfield_compatible=False,
        ),
        monitors=[{"name": "farfield (f=2.5)", "type": "Farfield"}],
        close=record_close,
    )
    monkeypatch.setattr(
        experiments,
        "_run_ids_for_path",
        lambda *_args: success_result(run_ids=[]),
    )

    result = experiments.run_experiment(
        "model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result["status"] == "error"
    assert result["error_type"] == "background_incompatible_with_farfield"
    assert "Farfield monitors are not supported" in result["message"]
    assert result["farfield_monitors"][0]["type"] == "Farfield"
    assert close_calls == [True]


def test_run_experiment_preflight_skips_without_farfield_monitors(monkeypatch) -> None:
    from cst_runtime.lib import experiments

    _patch_experiment_pipeline(
        monkeypatch,
        background=success_result(
            background_type="pec",
            farfield_compatible=False,
        ),
        monitors=[{"name": "e-field", "type": "Efield"}],
    )
    monkeypatch.setattr(
        experiments,
        "_run_ids_for_path",
        lambda *_args: success_result(run_ids=[]),
    )

    result = experiments.run_experiment(
        "model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    # 没有远场监视器时预检放行，走到无新 Run ID 的普通失败分支
    assert result["error_type"] == "solver_did_not_create_new_run"


def test_run_experiment_preflight_failures_become_warnings(monkeypatch) -> None:
    from cst_runtime.lib import experiments

    _patch_experiment_pipeline(
        monkeypatch,
        background=error_result("get_background_failed", "查询失败"),
    )
    monkeypatch.setattr(
        experiments,
        "list_monitors",
        lambda _path: error_result("list_monitors_failed", "查询失败"),
    )
    monkeypatch.setattr(
        experiments,
        "_run_ids_for_path",
        lambda *_args: success_result(run_ids=[]),
    )

    result = experiments.run_experiment(
        "model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result["error_type"] == "solver_did_not_create_new_run"
    assert len(result["preflight_warnings"]) == 2


def test_run_experiment_returns_cst_solver_error_text(monkeypatch) -> None:
    from cst_runtime.lib import experiments

    close_calls = []

    def record_close(*_args, **_kwargs):
        close_calls.append(True)
        return success_result()

    _patch_experiment_pipeline(
        monkeypatch,
        close=record_close,
        diagnostics=success_result(
            errors=[
                "13/Aug/2026 23:08:30  *** Error ***\nFarfield monitors are not "
                "supported with pec, dispersive, lossy or surface impedance as "
                "background material."
            ],
            error_lines=["Farfield monitors are not supported"],
            log_files=["Model.log"],
            log_tails={},
        ),
    )
    monkeypatch.setattr(
        experiments,
        "_run_ids_for_path",
        lambda *_args: success_result(run_ids=[]),
    )

    result = experiments.run_experiment(
        "model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result["status"] == "error"
    assert result["error_type"] == "solver_reported_error"
    assert "Farfield monitors are not supported" in result["cst_errors"][0]
    assert result["log_files"] == ["Model.log"]
    assert close_calls == [True]

# ---------------------------------------------------------------------------
# 首次仿真：结果节点尚不存在是正常初始状态，预检应视为空基线而不是失败
# ---------------------------------------------------------------------------

MISSING_NODE_ERROR = error_result(
    "list_run_ids_failed",
    "tree path not found: '1D Results\\S-Parameters\\S1,1'",
)


def test_run_experiment_first_run_missing_node_is_empty_baseline(monkeypatch) -> None:
    from cst_runtime.lib import experiments

    _patch_experiment_pipeline(monkeypatch)

    calls = []

    def run_ids(_project_path, result_path):
        calls.append(result_path)
        # 预检：节点不存在；后检：本次求解生成了 Run 1
        if len(calls) == 1:
            return MISSING_NODE_ERROR
        return success_result(run_ids=[1])

    monkeypatch.setattr(experiments, "_run_ids_for_path", run_ids)
    monkeypatch.setattr(
        experiments,
        "list_result_items",
        lambda project_path=None, **kwargs: success_result(items=[]),
    )
    monkeypatch.setattr(
        experiments,
        "inspect_1d_result",
        lambda _project, path, run_id, *, allow_interactive=False: success_result(
            result_path=path,
            run_id=run_id,
            point_count=3,
            xdata=[2.4, 2.5, 2.6],
            ydata=[{"real": 0.1, "imag": 0.0}] * 3,
        ),
    )

    result = experiments.run_experiment(
        "model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result["status"] == "success"
    assert result["run_id"] == 1
    assert result["solver_completed"] is True
    assert result["missing_result_nodes"] == ["1D Results\\S-Parameters\\S1,1"]


def test_run_experiment_preflight_other_errors_still_fail(monkeypatch) -> None:
    from cst_runtime.lib import experiments

    _patch_experiment_pipeline(monkeypatch)
    monkeypatch.setattr(
        experiments,
        "_run_ids_for_path",
        lambda *_args: error_result("list_run_ids_failed", "project file not found"),
    )

    result = experiments.run_experiment(
        "model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result["status"] == "error"
    assert result["error_type"] == "completion_result_preflight_failed"


def test_run_experiment_preflight_present_but_list_failed_still_fails(monkeypatch) -> None:
    from cst_runtime.lib import experiments

    _patch_experiment_pipeline(monkeypatch)
    monkeypatch.setattr(
        experiments,
        "_run_ids_for_path",
        lambda *_args: MISSING_NODE_ERROR,
    )
    # CST 报缺失，但树枚举显示节点存在 → 矛盾，按真实失败处理
    monkeypatch.setattr(
        experiments,
        "list_result_items",
        lambda project_path=None, **kwargs: success_result(
            items=["1D Results\\S-Parameters\\S1,1"]
        ),
    )

    result = experiments.run_experiment(
        "model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result["status"] == "error"
    assert result["error_type"] == "completion_result_preflight_failed"


def test_run_experiment_postflight_still_missing_reports_no_new_run(monkeypatch) -> None:
    from cst_runtime.lib import experiments

    _patch_experiment_pipeline(monkeypatch)
    monkeypatch.setattr(
        experiments,
        "_run_ids_for_path",
        lambda *_args: MISSING_NODE_ERROR,
    )
    monkeypatch.setattr(
        experiments,
        "list_result_items",
        lambda project_path=None, **kwargs: success_result(items=[]),
    )

    result = experiments.run_experiment(
        "model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result["status"] == "error"
    assert result["error_type"] == "solver_did_not_create_new_run"
    assert result["result_nodes_still_missing"] == [
        "1D Results\\S-Parameters\\S1,1"
    ]

