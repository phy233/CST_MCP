from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPO_ROOT / "skills" / "cst-runtime-cli" / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from cst_runtime.core import identity as project_identity


class FakeProject:
    def __init__(self, path: str) -> None:
        self._path = path

    def filename(self) -> str:
        return self._path


class FakeDesignEnvironment:
    def __init__(self, paths: list[str], active_path: str) -> None:
        self.paths = paths
        self.projects = {path: FakeProject(path) for path in paths}
        self.active_project = self.projects[active_path]
        self.requested_open_project: str | None = None

    def list_open_projects(self) -> list[str]:
        return self.paths

    def get_open_project(self, path: str) -> FakeProject:
        self.requested_open_project = path
        return self.projects[path]

    def has_active_project(self) -> bool:
        return self.active_project is not None


class TestProjectIdentity:
    def test_discovery_does_not_activate_existing_project(self, mocker) -> None:
        """首次发现只读取路径，不切换现有会话的活动工程。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = str(root / "first.cst")
            second = str(root / "second.cst")
            de = FakeDesignEnvironment(paths=[first, second], active_path=first)
            mocker.patch(
                "cst_runtime.core.identity.connect_design_environment",
                return_value=de,
            )

            pids, status = project_identity.discover_expected_project_pids(second, {1234})

            assert status["status"] == "success"
            assert pids == [1234]
            assert de.active_project is de.projects[first]
            assert de.requested_open_project is None

    def test_exact_attach_connects_only_confirmed_pid(self, mocker) -> None:
        """确认后只连接指定 PID，并在该会话内激活目标工程。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = str(root / "first.cst")
            second = str(root / "second.cst")
            de = FakeDesignEnvironment(paths=[first, second], active_path=first)
            connected_pids = []

            def connect(pid):
                connected_pids.append(pid)
                return de

            mocker.patch(
                "cst_runtime.core.identity.connect_design_environment",
                side_effect=connect,
            )

            project, connected_de, status = (
                project_identity.attach_expected_project_at_pid(second, 2222)
            )

            assert connected_pids == [2222]
            assert connected_de is de
            assert project is de.projects[second]
            assert status["design_environment_pid"] == 2222

    def test_multi_project_attach_activates_expected_project(self, mocker) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = str(root / "first.cst")
            second = str(root / "second.cst")
            de = FakeDesignEnvironment(paths=[first, second], active_path=first)

            mocker.patch("cst_runtime.core.identity._connected_design_environments", return_value=([(de, 1234)], ""))
            project, status = project_identity.attach_expected_project(second)

            assert project is de.projects[second]
            assert status["status"] == "success"
            assert status["was_activated"]
            assert de.requested_open_project == second

    def test_multi_project_attach_rejects_missing_expected_project(self, mocker) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = str(root / "first.cst")
            second = str(root / "second.cst")
            missing = str(root / "missing.cst")
            de = FakeDesignEnvironment(paths=[first, second], active_path=first)

            mocker.patch("cst_runtime.core.identity._connected_design_environments", return_value=([(de, 1234)], ""))
            project, status = project_identity.attach_expected_project(missing)

            assert project is None
            assert status["status"] == "error"
            assert status["error_type"] == "project_not_open"
            assert de.requested_open_project is None

    def test_attach_searches_across_design_environments(self, mocker) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            first = str(root / "first.cst")
            second = str(root / "second.cst")
            de_a = FakeDesignEnvironment(paths=[first], active_path=first)
            de_b = FakeDesignEnvironment(paths=[second], active_path=second)

            mocker.patch(
                "cst_runtime.core.identity._connected_design_environments",
                return_value=([(de_a, 1111), (de_b, 2222)], ""),
            )
            project, status = project_identity.attach_expected_project(second)

            assert project is de_b.projects[second]
            assert status["status"] == "success"
            assert status["design_environment_pid"] == 2222
