"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Scripts for checking the slope of the pitch, roll and yaw moments with respect to a certain angle
"""

# Imports

import math
import numpy as np

from sklearn.linear_model import LinearRegression
from pandas import (
    Series,
    DataFrame,
)
from typing import Optional

from ceasiompy.staticstability import STABILITY_DICT


# Methods

def _status_or_reason(is_stable: bool, coef_name: str, limit_text: str) -> str:
    if is_stable:
        return STABILITY_DICT[True]
    return f"{coef_name} {limit_text}"


def _fit_slope_or_nan(x_values: np.ndarray, y_values: np.ndarray) -> float:
    """Fit a 1D slope with linear regression, returning NaN when data is unusable."""

    x_arr = np.asarray(x_values, dtype=float).reshape(-1)
    y_arr = np.asarray(y_values, dtype=float).reshape(-1)
    valid_mask = np.isfinite(x_arr) & np.isfinite(y_arr)

    if np.count_nonzero(valid_mask) < 2:
        return float("nan")

    x_valid = x_arr[valid_mask]
    y_valid = y_arr[valid_mask]

    # Need at least two distinct x-values to define a slope.
    if np.unique(x_valid).size < 2:
        return float("nan")

    reg = LinearRegression().fit(x_valid.reshape(-1, 1), y_valid)
    return float(reg.coef_[0])


def _is_stable_from_slope(slope: float, stable_when_positive: bool) -> bool:
    if not math.isfinite(slope):
        return False
    return slope > 0 if stable_when_positive else slope < 0


def _compute_stability_cma(group: DataFrame) -> DataFrame:
    """
    Computes the longitudinal stability (cma) of an aircraft,
    for a given group using linear regression.

    Args:
        group (DataFrame): Contains aerodynamic coefficients.

    Returns:
        Series: A series containing the stability status for the longitudinal direction.

    """
    x_aoa = group["alpha"].values
    y_cms = group["cms"].values

    lr_cma = _fit_slope_or_nan(x_aoa, y_cms)
    cma_stable = _is_stable_from_slope(lr_cma, stable_when_positive=False)

    return Series({
        "lr_cma": lr_cma,
        "cma": lr_cma,
        "longitudinal": (
            _status_or_reason(cma_stable, "Cma", f"{lr_cma}>= 0.")
            if math.isfinite(lr_cma)
            else STABILITY_DICT[False]
        ),
    })


def _compute_stability_cnb_clb(group: DataFrame) -> DataFrame:
    """
    Computes the directional (cnb) and lateral (clb) stability of the aircraft
    for a given group using linear regression.

    Args:
        group (DataFrame): Aerodynamic coefficients for mach, altitude, and angle of attack.

    Returns:
        Series: Stability status for the directional and lateral directions.

    """
    # Linear regression for cnb (slope of cml to aos)
    x_aos = group["beta"].values
    y_cml = group["cml"].values
    lr_cnb = _fit_slope_or_nan(x_aos, y_cml)

    # Linear regression for clb (slope of cmd to aos)
    y_cmd = group["cmd"].values
    lr_clb = _fit_slope_or_nan(x_aos, y_cmd)

    cnb_stable = _is_stable_from_slope(lr_cnb, stable_when_positive=True)
    clb_stable = _is_stable_from_slope(lr_clb, stable_when_positive=False)

    return Series({
        "lr_cnb": lr_cnb,
        "lr_clb": lr_clb,
        "cnb": lr_cnb,
        "clb": lr_clb,
        "directional": (
            _status_or_reason(
                is_stable=cnb_stable,
                coef_name="Cnb",
                limit_text=f"{lr_cnb}<= 0",
            )
            if math.isfinite(lr_cnb)
            else STABILITY_DICT[False]
        ),
        "lateral": (
            _status_or_reason(
                is_stable=clb_stable,
                coef_name="Clb",
                limit_text=f"{lr_clb}>= 0",
            )
            if math.isfinite(lr_clb)
            else STABILITY_DICT[False]
        ),
    })


# Functions

def check_stability_lr(df: DataFrame) -> DataFrame:
    """
    Using linear regression to check if the aircraft is stable or not.

    Args:
        df (DataFrame): Aerodynamic coefficients for mach, alt, aoa and aos.

    Returns:
        (DataFrame): Stability status for mach, alt, aoa and aos.
    """

    grouped_cma = df.groupby([
        "mach",
        "alt",
        "beta",
    ]).apply(_compute_stability_cma, include_groups=False).reset_index()

    grouped_cnb_clb = df.groupby([
        "mach",
        "alt",
        "alpha",
    ]).apply(_compute_stability_cnb_clb, include_groups=False).reset_index()

    # Merge grouped_cma and grouped_cnb_clb with the original df
    df = df.merge(grouped_cma, on=["mach", "alt", "beta"], how="left")
    df = df.merge(grouped_cnb_clb, on=["mach", "alt", "alpha"], how="left")
    return df


def check_stability_tangent(cma: float, cnb: float, clb: float) -> tuple[str, str, str]:
    """
    We use tangents at the distinct points to check if the aircraft is stable or not.
    Returns:
        (tuple[str, str, str]): Stability status messages.
    """

    def _stable_or_unstable(value: Optional[float], stable_when_positive: bool) -> str:
        if value is None:
            return STABILITY_DICT[False]
        try:
            value_f = float(value)
        except (TypeError, ValueError):
            return STABILITY_DICT[False]
        if not math.isfinite(value_f):
            return STABILITY_DICT[False]
        is_stable = value_f > 0 if stable_when_positive else value_f < 0
        return STABILITY_DICT[is_stable]

    return (
        _stable_or_unstable(cma, stable_when_positive=False),
        _stable_or_unstable(cnb, stable_when_positive=True),
        _stable_or_unstable(clb, stable_when_positive=False),
    )
