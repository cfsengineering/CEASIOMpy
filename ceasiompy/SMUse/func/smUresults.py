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
from ceasiompy.utils.commonxpath import SM_PREDICTIONS, SMUSE_XPATH
from cpacspy.cpacsfunctions import create_branch, add_value
from cpacspy.cpacsfunctions import get_value
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_smu_results(cpacs_path, cpacs_out_path, results_path):
    """
    Updates the CPACS aeromap with predictions stored in CSV files.

    Parameters:
        cpacs_path (str): Path to the input CPACS file.
        cpacs_out_path (str): Path to save the updated CPACS file.
        results_path (str): Directory containing prediction datasets.
    """

    cpacs = CPACS(cpacs_path)

    # Get all CSV files in results_path, sorted to match aeromaps in order
    csv_files = sorted([f for f in os.listdir(results_path) if f.endswith(".csv")])

    if not csv_files:
        raise FileNotFoundError(f"No prediction dataset files found in {results_path}")

    valid_coefficients = {"cl", "cd", "cs", "cmd", "cml", "cms"}

    aeromap_with_predictions_xpath = SMUSE_XPATH + "/predictionDataset"
    aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, aeromap_with_predictions_xpath)

    log.info(f"Aeromap UIDs: {aeromap_uid_list}")

    # Associa ogni aeromap con il relativo dataset CSV
    for aeromap_uid, file_name in zip(aeromap_uid_list, csv_files):
        file_path = os.path.join(results_path, file_name)
        df = pd.read_csv(file_path)

        if df.shape[1] < 5:
            raise ValueError(f"Invalid dataset format in {file_name}")

        coef_column = df.columns[4]  # The coefficient column

        if coef_column not in valid_coefficients:
            raise ValueError(f"Invalid coefficient: {coef_column} in {file_name}")

        aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        if aeromap is None:
            log.error(f"Aeromap {aeromap_uid} not found.")
            continue

        log.info(f"Updating aeromap: {aeromap_uid} with {file_name}")

        altitudes = aeromap.get("altitude").tolist()
        mach_numbers = aeromap.get("machNumber").tolist()
        aoa_values = aeromap.get("angleOfAttack").tolist()
        aos_values = aeromap.get("angleOfSideslip").tolist()

        for i in range(len(altitudes)):
            aeromap.add_coefficients(
                altitudes[i],
                mach_numbers[i],
                aos_values[i],
                aoa_values[i],
                **{coef_column: df.iloc[i, 4]},  # Assigns coefficient value
            )

        log.info(f"Updated aeromap {aeromap_uid} with {coef_column} values.")

        aeromap.save()  # Salva ogni aeromap dopo l'aggiornamento

    # Salva il file CPACS aggiornato una sola volta
    cpacs.save_cpacs(cpacs_out_path, overwrite=True)

    log.info(f"Updated CPACS file saved at {cpacs_out_path}")


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
