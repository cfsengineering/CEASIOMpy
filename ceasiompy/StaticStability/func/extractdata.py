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

from ceasiompy.StaticStability.func.plot import plot_stability

from ceasiompy.StaticStability.func.stabilitystatus import (
    check_stability_lr,
    check_stability_tangent,
)

from typing import List
from pathlib import Path
from pandas import DataFrame
from tixi3.tixi3wrapper import Tixi3

from cpacspy.cpacspy import CPACS, AeroMap

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def generate_stab_df(cpacs: CPACS, aeromap_uid: str, lr_bool: bool) -> DataFrame:
    """
    Generate the Markdownpy Table for
    longitudinal/directional/lateral stability
    to show in the results directory.

    Args:
        cpacs (CPACS object): CPACS file.
        aeromap (AeroMap object): Chosen Aeromap.
        lr_bool (bool): True if using Linear Regression.

    Returns:
        (DataFrame): Contains stability data for each combination of mach, alt, aoa, and aos.

    """

    tixi: Tixi3 = cpacs.tixi
    aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)

    # Access correct xpath in CPACS file
    increment_map_xpath = f"{aeromap.xpath}/incrementMaps/incrementMap"

    # Create a DataFrame from the aeromap data
    grouped = aeromap.df.groupby(["machNumber", "altitude", "angleOfAttack", "angleOfSideslip"])

    # Check for more than two distinct lines in each group
    for name, group in grouped:
        if len(group) > 2:
            raise ValueError(f"More than two distinct lines found for group: {name}")

    df = grouped.first().reset_index()

    # Rename columns
    df.rename(columns={
        "machNumber": "mach",
        "altitude": "alt",
        "angleOfAttack": "aoa",
        "angleOfSideslip": "aos"
    }, inplace=True)

    # Extract values from CPACS
    if not lr_bool:
        log.info("Looking at the slopes of the stability derivatives.")

        clb_values = tixi.getTextElement(f"{increment_map_xpath}/dcmd").split(";")
        clb = [float(value) for value in clb_values]
        cma_values = tixi.getTextElement(f"{increment_map_xpath}/dcms").split(";")
        cma = [float(value) for value in cma_values]
        cnb_values = tixi.getTextElement(f"{increment_map_xpath}/dcml").split(";")
        cnb = [float(value) for value in cnb_values]

        if not clb or not cma or not cnb:
            raise ValueError("One of the stability derivative lists is empty.")

        # Add the extracted values to the DataFrame
        df["cma"] = cma
        df["cnb"] = cnb
        df["clb"] = clb

        # Check stability for each row
        (
            df["long_stab"],
            df["dir_stab"],
            df["lat_stab"],
            df["comment"],

        ) = zip(*df.apply(
                lambda row: check_stability_tangent(row["cma"], row["cnb"], row["clb"]),
                axis=1,
                )
                )

        return df[[
            "mach", "alt", "aoa", "aos",
            "cms", "cml", "cmd",
            "cma", "clb", "cnb",
            "long_stab", "dir_stab", "lat_stab",
            "comment",
        ]]

    else:
        log.info("Using Linear Regression to compute the stability derivatives.")
        df = check_stability_lr(df)

        return df[[
            "mach", "alt", "aoa", "aos",
            "cms", "cml", "cmd",
            "lr_cma", "lr_cma_intercept",
            "lr_clb", "lr_clb_intercept",
            "lr_cnb", "lr_cnb_intercept",
            "long_stab", "dir_stab", "lat_stab",
            "comment",
        ]]


def generate_stab_table(cpacs: CPACS, aeromap_uid: str, results_dir: Path,
                        lr_bool: bool) -> List[List[str]]:
    """
    Generate the Markdownpy Table for the longitudinal/directional/lateral
    stability to show in the results.

    Args:
        cpacs (CPACS object): CPACS file.

    Returns:
        (List[List[str]]): Contains stability data for each combination of mach, alt, aoa, and aos.

    """

    # Define what the stability table will contain
    stability_table = [[
        "mach", "alt", "aoa", "aos",
        "long_stab",
        "dir_stab",
        "lat_stab",
        "comment"
    ]]

    # Generate dataframe with necessary info
    df = generate_stab_df(cpacs, aeromap_uid, lr_bool)

    # Plot different stabilities
    plot_stability(results_dir, df, lr_bool)

    # Append the results to the stability_table
    stability_table.extend(df[[
        "mach", "alt", "aoa", "aos",
        "long_stab",
        "dir_stab",
        "lat_stab",
        "comment"
    ]].values.tolist())

    return stability_table

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
