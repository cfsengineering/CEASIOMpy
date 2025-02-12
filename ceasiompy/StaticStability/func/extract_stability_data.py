"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Data extraction from pyAVL for stability analysis

Python version: >=3.8

| Author: Leon Deligny
| Creation: 2025-01-27

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import math, pandas as pd

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.StaticStability.func.plot_stability import plot_stability
from ceasiompy.StaticStability.func.check_stability import check_stability_tangent, check_stability_lr

from pathlib import Path
from typing import Tuple
from tixi3.tixi3wrapper import Tixi3Exception
from cpacspy.cpacspy import CPACS, AeroMap

from typing import List

# =================================================================================================
#   FUNCTIONS
# =================================================================================================

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

STABILITY_DICT = {True: "Stable", False: "Unstable"}

def generate_stab_df(aeromap: AeroMap, cpacs: CPACS) -> Tuple[pd.DataFrame, bool]:
    """
    Generate the Markdownpy Table for the longitudinal/directional/lateral stability to show in the results.

    Args:
        cpacs (CPACS object): Cpacspy CPACS object.
        aeromap (AeroMap object): Cpacspy AeroMap object.
    Returns:
        df (dataframe): A dataframe containing stability data for each combination of mach, alt, aoa, and aos.
        using_tangent (bool): True if using AVL's tangents. False if using Linear Regression to compute the stability derivatives.
    
    """
    
    using_tangent = True
    tixi = cpacs.tixi

    # Access correct xpath in CPACS file
    increment_map_xpath = f"{aeromap.xpath}/incrementMaps/incrementMap"

    # Create a DataFrame from the aeromap data
    grouped = aeromap.df.groupby(["machNumber", "altitude", "angleOfAttack", "angleOfSideslip"])

    # Check for more than two distinct lines in each group
    for name, group in grouped:
        if len(group) > 2:
            raise ValueError(f"More than two distinct lines found for group: {name}")

    df = grouped.first().reset_index()

    # Degrees to radian
    df['angleOfAttack'] = df['angleOfAttack'] * math.pi / 180
    df['angleOfSideslip'] = df['angleOfSideslip'] * math.pi / 180

    # Extract values from CPACS
    try:
        clb_values = tixi.getTextElement(f"{increment_map_xpath}/dcmd").split(';')
        clb = [float(value) for value in clb_values]
        cma_values = tixi.getTextElement(f"{increment_map_xpath}/dcms").split(';')
        cma = [float(value) for value in cma_values]
        cnb_values = tixi.getTextElement(f"{increment_map_xpath}/dcml").split(';')
        cnb = [float(value) for value in cnb_values]

        if len(clb) == 0 or len(cma) == 0 or len(cnb) == 0:
            raise ValueError("One of the stability derivative lists is empty")

        # Add the extracted values to the DataFrame
        df['cma'] = cma
        df['cnb'] = cnb
        df['clb'] = clb

        # Check stability for each row
        df['longitudinal_stability'], df['directional_stability'], df['lateral_stability'], df['comment'] = zip(*df.apply(
            lambda row: check_stability_tangent(row['cma'], row['cnb'], row['clb']), axis=1))

        log.Info("Using AVL's computations to access the stability derivatives")

        return df[['machNumber', 'altitude', 'angleOfAttack', 'angleOfSideslip', "cms", "cml", "cmd", 'cma', 'cnb', 'clb', 'longitudinal_stability', 'directional_stability', 'lateral_stability', 'comment']], using_tangent

    except (Tixi3Exception, ValueError, Exception):

        not_using_tangent = False
        
        if len(clb) == 1 or len(cma) == 1 or len(cnb) == 1:
            raise ValueError(
                "One of the pitch/roll/yaw moments contains only 1 point. Linear Regression will not be possible.")

        df = check_stability_lr(df)

        log.Info("Using Linear Regression to compute the stability derivatives")

        return df[['machNumber', 'altitude', 'angleOfAttack', 'angleOfSideslip', "cms", "cml", "cmd", 'lr_cma', 'lr_cma_intercept', 'lr_clb', 'lr_clb_intercept', 'lr_cnb', 'lr_cnb_intercept', 'longitudinal_stability', 'directional_stability', 'lateral_stability', 'comment']], not_using_tangent


def generate_stab_table(aeromap: AeroMap, cpacs: CPACS) -> List[List[str]]:
    """
    Generate the Markdownpy Table for the longitudinal/directional/lateral stability to show in the results.

    Args:
        cpacs (CPACS object): Cpacspy CPACS object.
        aeromap (AeroMap object): Cpacspy AeroMap object.

    Returns:
        stability_table (list): A list of lists containing stability data for each combination of mach, alt, aoa, and aos.
        
    """

    # Define what the stability table will contain
    stability_table = [[
        "mach", "alt", "aoa", "aos", 
        "longitudinal stability",
        "directional stability", 
        "lateral stability", 
        "comment"
    ]]

    # Generate dataframe with necessary info
    df, tangent_bool = generate_stab_df(aeromap, cpacs)

    # Plot different stabilities
    plot_stability(df, tangent_bool)

    # Append the results to the stability_table
    stability_table.extend(df[[
        'machNumber', 'altitude', 'angleOfAttack', 'angleOfSideslip',
        'longitudinal_stability', 
        'directional_stability', 
        'lateral_stability', 
        'comment'
    ]].values.tolist())

    return stability_table
