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
import glob
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import SM_PREDICTIONS
from cpacspy.cpacsfunctions import create_branch, add_value
from cpacspy.cpacsfunctions import get_value
from cpacspy.cpacspy import CPACS

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_smu_results(cpacs_path, cpacs_out_path, results_path):

    cpacs = CPACS(cpacs_path)
    predictions_dataset_path = os.path.join(results_path, "predictions_dataset.csv")

    if not os.path.exists(predictions_dataset_path):
        print(f"File not found: {predictions_dataset_path}")
        predictions_dataset_path = None

    if predictions_dataset_path:
        create_branch(cpacs.tixi, SM_PREDICTIONS)
        add_value(cpacs.tixi, SM_PREDICTIONS, predictions_dataset_path)

        aeromap = cpacs.create_aeromap_from_csv(predictions_dataset_path)
        aeromap.save()
        print(f"New aeromap with predictions: {aeromap}")

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
