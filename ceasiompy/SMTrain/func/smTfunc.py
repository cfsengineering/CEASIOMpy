"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Many functions for SMTrain


Python version: >=3.8

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:

    *Improve loop and AVL and SU2 settings
    
"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonxpath import (
    AVL_AEROMAP_UID_XPATH,
    SU2_AEROMAP_UID_XPATH,
    SU2_NB_CPU_XPATH,
    SU2_CONFIG_RANS_XPATH,
    SU2_MAX_ITER_XPATH,
)
from cpacspy.cpacsfunctions import get_value_or_default, add_value, open_tixi
from cpacspy.cpacspy import CPACS
from ceasiompy.SMTrain.func.smTconfig import retrieve_aeromap_data
from ceasiompy.SMTrain.func.surrogate import Kriging, MF_Kriging, make_predictions
from ceasiompy.utils.ceasiompyutils import (
    get_results_directory,
    run_module,
    get_aeromap_list_from_xpath,
    get_reasonable_nb_cpu,
)
from smt.sampling_methods import LHS
from ceasiompy.PyAVL.avlrun import run_avl
from ceasiompy.PyAVL.func.avlresults import get_avl_results
from ceasiompy.SU2Run.su2run import run_SU2_multi
from ceasiompy.SU2Run.func.su2results import get_su2_results
from ceasiompy.SU2Run.func.su2config import generate_su2_cfd_config
from ceasiompy.SU2Run.func.su2config_rans import generate_su2_cfd_config_rans
from skopt.space import Real, Categorical

log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def split_data(datasets, data_repartition, val_test_size=0.3, random_state=42):
    """Function to split the highest fidelity dataset into training, validation, and testing sets.

    The function takes a dictionary of datasets with different fidelity levels, identifies the
    highest fidelity dataset, and splits it into training, validation, and test sets based on the
    specified proportions.

    Args:
        datasets (dict): Dictionary where keys represent fidelity levels, and values are (X, y) tup
        data_repartition (float): Fraction of data reserved for validation and test sets
            (e.g., 0.3 means 70% train, 15% val, 15% test).
        val_test_size (float, optional): Proportion of validation+test data allocated to the test
            set (default is 0.3).
        random_state (int, optional): Random seed for reproducibility.

    Returns:
        dict: Dictionary containing the split datasets with keys:
            - "X_train", "X_val", "X_test": Feature matrices for training, validation,
                and test sets.
            - "y_train", "y_val", "y_test": Target values for training, validation, and test sets.
    """

    if not datasets:
        log.error("Datasets dictionary is empty. Cannot proceed with splitting.")
        raise ValueError("Datasets dictionary is empty.")

    if not (0 < data_repartition < 1):
        log.warning(
            f"Invalid data_repartition value: {data_repartition}. It should be between 0 and 1."
        )
        data_repartition = max(0.1, min(data_repartition, 0.9))  # Limitiamo a un range ragionevole

    # Convert from "% of train" to "% of test"
    test_val_fraction = 1 - data_repartition

    try:
        highest_fidelity_level = max(datasets.keys(), key=lambda k: int(k.split("_")[-1]))
    except (ValueError, IndexError):
        log.error("Dataset keys are not in expected format (e.g., 'fidelity_1', 'fidelity_2').")
        raise ValueError("Invalid dataset keys format.")

    log.info(f"Using highest fidelity dataset: {highest_fidelity_level}")

    try:
        # Extract X and y from the highest fidelity level dataset
        X = datasets[highest_fidelity_level][0]  # Inputs
        y = datasets[highest_fidelity_level][1]  # Outputs (e.g., CL)
        if X.shape[0] != y.shape[0]:
            log.error("Mismatch between number of samples in X and y.")
            raise ValueError(f"X has {X.shape[0]} samples, but y has {y.shape[0]}.")
    except KeyError:
        log.error(f"Dataset '{highest_fidelity_level}' does not contain valid (X, y) pairs.")
        raise ValueError(f"Dataset '{highest_fidelity_level}' is incorrectly formatted.")

    log.info(f"Dataset shape - X: {X.shape}, y: {y.shape}")

    # Split into train and test/validation
    X_train, X_t, y_train, y_t = train_test_split(
        X, y, test_size=test_val_fraction, random_state=random_state
    )

    if X_t.shape[0] < 1:
        raise ValueError(
            f"Not enough samples for validation and test with data_repartition={data_repartition}"
            f"At least 1 samples is needed for test: avaiable {X_t.shape[0]}"
            f"Try to add some points or change '% of training data'"
        )

    log.info(f"Train size: {X_train.shape[0]}, Test+Validation size: {X_t.shape[0]}")

    # Split into validation and test
    X_val, X_test, y_val, y_test = train_test_split(
        X_t, y_t, test_size=val_test_size, random_state=random_state
    )

    log.info(f"Validation size: {X_val.shape[0]}, Test size: {X_test.shape[0]}")

    return {
        "X_train": X_train,
        "X_val": X_val,
        "X_test": X_test,
        "y_train": y_train,
        "y_val": y_val,
        "y_test": y_test,
    }


