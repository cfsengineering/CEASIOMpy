"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to the training of the surrogate model.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================


import time
import joblib
import numpy as np
import pandas as pd

from skopt import gp_minimize
from smt.utils.misc import compute_rmse
from ceasiompy.SMTrain.func.utils import unpack_data
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
from ceasiompy.SMTrain import (
    LEVEL_ONE,
    LEVEL_TWO,
)
from ceasiompy.SU2Run import MODULE_NAME as SU2RUN_NAME

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
    # elif fidelity_level == LEVEL_TWO:
    else:
        return mf_kriging(
            fidelity_level=fidelity_level,
            datasets=datasets,
            param_space=hyperparam_space,
            sets=sets,
        )


def save_model(
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

    model_metadata = {
        "model": model,
        "coefficient": coefficient_name,
        "removed_columns": list(datasets[highest_fidelity_level][3].keys()),
    }

    model_path = results_dir / f"surrogateModel_{coefficient_name}.pkl"
    with open(model_path, "wb") as file:
        joblib.dump(model_metadata, file)
    log.info(f"Model saved to {model_path}")


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

    # Retrieve and log the best hyperparameters
    best_params = result.x
    log.info("Best hyperparameters found:")
    log.info(f"Theta0: {best_params[0]}")
    log.info(f"Correlation: {best_params[1]}")
    log.info(f"Polynomial: {best_params[2]}")
    log.info(f"Optimizer: {best_params[3]}")
    log.info(f"Nugget: {best_params[4]}")
    log.info(f"Rho regressor: {best_params[5]}")
    log.info(f"Penalty weight (λ): {best_params[6]}")
    log.info(f"Lowest RMSE obtained: {result.fun:.6f}")
    log.info(f"Total optimization time: {total_time:.2f} seconds ({total_time / 60:.2f} minutes)")
    return best_params


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
        _, loss = compute_loss(
            params,
            model_type="KRG",
            x_train=x_train,
            y_train=y_train,
            x_=x_val,
            y_=y_val,
        )

        return loss

    # Then evaluate on the optimized hyper parameters
    best_params = optimize_hyper_parameters(objective, param_space, n_calls, random_state)
    best_model, best_loss = compute_loss(
        best_params,
        model_type="KRG",
        x_train=x_train,
        y_train=y_train,
        x_=x_test,
        y_=y_test,
    )
    log.info(f"Final RMSE on test set: {best_loss:.6f}")

    return best_model, best_loss


def compute_loss(
    params: Tuple,
    model_type: str,
    x_train: ndarray,
    y_train: ndarray,
    x_: ndarray,
    y_: ndarray,
) -> Tuple[Union[KRG, MFK], float]:
    """
    Returns model and the loss for this model on the x_, y_ set.
    """
    if model_type == "KRG":
        model = KRG(
            theta0=[params[0]],
            corr=params[1],
            poly=params[2],
            hyper_opt=params[3],
            nugget=params[4],
        )
    else:
        model = MFK(
            theta0=[params[0]],
            corr=params[1],
            poly=params[2],
            hyper_opt=params[3],
            nugget=params[4],
            rho_regr=params[5],
        )
    model.set_training_values(x_train, y_train)
    model.train()
    rmse = (
        compute_rmse(model, x_, y_) + params[6] * np.mean(model.predict_variances(x_))
    )
    return model, rmse


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
        x_train, y_train = np.vstack([x_train, x_mf]), np.vstack([y_train, y_mf])

    def objective(params) -> float:
        _, loss = compute_loss(
            params,
            model_type="MFK",
            x_train=x_train,
            y_train=y_train,
            x_=x_val,
            y_=y_val,
        )

        return loss

    best_params = optimize_hyper_parameters(objective, param_space, n_calls, random_state)
    best_model, best_loss = compute_loss(
        best_params,
        model_type="MFK",
        x_train=x_train,
        y_train=y_train,
        x_=x_val,
        y_=y_val,
    )
    log.info(f"Final RMSE on test set: {best_loss:.6f}")

    return best_model, best_loss


def run_first_level_training(
    cpacs: CPACS,
    results_dir: Path,
    avl: bool,
    lh_sampling_path: Path,
    obj_coef: str,
    split_ratio: float,
) -> Tuple[Union[KRG, MFK], Dict[str, ndarray], Dict[str, DataFrame]]:
    """
    Run surrogate model training on first level.
    """
    if avl:
        level1_dataset = launch_avl(cpacs, lh_sampling_path, obj_coef)
    else:
        level1_dataset = launch_su2(cpacs, results_dir, SU2RUN_NAME, obj_coef)
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
        if new_point_df.empty:
            log.warning("No new high-variance points found.")
            break
        new_point = new_point_df.values[0]
        high_var_pts.append(new_point)

        # Generate unique SU2 working directory using iteration
        wkdir_su2 = Path(SU2RUN_NAME) / f"SU2_{iteration}"
        wkdir_su2.mkdir(parents=True, exist_ok=True)
        su2_dataset = launch_su2(
            cpacs=cpacs,
            results_dir=results_dir,
            results_dir_su2=wkdir_su2,
            objective=obj_coef,
            high_variance_points=high_var_pts,
        )

        if LEVEL_TWO in datasets:
            # Stack new with old
            x_old, y_old, df_old, removed_old, df_cl_old = datasets[LEVEL_TWO]
            x_new, y_new, df_new, _ , df_cl_new = su2_dataset

            datasets[LEVEL_TWO] = (
                np.vstack([x_old, x_new]),
                np.vstack([y_old, y_new]),
                pd.concat([df_old, df_new], ignore_index=True),
                removed_old,  # Kept original from iteration 0
                pd.concat([df_cl_old, df_cl_new], ignore_index=True),
            )

        else:
            datasets[LEVEL_TWO] = su2_dataset

        sets = split_data(LEVEL_TWO, datasets, 0.7, 0.5)  # TODO: Not specified from GUI ???
        model, rmse = train_surrogate_model(LEVEL_TWO, datasets, sets)
        iteration += 1
