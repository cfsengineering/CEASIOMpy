"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Scripts for checking the slope of the pitch, roll and yaw moments with respect to a certain angle
"""

# Imports

from sklearn.linear_model import LinearRegression
from pandas import (
    Series,
    DataFrame,
)

from ceasiompy.staticstability import STABILITY_DICT


# Methods

def _status_or_reason(is_stable: bool, coef_name: str, limit_text: str) -> str:
    if is_stable:
        return STABILITY_DICT[True]
    return f"{coef_name} {limit_text}"


def _compute_stability_cma(group: DataFrame) -> DataFrame:
    """
    Computes the longitudinal stability (cma) of an aircraft,
    for a given group using linear regression.

    Args:
        group (DataFrame): Contains aerodynamic coefficients.

    Returns:
        Series: A series containing the stability status for the longitudinal direction.

    """
    X_aoa = group[["alpha"]].values.reshape(-1, 1)
    y_cms = group["cms"].values

    reg_cma = LinearRegression().fit(X_aoa, y_cms)
    lr_cma = reg_cma.coef_[0]
    cma_stable = lr_cma < 0

    return Series({
        "lr_cma": lr_cma,
        "longitudinal": _status_or_reason(cma_stable, "Cma", lr_cma, ">= 0."),
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
    x_aos = group[["beta"]].values.reshape(-1, 1)
    y_cml = group["cml"].values
    reg_cnb = LinearRegression().fit(x_aos, y_cml)
    lr_cnb = reg_cnb.coef_[0]

    # Linear regression for clb (slope of cmd to aos)
    y_cmd = group["cmd"].values
    reg_clb = LinearRegression().fit(x_aos, y_cmd)
    lr_clb = reg_clb.coef_[0]

    cnb_stable = -lr_cnb < 0
    clb_stable = lr_clb < 0

    return Series({
        "lr_cnb": lr_cnb,
        "lr_clb": lr_clb,
        "directional": _status_or_reason(cnb_stable, "Cnb", lr_cnb, "<= 0."),
        "lateral": _status_or_reason(clb_stable, "Clb", lr_clb, ">= 0."),
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

    if cma is None or cnb is None or clb is None:
        return "Undefined", "Undefined", "Undefined"

    cma_stable = cma < 0
    cnb_stable = -cnb < 0
    clb_stable = clb < 0

    return (
        _status_or_reason(cma_stable, "Cma", ">= 0."),
        _status_or_reason(cnb_stable, "Cnb", "<= 0."),
        _status_or_reason(clb_stable, "Clb", ">= 0."),
    )
