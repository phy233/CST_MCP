"""lib.materials 材料定义 VBA 的单元测试（方法名必须与 CST 2022 手册一致）。"""
from __future__ import annotations

from cst_runtime.lib.contracts import success_result


def test_define_uses_documented_mu_method(monkeypatch):
    """手册 Material 对象方法为 .Mu（GetMu 查询），不得出现未文档化的 .Mue。"""
    from cst_runtime.lib import materials

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
