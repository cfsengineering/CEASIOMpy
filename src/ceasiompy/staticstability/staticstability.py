"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Static stability module
"""

# Imports

from ceasiompy.staticstability.func.extractdata import compute_stab_table

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log


# Main

def main(cpacs: CPACS, results_dir: Path) -> None:
    """
    Analyses longitudinal, directional and lateral stability
    from the data of a CPACS file.
    """

    errors = []
    success_count = 0

    for aeromap_uid in cpacs.get_aeromap_uid_list():
        try:
            success = compute_stab_table(
                cpacs=cpacs,
                aeromap_uid=aeromap_uid,
                results_dir=results_dir,
            )
            if not success:
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
