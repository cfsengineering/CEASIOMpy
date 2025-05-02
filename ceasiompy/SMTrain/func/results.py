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

import glob

from cpacspy.cpacsfunctions import (
    add_value,
    create_branch,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonxpaths import (
    SM_XPATH,
    SUGGESTED_POINTS_XPATH,
)

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

    tixi = cpacs.tixi

    # Path to "suggested_points.csv"
    suggested_points_path = results_dir / "suggested_points.csv"
    if suggested_points_path.is_file():
        log.info(f"Suggested points path: {suggested_points_path}")
    else:
        log.info(f"File not found: {suggested_points_path}")
        suggested_points_path = None

    # Find the surrogate model file
    surrofate_files = str(results_dir / "surrogateModel_*.pkl")
    surrogate_model_files = glob.glob(surrofate_files)
    surrogate_model_path = (
        surrogate_model_files[0]
        if surrogate_model_files
        else None
    )

    if not surrogate_model_path:
        log.info("No surrogateModel_*.pkl file found.")

    # Add suggested_points and surrogate_model path to CPACS
    if suggested_points_path:
        create_branch(tixi, SUGGESTED_POINTS_XPATH)
        add_value(tixi, SUGGESTED_POINTS_XPATH, suggested_points_path)
        aeromap = cpacs.create_aeromap_from_csv(suggested_points_path)
        aeromap.save()
        log.info(f"New aeromap with suggested points: {aeromap}")

    if surrogate_model_path:
        create_branch(tixi, SM_XPATH)
        add_value(tixi, SM_XPATH, surrogate_model_path)
