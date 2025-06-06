"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Steady-derivatives computations through PyAVL.

| Author: Leon Deligny
| Creation: 2025-Feb-12

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pandas import concat

from typing import Tuple
from pandas import DataFrame
from ceasiompy.Database.func.storing import CeasiompyDb

from ceasiompy import log
from ceasiompy.DynamicStability import ALT
from ceasiompy.PyAVL import SOFTWARE_NAME as AVL_SOFTWARE

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def pick_with_zero(values, n):
    """Return a sorted list of n unique values, always including 0.0 if present."""
    values_set = set(values)
    if 0.0 in values_set:
        values_set.remove(0.0)
        chosen = [0.0] + sorted(values_set)[:n-1]
    else:
        chosen = sorted(values_set)[:n]
    return chosen


def compute_nb_rows_aero(
    nalpha: int,
    nmach: int,
    nbeta: int,
    nq: int,
    np: int,
    nr: int,
) -> int:
    return nalpha * nmach * (1 + nbeta + nq + np + nr)


def compute_nb_rows_ctrl(
    nalpha: int,
    nmach: int,
    nelevator: int,
    nrudder: int,
    naileron: int,
) -> int:
    return nalpha * nmach * (nelevator + nrudder + naileron)


def format_aero_data(df: DataFrame) -> DataFrame:
    """
    Format the data into the specified sequence.
    """
    formatted_data = []

    # Group by Mach number
    mach_groups = df.groupby("mach")
    for mach_val, mach_group in mach_groups:
        # Sort by alpha
        mach_group = mach_group.sort_values(by="alpha")

        # Extract the 9 series
        series = mach_group[
            (mach_group["beta"] == 0)
            & (mach_group["pb_2V"] == 0)
            & (mach_group["qc_2V"] == 0)
            & (mach_group["rb_2V"] == 0)
        ]
        log.info(f"Mach {mach_val}: appended alpha series with {series.shape[0]} rows")
        formatted_data.append(series)

        series = mach_group[
            (mach_group["pb_2V"] == 0)
            & (mach_group["qc_2V"] == 0)
            & (mach_group["rb_2V"] == 0)
        ].sort_values(by="beta")
        log.info(f"Mach {mach_val}: appended beta series with {series.shape[0]} rows")
        formatted_data.append(series)

        series = mach_group[
            (mach_group["beta"] == 0) & (mach_group["pb_2V"] == 0) & (mach_group["rb_2V"] == 0)
        ].sort_values(by="qc_2V")
        log.info(f"Mach {mach_val}: appended q series with {series.shape[0]} rows")
        formatted_data.append(series)

        series = mach_group[
            (mach_group["beta"] == 0) & (mach_group["qc_2V"] == 0) & (mach_group["rb_2V"] == 0)
        ].sort_values(by="pb_2V")
        log.info(f"Mach {mach_val}: appended p series with {series.shape[0]} rows")
        formatted_data.append(series)

        series = mach_group[
            (mach_group["beta"] == 0) & (mach_group["pb_2V"] == 0) & (mach_group["qc_2V"] == 0)
        ].sort_values(by="rb_2V")
        log.info(f"Mach {mach_val}: appended r series with {series.shape[0]} rows")
        formatted_data.append(series)

    return concat(formatted_data, ignore_index=True)


def format_ctrl_data(df: DataFrame, chosen_elevator, chosen_rudder, chosen_aileron) -> DataFrame:
    """
    Format the data into the SDSA-required sequence using elevator, rudder, and aileron.
    """
    formatted_data = []

    # Elevator series (rudder=aileron=0)
    for elev in chosen_elevator:
        for mach_val in sorted(df["mach"].unique()):
            series = df[
                (df["elevator"] == elev)
                & (df["rudder"] == 0)
                & (df["aileron"] == 0)
                & (df["mach"] == mach_val)
            ].sort_values(by="alpha")
            log.info(f"Elevator {elev}, Mach {mach_val}: appended series with {series.shape[0]} rows")
            formatted_data.append(series)

    # Rudder series (elevator=aileron=0)
    for rud in chosen_rudder:
        for mach_val in sorted(df["mach"].unique()):
            series = df[
                (df["elevator"] == 0)
                & (df["rudder"] == rud)
                & (df["aileron"] == 0)
                & (df["mach"] == mach_val)
            ].sort_values(by="alpha")
            log.info(f"Rudder {rud}, Mach {mach_val}: appended series with {series.shape[0]} rows")
            formatted_data.append(series)

    # Aileron series (elevator=rudder=0)
    for ail in chosen_aileron:
        for mach_val in sorted(df["mach"].unique()):
            series = df[
                (df["elevator"] == 0)
                & (df["rudder"] == 0)
                & (df["aileron"] == ail)
                & (df["mach"] == mach_val)
            ].sort_values(by="alpha")
            log.info(f"Aileron {ail}, Mach {mach_val}: appended series with {series.shape[0]} rows")
            formatted_data.append(series)

    return concat(formatted_data, ignore_index=True)


