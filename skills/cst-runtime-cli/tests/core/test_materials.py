from cst_runtime.core import modeling
from cst_runtime.core.modeling import _material_mtd_path, _material_vba_lines


def test_material_mtd_path_points_to_skill_reference_library() -> None:
    mtd_path = _material_mtd_path("FR-4 (loss free)")

    assert mtd_path.name == "FR-4 (loss free).mtd"
    assert mtd_path.parent.name == "Materials"
    assert mtd_path.parent.parent.name == "references"
    assert mtd_path.is_file()


def test_material_vba_uses_only_definition_section() -> None:
    mtd_content = _material_mtd_path("FR-4 (loss free)").read_text(encoding="utf-8")

    lines = _material_vba_lines("FR-4 (loss free)", mtd_content)

    assert lines[:3] == [
        "With Material",
        "    .Reset",
        '    .Name "FR-4 (loss free)"',
    ]
    assert "    .FrqType \"all\"" in lines
    assert "    .Create" in lines
    assert lines[-1] == "End With"
    assert "FrqType: all" not in lines
    assert "EM(HF) properties measured @ 10GHz" not in lines


def test_define_material_from_mtd_submits_complete_material_block(monkeypatch) -> None:
    project = object()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        modeling,
        "attach_expected_project",
        lambda _project_path: (project, {}),
    )

    def capture_history(project_path, history_name, vba_lines, project=None):
        captured.update(
            project_path=project_path,
            history_name=history_name,
            vba_lines=vba_lines,
            project=project,
        )
        return {"ok": True, "status": "success"}

    monkeypatch.setattr(modeling, "_add_vba_history", capture_history)

    result = modeling.define_material_from_mtd(
        "D:/work/demo.cst",
        "FR-4 (loss free)",
    )

    assert result["status"] == "success"
    assert captured["history_name"] == "Define Material: FR-4 (loss free)"
    assert captured["project"] is project
    assert captured["vba_lines"][0] == "With Material"
    assert captured["vba_lines"][-1] == "End With"
