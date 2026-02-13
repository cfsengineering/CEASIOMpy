"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Static stability module
"""

# Imports

from pathlib import Path

from cpacspy.cpacsfunctions import get_value
from ceasiompy.staticstability.func.extractdata import generate_stab_table

from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.staticstability import STATICSTABILITY_LR_XPATH


# Main

def main(cpacs: CPACS, results_dir: Path) -> None:
    """
    Analyses longitudinal, directional and lateral stability
    from the data of a CPACS file.
    """

    tixi = cpacs.tixi
    errors = []
    success_count = 0

    for aeromap_uid in cpacs.get_aeromap_uid_list():
        try:
            lr_bool = get_value(tixi, STATICSTABILITY_LR_XPATH)
            table = generate_stab_table(
                cpacs=cpacs,
                lr_bool=lr_bool,
                aeromap_uid=aeromap_uid,
                results_dir=results_dir,
            )
            if len(table) <= 1:
                continue

            log_msg = f"Static stability of '{aeromap_uid}' aeromap."
            log.info(log_msg)
            success_count += 1
        except Exception as e:
            err_msg = (
                f"Could not compute static stability of aeromap {aeromap_uid} due to {e=}"
            )
            log.warning(err_msg)
            errors.append(err_msg)

    if errors and success_count == 0:
        raise RuntimeError("StaticStability failed:\n" + "\n".join(errors))
