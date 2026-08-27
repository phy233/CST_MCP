"""MCP proxy 双态终止（L1 relinquish / L2 兜底）的离线单测。

不经真实 worker：以 object.__new__ 绕过 __init__，手工装配最小协作面，
聚焦 journal 终态、宽限收集与 worker 回收行为本身。
"""
from __future__ import annotations

import json
import queue
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcp_server import proxy as proxy_module
from mcp_server.proxy import CSTTransportError, CSTWorkerProxy


def _bare_proxy() -> CSTWorkerProxy:
    proxy = object.__new__(CSTWorkerProxy)
    proxy.config = SimpleNamespace(server_name="test-server")
    proxy._responses = queue.Queue()
    return proxy


@pytest.fixture()
def journal_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _journal_lines(tmp_path: Path) -> list[dict]:
    journal = (
        tmp_path / ".cst_runtime" / "interactions" / "default_session"
        / "mcp_interactions.jsonl"
    )
    assert journal.is_file()
    return [
        json.loads(line)
        for line in journal.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class TestGraceCollection:

    def _beacon(self, project: str, phase: str, age: float = 0.0) -> None:
        target = proxy_module._beacon_path_for(project)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "phase": phase,
            "updated_at": time.time() - age,
            "pid": 1234,
        }
        target.write_text(json.dumps(payload), encoding="utf-8")

    def test_collect_hits_matching_response(self, journal_cwd):
        self._beacon("C:/work/model.cst", "postflight")
        proxy = _bare_proxy()
        proxy._responses.put({"id": "rid-1", "status": "success", "value": 7})

        got = proxy._collect_grace_response(
            "rid-1", grace_seconds=5.0, grace_project_path="C:/work/model.cst"
        )
        assert got is not None
        assert got["value"] == 7

    def test_collect_requires_fresh_grace_phase(self, journal_cwd):
        self._beacon("C:/work/model.cst", "polling")
        proxy = _bare_proxy()
        assert (
            proxy._collect_grace_response(
                "rid", grace_seconds=5.0, grace_project_path="C:/work/model.cst"
            )
            is None
        )

        self._beacon("C:/work/model.cst", "closing", age=60.0)
        assert (
            proxy._collect_grace_response(
                "rid", grace_seconds=5.0, grace_project_path="C:/work/model.cst"
            )
            is None
        )

    def test_collect_returns_none_on_worker_exit_sentinel(self, journal_cwd):
        self._beacon("C:/work/model.cst", "closing")
        proxy = _bare_proxy()
        proxy._responses.put({"_transport_error": "worker_exited"})
        assert (
            proxy._collect_grace_response(
                "rid", grace_seconds=5.0, grace_project_path="C:/work/model.cst"
            )
            is None
        )

    def test_mirror_formula_matches_runtime_writer(self, journal_cwd):
        """双端契约：runtime 写出的信标必须能被 proxy 镜像公式命中。"""
        from cst_runtime.core import phase_beacon as beacon

        beacon.write_phase("C:/work/model.cst", beacon.CLOSING)
        assert proxy_module._phase_allows_grace("C:/work/model.cst") is True


class TestCallToolLifecycle:

    RELINQUISH = {
        "status": "error",
        "error_type": "long_run_relinquish",
        "terminal": True,
        "await_user_decision": True,
        "timeout_class": "expected_simulation",
        "solver_left_running": True,
    }

    def test_relinquish_records_state_and_terminates_worker(
        self, journal_cwd, monkeypatch
    ):
        proxy = _bare_proxy()
        kills: list[int] = []
        monkeypatch.setattr(
            proxy, "request", lambda *a, **kw: dict(self.RELINQUISH)
        )
        monkeypatch.setattr(
            proxy, "_terminate_worker", lambda: kills.append(1)
        )

        result = proxy.call_tool(
            "wait-simulation",
            {"project_path": "C:/work/model.cst"},
            timeout=5,
            timeout_class="expected_simulation",
        )

        assert result["error_type"] == "long_run_relinquish"
        assert kills == [1]
        final = _journal_lines(journal_cwd)[-1]
        assert final["state"] == "relinquished"
        assert final["timeout_class"] == "expected_simulation"
        assert final["result"]["terminal"] is True

    def test_transport_timeout_records_terminated(
        self, journal_cwd, monkeypatch
    ):
        proxy = _bare_proxy()
        kills: list[int] = []

        def _raise(*a, **kw):
            raise CSTTransportError(
                "worker 调用超时: call_tool",
                code="worker_request_timeout",
                context={
                    "action": "call_tool",
                    "timeout_class": "expected_simulation",
                    "grace_used": True,
                    "grace_seconds": 180.0,
                },
            )

        monkeypatch.setattr(proxy, "request", _raise)
        monkeypatch.setattr(proxy, "_terminate_worker", lambda: kills.append(1))

        with pytest.raises(CSTTransportError):
            proxy.call_tool(
                "run-experiment",
                {"project_path": "C:/work/model.cst"},
                timeout=1,
                timeout_class="expected_simulation",
            )

        assert kills == [1]
        final = _journal_lines(journal_cwd)[-1]
        assert final["state"] == "terminated"
        assert final["timeout_class"] == "expected_simulation"
        assert final["error"]["error"]["code"] == "worker_request_timeout"
        assert final["error"]["context"]["grace_used"] is True
