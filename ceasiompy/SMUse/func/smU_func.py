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
from ceasiompy.utils.commonxpath import SMUSE_PRED_DATASET
from cpacspy.cpacsfunctions import get_value_or_default, add_value, create_branch
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

    input_columns = ["altitude", "machNumber", "angleOfAttack", "angleOfSideslip"]

    df = pd.read_csv(prediction_dataset)

    # Remove constant input columns
    columns_to_keep = [col for col in input_columns if df[col].nunique() > 1]
    removed_columns = list(set(input_columns) - set(columns_to_keep))

    if removed_columns:
        print(f"Removing constant columns in {df}: {removed_columns}")
        df = df[columns_to_keep]  # Keep only relevant columns

    X_pred = df.to_numpy()
    y_pred = model.predict_values(X_pred)

    return y_pred


def save_new_dataset(prediction_dataset, predictions, result_dir, cpacs_path, cpacs_out_path):

    cpacs = CPACS(cpacs_path)

    df = pd.read_csv(prediction_dataset)
    col_name = "Predictions"
    df[col_name] = predictions

    old_filename = os.path.basename(prediction_dataset)
    new_filename = old_filename.replace(".csv", "_with_predictions.csv")
    output_file_path = os.path.join(result_dir, new_filename)
    df.to_csv(output_file_path, index=False)

    log.info(f"New dataset with prediction saved in: {output_file_path}")

    create_branch(cpacs.tixi, SMUSE_PRED_DATASET)
    add_value(cpacs.tixi, SMUSE_PRED_DATASET, output_file_path)

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)

    return output_file_path


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