def train_surrogate_model(fidelity_level, datasets, sets):
    """
    Train a surrogate model using Kriging or Multi-Fidelity Kriging, selecting
    appropriate polynomial regression types based on the number of training samples.

    The function first determines which polynomial basis functions can be used
    by checking if the number of training samples exceeds predefined thresholds
    based on the number of features. Then, it defines the hyperparameter space
    and trains the model accordingly.

    Args:
        fidelity_level (str): Specifies whether the model is single-fidelity ("One level")
            or multi-fidelity.
        datasets (dict): Dictionary containing datasets for different fidelity levels.
        sets (dict): Dictionary containing the split datasets. Expected keys:
            "X_train", "X_val", "X_test", "y_train", "y_val", "y_test".

    Returns:
        model: Trained surrogate model (Kriging or Multi-Fidelity Kriging).
        rmse (float): Root Mean Square Error of the trained model.

    Polynomial Selection Logic:
        - If training samples > (n_features + 1) * (n_features + 2) / 2 → Use
            ["constant", "linear", "quadratic"]
        - If training samples > (n_features + 1) → Use ["constant", "linear"]
        - Otherwise → Use ["constant"]
    """

    n_samples, n_features = sets["X_train"].shape

    # Determine allowed polynomial regression types based on sample count
    if n_samples > ((n_features + 1) * (n_features + 2) / 2):
        poly_options = ["constant", "linear", "quadratic"]
        x = (n_features + 1) * (n_features + 2) / 2
        log.info(f"Training points (n_samples): {n_samples}>{x} -> poly_options: {poly_options}")
    elif n_samples > (n_features + 2):
        poly_options = ["constant", "linear"]
        x = (n_features + 1) * (n_features + 2) / 2
        y = n_features + 2
        log.info(
            f"Training points (n_samples): {y}<{n_samples}<{x} -> poly_options: {poly_options}"
        )
    elif n_samples > 2:
        poly_options = ["constant"]
        y = n_features + 2
        log.info(f"Training points (n_samples): {n_samples}<{y} -> poly_options: {poly_options}")
    else:
        raise Warning(
            f"Number of training points must be greater than 2, current size: {n_samples}"
        )

    hyperparam_space = [
        Real(0.0001, 10, name="theta0"),
        Categorical(["abs_exp", "squar_exp", "matern52", "matern32"], name="corr"),
        Categorical(poly_options, name="poly"),
        Categorical(["Cobyla", "TNC"], name="opt"),
        Real(1e-12, 1e-4, name="nugget"),
        Categorical(poly_options, name="rho_regr"),
        Real(0.1, 1, name="lambda_penalty"),
    ]

    if fidelity_level == "One level":
        model, rmse = Kriging(hyperparam_space, sets)
    else:
        model, rmse = MF_Kriging(fidelity_level, datasets, hyperparam_space, sets)

    return model, rmse


def save_model(model, coefficient_name, datasets, result_dir):
    """
    Save the trained surrogate model along with its metadata.

    This function identifies the highest fidelity dataset, retrieves metadata
    such as removed columns, and saves the model with relevant information.

    Args:
        model: Trained surrogate model.
        coefficient_name (str): Name of the aerodynamic coefficient (e.g., "CL" or "CD").
        datasets (dict): Dictionary containing different fidelity datasets.
        result_dir (str): Path to the directory where the model will be saved.

    Returns:
        None
    """

    if not datasets:
        log.warning("Datasets dictionary is empty.")
        raise ValueError("Datasets dictionary is empty. Cannot save the model.")

    log.info("Saving model")

    # Find the dataset with the highest fidelity level (last in the dictionary)
    # Ensure fidelity levels are correctly extracted
    try:
        highest_fidelity_level = max(datasets.keys(), key=lambda k: int(k.split("_")[-1]))
    except (ValueError, IndexError):
        raise ValueError(
            "Invalid fidelity level format in dataset keys. Expected format: 'fidelity_X'."
        )

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


