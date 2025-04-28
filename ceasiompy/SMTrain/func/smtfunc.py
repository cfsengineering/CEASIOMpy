"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:
    *Improve loop and AVL and SU2 settings
"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import pickle
import numpy as np
import pandas as pd

from ceasiompy.PyAVL.pyavl import main as run_avl
from ceasiompy.SU2Run.su2run import run_SU2_multi
from sklearn.model_selection import train_test_split
from ceasiompy.PyAVL.func.results import get_avl_results
from ceasiompy.SU2Run.func.results import get_su2_results
from ceasiompy.SMTrain.func.config import retrieve_aeromap_data
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.SU2Run.func.config import generate_su2_cfd_config
from cpacspy.cpacsfunctions import (
    add_value,
    get_value,
)
from ceasiompy.SMTrain.func.surrogate import (
    kriging,
    mf_kriging,
    make_predictions,
)
from pathlib import Path
from numpy import ndarray
from smt.applications import MFK
from cpacspy.cpacspy import CPACS
from smt.surrogate_models import KRG
from smt.sampling_methods import LHS
from typing import (
    List,
    Dict,
    Tuple,
    Union,
    Literal,
)
from skopt.space import (
    Real,
    Categorical,
)

from ceasiompy import log
from ceasiompy.PyAVL import AVL_AEROMAP_UID_XPATH
from ceasiompy.utils.commonxpath import (
    SU2_AEROMAP_UID_XPATH,
    SU2_CONFIG_RANS_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_val_fraction(train_fraction: float) -> float:
    if not (0 < train_fraction < 1):
        log.warning(
            f"Invalid data_repartition value: {train_fraction}."
            "It should be between 0 and 1."
        )
        train_fraction = max(0.1, min(train_fraction, 0.9))

    # Convert from "% of train" to "% of test"
    test_val_fraction = 1 - train_fraction
    return test_val_fraction


def split_data(
    fidelity_datasets: Dict,
    train_fraction: float = 0.7,
    test_fraction_within_split: float = 0.3,
    random_state: int = 42,
) -> Dict[str, ndarray]:
    """
    Takes a dictionary of datasets with different fidelity levels and:
    1. identifies the highest fidelity dataset,
    2. splits it into training, validation, and test sets based on the specified proportions.

    Args:
        datasets (Dict): Keys represent fidelity levels with (x, y) values.
        data_repartition (float = 0.3):
            Fraction of data reserved for validation and test sets, for example:
            data_repartition=0.3 means 70% train, 15% val, 15% test
        val_test_size (float = 0.3):
            Proportion of validation+test data allocated to the test set.
        random_state (int, optional): Random seed for reproducibility.

    Returns:
        Dictionary containing the split datasets.
    """

    if not fidelity_datasets:
        raise ValueError("Datasets dictionary is empty.")

    test_val_fraction = get_val_fraction(train_fraction)

    try:
        highest_fidelity_level = max(fidelity_datasets.keys(), key=lambda k: int(k.split("_")[-1]))
    except (ValueError, IndexError):
        raise ValueError(
            "Dataset keys are not in expected format (e.g., 'fidelity_1', 'fidelity_2')."
        )

    log.info(f"Using highest fidelity dataset: {highest_fidelity_level}")

    try:
        # Extract X and y from the highest fidelity level dataset
        x: ndarray = fidelity_datasets[highest_fidelity_level][0]
        y: ndarray = fidelity_datasets[highest_fidelity_level][1]
        if x.shape[0] != y.shape[0]:
            raise ValueError(
                "Mismatch between number of samples"
                f"x has {x.shape[0]} samples, but y has {y.shape[0]}."
            )
    except KeyError:
        raise ValueError(f"Dataset '{highest_fidelity_level}' is incorrectly formatted.")

    log.info(f"Dataset shape - x: {x.shape}, y: {y.shape}")

    # Split into train and test/validation
    x_train: ndarray
    x_test: ndarray
    y_train: ndarray
    y_test: ndarray
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=test_val_fraction, random_state=random_state
    )

    if x_test.shape[0] < 1:
        raise ValueError(
            f"Not enough samples for validation and test with {train_fraction=}"
            f"At least 1 samples is needed for test: avaiable {x_test.shape[0]}"
            f"Try to add some points or change '% of training data'"
        )

    log.info(f"Train size: {x_train.shape[0]}, Test+Validation size: {x_test.shape[0]}")

    # Split into validation and test
    x_val: ndarray
    y_val: ndarray
    x_val, x_test, y_val, y_test = train_test_split(
        x_test, y_test, test_size=test_fraction_within_split, random_state=random_state
    )

    log.info(f"Validation size: {x_val.shape[0]}, Test size: {x_test.shape[0]}")

    return {
        "x_train": x_train, "x_val": x_val, "x_test": x_test,
        "y_train": y_train, "y_val": y_val, "y_test": y_test,
    }