def get_tables_values(self) -> Tuple[DataFrame, DataFrame, int, int]:
    """
    Go access steady derivatives in CPACS at xPaths table_xpath and ctrltable_xpath.

    Returns:
        df (DataFrame): AC in function of alpha, beta, mach, p, q, r.
        table_xpath (str): xPath to table data.
        ctrltable_xpath (str): xPath to ctrltable data.

    """
    log.info("--- Get Tables values ---")
    
    # Define constants
    nalpha: int = 20
    nmach: int = 6
    nbeta: int = 8

    nq: int = 8
    np: int = 8
    nr: int = 8

    nelevator: int = 3
    naileron: int = 3
    nrudder: int = 3

    # Choose from which software to get the data
    if self.software_data == AVL_SOFTWARE:
        table_name = "avl_data"
    else:
        log.warning(f"software {self.software_data} not implemented yet.")

    aero_columns = [
        "alpha", "mach", "beta", "pb_2V", "qc_2V", "rb_2V",  # Inputs
        "cl", "cd", "cms", "cs", "cmd", "cml",  # Outputs (of chosen model)
    ]

    # Retrieve data from db without control surface deflections
    ceasiompy_db = CeasiompyDb()
    data = ceasiompy_db.get_data(
        table_name=table_name,
        columns=aero_columns,
        db_close=False,
        filters=[
            f"mach IN ({self.mach_str})",
            f"aircraft = '{self.aircraft_name}'",
            f"alt = {ALT}",
            "elevator = 0.0",
            "aileron = 0.0",
            "rudder = 0.0",
        ],
    )

    # Convert the data list to a DataFrame
    aero_df = DataFrame(data, columns=aero_columns).drop_duplicates()

    # Choose distinct values
    chosen_alpha = pick_with_zero(aero_df["alpha"].unique(), nalpha)
    chosen_mach = sorted(aero_df["mach"].unique())[:nmach]
    chosen_beta = pick_with_zero(aero_df["beta"].unique(), nbeta)
    chosen_q = pick_with_zero(aero_df["qc_2V"].unique(), nq)
    chosen_p = pick_with_zero(aero_df["pb_2V"].unique(), np)
    chosen_r = pick_with_zero(aero_df["rb_2V"].unique(), nr)

    # Throw error if not enough distinct values
    if len(chosen_alpha) < nalpha:
        raise ValueError(
            f"Not enough distinct alpha values (needed {nalpha}, got {len(chosen_alpha)})"
        )
    if len(chosen_mach) < nmach:
        raise ValueError(
            f"Not enough distinct mach values (needed {nmach}, got {len(chosen_mach)})"
        )
    if len(chosen_beta) < nbeta:
        raise ValueError(
            f"Not enough distinct beta values (needed {nbeta}, got {len(chosen_beta)})"
        )
    if len(chosen_q) < nq:
        raise ValueError(f"Not enough distinct qc_2V (q) values (needed {nq}, got {len(chosen_q)})")
    if len(chosen_p) < np:
        raise ValueError(f"Not enough distinct pb_2V (p) values (needed {np}, got {len(chosen_p)})")
    if len(chosen_r) < nr:
        raise ValueError(f"Not enough distinct rb_2V (r) values (needed {nr}, got {len(chosen_r)})")

    log.info(f"Chosen alpha: {[float(x) for x in chosen_alpha]}")
    log.info(f"Chosen mach: {[float(x) for x in chosen_mach]}")
    log.info(f"Chosen beta: {[float(x) for x in chosen_beta]}")
    log.info(f"Chosen q: {[float(x) for x in chosen_q]}")
    log.info(f"Chosen p: {[float(x) for x in chosen_p]}")
    log.info(f"Chosen r: {[float(x) for x in chosen_r]}")

    # Filter aero_df
    aero_df = aero_df[
        aero_df["alpha"].isin(chosen_alpha) &
        aero_df["mach"].isin(chosen_mach) &
        aero_df["beta"].isin(chosen_beta) &
        aero_df["qc_2V"].isin(chosen_q) &
        aero_df["pb_2V"].isin(chosen_p) &
        aero_df["rb_2V"].isin(chosen_r)
    ].drop_duplicates()

    # After filtering aero_df
    if aero_df.empty:
        raise ValueError("Filtered aero_df is empty. No data matches the chosen alpha, mach, beta, q, p, r values.")

    ctrl_columns = [
        "alpha", "mach", "elevator", "rudder", "aileron",  # Inputs
        "cl", "cd", "cms", "cs", "cmd", "cml",  # Outputs (of chosen model)
    ]

    # Retrieve data from db with standard aero setting
    data = ceasiompy_db.get_data(
        table_name=table_name,
        columns=ctrl_columns,
        db_close=True,
        filters=[
            f"mach IN ({self.mach_str})",
            f"aircraft = '{self.aircraft_name}'",
            f"alt = {ALT}",
            "beta = 0.0",
            "qc_2V = 0.0",
            "pb_2V = 0.0",
            "rb_2V = 0.0",
        ],
    )

    # Convert the data list to a DataFrame
    ctrl_df = DataFrame(data, columns=ctrl_columns).drop_duplicates()

    chosen_elevator = pick_with_zero(ctrl_df["elevator"].unique(), nelevator)
    chosen_rudder = pick_with_zero(ctrl_df["rudder"].unique(), nrudder)
    chosen_aileron = pick_with_zero(ctrl_df["aileron"].unique(), naileron)

    # Throw error if not enough distinct values for control surfaces
    if len(chosen_elevator) < nelevator:
        raise ValueError(
            f"Not enough distinct elevator values (needed {nelevator}, got {len(chosen_elevator)})"
        )
    if len(chosen_rudder) < nrudder:
        raise ValueError(
            f"Not enough distinct rudder values (needed {nrudder}, got {len(chosen_rudder)})"
        )
    if len(chosen_aileron) < naileron:
        raise ValueError(
            f"Not enough distinct aileron values (needed {naileron}, got {len(chosen_aileron)})"
        )

    log.info(f"Chosen elevator: {[float(x) for x in chosen_elevator]}")
    log.info(f"Chosen rudder: {[float(x) for x in chosen_rudder]}")
    log.info(f"Chosen aileron: {[float(x) for x in chosen_aileron]}")

    # Filter ctrl_df
    ctrl_df = ctrl_df[
        ctrl_df["alpha"].isin(chosen_alpha) &
        ctrl_df["mach"].isin(chosen_mach) &
        ctrl_df["elevator"].isin(chosen_elevator) &
        ctrl_df["rudder"].isin(chosen_rudder) &
        ctrl_df["aileron"].isin(chosen_aileron)
    ].drop_duplicates()

    # After filtering ctrl_df
    if ctrl_df.empty:
        raise ValueError("Filtered ctrl_df is empty. No data matches the chosen alpha, mach, elevator, rudder, aileron values.")

    log.info("--- Finished retrieving the Tables values ---")

    aero_df = format_aero_data(aero_df)
    ctrl_df = format_ctrl_data(ctrl_df, chosen_elevator, chosen_rudder, chosen_aileron)
    aero_nb = compute_nb_rows_aero(nalpha, nmach, nbeta, nq, np, nr)
    ctrl_nb = compute_nb_rows_ctrl(nalpha, nmach, nelevator, nrudder, naileron)

    aero_rows = aero_df.shape[0]
    if aero_rows != aero_nb:
        raise ValueError(
            "Uncorrect number of rows for aero table: "
            f"SDSA requires {aero_nb=} which is distinct from {aero_rows=}."
        )
    
    ctrl_df_rows = ctrl_df.shape[0]
    if ctrl_df_rows != ctrl_nb:
        raise ValueError(
            "Uncorrect number of rows for control table: "
            f"SDSA requires {ctrl_nb=} which is distinct from {ctrl_df_rows=}."
        )
    else:
        log.info(f"Found the correct number of rows ({ctrl_df_rows=}) for control table.")

    return aero_df, ctrl_df, aero_nb, ctrl_nb