def plot_validation(model, sets, label, result_dir):
    """
    Generate and save a Predicted vs Actual plot for model validation.

    This function takes a trained surrogate model, evaluates it on test data, and
    generates a scatter plot comparing predicted values to actual values.

    Args:
        model: Trained surrogate model.
        sets (dict): Dictionary containing test dataset with keys:
                     "X_test" (features) and "y_test" (target values).
        label (str): Label for the aerodynamic coefficient being validated.

    Returns:
        None
    """

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

    fig_name = "validation_plot_" + label + ".png"
    fig_path = Path(result_dir, fig_name)
    plt.savefig(fig_path)
    plt.close(fig)


def new_doe(datasets, model, fraction_of_new_samples, result_dir):
    """
    Generate a new set of suggested sampling points based on model uncertainty.

    This function selects the highest uncertainty points from the dataset with
    the highest fidelity level and suggests them for additional sampling.

    Args:
        datasets (dict): A dictionary containing datasets for different fidelity levels.
                         Expected format: { "fidelity_X": (X, y, df_filt, rmv_col, df) }.
        model: The trained surrogate model used for making predictions.
        fraction_of_new_samples (int): Determines the number of new samples by dividing
                                       the dataset size by this value.
        result_dir (str): Path to the directory where the new dataset will be saved.

    Returns:
        None
    """

    if fraction_of_new_samples <= 0:
        raise ValueError("Fraction of new samples must be greater than 0.")

    if not datasets:
        raise ValueError("Datasets dictionary is empty. Cannot generate new DOE points.")

    # Find the dataset with the highest fidelity level (last in the dictionary)
    try:
        highest_fidelity_level = max(datasets.keys(), key=lambda k: int(k.split("_")[-1]))
    except (ValueError, IndexError):
        raise ValueError(
            "Invalid fidelity level format in dataset keys. Expected format: 'fidelity_X'."
        )

    log.info(f"Using highest fidelity dataset: {highest_fidelity_level}")

    try:
        X, _, df_filt, rmv_col, df = datasets[highest_fidelity_level]
    except ValueError:
        raise ValueError(
            f"Dataset structure for {highest_fidelity_level} is incorrect."
            f"Expected tuple (X, y, df_filt, rmv_col, df)."
        )

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

    # Restore removed columns with constant values
    for col, value in rmv_col.items():
        new_df[col] = value

    # Keep only input columns
    input_columns = df.columns[:4]
    new_df = new_df[input_columns]

    # Save suggested points
    filename = "suggested_points.csv"
    output_file_path = os.path.join(result_dir, filename)
    new_df.to_csv(output_file_path, index=False)

    log.info(f"New suggested points saved in {output_file_path}")


def lh_sampling(n_samples, ranges, result_dir, random_state=None):
    """
    Generate a Latin Hypercube Sampling (LHS) dataset within specified variable ranges.

    This function performs Latin Hypercube Sampling (LHS) using the Enhanced Stochastic
    Evolutionary (ESE) criterion to generate a diverse set of samples within given variable limits.

    Args:
        n_samples (int): Number of samples to generate.
        ranges (dict): Dictionary specifying the variable ranges in the format:
                       { "variable_name": (min_value, max_value) }.
        result_dir (str): Path to the directory where the sampled dataset will be saved.
        random_state (int, optional): Seed for random number generation to ensure reproducibility.

    Returns:
        None
    """

    if n_samples <= 0:
        raise ValueError("New samples must be greater than 0.")

    xlimits = np.array(list(ranges.values()))

    # Identify variables with fixed values (min == max)
    fixed_cols = [idx for idx, (low, high) in enumerate(xlimits) if low == high]

    sampling = LHS(xlimits=xlimits, criterion="ese", random_state=random_state)
    samples = sampling(n_samples)

    # mantain constant variables with fixed ranges
    for idx in fixed_cols:
        samples[:, idx] = xlimits[idx, 0]

    # Map sampled values back to variable names
    sampled_dict = {key: samples[:, idx] for idx, key in enumerate(ranges.keys())}

    # Post-process sampled data to apply precision constraints
    for key in sampled_dict:
        if key == "altitude":
            sampled_dict[key] = np.round(sampled_dict[key]).astype(int)  # Convert to int
        elif key in ["machNumber", "angleOfAttack", "angleOfSideslip"]:
            sampled_dict[key] = np.round(sampled_dict[key] / 0.01) * 0.01  # Round to nearest 0.01

    # Convert to DataFrame
    sampled_df = pd.DataFrame(sampled_dict)

    # Save sampled dataset
    filename = "lh_sampling_dataset.csv"
    output_file_path = os.path.join(result_dir, filename)
    sampled_df.to_csv(output_file_path, index=False)

    log.info(f"LHS dataset saved in {output_file_path}")


