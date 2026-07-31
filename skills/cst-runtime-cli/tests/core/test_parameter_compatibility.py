"""CST 新旧版本参数对象兼容测试。"""
from cst_runtime.core.compatibility.parameters import list_parameter_values


class ParameterApi:
    def GetNumberOfParameters(self):
        return 2

    def GetParameterName(self, index):
        return ("length", "width")[index]

    def RestoreDoubleParameter(self, name):
        return {"length": 10.0, "width": 5.0}[name]


def test_uses_2026_model3d_parameter_api() -> None:
    project = type("Project", (), {"model3d": ParameterApi()})()
    assert list_parameter_values(project) == {"length": 10.0, "width": 5.0}


def test_falls_back_to_2022_modeler_parameter_api() -> None:
    project = type("Project", (), {"modeler": ParameterApi()})()
    assert list_parameter_values(project) == {"length": 10.0, "width": 5.0}
