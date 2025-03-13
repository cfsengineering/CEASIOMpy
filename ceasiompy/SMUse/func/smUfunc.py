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


def make_predictions(prediction_dataset, model):

    if prediction_dataset.empty:
        log.error("Prediction dataset is empty. No predictions can be made.")
        raise ValueError("The prediction dataset is empty.")

    X_pred = prediction_dataset.to_numpy()

    y_pred = model.predict_values(X_pred)

    rmse = compute_rms_error(model, X_pred, y_pred)
    log.info(f"RMSE Model: {rmse}")

    return y_pred


def save_new_dataset(
    predictions_dataset, predictions, coefficient, removed_columns, df, result_dir
):

    for col, value in removed_columns.items():
        predictions_dataset[col] = value

    if list(predictions_dataset.columns[:4]) != list(df.columns[:4]):
        raise ValueError("Input columns are not in the correct order")

    predictions_dataset[coefficient] = predictions

    filename = "predictions_dataset.csv"
    output_file_path = os.path.join(result_dir, filename)
    predictions_dataset.to_csv(output_file_path, index=False)

    log.info(f"New dataset with predictions saved in: {output_file_path}")


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
