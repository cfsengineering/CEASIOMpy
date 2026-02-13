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


# Functions

def _status_or_reason(is_stable: bool, coef_name: str, limit_text: str) -> str:
    if is_stable:
        return STABILITY_DICT[True]
    return f"{coef_name} {limit_text}"


def compute_stability_cma(group: DataFrame) -> DataFrame:
    """
    Computes the longitudinal stability (cma) of an aircraft,
    for a given group using linear regression.

    Args:
        group (DataFrame): Contains aerodynamic coefficients.

    Returns:
        Series: A series containing the stability status for the longitudinal direction.

    """
    X_aoa = group[["aoa"]].values.reshape(-1, 1)
    y_cms = group["cms"].values

    reg_cma = LinearRegression().fit(X_aoa, y_cms)
    lr_cma = reg_cma.coef_[0]
    lr_cma_intercept = reg_cma.intercept_

    cma_stable = lr_cma < 0

    return Series(
        {
            "lr_cma": lr_cma,
            "lr_cma_intercept": lr_cma_intercept,
            "long_stab": _status_or_reason(cma_stable, "Cma", lr_cma, ">= 0."),
        }
    )


def compute_stability_cnb_clb(group: DataFrame) -> DataFrame:
    """
    Computes the directional (cnb) and lateral (clb) stability of the aircraft
    for a given group using linear regression.

    Args:
        group (DataFrame): Aerodynamic coefficients for mach, altitude, and angle of attack.

    Returns:
        Series: Stability status for the directional and lateral directions.

    """
    # Linear regression for cnb (slope of cml to aos)
    X_aos = group[["aos"]].values.reshape(-1, 1)
    y_cml = group["cml"].values
    reg_cnb = LinearRegression().fit(X_aos, y_cml)
    lr_cnb = reg_cnb.coef_[0]
    lr_cnb_intercept = reg_cnb.intercept_

    # Linear regression for clb (slope of cmd to aos)
    y_cmd = group["cmd"].values
    reg_clb = LinearRegression().fit(X_aos, y_cmd)
    lr_clb = reg_clb.coef_[0]
    lr_clb_intercept = reg_cnb.intercept_

    cnb_stable = -lr_cnb < 0
    clb_stable = lr_clb < 0

    return Series(
        {
            "lr_cnb": lr_cnb,
            "lr_cnb_intercept": lr_cnb_intercept,
            "lr_clb": lr_clb,
            "lr_clb_intercept": lr_clb_intercept,
            "dir_stab": _status_or_reason(cnb_stable, "Cnb", lr_cnb, "<= 0."),
            "lat_stab": _status_or_reason(clb_stable, "Clb", lr_clb, ">= 0."),
        }
    )


def check_stability_lr(df: DataFrame) -> DataFrame:
    """
    Using linear regression to check if the aircraft is stable or not.

    Args:
        df (DataFrame): Aerodynamic coefficients for mach, alt, aoa and aos.

    Returns:
        (DataFrame): Stability status for mach, alt, aoa and aos.
    """

    grouped_cma = (
        df.groupby(
            [
                "mach",
                "alt",
                "aos",
            ]
        )
        .apply(compute_stability_cma, include_groups=False)
        .reset_index()
    )

    grouped_cnb_clb = (
        df.groupby(
            [
                "mach",
                "alt",
                "aoa",
            ]
        )
        .apply(compute_stability_cnb_clb, include_groups=False)
        .reset_index()
    )

    # Merge grouped_cma and grouped_cnb_clb with the original df
    df = df.merge(grouped_cma, on=["mach", "alt", "aos"], how="left")
    df = df.merge(grouped_cnb_clb, on=["mach", "alt", "aoa"], how="left")

    return df


def check_stability_tangent(cma: float, cnb: float, clb: float) -> tuple[str, str, str]:
    """
    We use tangents at the distinct points to check if the aircraft is stable or not.

    Args:
        cma (float): Derivative of pitching moment with respect to the angle of attack.
        cnb (float): Derivative of yawing moment with respect to the sideslip angle.
        clb (float): Derivative of rolling moment with respect to the sideslip angle.

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
