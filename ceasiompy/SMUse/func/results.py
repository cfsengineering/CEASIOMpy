"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import pandas as pd

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath

from ceasiompy import log
from ceasiompy.utils.commonxpath import SMUSE_XPATH

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def save_new_dataset(datasets, predictions_dict, coefficient, result_dir):
    """
    Saves new datasets with predictions,
    ensuring correct column order and updating only necessary fields.
    """

    for dataset_name, dataset_content in datasets.items():
        df_filtered = dataset_content["df_filtered"]
        removed_columns = dataset_content["removed_columns"]
        df_original = dataset_content["df_original"]

        if dataset_name not in predictions_dict:
            log.warning(f"No predictions found for {dataset_name}, skipping.")
            continue

        predictions = predictions_dict[dataset_name]["predictions"]

        # Restore removed columns with their original constant values
        for col in removed_columns:
            df_filtered[col] = df_original[col]

        log.info(f"Updated dataset: {dataset_name}")

        # Ensure only relevant input columns are retained
        input_columns = df_original.columns[:4]  # First 4 columns are input features
        df_filtered = df_filtered[input_columns]

        # Validate that input columns are in the correct order
        if list(df_filtered.columns) != list(df_original.columns[:4]):
            raise ValueError(f"Input columns are not in the correct order for {dataset_name}")

        # Add predictions to the dataset
        df_filtered[coefficient] = predictions

        # Save dataset as CSV
        filename = f"{dataset_name}_with_{coefficient}.csv"
        output_file_path = os.path.join(result_dir, filename)
        df_filtered.to_csv(output_file_path, index=False)

        log.info(f"New dataset saved: {output_file_path}")


def get_smu_results(cpacs: CPACS, results_dir: Path) -> None:
    """
    Updates the CPACS aeromap with predictions stored in CSV files.
    """

    # Get all CSV files in results_dir, sorted to match aeromaps in order
    csv_files = sorted([f for f in os.listdir(results_dir) if f.endswith(".csv")])

    if not csv_files:
        raise FileNotFoundError(f"No prediction dataset files found in {results_dir}")

    valid_coefficients = {"cl", "cd", "cs", "cmd", "cml", "cms"}

    aeromap_with_predictions_xpath = SMUSE_XPATH + "/predictionDataset"
    aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, aeromap_with_predictions_xpath)

    log.info(f"Aeromap UIDs: {aeromap_uid_list}")

    # Associa ogni aeromap con il relativo dataset CSV
    for aeromap_uid, file_name in zip(aeromap_uid_list, csv_files):
        file_path = os.path.join(results_dir, file_name)
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


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
