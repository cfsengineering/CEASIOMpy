"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Store data from workflow modules.

| Author: Leon Deligny
| Creation: 2025-Mar-03

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.Database.func.utils import data_to_db
from ceasiompy.utils.ceasiompyutils import aircraft_name

from pathlib import Path
from sqlite3 import Cursor
from tixi3.tixi3wrapper import Tixi3

from ceasiompy import log

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def store_cpacs2gmsh_data(
    cursor: Cursor,
    wkdir: Path,
    tixi: Tixi3,
    table_name: str,
) -> None:
    """
    Store data from Results/GMSH.

    Args:
        cursor (Cursor): gmsh_data table from 'ceasiompy.db' cursor.
        wkdir (Path): Results/GMSH directory.
        tixi (Tixi3): Tixi handle of CPACS file.

    """
    table_name = "gmsh_data"
    files_list = list(wkdir.glob("*.su2"))

    name = str(aircraft_name(tixi))

    for file in sorted(files_list):
        file_name = str(file.name)

        if "_" in str(file_name):
            deformation: str = file_name.split("_")[1]
            angle = float(file_name.split("_")[2].replace(".su2", ""))
        else:
            deformation: str = "no_deformation"
            angle: float = 0.0

        log.info(
            f"Storing file {file_name}, "
            f"aircraft={name}, "
            f"deformation={deformation}, "
            f"angle={angle}."
        )

        with open(file, "rb") as file:
            file_data = file.read()
            data = {
                "su2_file_data": file_data,
                "aircraft": name,
                "deformation": deformation,
                "angle": angle,
            }

            data_to_db(cursor, data, table_name)
