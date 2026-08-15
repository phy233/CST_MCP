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


def test_define_uses_documented_mu_method(monkeypatch):
    """手册 Material 对象方法为 .Mu（GetMu 查询），不得出现未文档化的 .Mue。"""
    from cst_runtime.lib import materials
    from cst_runtime.lib.contracts import success_result

    captured = {}

    def fake_add_to_history(project_path, vba, history_name):
        captured["vba"] = vba
        return success_result()

    monkeypatch.setattr(materials, "_add_to_history", fake_add_to_history)

    result = materials.define(
        "C:/work/working.cst",
        name="FR4",
        epsilon=4.3,
        mue=1.2,
        tan_d=0.02,
    )

    assert result["status"] == "success"
    vba = captured["vba"]
    assert ".Mu 1.2" in vba
    assert ".Mue" not in vba
    assert ".Epsilon 4.3" in vba
