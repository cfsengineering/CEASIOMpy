"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to the training of the surrogate model.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import glob
import time
import joblib
import numpy as np
import pandas as pd

from skopt import gp_minimize
from cpacspy.cpacsfunctions import (
    add_value,
    create_branch,
)
from ceasiompy.SMTrain.func.loss import (
    compute_first_level_loss,
    compute_multi_level_loss,
)
from ceasiompy.SMTrain.func.utils import (
    log_params,
    unpack_data,
    generate_su2_wkdir,
)
from ceasiompy.SMTrain.func.sampling import (
    split_data,
    new_points,
)
from ceasiompy.SMTrain.func.createdata import (
    launch_avl,
    launch_su2,
)

from pathlib import Path
from numpy import ndarray
from cpacspy.cpacspy import CPACS
from smt.applications import MFK
from smt.surrogate_models import KRG
from scipy.optimize import OptimizeResult
from pandas import DataFrame
from skopt.space import (
    Real,
    Categorical,
)
from typing import (
    List,
    Dict,
    Tuple,
    Union,
    Callable,
)

from ceasiompy import log
from ceasiompy.utils.commonxpaths import SM_XPATH
from ceasiompy.SMTrain import (
    LEVEL_ONE,
    LEVEL_TWO,
)

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
    fidelity_level: str,
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
        fidelity_level (str): Either LEVEL_ONE or LEVEL_TWO.
        datasets (Dict): Contains datasets for different fidelity levels.
        sets (Dict):
            Contains the split datasets. Expected keys:
            "x_train", "x_val", "x_test", "y_train", "y_val", "y_test".

    Returns:
        model: Trained surrogate model (kriging or Multi-Fidelity kriging).
        rmse (float): Root Mean Square Error of the trained model.
    """

    hyperparam_space = get_hyperparam_space(sets)

    if fidelity_level == LEVEL_ONE:
        return kriging(
            param_space=hyperparam_space,
            sets=sets
        )
    else:
        # It will always be multi-fidelity level if not 1
        return mf_kriging(
            fidelity_level=fidelity_level,
            datasets=datasets,
            param_space=hyperparam_space,
            sets=sets,
        )


def save_model(
    cpacs: CPACS,
    model: Union[KRG, MFK],
    coefficient_name: str,
    datasets: Dict,
    results_dir: Path,
) -> None:
    """
    Save the trained surrogate model along with its metadata.

    Args:
        model: Trained surrogate model.
        coefficient_name (str): Name of the aerodynamic coefficient (e.g., "cl" or "cd").
        datasets (Dict): Contains different fidelity datasets.
        results_dir (Path): Where the model will be saved.
    """
    tixi = cpacs.tixi

    if not datasets:
        log.warning("Datasets dictionary is empty.")
        raise ValueError("Datasets dictionary is empty. Cannot save the model.")

    # Find the dataset with the highest fidelity level (last in the dictionary)
    # Ensure fidelity levels are correctly extracted
    # try:
    #     highest_fidelity_level = max(datasets.keys(), key=lambda k: int(k.split("_")[-1]))
    # except (ValueError, IndexError):
    #     raise ValueError(
    #         "Invalid fidelity level format in dataset keys. Expected format: 'fidelity_X'."
    #     )

    model_metadata = {
        "model": model,
        "coefficient": coefficient_name,
        # "removed_columns": list(datasets[highest_fidelity_level][3].keys()),
    }

    model_path = results_dir / f"surrogateModel_{coefficient_name}.pkl"
    with open(model_path, "wb") as file:
        joblib.dump(model_metadata, file)
    log.info(f"Model saved to {model_path}")

    # Find the surrogate model file
    surrofate_files = str(results_dir / "surrogateModel_*.pkl")
    surrogate_model_files = glob.glob(surrofate_files)
    surrogate_model_path = (
        surrogate_model_files[0]
        if surrogate_model_files
        else None
    )

    if not surrogate_model_path:
        log.info("No surrogateModel_*.pkl file found.")
        return None

    # TODO: Understand why need to reload
    # Reload CPACS file
    cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)
    cpacs = CPACS(cpacs.cpacs_file)
    tixi = cpacs.tixi

    create_branch(tixi, SM_XPATH)
    add_value(tixi, SM_XPATH, surrogate_model_path)
    log.info("Finished Saving model.")


def optimize_hyper_parameters(
    objective: Callable,
    param_space,
    n_calls: int,
    random_state: int,
) -> ndarray:
    """
    Using Bayesian Optimization.
    """

    # Perform Bayesian optimization
    start_time = time.time()
    result: OptimizeResult = gp_minimize(
        objective,
        param_space,
        n_calls=n_calls,
        random_state=random_state
    )
    total_time = time.time() - start_time
    log.info(f"Total optimization time: {total_time:.2f} seconds ({total_time / 60:.2f} minutes)")
    log.info("Best hyperparameters found:")
    log_params(result)

    return result.x


def kriging(
    param_space: List,
    sets: Dict[str, ndarray],
    n_calls: int = 50,
    random_state: int = 42,
) -> Tuple[KRG, float]:
    """
    Trains a kriging model using Bayesian optimization.

    Args:
        param_space (list): Hyper-parameters for Bayesian optimization.
        sets (dict): Dictionary containing training, validation, and test datasets.
        n_calls (int = 50):
            Number of iterations for Bayesian optimization.
            The lower the faster.
        random_state (int = 42): Random seed for reproducibility.

    Returns:
        tuple: Trained kriging model and RMSE on the test set.
    """
    x_train, x_test, x_val, y_train, y_test, y_val = unpack_data(sets)

    def objective(params) -> float:
        """
        Needs to have params as an argument (gp_minimize restriction).
        """
        _, loss = compute_first_level_loss(
            params,
            x_train=x_train,
            y_train=y_train,
            x_=x_val,
            y_=y_val,
        )

        return loss

    best_params = optimize_hyper_parameters(objective, param_space, n_calls, random_state)
    log.info("Evaluating on optimized hyper-parameters")
    best_model, best_loss = compute_first_level_loss(
        best_params,
        x_train=x_train,
        y_train=y_train,
        x_=x_test,
        y_=y_test,
    )
    log.info(f"Final RMSE on test set: {best_loss:.6f}")

    return best_model, best_loss


def mf_kriging(
    fidelity_level: str,
    datasets: Dict,
    param_space: List,
    sets: Dict,
    n_calls: int = 30,
    random_state: int = 42,
) -> Tuple[MFK, float]:
    """
    Trains a multi-fidelity kriging model with 2 or 3 fidelity levels.

    Args:
        fidelity_level (str): Either 'Two levels' or 'Three levels'.
        datasets (dict): Contains datasets for different fidelity levels.
        param_space (list): List of parameter ranges for Bayesian optimization.
        sets (dict): Training, validation, and test datasets.
        n_calls (int = 30): Number of iterations for Bayesian optimization.
        random_state (int = 42): Random seed for reproducibility.
    """
    x_train, x_test, x_val, y_train, y_test, y_val = unpack_data(sets)

    # Extract datasets for different fidelity levels
    x_lf, y_lf = datasets[LEVEL_ONE][:2]
    x_train, y_train = np.vstack([x_train, x_lf]), np.vstack([y_train, y_lf])

    # Add the LEVEL_TWO fidelity data if we are on a 3d level
    if fidelity_level == "Three levels":
        x_mf, y_mf = datasets[LEVEL_TWO][:2]

    def objective(params) -> float:
        _, loss = compute_multi_level_loss(
            params,
            x_fl_train=x_train,
            y_fl_train=y_train,
            x_ml_train=x_mf,
            y_ml_train=y_mf,
            x_=x_val,
            y_=y_val,
        )

        return loss

    best_params = optimize_hyper_parameters(objective, param_space, n_calls, random_state)
    best_model, best_loss = compute_multi_level_loss(
        best_params,
        x_fl_train=x_train,
        y_fl_train=y_train,
        x_ml_train=x_mf,
        y_ml_train=y_lf,
        x_=x_test,
        y_=y_test,
    )
    log.info(f"Final RMSE on test set: {best_loss:.6f}")

    return best_model, best_loss


def run_first_level_training(
    cpacs: CPACS,
    lh_sampling_path: Union[Path, None],
    obj_coef: str,
    split_ratio: float,
) -> Tuple[Union[KRG, MFK], Dict[str, ndarray], Dict[str, DataFrame]]:
    """
    Run surrogate model training on first level of fidelity (AVL).
    """
    level1_dataset = launch_avl(cpacs, lh_sampling_path, obj_coef)
    datasets = {LEVEL_ONE: level1_dataset}
    sets = split_data(LEVEL_ONE, datasets, split_ratio)
    model, _ = train_surrogate_model(LEVEL_ONE, datasets, sets)
    return model, sets, datasets


def run_adaptative_refinement(
    cpacs: CPACS,
    results_dir: Path,
    model: Union[KRG, MFK],
    datasets: Dict[str, DataFrame],
    rmse_obj: float,
    obj_coef: str,
) -> None:
    """
    Iterative improvement using SU2 data.
    """
    high_var_pts = []
    avl_dataset = datasets[LEVEL_ONE]
    max_iters = len(avl_dataset[0])
    iteration = 0
    rmse = float("inf")
    log.info(f"Starting adaptive refinement with {max_iters=}.")

    while (
        iteration < max_iters
        and rmse > rmse_obj
    ):
        # 1. Find new high variance points
        new_point_df = new_points(datasets, model, results_dir, high_var_pts)
        if new_point_df.empty or (new_point_df is None):
            log.warning("No new high-variance points found.")
            break
        high_var_pts.append(new_point_df.values[0])

        dataset = launch_su2(
            cpacs=cpacs,
            results_dir=results_dir,
            results_dir_su2=generate_su2_wkdir(iteration),
            objective=obj_coef,
            high_variance_points=high_var_pts,
        )

        if LEVEL_TWO in datasets:
            # Stack new with old
            x_old, y_old, df_old, removed_old, df_cl_old = datasets[LEVEL_TWO]
            x_new, y_new, df_new, _ , df_cl_new = dataset

            datasets[LEVEL_TWO] = (
                np.vstack([x_old, x_new]),
                np.vstack([y_old, y_new]),
                pd.concat([df_old, df_new], ignore_index=True),
                removed_old,  # Kept original from iteration 0
                pd.concat([df_cl_old, df_cl_new], ignore_index=True),
            )

        else:
            datasets[LEVEL_TWO] = dataset

        sets = split_data(LEVEL_TWO, datasets, 0.7, 0.5)  # TODO: Not specified from GUI ???
        model, rmse = train_surrogate_model(LEVEL_TWO, datasets, sets)
        iteration += 1
