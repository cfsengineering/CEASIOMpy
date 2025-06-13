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
from numpy import isclose

from collections import Counter
from ambiance import Atmosphere
from ceasiompy.Database.func.storing import CeasiompyDb
from pandas import (
    Series,
    DataFrame,
)
from typing import (
    Any,
    List,
    Tuple,
)

from ceasiompy import log
from ceasiompy.DynamicStability import ALT
from ceasiompy.PyAVL import SOFTWARE_NAME as AVL_SOFTWARE

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def dimensionalize_rate(df: DataFrame, alt: float, c: float, b: float) -> DataFrame:
    """
    Add dimensional rates (q, p, r) to the DataFrame using local Mach and altitude.
    """
    def compute_rates(row: Series) -> Series:
        Atm = Atmosphere(alt)
        v = Atm.speed_of_sound[0] * row["mach"]
        p = round(row["pb_2V"] * 2 * v / b, 1)
        q = round(row["qc_2V"] * 2 * v / c, 1)
        r = round(row["rb_2V"] * 2 * v / b, 1)
        return Series({"q": q, "p": p, "r": r})

    rates = df.apply(compute_rates, axis=1)
    df = df.join(rates)
    return df


def pick_with_zero(values: Any, n: int) -> List[float]:
    """Return a list of n unique values, always including 0.0 if present,
    and the rest being the most frequent values."""
    values_list = list(values)
    counter = Counter(values_list)
    chosen = []
    if 0.0 in counter:
        chosen.append(0.0)
        del counter[0.0]
        n_needed = n
    else:
        n_needed = n + 1
    # Sort by frequency (descending), then by value (ascending)
    most_common = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    chosen += [val for val, _ in most_common[:n_needed]]
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


def format_aero_data(df: DataFrame, chosen_beta, chosen_q, chosen_p, chosen_r) -> DataFrame:
    """
    Format the data into the SDSA-required sequence.
    """
    formatted_data = []
    tol = 1e-4

    mach_groups = df.groupby("mach")
    for mach_val, mach_group in mach_groups:
        mach_group = mach_group.sort_values(by="alpha")

        # Alpha series (beta=0, p=q=r=0)
        series = mach_group[
            (mach_group["beta"] == 0.0)
            & (mach_group["p"] == 0.0)
            & (mach_group["q"] == 0.0)
            & (mach_group["r"] == 0.0)
        ]
        log.info(f"Mach {mach_val}: appended alpha series with {series.shape[0]} rows")
        formatted_data.append(series)

        # Beta series (for each beta != 0, p=q=r=0)
        for beta_val in chosen_beta:
            if beta_val == 0.0:
                continue
            series = mach_group[
                isclose(mach_group["beta"], beta_val, atol=tol)
                & (mach_group["p"] == 0.0)
                & (mach_group["q"] == 0.0)
                & (mach_group["r"] == 0.0)
            ].sort_values(by="alpha")
            log.info(
                f"Mach {mach_val}: appended beta={beta_val} series with {series.shape[0]} rows"
            )
            formatted_data.append(series)

        # q series (for each q != 0, beta=p=r=0)
        for q_val in chosen_q:
            if q_val == 0.0:
                continue
            series = mach_group[
                isclose(mach_group["q"], q_val, atol=tol)
                & (mach_group["beta"] == 0.0)
                & (mach_group["p"] == 0.0)
                & (mach_group["r"] == 0.0)
            ].sort_values(by="alpha")
            log.info(f"Mach {mach_val}: appended q={q_val} series with {series.shape[0]} rows")
            formatted_data.append(series)

        # p series (for each p != 0, beta=q=r=0)
        for p_val in chosen_p:
            if p_val == 0.0:
                continue
            series = mach_group[
                isclose(mach_group["p"], p_val, atol=tol)
                & (mach_group["beta"] == 0.0)
                & (mach_group["q"] == 0.0)
                & (mach_group["r"] == 0.0)
            ].sort_values(by="alpha")
            log.info(f"Mach {mach_val}: appended p={p_val} series with {series.shape[0]} rows")
            formatted_data.append(series)

        # r series (for each r != 0, beta=q=p=0)
        for r_val in chosen_r:
            if r_val == 0.0:
                continue
            series = mach_group[
                isclose(mach_group["r"], r_val, atol=tol)
                & (mach_group["beta"] == 0.0)
                & (mach_group["p"] == 0.0)
                & (mach_group["q"] == 0.0)
            ].sort_values(by="alpha")
            log.info(f"Mach {mach_val}: appended r={r_val} series with {series.shape[0]} rows")
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
                & (df["rudder"] == 0.0)
                & (df["aileron"] == 0.0)
                & (df["mach"] == mach_val)
            ].sort_values(by="alpha")
            log.info(
                f"Elevator {elev}, Mach {mach_val}: "
                f"appended series with {series.shape[0]} rows"
            )
            formatted_data.append(series)

    # Rudder series (elevator=aileron=0)
    for rud in chosen_rudder:
        for mach_val in sorted(df["mach"].unique()):
            series = df[
                (df["elevator"] == 0.0)
                & (df["rudder"] == rud)
                & (df["aileron"] == 0.0)
                & (df["mach"] == mach_val)
            ].sort_values(by="alpha")
            log.info(
                f"Rudder {rud}, Mach {mach_val}: "
                f"appended series with {series.shape[0]} rows"
            )
            formatted_data.append(series)

    # Aileron series (elevator=rudder=0)
    for ail in chosen_aileron:
        for mach_val in sorted(df["mach"].unique()):
            series = df[
                (df["elevator"] == 0.0)
                & (df["rudder"] == 0.0)
                & (df["aileron"] == ail)
                & (df["mach"] == mach_val)
            ].sort_values(by="alpha")
            log.info(
                f"Aileron {ail}, Mach {mach_val}: "
                f"appended series with {series.shape[0]} rows"
            )
            formatted_data.append(series)

    return concat(formatted_data, ignore_index=True)


