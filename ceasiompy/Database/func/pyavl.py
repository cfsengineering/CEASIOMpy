"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Store data from workflow modules.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 2025-Mar-03

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.ceasiompyutils import aircraft_name

from ceasiompy.Database.func.utils import (
    data_to_db,
    split_line,
)

from typing import Dict
from pathlib import Path
from sqlite3 import Cursor
from tixi3.tixi3wrapper import Tixi3

from ceasiompy import log

# ==============================================================================
#   CONSTANTS
# ==============================================================================

DATA = {
    "Alpha": (1, "alpha"),
    "Beta": (1, "beta"),
    "Mach": (1, "mach"),

    "pb/2V": (2, "pb_2v"),
    "qc/2V": (2, "qc_2v"),
    "rb/2V": (2, "rb_2v"),

    "flap": (1, "flap"),
    "aileron": (1, "aileron"),
    "elevator": (1, "elevator"),
    "rudder": (1, "rudder"),

    "Xref": (1, "xref"),
    "Yref": (2, "yref"),
    "Zref": (3, "zref"),

    "CDtot": (1, "cd"),
    "CYtot": (1, "cs"),
    "CLtot": (1, "cl"),

    "Cltot": (2, "cmd"),
    "Cmtot": (2, "cms"),
    "Cntot": (2, "cml"),

    "Cla": (1, "cmd_a"),
    "Cma": (1, "cms_a"),
    "Cna": (1, "cml_a"),

    "Clb": (2, "cmd_b"),
    "Cmb": (2, "cms_b"),
    "Cnb": (2, "cml_b"),
}

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def get_avl_data(force_file: Path) -> Dict:
    """
    Get aerodynamic coefficients and velocity from AVL total forces file (sb.txt).

    Args:
        force_file_ft (Path): Path to the AVL total forces file.

    Returns:
        (Dict[str, float]): Results from AVL.

    """

    if not force_file.is_file():
        raise FileNotFoundError(f"The AVL forces file '{force_file}' has not been found!")

    results = {var_name: None for _, var_name in DATA.values()}

    with open(force_file) as f:
        for line in f.readlines():
            for key, (index, var_name) in DATA.items():
                if key in line:
                    # Exception as they appear twice in .txt file
                    if key in ["Clb", "Cnb"]:
                        parts = line.split('=')
                        if len(parts) > 2:
                            results[var_name] = split_line(line, index)
                    elif key in ["flap", "aileron", "elevator", "rudder"]:
                        parts = line.split('=')
                        if len(parts) == 2:
                            results[var_name] = split_line(line, index)
                    else:
                        results[var_name] = split_line(line, index)

    return results


def store_avl_data(
    cursor: Cursor,
    wkdir: Path,
    tixi: Tixi3,
    table_name: str,
) -> None:
    """
    Store data from Results/GMSH.

    Args:
        cursor (Cursor): avl_data table from 'ceasiompy.db' cursor.
        wkdir (Path): Results/PyAVL directory.
        tixi (Tixi3): Tixi handle of CPACS file.

    Raises:
        FileNotFoundError: If no Force files are found.

    """

    case_dir_list = [case_dir for case_dir in wkdir.iterdir() if "Case" in case_dir.name]

    txt_file_name = "st.txt"

    name = str(aircraft_name(tixi))

    for config_dir in sorted(case_dir_list):
        # Checks if config_dir is a directory
        if not config_dir.is_dir():
            continue

        alt = float(config_dir.name.split("_")[1].split("alt")[1])

        file_path = Path(config_dir, txt_file_name)

        if not file_path.exists():
            raise FileNotFoundError(
                f"No result total forces '{txt_file_name}' file have been found!")

        # Append data to it
        data = get_avl_data(file_path)

        # Add aircraft name
        data["aircraft"] = name
        data["alt"] = alt

        data_to_db(cursor, data, table_name)

# ==============================================================================
#    MAIN
# ==============================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
