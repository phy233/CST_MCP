"""参数扫描查找表的纯数据处理工具。"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def load_lut(filepath: str | Path) -> pd.DataFrame:
    """从 CSV 或 NPZ 文件加载查找表。"""
    path = Path(filepath)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() == ".npz":
        data = np.load(path)
        return pd.DataFrame({key: data[key] for key in data.files})
    raise ValueError(f"不支持的查找表格式: {path.suffix}")


def interpolate_lut(
    lut: pd.DataFrame,
    param_columns: list[str],
    value_column: str,
    target_params: dict[str, float],
) -> float:
    """对规则网格查找表执行线性插值。"""
    from scipy.interpolate import RegularGridInterpolator

    parameter_values = [lut[column].unique() for column in param_columns]
    shape = [len(values) for values in parameter_values]
    value_grid = lut[value_column].values.reshape(shape)
    interpolator = RegularGridInterpolator(
        parameter_values,
        value_grid,
        method="linear",
    )
    point = [target_params[column] for column in param_columns]
    return float(interpolator(point))
