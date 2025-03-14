# ==============================================================================
#   IMPORTS
# ==============================================================================
import numpy as np
import csv
import os
import pandas as pd
import pickle
import matplotlib as plt
import matplotlib.tri as tri
from pathlib import Path
from sklearn.model_selection import train_test_split
from skopt.space import Real, Categorical
from ceasiompy.utils.ceasiomlogger import get_logger
from smt.utils.misc import compute_rms_error
from cpacspy.cpacsfunctions import get_value_or_default, add_value, create_branch, get_value
from ceasiompy.utils.moduleinterfaces import get_module_path
from cpacspy.cpacspy import CPACS
from ceasiompy.SMTrain.func.surrogate import Kriging, MF_Kriging
from smt.surrogate_models import KRG
from smt.applications import MFK

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def make_predictions(datasets, model):
    predictions_dict = {}

    # Iterate through all datasets in the dictionary
    for dataset_name, dataset_content in datasets.items():
        prediction_dataset = dataset_content["df_filtered"]

        # Check if the dataset is empty
        if prediction_dataset.empty:
            log.error(f"{dataset_name} is empty. No predictions can be made.")
            raise ValueError(f"The prediction dataset {dataset_name} is empty.")

        # Convert the dataset into a NumPy array for prediction
        X_pred = prediction_dataset.to_numpy()

        # Make predictions using the trained model
        y_pred = model.predict_values(X_pred)

        # Compute RMSE for the dataset
        rmse = compute_rms_error(model, X_pred, y_pred)
        log.info(f"RMSE for {dataset_name}: {rmse}")

        # Store the predictions in the dictionary
        predictions_dict[dataset_name] = {"predictions": y_pred, "rmse": rmse}

    return predictions_dict


def save_new_dataset(datasets, predictions_dict, coefficient, result_dir):
    """
    Saves new datasets with predictions, ensuring correct column order and updating only necessary fields.

    Parameters:
        datasets (dict): Dictionary containing multiple datasets.
        predictions_dict (dict): Dictionary of predictions, indexed by dataset name.
        coefficient (str): Name of the coefficient to be added to the dataset.
        result_dir (str): Directory where the new datasets will be saved.
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


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
