"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to the training of the surrogate model.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import pickle

from ceasiompy.SMTrain.func.surrogate import (
    kriging,
    mf_kriging,
)
from numpy import ndarray
from smt.applications import MFK
from smt.surrogate_models import KRG
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

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


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