def get_hyperparam_space(sets: Dict[str, ndarray]) -> List[str]:
    n_samples, n_features = sets["x_train"].shape

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

    return hyperparam_space


def train_surrogate_model(
    fidelity_level: Literal["One level", "Multi Fidelity"],
    datasets: Dict,
    sets: Dict[str, ndarray],
) -> Tuple[Union[KRG, MFK], float]:
    """
    Train a surrogate model using kriging or Multi-Fidelity kriging:
    1. selects appropriate polynomial basis functions for regression
    2. defines the hyperparameter space accordingly
    3. trains the model

    Polynomial Selection Logic:
        if training samples > (n_features + 1) * (n_features + 2) / 2
            Use ["constant", "linear", "quadratic"]
        elif training samples > (n_features + 1)
            Use ["constant", "linear"]
        else
            Use ["constant"]

    Args:
        fidelity_level (str): Either "One level" or "Multi Fidelity".
        datasets (Dict): Contains datasets for different fidelity levels.
        sets (Dict):
            Contains the split datasets. Expected keys:
            "x_train", "x_val", "x_test", "y_train", "y_val", "y_test".

    Returns:
        model: Trained surrogate model (kriging or Multi-Fidelity kriging).
        rmse (float): Root Mean Square Error of the trained model.
    """

    hyperparam_space = get_hyperparam_space(sets)

    if fidelity_level == "One level":
        model, rmse = kriging(
            param_space=hyperparam_space,
            sets=sets
        )
    elif fidelity_level == "Multi Fidelity":
        model, rmse = mf_kriging(
            fidelity_level=fidelity_level,
            datasets=datasets,
            param_space=hyperparam_space,
            sets=sets,
        )

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


def lh_sampling(
    n_samples: int,
    ranges: Dict,
    results_dir: Path,
    random_state: Union[int, None] = None,
) -> Path:
    """
    Generate a Latin Hypercube Sampling (LHS) dataset within specified variable ranges.
    Uses the Enhanced Stochastic Evolutionary (ESE) criterion
    to generate a diverse set of samples within given variable limits.

    Args:
        n_samples (int): Number of samples to generate.
        ranges (dict): Dictionary specifying the variable ranges in the format:
                       { "variable_name": (min_value, max_value) }.
        results_dir (str): Path to the directory where the sampled dataset will be saved.
        random_state (int = None): Seed for random number generation to ensure reproducibility.
    """

    if n_samples <= 0:
        raise ValueError("New samples must be greater than 0.")

    xlimits = np.array(list(ranges.values()))

    # Identify variables with fixed values (min == max)
    fixed_cols = [idx for idx, (low, high) in enumerate(xlimits) if low == high]

    sampling = LHS(xlimits=xlimits, criterion="ese", random_state=random_state)
    samples = sampling(n_samples)

    # maintain constant variables with fixed ranges
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

    # Save sampled dataset
    sampled_df = pd.DataFrame(sampled_dict)
    output_file_path = os.path.join(results_dir, "lh_sampling_dataset.csv")
    sampled_df.to_csv(output_file_path, index=False)
    log.info(f"LHS dataset saved in {output_file_path}")

    return output_file_path


