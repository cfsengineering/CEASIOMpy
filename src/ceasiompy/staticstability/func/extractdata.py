"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Data extraction from pyAVL for stability analysis
"""

# Imports

from ceasiompy.staticstability.func.plot import plot_stability
from ceasiompy.staticstability.func.stabilitystatus import (
    # check_stability_lr,
    check_stability_tangent,
)

from pathlib import Path
from pandas import DataFrame
from tixi3.tixi3wrapper import Tixi3
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy import log


# Methods

def _safe_filename(name: str) -> str:
    return "".join(char if char.isalnum() or char in ("-", "_", ".") else "_" for char in name)


def _read_increment_values(tixi: Tixi3, increment_map_xpath: str, tag: str) -> list[float]:
    xpath = f"{increment_map_xpath}/{tag}"
    if not tixi.checkElement(xpath):
        return []
    raw = tixi.getTextElement(xpath).strip()
    if not raw:
        return []
    return [float(value) for value in raw.split(";") if value != ""]


def generate_stab_df(cpacs: CPACS, aeromap_uid: str) -> DataFrame:
    """
    Generate the Markdownpy Table for
    longitudinal/directional/lateral stability
    to show in the results directory.

    Args:
        cpacs (CPACS object): CPACS file.
        aeromap (AeroMap object): Chosen Aeromap.

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
    df.rename(
        columns={
            "machNumber": "mach",
            "altitude": "alt",
            "angleOfAttack": "alpha",
            "angleOfSideslip": "beta",
        },
        inplace=True,
    )

    # Extract values from CPACS
    log.info("Looking at the slopes of the stability derivatives.")

    clb = _read_increment_values(tixi, increment_map_xpath, "dcmd")
    cma = _read_increment_values(tixi, increment_map_xpath, "dcms")
    cnb = _read_increment_values(tixi, increment_map_xpath, "dcml")

    # if not clb or not cma or not cnb:
    #     log.info(f'{clb=} {cma=} {cnb=}')
    #     log.info("Using Linear Regression to compute the stability derivatives.")
    #     return check_stability_lr(df)

    log.info("Using the direct values of the stability derivatives.")
    n_der = min(len(clb), len(cma), len(cnb))
    if n_der == 0:
        return DataFrame()

    if len(df) != n_der:
        flat_df = aeromap.df.rename(
            columns={
                "machNumber": "mach",
                "altitude": "alt",
                "angleOfAttack": "alpha",
                "angleOfSideslip": "beta",
            }
        ).reset_index(drop=True)
        if len(flat_df) == n_der:
            df = flat_df
        else:
            align_n = min(len(df), n_der)
            log.warning(
                f"Aeromap '{aeromap_uid}' has inconsistent lengths between sampled points "
                f"({len(df)}) and increment derivatives ({n_der}); truncating to {align_n}."
            )
            df = df.iloc[:align_n].reset_index(drop=True)
            n_der = align_n

    # Add the extracted values to the DataFrame
    df["cma"] = cma[:n_der]
    df["cnb"] = cnb[:n_der]
    df["clb"] = clb[:n_der]
    for coeff_name in ("cms", "cml", "cmd"):
        if coeff_name not in df.columns:
            df[coeff_name] = float("nan")

    # Check stability for each row
    (
        df["longitudinal"],
        df["directional"],
        df["lateral"],
    ) = zip(
        *df.apply(
            lambda row: check_stability_tangent(row["cma"], row["cnb"], row["clb"]),
            axis=1,
        )
    )

    return df


# Functions

def compute_stab_table(
    cpacs: CPACS,
    aeromap_uid: str,
    results_dir: Path,
) -> bool:
    """
    Generate the Markdownpy Table for the longitudinal/directional/lateral
    stability to show in the results.
    """

    # Generate dataframe with necessary info
    stab_df = generate_stab_df(
        cpacs=cpacs,
        aeromap_uid=aeromap_uid,
    )

    if stab_df.empty:
        log.info(
            f"No static stability data found for aeromap '{aeromap_uid}'. "
            "Skipping table and plots."
        )
        return False

    # Plot different stabilities
    plot_stability(
        stab_df=stab_df,
        results_dir=results_dir,
    )

    # Save tabular results to CSV so they can be loaded directly as a dataframe in the UI.
    csv_name = f"staticstability_{_safe_filename(aeromap_uid)}.csv"
    csv_path = Path(results_dir, csv_name)
    try:
        export_df = stab_df.copy()

        export_df[[
            "mach",
            "alt",
            "alpha",
            "beta",
            "cma",
            "clb",
            "cnb",
            "longitudinal",
            "directional",
            "lateral",
        ]].to_csv(csv_path, index=False, float_format="%.12g")
    except Exception as e:
        log.warning(f"Could not save static stability dataframe to .csv at {csv_path}: {e=}")

    return True
