"""执行上下文隔离的离线回归测试。"""

from cst_runtime.context import (
    get_current_execution_context,
    set_current_execution_context,
)


def test_new_request_clears_fields_missing_from_previous_request():
    set_current_execution_context(
        interaction_id="interaction_old",
        task_id="task_old",
        run_id="run_old",
        project_path="C:/old/project.cst",
    )

    set_current_execution_context(interaction_id="interaction_new")

    assert get_current_execution_context() == {
        "interaction_id": "interaction_new",
        "task_id": None,
        "run_id": None,
        "project_path": None,
    }
