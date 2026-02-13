"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Data extraction from pyAVL for stability analysis

| Author: Leon Deligny
| Creation: 2025-01-27

"""

# Imports

from ceasiompy.staticstability.func.plot import plot_stability
from ceasiompy.staticstability.func.stabilitystatus import (
    check_stability_lr,
    check_stability_tangent,
)

from typing import List
from pathlib import Path
from pandas import DataFrame
from tixi3.tixi3wrapper import Tixi3
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy import log


# Functions


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
    df.rename(
        columns={
            "machNumber": "mach",
            "altitude": "alt",
            "angleOfAttack": "aoa",
            "angleOfSideslip": "aos",
        },
        inplace=True,
    )

    # Extract values from CPACS
    if not lr_bool:
        log.info("Looking at the slopes of the stability derivatives.")

        clb = _read_increment_values(tixi, increment_map_xpath, "dcmd")
        cma = _read_increment_values(tixi, increment_map_xpath, "dcms")
        cnb = _read_increment_values(tixi, increment_map_xpath, "dcml")

        if not clb or not cma or not cnb:
            log.info(
                f"Skipping aeromap '{aeromap_uid}': missing incrementMap derivatives "
                "(expected dcmd, dcms, dcml)."
            )
            return DataFrame()

        n_der = min(len(clb), len(cma), len(cnb))
        if n_der == 0:
            return DataFrame()

        if len(df) != n_der:
            flat_df = aeromap.df.rename(
                columns={
                    "machNumber": "mach",
                    "altitude": "alt",
                    "angleOfAttack": "aoa",
                    "angleOfSideslip": "aos",
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
            df["long_stab"],
            df["dir_stab"],
            df["lat_stab"],
        ) = zip(
            *df.apply(
                lambda row: check_stability_tangent(row["cma"], row["cnb"], row["clb"]),
                axis=1,
            )
        )

        return df[
            [
                "mach",
                "alt",
                "aoa",
                "aos",
                "cms",
                "cml",
                "cmd",
                "cma",
                "clb",
                "cnb",
                "long_stab",
                "dir_stab",
                "lat_stab",
            ]
        ]

    else:
        log.info("Using Linear Regression to compute the stability derivatives.")
        df = check_stability_lr(df)
        required_cols = [
            "mach",
            "alt",
            "aoa",
            "aos",
            "cms",
            "cml",
            "cmd",
            "lr_cma",
            "lr_cma_intercept",
            "lr_clb",
            "lr_clb_intercept",
            "lr_cnb",
            "lr_cnb_intercept",
            "long_stab",
            "dir_stab",
            "lat_stab",
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            sample_row = {}
            if not df.empty:
                sample_row = df.iloc[0].to_dict()
            log.warning(
                f"Aeromap '{aeromap_uid}' missing LR stability columns {missing_cols}. "
                f"Available columns: {list(df.columns)}. Sample row: {sample_row}"
            )
            return DataFrame()

        return df[required_cols]


def generate_stab_table(
    cpacs: CPACS,
    aeromap_uid: str,
    results_dir: Path,
    lr_bool: bool,
) -> List[List[str]]:
    """
    Generate the Markdownpy Table for the longitudinal/directional/lateral
    stability to show in the results.

    Args:
        cpacs (CPACS object): CPACS file.

    Returns:
        (List[List[str]]): Contains stability data for each combination of mach, alt, aoa, and aos.

    """

    # Define what the stability table will contain
    stability_table = [
        ["mach", "alt", "aoa", "aos", "long_stab", "dir_stab", "lat_stab"]
    ]

    # Generate dataframe with necessary info
    df = generate_stab_df(cpacs, aeromap_uid, lr_bool)

    if df.empty:
        log.info(
            f"No static stability data found for aeromap '{aeromap_uid}'. "
            "Skipping table and plots."
        )
        return stability_table

    # Plot different stabilities
    plot_stability(results_dir, df, lr_bool)

    # Save tabular results to CSV so they can be loaded directly as a dataframe in the UI.
    csv_name = f"staticstability_{_safe_filename(aeromap_uid)}.csv"
    csv_path = Path(results_dir, csv_name)
    try:
        if lr_bool:
            export_cols = [
                "mach",
                "alt",
                "aoa",
                "aos",
                "cms",
                "cml",
                "cmd",
                "lr_cma",
                "lr_cma_intercept",
                "lr_clb",
                "lr_clb_intercept",
                "lr_cnb",
                "lr_cnb_intercept",
                "long_stab",
                "dir_stab",
                "lat_stab",
            ]
        else:
            export_cols = [
                "mach",
                "alt",
                "aoa",
                "aos",
                "cma",
                "clb",
                "cnb",
                "long_stab",
                "dir_stab",
                "lat_stab",
            ]
        export_df = df[[col for col in export_cols if col in df.columns]]
        export_df.to_csv(csv_path, index=False, float_format="%.12g")
    except Exception as exc:
        log.warning(f"Could not save static stability dataframe to CSV at {csv_path}: {exc}")

    # Append the results to the stability_table
    stability_table.extend(
        df[
            [
                "mach",
                "alt",
                "aoa",
                "aos",
                "long_stab",
                "dir_stab",
                "lat_stab",
            ]
        ].values.tolist()
    )

    return stability_table
