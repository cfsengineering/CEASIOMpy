"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Store data from SU2Run results.

| Author: Leon Deligny
| Creation: 2025-Mar-03

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path
from sqlite3 import Cursor
from tixi3.tixi3wrapper import Tixi3

from ceasiompy import log

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def store_su2run_data(
    cursor: Cursor,
    wkdir: Path,
    tixi: Tixi3,
    table_name: str,
) -> None:
    """
    Store data from Results/SU2.

    Args:
        cursor (Cursor): gmsh_data table from 'ceasiompy.db' cursor.
        wkdir (Path): Results/SU2 directory.
        tixi (Tixi3): Tixi handle of CPACS file.

    """
    raise NotImplementedError("store_su2run_data not implemented")


# ==============================================================================
#    MAIN
# ==============================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
