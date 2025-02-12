"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Scripts for checking the slope of the pitch, roll and yaw moments with respect to a certain angle

Python version: >=3.8

| Author: Leon Deligny
| Creation: 2025-01-27
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pandas as pd

from ceasiompy.utils.ceasiomlogger import get_logger

from pathlib import Path
from typing import Tuple
from sklearn.linear_model import LinearRegression

# =================================================================================================
#   FUNCTIONS
# =================================================================================================

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

STABILITY_DICT = {True: "Stable", False: "Unstable"}

def generate_message(row: pd.Series) -> str:
    """
    Generates a message indicating the stability of the aircraft based on the stability status of longitudinal, directional, and lateral directions.

    Args:
        row (Series): A series containing the stability status for longitudinal, directional, and lateral directions.

    Returns:
        str: A message indicating the stability of the aircraft.
    """

    msg = ""
    if (row['longitudinal_stability'] == "Stable") and (row['directional_stability'] == "Stable") and (row['lateral_stability'] == "Stable"):
        msg += "Aircraft is stable along all axes"
    if (row['longitudinal_stability'] == "Unstable"):
        msg += "Aircraft is unstable for Longitudinal axis i.e. Cma >=0. "
    if (row['directional_stability'] == "Unstable"):
        msg += "Aircraft is unstable for Directional axis i.e. Cnb <=0. "
    if (row['lateral_stability'] == "Stable"):
        msg += "Aircraft is unstable for Lateral axis i.e. Clb >=0. "
    return msg


def check_stability_lr(df: pd.DataFrame) -> pd.DataFrame:
    """
    We use linear regression to check if the aircraft is stable or not.

    Args:
        df (dataframe): A dataframe containing the aerodynamic coefficients for a specific combination of mach, alt and (aoa/aos).

    Returns:
        df (dataframe): A dataframe containing the stability status for longitudinal, directional and lateral direction for each mach, alt and (aoa/aos).
    """

    def compute_stability_cma(group: pd.DataFrame) -> pd.DataFrame:
        """
        Computes the longitudinal stability (cma) of the aircraft for a given group using linear regression.

        Args:
            group (DataFrame): A dataframe containing the aerodynamic coefficients for a specific combination of mach, altitude, and angle of sideslip.

        Returns:
            pd.Series: A series containing the stability status for the longitudinal direction.
        """

        X_aoa = group[['angleOfAttack']].values.reshape(-1, 1)
        y_cms = group['cms'].values
        reg_cma = LinearRegression().fit(X_aoa, y_cms)
        lr_cma = reg_cma.coef_[0]
        lr_cma_intercept = reg_cma.intercept_

        cma_stable = (lr_cma < 0)

        return pd.Series({
            'lr_cma': lr_cma,
            'lr_cma_intercept': lr_cma_intercept,
            'longitudinal_stability': STABILITY_DICT[cma_stable],
        })

    def compute_stability_cnb_clb(group: pd.DataFrame) -> pd.DataFrame:
        """
        Computes the directional (cnb) and lateral (clb) stability of the aircraft for a given group using linear regression.

        Args:
            group (DataFrame): A dataframe containing the aerodynamic coefficients for a specific combination of mach, altitude, and angle of attack.

        Returns:
            pd.Series: A series containing the stability status for the directional and lateral directions.
        """

        # Linear regression for cnb (slope of cml to aos)
        X_aos = group[['angleOfSideslip']].values.reshape(-1, 1)
        y_cml = group['cml'].values
        reg_cnb = LinearRegression().fit(X_aos, y_cml)
        lr_cnb = reg_cnb.coef_[0]
        lr_cnb_intercept = reg_cnb.intercept_

        # Linear regression for clb (slope of cmd to aos)
        y_cmd = group['cmd'].values
        reg_clb = LinearRegression().fit(X_aos, y_cmd)
        lr_clb = reg_clb.coef_[0]
        lr_clb_intercept = reg_cnb.intercept_

        cnb_stable = (-lr_cnb < 0)
        clb_stable = (lr_clb < 0)

        return pd.Series({
            'lr_cnb': lr_cnb,
            'lr_cnb_intercept': lr_cnb_intercept,
            'lr_clb': lr_clb,
            'lr_clb_intercept': lr_clb_intercept,
            'directional_stability': STABILITY_DICT[cnb_stable],
            'lateral_stability': STABILITY_DICT[clb_stable],
        })

    grouped_cma = df.groupby(['machNumber', 'altitude', 'angleOfSideslip']
                             ).apply(compute_stability_cma).reset_index()
    grouped_cnb_clb = df.groupby(['machNumber', 'altitude', 'angleOfAttack']).apply(
        compute_stability_cnb_clb).reset_index()

    result_df = pd.merge(grouped_cma, grouped_cnb_clb, on=['machNumber', 'altitude'])

    result_df['msg'] = result_df.apply(generate_message, axis=1)

    return result_df


def check_stability_tangent(cma: float, cnb: float, clb: float) -> Tuple[str, str, str, str]:
    """
    We use tangents at the distinct points to check if the aircraft is stable or not.

    Args:
        cma (float): Derivative of pitching moment with respect to the angle of attack.
        cnb (float): Derivative of yawing moment with respect to the sideslip angle.
        clb (float): Derivative of rolling moment with respect to the sideslip angle.

    Returns:
        stable (str tuple): Tuple containing stability status for longitudinal, directional and lateral direction.
        msg (str): Comment on the stability of the aircraft.
    """

    if cma is None or cnb is None or clb is None:
        return (None, None, None), "Stability parameters are not well defined"

    cma_stable = (cma < 0)
    cnb_stable = (-cnb < 0)
    clb_stable = (clb < 0)

    cma_stable_str = STABILITY_DICT[cma_stable]
    cnb_stable_str = STABILITY_DICT[cnb_stable]
    clb_stable_str = STABILITY_DICT[clb_stable]

    stability_dict = {
        'longitudinal_stability': cma_stable_str,
        'directional_stability': cnb_stable_str,
        'lateral_stability': clb_stable_str
    }

    msg = generate_message(pd.Series(stability_dict))

    return cma_stable_str, cnb_stable_str, clb_stable_str, msg