def launch_avl(cpacs: CPACS, lh_sampling_path: Path, objective: str):
    """
    Executes AVL aerodynamic analysis running PyAVL Module

    This function processes a CPACS file, integrates a new aeromap from a previously
    generated dataset, and runs PyAVL module to compute aerodynamic coefficients.

    Args:
        result_dir (str): Directory where AVL results and intermediate files are stored.
        cpacs_path (str): Path to the CPACS XML file.
        objective (str): The aerodynamic coefficient to extract from the AVL results.
            Expected values: ["cl", "cd", "cs", "cmd", "cml", "cms"].

    Returns:
        pd.DataFrame: A DataFrame containing the AVL results for the requested objective.
    """
    tixi = cpacs.tixi
    if not os.path.exists(lh_sampling_path):
        raise FileNotFoundError(f"LHS dataset not found: {lh_sampling_path}")

    # Remove existing aeromap if present
    if tixi.uIDCheckExists("lh_sampling_dataset"):
        cpacs.delete_aeromap("lh_sampling_dataset")

    # Create and save new aeromap from LHS dataset
    aeromap = cpacs.create_aeromap_from_csv(lh_sampling_path)
    aeromap.save()

    # Update CPACS with the new aeromap
    add_value(tixi, AVL_AEROMAP_UID_XPATH, aeromap.uid)
    cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)

    # Run AVL analysis
    results_dir = get_results_directory("PyAVL")
    run_avl(cpacs, results_dir)
    get_avl_results(cpacs, results_dir)

    log.info("----- End of " + "PyAVL" + " -----")

    # Reload CPACS file with updated AVL results
    cpacs = CPACS(cpacs.cpacs_file)

    # Validate objective
    objective_map = {"cl": "cl", "cd": "cd", "cs": "cs", "cmd": "cmd", "cml": "cml", "cms": "cms"}
    if objective not in objective_map:
        raise ValueError(
            f"Invalid objective '{objective}'. Expected one of {list(objective_map.keys())}."
        )

    # Retrieve aerodynamic data
    dataset = retrieve_aeromap_data(cpacs, aeromap.uid, objective, objective_map)
    cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)

    log.info(f"AVL results extracted for {objective}:")
    log.info(dataset)

    return dataset


def launch_su2(
    cpacs: CPACS,
    results_dir: Path,
    results_dir_su2: Path,
    objective: str,
    high_variance_points=None  # TODO: For sure there is an issue with this argument
):
    """
    Executes SU2 CFD analysis using an aeromap or high-variance points.

    1. Processes a CPACS file
    2. Selects or generates an aeromap or high-variance points
    3. Runs SU2 to compute aerodynamic coefficients
    4. Retrieves the results

    """

    tixi = cpacs.tixi

    # Select dataset based on high-variance points or LHS sampling
    if high_variance_points is None:
        dataset_path = os.path.join(results_dir, "lh_sampling_dataset.csv")
        aeromap_uid = "lh_sampling_dataset"
    else:
        dataset_path = os.path.join(results_dir, "new_points.csv")
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
    cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)

    log.info(f"Selected aeromap: {aeromap_uid}")

    # Determine SU2 configuration
    cpacs = CPACS(cpacs.cpacs_file)
    # iterations = get_value_or_default(cpacs.tixi, SU2_MAX_ITER_XPATH, 2)
    # nb_proc = get_value_or_default(cpacs.tixi, SU2_NB_CPU_XPATH, get_reasonable_nb_cpu())
    config_file_type = get_value(tixi, SU2_CONFIG_RANS_XPATH)

    rans = (config_file_type == "RANS")
    generate_su2_cfd_config(
        cpacs=cpacs,
        wkdir=results_dir_su2,
        su2_mesh_paths=[],
        mesh_markers=[],
        rans=rans,
        dyn_stab=False,
    )

    # Execute SU2 simulation
    run_SU2_multi(results_dir_su2)
    get_su2_results(cpacs, results_dir_su2)

    log.info("----- End of " + "SU2Run" + " -----")

    # Reload CPACS with updated results
    cpacs = CPACS(cpacs.cpacs_file)

    # Validate objective
    objective_map = {"cl": "cl", "cd": "cd", "cs": "cs", "cmd": "cmd", "cml": "cml", "cms": "cms"}
    if objective not in objective_map:
        raise ValueError(
            f"Invalid objective '{objective}'. Expected one of {list(objective_map.keys())}."
        )

    # Retrieve aerodynamic data
    dataset = retrieve_aeromap_data(cpacs, aeromap.uid, objective, objective_map)
    cpacs.save_cpacs(cpacs, overwrite=True)

    log.info(f"SU2 results extracted for {objective}:")
    log.info(dataset)

    return dataset


def new_points(
    datasets: Dict,
    model,
    results_dir,
    high_variance_points
):
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

    Returns:
        pd.DataFrame or None: A DataFrame containing the newly selected points.
                              Returns None if all high-variance points have already been chosen.
    """

    # Retrieve the first fidelity dataset
    first_dataset = datasets["level_1"]
    X, _, df, _, _ = first_dataset  # Unpack dataset

    # Compute variance prediction
    _, y_var = make_predictions(model, X)
    y_var_flat = np.asarray(y_var).flatten()
    sorted_indices = np.argsort(y_var_flat)[::-1]  # Sort indices by variance (descending)

    output_file_path = os.path.join(results_dir, "new_points.csv")
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
