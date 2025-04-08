"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Steady-derivatives computations through PyAVL.

Python version: >=3.8

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


def format_aero_data(df: DataFrame) -> DataFrame:
    """
    Format the data into the specified sequence.
    """
    formatted_data = []

    # Group by Mach number
    mach_groups = df.groupby("mach")
    for _, mach_group in mach_groups:
        # Sort by alpha
        mach_group = mach_group.sort_values(by="alpha")

        # Extract the 9 series
        formatted_data.append(mach_group[(mach_group["beta"] == 0)
                                         & (mach_group["pb_2V"] == 0)
                                         & (mach_group["qc_2V"] == 0)
                                         & (mach_group["rb_2V"] == 0)])

        # Sort by beta with q=p=r=0
        formatted_data.append(mach_group[(mach_group["pb_2V"] == 0)
                                         & (mach_group["qc_2V"] == 0)
                                         & (mach_group["rb_2V"] == 0)].sort_values(by="beta"))

        # Sort by q with beta=p=r=0
        formatted_data.append(mach_group[(mach_group["beta"] == 0)
                                         & (mach_group["pb_2V"] == 0)
                                         & (mach_group["rb_2V"] == 0)].sort_values(by="qc_2V"))

        # Sort by p with beta=q=r=0
        formatted_data.append(mach_group[(mach_group["beta"] == 0)
                                         & (mach_group["qc_2V"] == 0)
                                         & (mach_group["rb_2V"] == 0)].sort_values(by="pb_2V"))

        # Sort by r with beta=q=p=0
        formatted_data.append(mach_group[(mach_group["beta"] == 0)
                                         & (mach_group["pb_2V"] == 0)
                                         & (mach_group["qc_2V"] == 0)].sort_values(by="rb_2V"))

    return concat(formatted_data, ignore_index=True)


def format_ctrl_data(df: DataFrame) -> DataFrame:
    """
    Format the data into the specified sequence using elevator, rudder, and aileron.
    """
    formatted_data = []

    # Group by Mach number
    mach_groups = df.groupby("mach")
    for _, mach_group in mach_groups:
        # Sort by alpha
        mach_group = mach_group.sort_values(by="alpha")

        # Extract the 9 series
        formatted_data.append(mach_group[(mach_group["elevator"] == 0)
                                         & (mach_group["rudder"] == 0)
                                         & (mach_group["aileron"] == 0)])

        # Sort by elevator with rudder=aileron=0
        formatted_data.append(mach_group[
            (mach_group["rudder"] == 0)
            & (mach_group["aileron"] == 0)].sort_values(by="elevator")
        )

        # Sort by rudder with elevator=aileron=0
        formatted_data.append(mach_group[(mach_group["elevator"] == 0)
                                         & (mach_group["aileron"] == 0)].sort_values(by="rudder"))

        # Sort by aileron with elevator=rudder=0
        formatted_data.append(mach_group[(mach_group["elevator"] == 0)
                                         & (mach_group["rudder"] == 0)].sort_values(by="aileron"))

    return concat(formatted_data, ignore_index=True)


def get_tables_values(
    self
) -> Tuple[DataFrame, DataFrame]:
    """
    Go access steady derivatives in CPACS at xPaths table_xpath and ctrltable_xpath.

    Returns:
        df (DataFrame): AC in function of alpha, beta, mach, p, q, r.
        table_xpath (str): xPath to table data.
        ctrltable_xpath (str): xPath to ctrltable data.

    """
    log.info("--- Get Tables values ---")

    if self.software_data == AVL_SOFTWARE:
        table_name = "avl_data"
    else:
        log.warning(f"software {self.software_data} not implemented yet.")

    aero_columns = [
        "alpha", "mach", "beta", "pb_2V", "qc_2V", "rb_2V",
        "cl", "cd", "cms", "cs", "cmd", "cml"
    ]

    # Retrieve data from db
    ceasiompy_db = CeasiompyDb()
    data = ceasiompy_db.get_data(
        table_name=table_name,
        columns=aero_columns,
        db_close=False,
        filters=[
            f"mach IN ({self.mach_str})",
            f"aircraft = '{self.aircraft_name}'",
            f"alt = {ALT}"
        ]
    )

    # Convert the data list to a DataFrame
    aero_df = DataFrame(data, columns=aero_columns)

    ctrl_columns = [
        "alpha", "mach", "elevator", "rudder", "aileron",
        "cl", "cd", "cms", "cs", "cmd", "cml"
    ]

    data = ceasiompy_db.get_data(
        table_name=table_name,
        columns=ctrl_columns,
        db_close=True,
        filters=[
            f"mach IN ({self.mach_str})",
            f"aircraft = '{self.aircraft_name}'",
            f"alt = {ALT}"
        ]
    )

    # Convert the data list to a DataFrame
    ctrl_df = DataFrame(data, columns=ctrl_columns)

    log.info("--- Finished retrieving the Tables values ---")

    return format_aero_data(aero_df), format_ctrl_data(ctrl_df)

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute.")
