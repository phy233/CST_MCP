"""Test core/results.py: error paths for results functions."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers import assert_json_error


def test_open_project_file_missing():
    """open_project returns error when file doesn't exist."""
    from cst_runtime.core.results import open_project

    result = open_project("/nonexistent/path.cst")
    assert_json_error(result, "project_file_missing")


def test_get_1d_result_export_not_json(mocker):
    """get_1d_result with non-.json export path returns error."""
    mocker.patch("cst_runtime.core.results._load_project", return_value=(
        mocker.MagicMock(), {"fullpath": "/tmp/test.cst"},
    ))
    mocker.patch("cst_runtime.core.results._get_result_module", return_value=(
        mocker.MagicMock(), "3d",
    ))

    from cst_runtime.core.results import get_1d_result
    result = get_1d_result(
        "/tmp/test.cst", treepath="S1,1", export_path="/tmp/test.txt",
    )
    assert_json_error(result, "invalid_export_extension")


def test_get_1d_result_resolves_zero_to_latest_run_id(mocker, tmp_path):
    """run_id=0 应解析为结果树中最新的具体 Run ID。"""
    result_item = mocker.MagicMock()
    result_item.treepath = "1D Results\\S-Parameters\\S1,1"
    result_item.title = "S1,1"
    result_item.xlabel = "Frequency"
    result_item.ylabel = "S-Parameter"
    result_item.length = 2
    result_item.run_id = 7
    result_item.get_xdata.return_value = [1.0, 2.0]
    result_item.get_ydata.return_value = [complex(-10, 0), complex(-20, 0)]
    result_item.get_parameter_combination.return_value = {}

    result_module = mocker.MagicMock()
    result_module.get_run_ids.return_value = [0, 3, 7, 5]
    result_module.get_result_item.return_value = result_item
    mocker.patch(
        "cst_runtime.core.results._load_project",
        return_value=(
            mocker.MagicMock(),
            {"fullpath": str(tmp_path / "working.cst"), "active_subproject": None},
        ),
    )
    mocker.patch(
        "cst_runtime.core.results._get_result_module",
        return_value=(result_module, "3d"),
    )

    from cst_runtime.core.results import get_1d_result
    result = get_1d_result(
        str(tmp_path / "working.cst"),
        treepath="1D Results\\S-Parameters\\S1,1",
        run_id=0,
        export_path=str(tmp_path / "s11.json"),
    )

    assert result["status"] == "success"
    assert result["requested_run_id"] == 0
    assert result["run_id"] == 7
    result_module.get_result_item.assert_called_once_with(
        "1D Results\\S-Parameters\\S1,1",
        run_id=7,
        load_impedances=True,
    )


def test_get_1d_result_keeps_zero_for_nonparametric_result(mocker, tmp_path):
    """非参数化结果仅返回 [0] 时，0 必须作为真实 Run ID 直接读取。"""
    result_item = mocker.MagicMock()
    result_item.treepath = "1D Results\\S-Parameters\\S1,1"
    result_item.title = "S1,1"
    result_item.xlabel = "Frequency"
    result_item.ylabel = "S-Parameter"
    result_item.length = 1
    result_item.run_id = 0
    result_item.get_xdata.return_value = [2.45]
    result_item.get_ydata.return_value = [complex(-18, 0)]
    result_item.get_parameter_combination.return_value = {}

    result_module = mocker.MagicMock()
    result_module.get_run_ids.return_value = [0]
    result_module.get_result_item.return_value = result_item
    mocker.patch(
        "cst_runtime.core.results._load_project",
        return_value=(
            mocker.MagicMock(),
            {"fullpath": str(tmp_path / "working.cst"), "active_subproject": None},
        ),
    )
    mocker.patch(
        "cst_runtime.core.results._get_result_module",
        return_value=(result_module, "3d"),
    )

    from cst_runtime.core.results import get_1d_result
    result = get_1d_result(
        str(tmp_path / "working.cst"),
        treepath="1D Results\\S-Parameters\\S1,1",
        run_id=0,
        load_impedances=False,
        export_path=str(tmp_path / "s11.json"),
    )

    assert result["status"] == "success"
    assert result["requested_run_id"] == 0
    assert result["run_id"] == 0
    result_module.get_result_item.assert_called_once_with(
        "1D Results\\S-Parameters\\S1,1",
        run_id=0,
        load_impedances=False,
    )


