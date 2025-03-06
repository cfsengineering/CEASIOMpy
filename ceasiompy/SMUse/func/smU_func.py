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
import numpy as np
from skopt.space import Real, Categorical
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import SMTRAIN_SM_XPATH
from cpacspy.cpacsfunctions import get_value_or_default, add_string_vector
from ceasiompy.utils.moduleinterfaces import get_module_path
from cpacspy.cpacspy import CPACS
from ceasiompy.SMTrain.func.surrogate import Kriging, MF_Kriging
from smt.surrogate_models import KRG
from smt.applications import MFK

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def make_predictions(cpacs_path, prediction_dataset, model):

    df = pd.read_csv(prediction_dataset)

    # Remove constant input columns
    columns_to_keep = [col for col in input_columns if df[col].nunique() > 1]
    removed_columns = list(set(input_columns) - set(columns_to_keep))

    if removed_columns:
        print(f"Removing constant columns in {level}: {removed_columns}")
        df = df[columns_to_keep + [objective_coefficient]]  # Keep only relevant columns
        # df.to_csv(output_file_path, index=False)  # Save the modified dataset

    X_pred = df.to_numpy()
    y_pred = model.predict_values(X_pred)

    return y_pred


def save_new_dataset(prediction_dataset, predictions, cpacs_path, result_dir):

    cpacs = CPACS(cpacs_path)

    df = pd.read_csv(prediction_dataset)
    col_name = "Predictions"
    df[col_name] = predictions

    old_filename = os.path.basename(prediction_dataset)
    new_filename = old_filename.replace(".csv", "_with_predictions.csv")
    output_file_path = os.path.join(result_dir, filename)
    df.to_csv(output_file_path, index=False)

    log.info(f"New dataset with prediction saved in: {output_file_path}")

    return output_file_path


def response_surface(x_rs, y_rs, dataset_path):
    
    # per il momento no scatter e solo "predictions"

    df = pd.read_csv(dataset_path)

    x = df[x_rs]
    y = df[y_rs]
    z = df["Predictions"]

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    ax.plot_trisurf(x, y, z, cmap="viridis", alpha=0.5, edgecolor="none")
    ax.set_xlabel(f"{x_rs}")
    ax.set_ylabel(f"{y_rs}")
    ax.set_zlabel("Predictions")
    ax.set_title(f"Response Surface")
    ax.view_init(elev=25, azim=45)
    ax.legend()
    
    colorbar = plt.colorbar(ax.collections[0], ax=ax, shrink=0.5, aspect=10)
    colorbar.set_label("Predictions")

    plt.show()
    
    


# plot(se attivato)

# suggest new values(se attivato)

# aeromap (x workflow)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