def get_tables_values(self) -> Tuple[DataFrame, DataFrame]:
    """
    Go access steady derivatives in CPACS at xPaths table_xpath and ctrltable_xpath.

    Returns:
        df (DataFrame): AC in function of alpha, beta, mach, p, q, r.
        table_xpath (str): xPath to table data.
        ctrltable_xpath (str): xPath to ctrltable data.

    """
    log.info("--- Get Tables values ---")

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

    aero_df = dimensionalize_rate(
        aero_df,
        alt=0.0,
        c=self.c,
        b=self.b,
    )

    # Choose distinct values
    chosen_alpha = pick_with_zero(aero_df["alpha"], self.nalpha)
    chosen_mach = sorted(aero_df["mach"].unique())[:self.nmach]
    chosen_beta = pick_with_zero(aero_df["beta"], self.nbeta)
    chosen_q = pick_with_zero(aero_df["q"], self.nq)
    chosen_p = pick_with_zero(aero_df["p"], self.np)
    chosen_r = pick_with_zero(aero_df["r"], self.nr)

    # Throw error if not enough distinct values
    if len(chosen_alpha) < self.nalpha:
        raise ValueError(
            f"Not enough distinct alpha values (needed {self.nalpha}, got {len(chosen_alpha)})"
        )
    if len(chosen_mach) < self.nmach:
        raise ValueError(
            f"Not enough distinct mach values (needed {self.nmach}, got {len(chosen_mach)})"
        )
    if len(chosen_beta) < self.nbeta:
        raise ValueError(
            f"Not enough distinct beta values (needed {self.nbeta}, got {len(chosen_beta)})"
        )
    if len(chosen_q) < self.nq:
        raise ValueError(
            f"Not enough distinct q (q) values (needed {self.nq}, got {len(chosen_q)})"
        )
    if len(chosen_p) < self.np:
        raise ValueError(
            f"Not enough distinct p (p) values (needed {self.np}, got {len(chosen_p)})"
        )
    if len(chosen_r) < self.nr:
        raise ValueError(
            f"Not enough distinct r (r) values (needed {self.nr}, got {len(chosen_r)})"
        )

    log.info(f"Chosen alpha: {[float(x) for x in chosen_alpha]}")
    log.info(f"Chosen mach: {[float(x) for x in chosen_mach]}")
    log.info(f"Chosen beta: {[float(x) for x in chosen_beta]}")
    log.info(f"Chosen q: {[float(x) for x in chosen_q]}")
    log.info(f"Chosen p: {[float(x) for x in chosen_p]}")
    log.info(f"Chosen r: {[float(x) for x in chosen_r]}")

    # Filter aero_df
    aero_df = aero_df[
        aero_df["alpha"].isin(chosen_alpha)
        & aero_df["mach"].isin(chosen_mach)
        & aero_df["beta"].isin(chosen_beta)
        & aero_df["q"].isin(chosen_q)
        & aero_df["p"].isin(chosen_p)
        & aero_df["r"].isin(chosen_r)
    ].drop_duplicates()

    # After filtering aero_df
    if aero_df.empty:
        raise ValueError(
            "Filtered aero_df is empty. "
            "No data matches the chosen alpha, mach, beta, q, p, r values."
        )

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

    chosen_elevator = pick_with_zero(ctrl_df["elevator"], self.nelevator)
    chosen_rudder = pick_with_zero(ctrl_df["rudder"], self.nrudder)
    chosen_aileron = pick_with_zero(ctrl_df["aileron"], self.naileron)

    # Throw error if not enough distinct values for control surfaces
    if len(chosen_elevator) < self.nelevator:
        raise ValueError(
            f"Not enough distinct elevator values (needed {self.nelevator}, "
            f"got {len(chosen_elevator)})"
        )
    if len(chosen_rudder) < self.nrudder:
        raise ValueError(
            f"Not enough distinct rudder values (needed {self.nrudder}, "
            f"got {len(chosen_rudder)})"
        )
    if len(chosen_aileron) < self.naileron:
        raise ValueError(
            f"Not enough distinct aileron values (needed {self.aileron}, "
            f"got {len(chosen_aileron)})"
        )

    log.info(f"Chosen elevator: {[float(x) for x in chosen_elevator]}")
    log.info(f"Chosen rudder: {[float(x) for x in chosen_rudder]}")
    log.info(f"Chosen aileron: {[float(x) for x in chosen_aileron]}")

    # Filter ctrl_df
    ctrl_df = ctrl_df[
        ctrl_df["alpha"].isin(chosen_alpha)
        & ctrl_df["mach"].isin(chosen_mach)
        & ctrl_df["elevator"].isin(chosen_elevator)
        & ctrl_df["rudder"].isin(chosen_rudder)
        & ctrl_df["aileron"].isin(chosen_aileron)
    ].drop_duplicates()

    # After filtering ctrl_df
    if ctrl_df.empty:
        raise ValueError(
            "Filtered ctrl_df is empty."
            "No data matches the chosen alpha, mach, elevator, rudder, aileron values."
        )

    log.info("--- Finished retrieving the Tables values ---")

    aero_df = format_aero_data(aero_df, chosen_beta, chosen_q, chosen_p, chosen_r)
    ctrl_df = format_ctrl_data(ctrl_df, chosen_elevator, chosen_rudder, chosen_aileron)

    aero_rows = aero_df.shape[0]
    if aero_rows != self.aero_nb:
        raise ValueError(
            "Uncorrect number of rows for aero table: "
            f"SDSA requires {self.aero_nb=} which is distinct from {aero_rows=}."
        )

    ctrl_df_rows = ctrl_df.shape[0]
    if ctrl_df_rows != self.ctrl_nb:
        raise ValueError(
            "Uncorrect number of rows for control table: "
            f"SDSA requires {self.ctrl_nb=} which is distinct from {ctrl_df_rows=}."
        )
    else:
        log.info(f"Found the correct number of rows ({ctrl_df_rows=}) for control table.")

    return aero_df, ctrl_df