def test_get_1d_result_ignores_missing_nonparametric_combination(mocker, tmp_path):
    """参数组合元数据失败不能阻止已经成功读取的非参数化曲线导出。"""
    result_item = mocker.MagicMock()
    result_item.treepath = "1D Results\\S-Parameters\\S1,1"
    result_item.title = "S1,1"
    result_item.xlabel = "Frequency"
    result_item.ylabel = "S-Parameter"
    result_item.length = 1
    result_item.run_id = 0
    result_item.get_xdata.return_value = [2.45]
    result_item.get_ydata.return_value = [complex(-18, 0)]
    result_item.get_parameter_combination.side_effect = RuntimeError(
        "run id does not exist: 0"
    )

    result_module = mocker.MagicMock()
    result_module.get_run_ids.return_value = [0]
    result_module.get_result_item.return_value = result_item
    mocker.patch(
        "cst_runtime.core.results._load_project",
        return_value=(
            mocker.MagicMock(),
            {"fullpath": str(tmp_path / "working.cst"), "active_subproject": None},
        ),
    )
    mocker.patch(
        "cst_runtime.core.results._get_result_module",
        return_value=(result_module, "3d"),
    )

    from cst_runtime.core.results import get_1d_result
    export_path = tmp_path / "s11.json"
    result = get_1d_result(
        str(tmp_path / "working.cst"),
        treepath="1D Results\\S-Parameters\\S1,1",
        run_id=0,
        load_impedances=False,
        export_path=str(export_path),
    )

    assert result["status"] == "success"
    assert result["point_count"] == 1
    assert result["parameter_combination_warning"] == "run id does not exist: 0"
    payload = __import__("json").loads(export_path.read_text(encoding="utf-8"))
    assert payload["parameter_combination"] == {}
    assert payload["parameter_combination_available"] is False
    assert payload["xdata"] == [2.45]


def test_get_1d_result_serializes_documented_0d_scalar(mocker, tmp_path):
    """CST 2022 的 0D 标量没有可用 x 轴时仍应正常导出。"""
    result_item = mocker.MagicMock()
    result_item.treepath = "0D Results\\Value"
    result_item.title = "Value"
    result_item.xlabel = ""
    result_item.ylabel = "Value"
    result_item.length = 1
    result_item.run_id = 0
    result_item.get_xdata.side_effect = RuntimeError("0D result has no x-axis")
    result_item.get_ydata.return_value = 3.5
    result_item.get_parameter_combination.return_value = {}

    result_module = mocker.MagicMock()
    result_module.get_run_ids.return_value = [0]
    result_module.get_result_item.return_value = result_item
    mocker.patch(
        "cst_runtime.core.results._load_project",
        return_value=(
            mocker.MagicMock(),
            {"fullpath": str(tmp_path / "working.cst"), "active_subproject": None},
        ),
    )
    mocker.patch(
        "cst_runtime.core.results._get_result_module",
        return_value=(result_module, "3d"),
    )

    from cst_runtime.core.results import get_1d_result
    export_path = tmp_path / "value.json"
    result = get_1d_result(
        str(tmp_path / "working.cst"),
        treepath="0D Results\\Value",
        export_path=str(export_path),
    )

    assert result["status"] == "success"
    assert result["point_count"] == 1
    payload = __import__("json").loads(export_path.read_text(encoding="utf-8"))
    assert payload["xdata"] is None
    assert payload["ydata"] == 3.5


