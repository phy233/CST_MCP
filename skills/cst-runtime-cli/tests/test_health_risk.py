"""环境检查与修复的副作用边界。"""
from __future__ import annotations


def test_health_check_forces_read_only_mode(monkeypatch) -> None:
    from cst_runtime.core import environment

    captured = {}

    def fake(workspace, *, auto_fix):
        captured.update(workspace=workspace, auto_fix=auto_fix)
        return {"status": "success"}

    monkeypatch.setattr(environment, "_health_check", fake)

    assert environment.health_check("D:/workspace")["status"] == "success"
    assert captured == {"workspace": "D:/workspace", "auto_fix": False}


def test_health_repair_forces_mutating_mode(monkeypatch) -> None:
    from cst_runtime.core import environment

    captured = {}

    def fake(workspace, *, auto_fix):
        captured.update(workspace=workspace, auto_fix=auto_fix)
        return {"status": "success"}

    monkeypatch.setattr(environment, "_health_check", fake)

    assert environment.health_repair("D:/workspace")["status"] == "success"
    assert captured == {"workspace": "D:/workspace", "auto_fix": True}
