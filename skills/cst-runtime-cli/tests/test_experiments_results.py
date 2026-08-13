"""run-experiment 的通用结果完成性验证。"""
from __future__ import annotations


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
    from cst_runtime.lib.contracts import success_result

    paths = [
        "1D Results\\S-Parameters\\S1,1",
        "1D Results\\S-Parameters\\SZmin(1),Zmax(1)",
    ]
    calls = {path: 0 for path in paths}
    inspect_calls = []

    def list_ids(_project_path, result_path):
        calls[result_path] += 1
        return success_result(run_ids=[1] if calls[result_path] == 1 else [1, 7])

    monkeypatch.setattr(experiments, "_run_ids_for_path", list_ids)
    monkeypatch.setattr(experiments, "open_project", lambda _path: success_result(project_path="model.cst"))
    monkeypatch.setattr(experiments, "start_simulation_async", lambda _path: success_result())
    monkeypatch.setattr(experiments, "is_simulation_running", lambda _path: success_result(running=False))
    monkeypatch.setattr(experiments, "close_project", lambda *_args, **_kwargs: success_result())
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
    assert all(item["allow_interactive"] is True for item in inspect_calls)


def test_run_experiment_rejects_cached_run_ids(monkeypatch) -> None:
    from cst_runtime.lib import experiments
    from cst_runtime.lib.contracts import success_result

    monkeypatch.setattr(
        experiments,
        "_run_ids_for_path",
        lambda *_args: success_result(run_ids=[0]),
    )
    monkeypatch.setattr(experiments, "open_project", lambda _path: success_result(project_path="model.cst"))
    monkeypatch.setattr(experiments, "start_simulation_async", lambda _path: success_result())
    monkeypatch.setattr(experiments, "is_simulation_running", lambda _path: success_result(running=False))
    monkeypatch.setattr(experiments, "close_project", lambda *_args, **_kwargs: success_result())

    result = experiments.run_experiment(
        "model.cst",
        ["1D Results\\S-Parameters\\S1,1"],
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert result["error_type"] == "solver_did_not_create_new_run"
