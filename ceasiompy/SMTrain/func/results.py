"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Get suggested points and model paths and save them in CPACS File.
Save new aeromap suggested points

| Author: Giacomo Gronda
| Creation: 2025-03-20

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from cpacspy.cpacsfunctions import (
    add_value,
    create_branch,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonxpaths import SUGGESTED_POINTS_XPATH

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


# TODO: Improve function's logic
def get_smt_results(cpacs: CPACS, results_dir: Path) -> None:
    """Function to write SMTrain result in the CPACS file

    Finds the files "suggested_points.csv" and "surrogateModel_*.pkl" in the results_dir directory
    Updates the CPACS file with the paths.
    Add aeromap.
    """

    # TODO: Understand why need to reload
    # Reload CPACS file
    cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)
    cpacs = CPACS(cpacs.cpacs_file)
    tixi = cpacs.tixi

    # Path to "suggested_points.csv"
    suggested_points_path = results_dir / "suggested_points.csv"
    if not suggested_points_path.is_file():
        log.info(f"File not found: {suggested_points_path}")
        return None
    else:
        create_branch(tixi, SUGGESTED_POINTS_XPATH)
        add_value(tixi, SUGGESTED_POINTS_XPATH, suggested_points_path)
        aeromap = cpacs.create_aeromap_from_csv(suggested_points_path)
        aeromap.save()
        log.info(f"New aeromap with suggested points: {aeromap}")
