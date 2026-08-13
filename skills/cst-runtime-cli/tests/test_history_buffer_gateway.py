from __future__ import annotations

import pytest

from cst_runtime.core import buffer
from cst_runtime.core import modeling
from cst_runtime.core.errors import error_response, success_response


@pytest.fixture(autouse=True)
def clear_command_buffers():
    buffer._buffers.clear()
    yield
    buffer._buffers.clear()


def test_peek_requires_explicit_commit() -> None:
    buffer.begin_batch("model.cst", "two phase")
    buffer.append_to_batch("model.cst", ["first", "second"])

    summary, script = buffer.peek_batch("model.cst")

    assert summary == "two phase"
    assert script == "first\nsecond\n"
    assert buffer.is_batch_mode("model.cst")
    buffer.commit_batch("model.cst")
    assert not buffer.is_batch_mode("model.cst")


def test_buffered_history_is_not_reported_as_executed() -> None:
    project_path = modeling._abs_project_path("model.cst")
    buffer.begin_batch(project_path, "buffered")

    result = modeling._add_vba_history("model.cst", "Define Brick", ["With Brick"])

    assert result["ok"] is True
    assert result["submission"] == "buffered"
    assert result["execution"] == "not_run"
    assert "verification" not in result
    assert buffer.peek_batch(project_path)[1] == "With Brick\n"


def test_flush_commits_only_after_gateway_success(monkeypatch) -> None:
    project_path = modeling._abs_project_path("model.cst")
    project = object()
    submitted = {}
    buffer.begin_batch(project_path, "batch")
    buffer.append_to_batch(project_path, ["With Brick", "End With"])
    monkeypatch.setattr(
        modeling,
        "attach_expected_project",
        lambda path: (project, {"status": "success"}),
    )

    def submit(received_project, label, lines, **kwargs):
        submitted.update(project=received_project, label=label, lines=lines, kwargs=kwargs)
        return success_response(submission="accepted", execution="reported_ok")

    monkeypatch.setattr(modeling, "submit_vba_history", submit)

    result = modeling.flush_batch("model.cst")

    assert result["ok"] is True
    assert result["batch_committed"] is True
    assert not buffer.is_batch_mode(project_path)
    assert submitted["project"] is project
    assert submitted["label"] == "batch"
    assert submitted["lines"] == ["With Brick\nEnd With\n"]


def test_flush_retains_batch_after_vba_failure(monkeypatch) -> None:
    project_path = modeling._abs_project_path("model.cst")
    buffer.begin_batch(project_path, "retryable")
    buffer.append_to_batch(project_path, ["broken command"])
    monkeypatch.setattr(
        modeling,
        "attach_expected_project",
        lambda path: (object(), {"status": "success"}),
    )
    monkeypatch.setattr(
        modeling,
        "submit_vba_history",
        lambda *args, **kwargs: error_response(
            "vba_runtime_error", "missing material", phase="execution"
        ),
    )

    result = modeling.flush_batch("model.cst")

    assert result["status"] == "error"
    assert result["batch_retained"] is True
    assert result["retry_safe"] is False
    assert buffer.is_batch_mode(project_path)
    assert buffer.peek_batch(project_path)[1] == "broken command\n"


def test_flush_retains_batch_when_project_attach_fails(monkeypatch) -> None:
    project_path = modeling._abs_project_path("model.cst")
    buffer.begin_batch(project_path, "retryable")
    buffer.append_to_batch(project_path, ["command"])
    monkeypatch.setattr(
        modeling,
        "attach_expected_project",
        lambda path: (
            None,
            error_response("project_not_open", "project is not attached"),
        ),
    )

    result = modeling.flush_batch("model.cst")

    assert result["status"] == "error"
    assert result["batch_retained"] is True
    assert result["retry_safe"] is True
    assert buffer.is_batch_mode(project_path)


def test_empty_flush_commits_without_attaching(monkeypatch) -> None:
    project_path = modeling._abs_project_path("model.cst")
    buffer.begin_batch(project_path, "empty")
    monkeypatch.setattr(
        modeling,
        "attach_expected_project",
        lambda path: pytest.fail("empty batch must not attach to CST"),
    )

    result = modeling.flush_batch("model.cst")

    assert result["status"] == "success"
    assert result["submission"] == "not_required"
    assert result["batch_committed"] is True
    assert not buffer.is_batch_mode(project_path)