def launch_avl(result_dir, cpacs_path, cpacs_tmp_cfg, objective):
    """
    Executes AVL aerodynamic analysis running PyAVL Module

    This function processes a CPACS file, integrates a new aeromap from a previously
    generated dataset, and runs PyAVL module to compute aerodynamic coefficients.

    Args:
        result_dir (str): Directory where AVL results and intermediate files are stored.
        cpacs_path (str): Path to the CPACS XML file.
        cpacs_tmp_cfg (str): Path to the temporary CPACS file used during processing.
        objective (str): The aerodynamic coefficient to extract from the AVL results.
                         Expected values: ["cl", "cd", "cs", "cmd", "cml", "cms"].

    Returns:
        pd.DataFrame: A DataFrame containing the AVL results for the requested objective.
    """

    cpacs = CPACS(cpacs_path)
    tixi = open_tixi(cpacs_path)

    lh_sampling_path = os.path.join(result_dir, "lh_sampling_dataset.csv")
    if not os.path.exists(lh_sampling_path):
        raise FileNotFoundError(f"LHS dataset not found: {lh_sampling_path}")

    # Remove existing aeromap if present
    if tixi.uIDCheckExists("lh_sampling_dataset"):
        cpacs.delete_aeromap("lh_sampling_dataset")

    # Create and save new aeromap from LHS dataset
    aeromap = cpacs.create_aeromap_from_csv(lh_sampling_path)
    aeromap.save()

    # Update CPACS with the new aeromap
    add_value(cpacs.tixi, AVL_AEROMAP_UID_XPATH, aeromap.uid)
    cpacs.save_cpacs(cpacs_path, overwrite=True)

    # Run AVL analysis
    result_dir = get_results_directory("PyAVL")
    run_avl(cpacs_path, result_dir)
    get_avl_results(cpacs_path, cpacs_path, result_dir)

    log.info("----- End of " + "PyAVL" + " -----")

    # Reload CPACS file with updated AVL results
    cpacs = CPACS(cpacs_path)

    # Validate objective
    objective_map = {"cl": "cl", "cd": "cd", "cs": "cs", "cmd": "cmd", "cml": "cml", "cms": "cms"}
    if objective not in objective_map:
        raise ValueError(
            f"Invalid objective '{objective}'. Expected one of {list(objective_map.keys())}."
        )
    objective_map = {"cl": "cl", "cd": "cd", "cs": "cs", "cmd": "cmd", "cml": "cml", "cms": "cms"}

    # Retrieve aerodynamic data
    dataset = retrieve_aeromap_data(cpacs, aeromap.uid, objective, objective_map)
    cpacs.save_cpacs(cpacs_path, overwrite=True)

    log.info(f"AVL results extracted for {objective}:")
    log.info(dataset)

    return dataset


