"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Extract results from AVL calculations and save them in a CPACS file.
Plot the lift distribution from AVL strip forces file 'fs.txt'.
Convert AVL 'plot.ps' to 'plot.pdf'.

Python version: >=3.8

| Author: Romain Gauthier
| Creation: 2024-03-18

TODO:

    *

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import os
import csv
import glob
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import SM_XPATH, SUGGESTED_POINTS_XPATH, SMTRAIN_XPATH
from cpacspy.cpacsfunctions import create_branch, add_value
from cpacspy.cpacsfunctions import get_value
from cpacspy.cpacspy import CPACS
from ceasiompy.SMUse.func.smUconfig import load_surrogate
import pickle

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_smt_results(cpacs_path, cpacs_out_path, results_path):
    """Function to write SMTrain result in the CPACS file

    Finds the files "suggested_points.csv" and "surrogateModel_*.pkl" in the results_path directory.
    Updates the CPACS file with the paths.

    Args:
        cpacs_path (str): Path to the input CPACS file.
        cpacs_out_path (str): Path to the output CPACS file.
        results_path (str): Directory where the files are located.
    """

    cpacs = CPACS(cpacs_path)
    input_columns = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]

    # Path to "suggested_points.csv"
    suggested_points_path = os.path.join(results_path, "suggested_points.csv")
    if os.path.exists(suggested_points_path):
        df = pd.read_csv(suggested_points_path)
    else:
        log.info(f"File not found: {suggested_points_path}")
        suggested_points_path = None

    # Find the surrogate model file
    surrogate_model_files = glob.glob(os.path.join(results_path, "surrogateModel_*.pkl"))
    surrogate_model_path = surrogate_model_files[0] if surrogate_model_files else None

    if not surrogate_model_path:
        log.info("No surrogateModel_*.pkl file found.")

    # Add suggested_points and surrogate_model path to CPACS
    if suggested_points_path:
        create_branch(cpacs.tixi, SUGGESTED_POINTS_XPATH)
        add_value(cpacs.tixi, SUGGESTED_POINTS_XPATH, suggested_points_path)

    if surrogate_model_path:
        create_branch(cpacs.tixi, SM_XPATH)
        add_value(cpacs.tixi, SM_XPATH, surrogate_model_path)

    # Create the aeromap
    if suggested_points_path:
        aeromap = cpacs.create_aeromap_from_csv(suggested_points_path)
        aeromap.save()
        log.info(f"New aeromap with suggested points: {aeromap}")

    # Save the updated CPACS
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
