"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Scripts for checking the slope of the pitch, roll and yaw moments with respect to a certain angle

| Author: Leon Deligny
| Creation: 2025-01-27

"""

# Imports

from typing import Tuple
from sklearn.linear_model import LinearRegression

from pandas import (
    Series,
    DataFrame,
)

from ceasiompy.StaticStability import STABILITY_DICT

# Functions

def generate_message(row: Series) -> str:
    """
    Generates a message indicating the stability of the aircraft
    based on the stability status of longitudinal, directional, and lateral directions.

    Args:
        row (Series): Stability status for longitudinal, directional, and lateral directions.

    Returns:
        (str): Message indicating the stability of the aircraft.

    """

    if (
        (row["long_stab"] == "Stable")
        and (row["dir_stab"] == "Stable")
        and (row["lat_stab"] == "Stable")
    ):
        return "Aircraft is stable along all axes."
    elif (
        (row["long_stab"] == "Unstable")
        and (row["dir_stab"] == "Unstable")
        and (row["lat_stab"] == "Unstable")
    ):
        return "Aircraft is UN-stable along ALL axes."
    else:
        msg = ""
        if row["long_stab"] == "Unstable":
            msg += "Aircraft is unstable for Longitudinal axis i.e. Cma >=0. "
        if row["dir_stab"] == "Unstable":
            msg += "Aircraft is unstable for Directional axis i.e. Cnb <=0. "
        if row["lat_stab"] == "Unstable":
            msg += "Aircraft is unstable for Lateral axis i.e. Clb >=0. "

    return msg


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
            "long_stab": STABILITY_DICT[cma_stable],
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
            "dir_stab": STABILITY_DICT[cnb_stable],
            "lat_stab": STABILITY_DICT[clb_stable],
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

    df["comment"] = df.apply(generate_message, axis=1)

    return df


def check_stability_tangent(cma: float, cnb: float, clb: float) -> Tuple[str, str, str, str]:
    """
    We use tangents at the distinct points to check if the aircraft is stable or not.

    Args:
        cma (float): Derivative of pitching moment with respect to the angle of attack.
        cnb (float): Derivative of yawing moment with respect to the sideslip angle.
        clb (float): Derivative of rolling moment with respect to the sideslip angle.

    Returns:
        (Tuple[str, str, str, str]): Stability status messages.

    """

    if cma is None or cnb is None or clb is None:
        return (None, None, None), "Stability parameters are not well defined"

    cma_stable = cma < 0
    cnb_stable = -cnb < 0
    clb_stable = clb < 0

    cma_stable_str = STABILITY_DICT[cma_stable]
    cnb_stable_str = STABILITY_DICT[cnb_stable]
    clb_stable_str = STABILITY_DICT[clb_stable]

    stability_dict = {
        "long_stab": cma_stable_str,
        "dir_stab": cnb_stable_str,
        "lat_stab": clb_stable_str,
    }

    msg = generate_message(Series(stability_dict))

    return cma_stable_str, cnb_stable_str, clb_stable_str, msg