def test_get_parameter_combination_resolves_zero_to_latest_run_id(mocker):
    """参数组合接口也应遵守 run_id=0 的公开契约。"""
    result_module = mocker.MagicMock()
    result_module.get_all_run_ids.return_value = [0, 2, 9]
    result_module.get_parameter_combination.return_value = {"width": 10}
    mocker.patch(
        "cst_runtime.core.results._load_project",
        return_value=(
            mocker.MagicMock(),
            {"fullpath": "C:/test/working.cst", "active_subproject": None},
        ),
    )
    mocker.patch(
        "cst_runtime.core.results._get_result_module",
        return_value=(result_module, "3d"),
    )

    from cst_runtime.core.results import get_parameter_combination
    result = get_parameter_combination("C:/test/working.cst", run_id=0)

    assert result["status"] == "success"
    assert result["requested_run_id"] == 0
    assert result["run_id"] == 9
    result_module.get_parameter_combination.assert_called_once_with(9)


def test_canonical_run_ids_keeps_zero_only_result():
    """批量导出也必须保留非参数化仿真的唯一 Run ID 0。"""
    from cst_runtime.core.results import _canonical_run_ids

    assert _canonical_run_ids([0]) == [0]
    assert _canonical_run_ids([0, 2, 5]) == [2, 5]


def test_discover_farfield_names_from_loaded_result_tree(mocker):
    """远场发现应复用离线结果树，不需要另外打开 GUI 工程。"""
    mocker.patch(
        "cst_runtime.core.results.list_all_result_items",
        return_value=[
            "1D Results\\S-Parameters\\S1,1",
            "Farfields\\farfield (f=2.45) [1]",
            "Farfields\\Farfield Cuts\\cut1",
        ],
    )

    from cst_runtime.core.results import _discover_farfield_names_from_result_module
    names = _discover_farfield_names_from_result_module(mocker.MagicMock())

    assert names == ["farfield (f=2.45) [1]"]


def test_get_2d_result_export_not_json(mocker):
    """get_2d_result with non-.json export path returns error."""
    mocker.patch("cst_runtime.core.results._load_project", return_value=(
        mocker.MagicMock(), {"fullpath": "/tmp/test.cst"},
    ))
    mocker.patch("cst_runtime.core.results._get_result_module", return_value=(
        mocker.MagicMock(), "3d",
    ))

    from cst_runtime.core.results import get_2d_result
    result = get_2d_result(
        "/tmp/test.cst", treepath="test", export_path="/tmp/test.txt",
    )
    assert_json_error(result, "invalid_export_extension")


def test_get_2d_result_preserves_unsupported_feature_contract(mocker):
    """缺少 CST 2022 的 2D 接口时应保留结构化兼容性错误。"""
    mocker.patch("cst_runtime.core.results._load_project", return_value=(
        mocker.MagicMock(), {"fullpath": "/tmp/test.cst"},
    ))
    mocker.patch("cst_runtime.core.results._get_result_module", return_value=(
        object(), "3d",
    ))

    from cst_runtime.core.results import get_2d_result

    result = get_2d_result("/tmp/test.cst", treepath="2D/3D Results\\Field")

    assert_json_error(result, "unsupported_feature")
    assert result["error"]["phase"] == "compatibility"
    assert result["feature"] == "results.2d"
    assert result["context"]["required_capability"] == "result2d"


def test_get_parameter_combination_no_cst():
    """get_parameter_combination with nonexistent project — cst.results not available."""
    from cst_runtime.core.results import get_parameter_combination
    try:
        result = get_parameter_combination("/nonexistent.cst", run_id=1)
        assert result["status"] == "error"
    except ImportError:
        pass


def test_get_1d_result_no_cst():
    """get_1d_result with nonexistent project — cst.results not available."""
    from cst_runtime.core.results import get_1d_result
    try:
        result = get_1d_result("/nonexistent.cst", treepath="S1,1")
        assert result["status"] == "error"
    except ImportError:
        pass


def test_list_result_items_no_cst():
    """list_result_items without CST — cst.results not available."""
    from cst_runtime.core.results import list_result_items
    try:
        result = list_result_items("/nonexistent.cst")
        assert result["status"] == "error"
    except ImportError:
        pass
