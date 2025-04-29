"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Store data from workflow modules.


| Author: Leon Deligny
| Creation: 10-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import pandas as pd

from cpacspy.cpacsfunctions import get_value
from ceasiompy.Database.func.utils import data_to_db
from ceasiompy.utils.ceasiompyutils import aircraft_name

from pathlib import Path
from sqlite3 import Cursor
from tixi3.tixi3wrapper import Tixi3

from ceasiompy import log

from ceasiompy.DynamicStability import (
    DYNAMICSTABILITY_NSPANWISE_XPATH,
    DYNAMICSTABILITY_NCHORDWISE_XPATH,
)

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def store_dynstab_data(
    cursor: Cursor,
    wkdir: Path,
    tixi: Tixi3,
    table_name: str,
) -> None:
    """
    Store data from Results/DynamicStability.

    Args:
        cursor (Cursor): avl_data table from 'ceasiompy.db' cursor.
        wkdir (Path): Results/PyAVL directory.
        tixi (Tixi3): Tixi handle of CPACS file.

    Raises:
        FileNotFoundError: If no Force files are found.

    """
    table_name = "derivatives_data"
    name = str(aircraft_name(tixi))

    # Append data to it
    data = {}

    # Add aircraft name
    data["aircraft"] = name

    # Define the path to the SDSA_input.xml file
    csv = wkdir / "alpha_beta_dot_derivatives.csv"

    # For sure is DLM Method
    if csv.exists():
        # Load the CSV file into a DataFrame
        df = pd.read_csv(csv)

        chord = get_value(tixi, DYNAMICSTABILITY_NCHORDWISE_XPATH)
        span = get_value(tixi, DYNAMICSTABILITY_NSPANWISE_XPATH)
        method = "DLM"

        # Iterate over the rows of the DataFrame
        for _, row in df.iterrows():
            # Populate the data dictionary with the values from the DataFrame row
            data = {
                "aircraft": name,
                "method": method,
                "chord": chord,
                "span": span,
                "mach": row['mach'],
                "x_ref": row['x_ref'],
                "y_ref": row['y_ref'],
                "z_ref": row['z_ref'],
                "cm_alphaprim": row['cm_alphaprim'],
                "cz_alphaprim": row['cz_alphaprim'],
                "cx_alphaprim": row['cx_alphaprim'],
                "cy_betaprim": row['cy_betaprim'],
                "cl_betaprim": row['cl_betaprim'],
                "cn_betaprim": row['cn_betaprim'],
            }

            data_to_db(cursor, data, table_name)

# ==============================================================================
#    MAIN
# ==============================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
