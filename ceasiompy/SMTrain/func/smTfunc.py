# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import matplotlib.pyplot as plt
import pandas as pd
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split
import numpy as np
from skopt.space import Real, Categorical
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import SM_XPATH, SMTRAIN_XPATH, SUGGESTED_POINTS_XPATH
from cpacspy.cpacsfunctions import get_value_or_default, create_branch, add_value
from ceasiompy.utils.moduleinterfaces import get_module_path
from cpacspy.cpacspy import CPACS
from ceasiompy.SMTrain.func.surrogate import Kriging, MF_Kriging, make_predictions
from ceasiompy.utils.ceasiompyutils import get_results_directory
from smt.sampling_methods import LHS

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def filter_constant_columns(df, input_columns):
    """
    Remove constant input columns from the dataset and store their values.

    param df: DataFrame containing the dataset.
    param input_columns: List of input column names to check.
    return: DataFrame with constant columns removed, dictionary of removed columns and their values.
    """

    columns_to_keep = [col for col in input_columns if df[col].nunique() > 1]
    removed_columns = {col: df[col].iloc[0] for col in input_columns if col not in columns_to_keep}

    if removed_columns:
        print(f"Removing constant columns: {list(removed_columns.keys())}")

    return df[columns_to_keep], removed_columns


def split_data(datasets, data_repartition, random_state=42):
    """Divide the highest fidelity dataset into training, validation, and testing sets.

    Args:
        datasets (dict): Dictionary with fidelity levels as keys and (X, y) tuples as values.
        data_repartition (float): Fraction of data to use for validation+test (e.g., 0.3 means 70% train, 15% val, 15% test).
        random_state (int): Random seed for reproducibility.

    Returns:
        dict: Dictionary containing split datasets (X_train, X_val, X_test, y_train, y_val, y_test).
    """

    data_repartition = 1 - data_repartition

    if not datasets:
        log.warning("Datasets dictionary is empty. Returning None.")
        return None

    # Find the dataset with the highest fidelity level (last in the dictionary)
    highest_fidelity_level = max(datasets.keys(), key=lambda k: int(k.split("_")[-1]))
    log.info(f"Using highest fidelity dataset: {highest_fidelity_level}")

    # Extract X and y from the highest fidelity level dataset
    X = datasets[highest_fidelity_level][0]  # Inputs
    y = datasets[highest_fidelity_level][1]  # Outputs (e.g., CL)

    log.info(f"Original X shape: {X.shape}, y shape: {y.shape}")
    log.info(f"Original X content: {X}")
    log.info(f"Original y content: {y}")

    # Split into train and test/validation
    X_train, X_t, y_train, y_t = train_test_split(
        X, y, test_size=data_repartition, random_state=random_state
    )

    log.info(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
    log.info(f"X_train content: {X_train}")
    log.info(f"y_train content: {y_train}")

    log.info(f"X_t shape: {X_t.shape}, y_t shape: {y_t.shape}")
    log.info(f"X_t content: {X_t}")
    log.info(f"y_t content: {y_t}")

    # Split into validation and test
    X_val, X_test, y_val, y_test = train_test_split(
        X_t, y_t, test_size=0.3, random_state=random_state
    )

    log.info(f"X_val shape: {X_val.shape}, y_val shape: {y_val.shape}")
    log.info(f"X_val content: {X_val}")
    log.info(f"y_val content: {y_val}")

    log.info(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")
    log.info(f"X_test content: {X_test}")
    log.info(f"y_test content: {y_test}")

    return {
        "X_train": X_train,
        "X_val": X_val,
        "X_test": X_test,
        "y_train": y_train,
        "y_val": y_val,
        "y_test": y_test,
    }


def train_surrogate_model(fidelity_level, datasets, sets):

    hyperparam_space = [
        Real(0.0001, 10, name="theta0"),
        Categorical(["abs_exp", "squar_exp", "matern52", "matern32"], name="corr"),
        Categorical(["constant", "linear", "quadratic"], name="poly"),
        Categorical(["Cobyla", "TNC"], name="opt"),
        Real(1e-12, 1e-1, name="nugget"),
        Categorical(["constant", "linear", "quadratic"], name="rho_regr"),
        Real(0.1, 1, name="lambda_penalty"),
    ]

    if fidelity_level == 1:
        model = Kriging(hyperparam_space, sets)

    else:
        model = MF_Kriging(fidelity_level, datasets, hyperparam_space, sets)

    return model


def save_model(model, coefficient_name, datasets, result_dir):

    if not datasets:
        log.warning("Datasets dictionary is empty. Returning None.")
        return None

    # Find the dataset with the highest fidelity level (last in the dictionary)
    highest_fidelity_level = max(datasets.keys(), key=lambda k: int(k.split("_")[-1]))

    # Extract removed columns
    removed_columns = list(datasets[highest_fidelity_level][3].keys())

    model_name = f"surrogateModel_{coefficient_name}.pkl"
    model_path = os.path.join(result_dir, model_name)

    # Crea un dizionario con il modello e le informazioni sui metadati
    model_metadata = {
        "model": model,
        "coefficient": coefficient_name,
        "removed_columns": removed_columns,
    }

    with open(model_path, "wb") as file:
        pickle.dump(model_metadata, file)

    log.info(f"Model saved to {model_path}")


def plot_validation(model, sets, label):
    """Crea un grafico Predicted vs Actual"""

    X_test = sets["X_test"]
    y_test = sets["y_test"]

    predictions, _ = make_predictions(model, X_test, y_test)

    fig = plt.figure(figsize=(6, 6))
    plt.scatter(y_test, predictions, color="blue", alpha=0.5)
    plt.plot(
        [y_test.min(), y_test.max()],
        [y_test.min(), y_test.max()],
        "r--",
        lw=2,
    )
    plt.title(f"Predicted vs Actual {label}")
    plt.xlabel(f"Actual {label}")
    plt.ylabel(f"Predicted {label}")
    plt.grid()

    results_dir = get_results_directory("SMTrain")
    fig_name = "validatio_plot_" + label + ".png"
    fig_path = Path(results_dir, fig_name)
    plt.savefig(fig_path)
    plt.close(fig)


def new_doe(datasets, model, fraction_of_new_samples, result_dir):
    """Generates a new set of suggested sampling points based on model uncertainty.

    Args:
        datasets (dict): A dictionary containing datasets for different fidelity levels.
        model: The surrogate model used for making predictions.
        fraction_of_new_samples (int): The divisor to determine the number of new samples.
        result_dir (str): Path to the directory where the new dataset will be saved.

    Raises:
        ValueError: If fraction_of_new_samples is less than or equal to 0.
    """

    if fraction_of_new_samples <= 0:
        raise ValueError("fraction_of_new_samples must be greater than 0.")

    # Find the dataset with the highest fidelity level (last in the dictionary)
    highest_fidelity_level = max(datasets.keys(), key=lambda k: int(k.split("_")[-1]))
    log.info(f"Using highest fidelity dataset: {highest_fidelity_level}")

    X, _, df_filt, rmv_col, df = datasets[highest_fidelity_level]

    _, y_var = make_predictions(model, X)

    y_var_flat = np.asarray(y_var).flatten()
    sorted_indices = np.argsort(y_var_flat)[::-1]  # Sort in descending order
    n_new_samples = max(1, len(X) // fraction_of_new_samples)  # Ensure at least one sample
    top_n_indices = sorted_indices[:n_new_samples]
    top_X = X[top_n_indices]

    if top_X.shape[0] == 0:
        log.warning("No new suggested points, file not created.")
        return

    new_df = pd.DataFrame(top_X, columns=df_filt.columns)

    for col, value in rmv_col.items():
        new_df[col] = value

    input_columns = df.columns[:4]
    new_df = new_df[input_columns]

    filename = "suggested_points.csv"
    output_file_path = os.path.join(result_dir, filename)
    new_df.to_csv(output_file_path, index=False)

    log.info(f"New suggested points saved in {output_file_path}")


def lh_sampling(n_samples, ranges, random_state=None):

    sampling = LHS(
        xlimits=np.array(list(ranges.values())), criterion="ese", random_state=random_state
    )
    samples = sampling(n_samples)

    # Map sampled values back to variable names
    sampled_dict = {key: samples[:, idx] for idx, key in enumerate(ranges.keys())}

    # Post-process sampled data to apply precision constraints
    for key in sampled_dict:
        if key == "altitude":
            sampled_dict[key] = np.round(sampled_dict[key]).astype(int)  # Convert to int
        elif key == "machNumber":
            sampled_dict[key] = np.round(sampled_dict[key] / 0.01) * 0.01  # Round to nearest 0.01
        elif key in ["angleOfAttack", "angleOfSideslip"]:
            sampled_dict[key] = np.round(sampled_dict[key] / 0.01) * 0.01  # Round to nearest 0.01


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