def launch_su2(
    result_dir, result_dir_su2, cpacs_path, cpacs_tmp_cfg, objective, high_variance_points=None
):
    """
    Executes SU2 CFD analysis using an aeromap or high-variance points.

    This function processes a CPACS file, selects or generates a new aeromap or high-variance
    points, runs SU2 to compute aerodynamic coefficients, and retrieves the results.

    Args:
        result_dir (str): Directory containing the LHS dataset and results.
        result_dir_su2 (str): Directory where SU2 results will be stored.
        cpacs_path (str): Path to the CPACS XML file.
        cpacs_tmp_cfg (str): Path to the temporary CPACS file used during processing.
        objective (str): The aerodynamic coefficient to extract from the SU2 results.
                         Expected values: ["cl", "cd", "cs", "cmd", "cml", "cms"].
        high_variance_points (bool, optional): If True, uses a new set of high-variance points
                                               instead of the LHS dataset. Defaults to None.

    Returns:
        pd.DataFrame: A DataFrame containing the SU2 results for the requested objective.
    """

    cpacs = CPACS(cpacs_path)
    tixi = open_tixi(cpacs_path)

    # Select dataset based on high-variance points or LHS sampling
    if high_variance_points is None:
        dataset_path = os.path.join(result_dir, "lh_sampling_dataset.csv")
        aeromap_uid = "lh_sampling_dataset"
    else:
        dataset_path = os.path.join(result_dir, "new_points.csv")
        aeromap_uid = "new_points"

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    # Remove existing aeromap if present
    if tixi.uIDCheckExists(aeromap_uid):
        cpacs.delete_aeromap(aeromap_uid)

    # Create and save new aeromap from the dataset
    aeromap = cpacs.create_aeromap_from_csv(dataset_path)
    if not aeromap:
        raise ValueError(f"Failed to create aeromap '{aeromap_uid}'.")

    aeromap.save()

    add_value(cpacs.tixi, SU2_AEROMAP_UID_XPATH, aeromap.uid)
    cpacs.save_cpacs(cpacs_path, overwrite=True)

    log.info(f"Selected aeromap: {aeromap_uid}")

    # Determine SU2 configuration
    cpacs = CPACS(cpacs_path)
    # iterations = get_value_or_default(cpacs.tixi, SU2_MAX_ITER_XPATH, 2)
    # nb_proc = get_value_or_default(cpacs.tixi, SU2_NB_CPU_XPATH, get_reasonable_nb_cpu())
    config_file_type = get_value_or_default(cpacs.tixi, SU2_CONFIG_RANS_XPATH, "Euler")

    if config_file_type == "RANS":
        log.info("Running RANS simulation")
        generate_su2_cfd_config_rans(cpacs_path, cpacs_tmp_cfg, result_dir_su2)
    else:
        log.info("Running Euler simulation")
        generate_su2_cfd_config(cpacs_path, cpacs_tmp_cfg, result_dir_su2)

    # Execute SU2 simulation
    run_SU2_multi(result_dir_su2)
    get_su2_results(cpacs_tmp_cfg, cpacs_tmp_cfg, result_dir_su2)

    log.info("----- End of " + "SU2Run" + " -----")

    # Reload CPACS with updated results
    cpacs = CPACS(cpacs_tmp_cfg)

    # Validate objective
    objective_map = {"cl": "cl", "cd": "cd", "cs": "cs", "cmd": "cmd", "cml": "cml", "cms": "cms"}
    if objective not in objective_map:
        raise ValueError(
            f"Invalid objective '{objective}'. Expected one of {list(objective_map.keys())}."
        )

    # Retrieve aerodynamic data
    dataset = retrieve_aeromap_data(cpacs, aeromap.uid, objective, objective_map)
    cpacs.save_cpacs(cpacs_tmp_cfg, overwrite=True)

    log.info(f"SU2 results extracted for {objective}:")
    log.info(dataset)

    return dataset


def new_points(datasets, model, result_dir, high_variance_points):
    """
    Selects new sampling points based on variance predictions from a surrogate model.

    This function identifies high-variance points from the `level_1` dataset for adaptive sampling.
    In the first iteration, it selects the top 6 points with the highest variance. In subsequent
    iterations, it picks the next highest variance point not previously selected.

    Args:
        datasets (dict): Dictionary containing different fidelity datasets (expects 'level_1').
        model (object): Surrogate model used to predict variance.
        result_dir (str): Directory where the selected points CSV file will be saved.
        high_variance_points (list, optional): List of previously selected high-variance points.
                                               Defaults to None.

    Returns:
        pd.DataFrame or None: A DataFrame containing the newly selected points.
                              Returns None if all high-variance points have already been chosen.
    """

    # Retrieve the first fidelity dataset
    first_dataset = datasets["level_1"]
    X, y, df, _, _ = first_dataset  # Unpack dataset

    # Compute variance prediction
    _, y_var = make_predictions(model, X)
    y_var_flat = np.asarray(y_var).flatten()
    sorted_indices = np.argsort(y_var_flat)[::-1]  # Sort indices by variance (descending)

    output_file_path = os.path.join(result_dir, "new_points.csv")
    columns = df.columns

    # First iteration: generate boundary points
    if not high_variance_points:
        log.info("First iteration: selecting the first 6 highest variance points.")
        selected_points = [tuple(X[idx]) for idx in sorted_indices[:6]]
        high_variance_points.extend(selected_points)

        sampled_df = pd.DataFrame(selected_points, columns=columns)

        # Save the CSV
        sampled_df.to_csv(output_file_path, index=False)
        return sampled_df

    log.info("Selecting next highest variance point.")

    # Convert list of points to a set for fast lookup
    high_variance_set = set(tuple(p) for p in high_variance_points)

    for idx in sorted_indices:
        new_point = tuple(X[idx])
        if new_point not in high_variance_set:
            high_variance_points.append(new_point)  # Add new point to the list
            sampled_df = pd.DataFrame([new_point], columns=columns)

            # Save the CSV
            sampled_df.to_csv(output_file_path, index=False)
            return sampled_df

    log.warning("No new points found, all have been selected.")
    return None


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
