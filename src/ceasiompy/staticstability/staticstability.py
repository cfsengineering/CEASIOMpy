"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Static stability module
"""

# Imports
from cpacspy.cpacsfunctions import get_value
from ceasiompy.staticstability.func.extractdata import compute_stab_table

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonxpaths import SELECTED_AEROMAP_XPATH


# Main

def main(cpacs: CPACS, results_dir: Path) -> None:
    """
    Analyses longitudinal, directional and lateral stability
    from the data of a CPACS file.
    """

    errors = []
    aeromap_uid = str(get_value(
        tixi=cpacs.tixi,
        xpath=SELECTED_AEROMAP_XPATH,
    ))

    try:
        compute_stab_table(
            cpacs=cpacs,
            aeromap_uid=aeromap_uid,
            results_dir=results_dir,
        )
        log_msg = f"Static stability of '{aeromap_uid}' aeromap."
        log.info(log_msg)
    except Exception as e:
        err_msg = (
            f"Could not compute static stability of aeromap {aeromap_uid} due to {e=}"
        )
        log.warning(err_msg)
        errors.append(err_msg)

    if errors:
        raise RuntimeError("StaticStability failed:\n" + "\n".join(errors))
