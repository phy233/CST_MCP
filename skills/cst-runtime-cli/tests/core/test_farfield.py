"""Test core/farfield.py: guard integration."""
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers import assert_json_error


def test_gui_execute_vba_routes_history_fallback_through_gateway(monkeypatch):
    from cst_runtime.core import farfield

    captured = {}

    def fake_submit(project, history_label, vba_lines, **kwargs):
        captured.update(
            project=project,
            history_label=history_label,
            vba_lines=list(vba_lines),
            kwargs=kwargs,
        )
        return {
            "ok": False,
            "status": "error",
            "error_type": "vba_runtime_error",
            "message": "navigator failed",
            "error": {
                "type": "vba_runtime_error",
                "message": "navigator failed",
                "phase": "execution",
            },
            "context": {"operation_id": "op-1"},
        }

    monkeypatch.setattr(farfield, "get_model3d", lambda _project: None)
    monkeypatch.setattr(farfield, "submit_vba_history", fake_submit)
    project = SimpleNamespace(schematic=SimpleNamespace())
    macro = "Sub Main()\n    Err.Raise 5\nEnd Sub"

    result = farfield._gui_execute_vba(project, macro, project_path="C:/demo.cst")

    assert captured["history_label"] == "ExecuteVBA"
    assert captured["vba_lines"] == ["    Err.Raise 5"]
    assert captured["kwargs"] == {
        "project_path": "C:/demo.cst",
        "feature": "farfield.execute_vba_fallback",
    }
    assert result["error_type"] == "vba_runtime_error"
    assert result["error"]["phase"] == "execution"
    assert result["context"]["operation_id"] == "op-1"


def test_result_navigator_passes_project_path_to_vba_gateway(monkeypatch):
    from cst_runtime.core import farfield

    captured = {}

    def fake_execute(project, code, project_path=""):
        captured.update(project=project, code=code, project_path=project_path)
        return {"status": "success"}

    monkeypatch.setattr(farfield, "_gui_execute_vba", fake_execute)
    project = object()

    result = farfield._gui_set_result_navigator_selection(
        project,
        [3, 1, 3],
        project_path="C:/demo.cst",
    )

    assert result["status"] == "success"
    assert captured["project"] is project
    assert captured["project_path"] == "C:/demo.cst"
    assert "Sub Main()" in captured["code"]
    assert "If Not SelectTreeItem" in captured["code"]
    assert "ReportError" in captured["code"]
    assert result["selected_run_ids"] == [1, 3]


def test_export_farfield_grid_missing_file():
    """export_farfield_grid returns error for missing project file."""
    from cst_runtime.core.farfield import export_farfield_grid
    result = export_farfield_grid(
        project_path="/nonexistent.cst",
        farfield_name="test",
        export_dir="/tmp",
    )
    assert_json_error(result, "project_file_missing")


def test_export_farfield_grid_invalid_quantity(tmp_path):
    """T8: Abs(E) rejected."""
    dummy_cst = tmp_path / "project.cst"
    dummy_cst.write_text("")
    from cst_runtime.core.farfield import export_farfield_grid
    result = export_farfield_grid(
        project_path=str(dummy_cst),
        farfield_name="test",
        export_dir=str(tmp_path / "exports"),
        quantity="Abs(E)",
    )
    assert_json_error(result, "not_gain_evidence")


def test_export_farfield_grid_no_run_id(tmp_path):
    """T11 was here — now passes through to project open which fails."""
    dummy_cst = tmp_path / "project.cst"
    dummy_cst.write_text("")
    from cst_runtime.core.farfield import export_farfield_grid
    result = export_farfield_grid(
        project_path=str(dummy_cst),
        farfield_name="test",
        export_dir=str(tmp_path / "exports"),
        quantity="Gain",
        run_id=None,
    )
    assert result["status"] == "error"


def test_gui_close_project_delegates_to_session_close(monkeypatch):
    """远场清理不能先直接关闭工程再让会话层重复关闭。"""
    from cst_runtime.core import farfield

    class FakeProject:
        def close(self):
            raise AssertionError("不应直接重复调用 project.close()")

    calls = []

    def fake_close_project(fullpath, save=False):
        calls.append((fullpath, save))
        return {"status": "success"}

    monkeypatch.setattr(farfield, "close_project", fake_close_project)

    result = farfield._gui_close_project(FakeProject(), "C:/test.cst", save=True)

    assert result["status"] == "success"
    assert calls == [("C:/test.cst", True)]


def test_export_farfield_grid_valid_quantity_passes_gate():
    """T8: Realized Gain passes quantity guard — fails on file check."""
    from cst_runtime.core.farfield import export_farfield_grid
    result = export_farfield_grid(
        project_path="/nonexistent.cst",
        farfield_name="test",
        export_dir="/tmp",
        quantity="Realized Gain",
        run_id=1,
    )
    assert_json_error(result, "project_file_missing")


def test_export_farfield_cut_missing_file():
    """export_farfield_cut returns error for missing project file."""
    from cst_runtime.core.farfield import export_farfield_cut
    result = export_farfield_cut(
        project_path="/nonexistent.cst",
        tree_path="Farfields\\Farfield Cuts\\test",
        export_dir="/tmp",
    )
    assert_json_error(result, "project_file_missing")


def test_export_farfield_cut_invalid_tree_path(tmp_path):
    """export_farfield_cut with non-Farfield Cuts tree path returns error."""
    dummy_cst = tmp_path / "project.cst"
    dummy_cst.write_text("")
    from cst_runtime.core.farfield import export_farfield_cut
    result = export_farfield_cut(
        project_path=str(dummy_cst),
        tree_path="1D Results\\S-Parameters",
        export_dir=str(tmp_path / "exports"),
    )
    assert_json_error(result, "invalid_farfield_cut_tree_path")
