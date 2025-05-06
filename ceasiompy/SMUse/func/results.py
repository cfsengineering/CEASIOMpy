"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import pandas as pd

from typing import Dict
from pathlib import Path
from pandas import DataFrame
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath

from ceasiompy import log
from ceasiompy.SMUse import SMUSE_PREDICTIONDATASET_XPATH

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def save_new_dataset(
    datasets: Dict[str, DataFrame],
    predictions_dict: Dict[str, Dict],
    objective: str,
    results_dir: Path,
) -> None:
    """
    Saves new datasets with predictions,
    ensuring correct column order and updating only necessary fields.
    """

    for dataset_name, df in datasets.items():
        # Add predictions to the dataset
        df[objective] = predictions_dict[dataset_name]["predictions"]

        # Save dataset as CSV
        output_file_path = results_dir / f"{dataset_name}_with_{objective}.csv"
        df.to_csv(output_file_path, index=False)

        log.info(f"Updated dataset: {dataset_name} with predictions.")
        log.info(f"New dataset saved: {output_file_path}")


def get_smu_results(
    cpacs: CPACS,
    results_dir: Path,
    objective: str,
) -> None:
    """
    Updates the CPACS aeromap with predictions stored in CSV files.
    """

    # Get all CSV files in results_dir, sorted to match aeromaps in order
    csv_files = sorted([f for f in os.listdir(results_dir) if f.endswith(".csv")])
    aeromap_uid_list = get_aeromap_list_from_xpath(
        cpacs, SMUSE_PREDICTIONDATASET_XPATH
    )

    log.info(f"Aeromap UIDs: {aeromap_uid_list}")
    for aeromap_uid, file_name in zip(aeromap_uid_list, csv_files):
        df = pd.read_csv(results_dir / file_name)
        if df.shape[1] < 5:
            raise ValueError(f"Invalid dataset format in {file_name}")

        aeromap: AeroMap = cpacs.get_aeromap_by_uid(aeromap_uid)
        altitudes = aeromap.get("altitude").tolist()
        mach_numbers = aeromap.get("machNumber").tolist()
        aoa_values = aeromap.get("angleOfAttack").tolist()
        aos_values = aeromap.get("angleOfSideslip").tolist()

        log.info(f"Updating aeromap: {aeromap_uid} with {file_name}")

        for i, alt in enumerate(altitudes):
            aeromap.add_coefficients(
                alt=alt,
                mach=mach_numbers[i],
                aos=aos_values[i],
                aoa=aoa_values[i],
                objective=df[objective][i],
            )

        log.info(f"Updated aeromap {aeromap_uid} with {objective} values.")
        aeromap.save()
