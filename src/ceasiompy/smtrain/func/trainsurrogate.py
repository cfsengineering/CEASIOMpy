"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to the training of the surrogate model.

"""

# Imports

import time
import joblib
import numpy as np

from pandas import concat
from skopt import gp_minimize
from cpacspy.cpacsfunctions import (
    add_value,
    create_branch,
)
from ceasiompy.smtrain.func.loss import (
    compute_first_level_loss,
    compute_multi_level_loss,
)
from ceasiompy.smtrain.func.sampling import (
    split_data,
    new_points,
)
from ceasiompy.smtrain.func.createdata import (
    launch_avl,
    launch_su2,
)
from ceasiompy.smtrain.func.utils import (
    log_params,
    unpack_data,
    collect_level_data,
)

from pathlib import Path
from numpy import ndarray
from typing import Callable
from pandas import DataFrame
from cpacspy.cpacspy import CPACS
from smt.applications import MFK
from smt.surrogate_models import KRG
from scipy.optimize import OptimizeResult
from skopt.space import (
    Real,
    Categorical,
)

from ceasiompy import log
from ceasiompy.utils.commonxpaths import SM_XPATH


# Functions

def get_hyperparam_space_kriging(
    level1_sets: dict[str, ndarray],
    level2_sets: dict[str, ndarray] | None,
    level3_sets: dict[str, ndarray] | None,
) -> list[str]:
    """
    Get Hyper-parameters space from the different fidelity datasets.
    Uniquely determined by the training set x_train.
    """

    # Concatenate only non-None arrays
    arrays = [level1_sets["x_train"]]
    if level2_sets is not None:
        arrays.append(level2_sets["x_train"])
    if level3_sets is not None:
        arrays.append(level3_sets["x_train"])

    x_train = np.concatenate(arrays, axis=0)
    n_samples, n_features = x_train.shape

    # Determine allowed polynomial regression types based on sample count
    if n_samples > ((n_features + 1) * (n_features + 2) / 2):
        poly_options = ["constant", "linear", "quadratic"]
        x = (n_features + 1) * (n_features + 2) / 2
        log.info(f"Training points (n_samples): {x}<{n_samples} -> poly_options: {poly_options}")
    elif n_samples > (n_features + 2):
        poly_options = ["constant", "linear"]
        x = (n_features + 1) * (n_features + 2) / 2
        y = n_features + 2
        log.info(
            f"Training points (n_samples): {y}<{n_samples}<={x} -> poly_options: {poly_options}"
        )
    elif n_samples > 2:
        poly_options = ["constant"]
        y = n_features + 2
        log.info(f"Training points (n_samples): {n_samples}<={y} -> poly_options: {poly_options}")
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


def save_model(
    cpacs: CPACS,
    model: KRG | MFK,
    objective: str,
    results_dir: Path,
) -> None:
    """
    Save the trained surrogate model along with its metadata.

    Args:
        cpacs: CPACS file.
        model: Trained surrogate model.
        coefficient_name (str): Name of the aerodynamic coefficient (e.g., "cl" or "cd").
        results_dir (Path): Where the model will be saved.
    """
    tixi = cpacs.tixi

    model_path = results_dir / f"surrogateModel_{objective}.pkl"
    with open(model_path, "wb") as file:
        joblib.dump(
            value={
                "model": model,
                "coefficient": objective,
            },
            filename=file,
        )
    log.info(f"Model saved to {model_path}")

    create_branch(tixi, SM_XPATH)
    add_value(tixi, SM_XPATH, model_path)
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
        objective, param_space, n_calls=n_calls, random_state=random_state
    )
    total_time = time.time() - start_time
    log.info(f"Total optimization time: {total_time:.2f} seconds ({total_time / 60:.2f} minutes)")
    log.info("Best hyperparameters found:")
    log_params(result)

    return result.x


def run_adaptative_refinement(
    cpacs: CPACS,
    results_dir: Path,
    model: KRG | MFK,
    level1_sets: dict[str, ndarray],
    rmse_obj: float,
    objective: str,
) -> None:
    """
    Iterative improvement using SU2 data.
    """
    high_var_pts = []
    rmse = float("inf")
    df = DataFrame(
        {
            "altitude": [],
            "machNumber": [],
            "angleOfAttack": [],
            "angleOfSideslip": [],
            objective: [],
        }
    )
    x_array = level1_sets["x_train"]
    nb_iters = len(x_array)
    log.info(f"Starting adaptive refinement with maximum {nb_iters=}.")

    for _ in range(nb_iters):
        # Find new high variance points based on inputs x_train
        new_point_df = new_points(
            x_array=x_array,
            model=model,
            results_dir=results_dir,
            high_var_pts=high_var_pts,
        )

        # 1st Breaking condition
        if new_point_df.empty or (new_point_df is None):
            log.warning("No new high-variance points found.")
            break
        high_var_pts.append(new_point_df.values[0])

        # Get data from SU2 at the high variance points
        new_df = launch_su2(
            cpacs=cpacs,
            results_dir=results_dir,
            objective=objective,
            high_variance_points=high_var_pts,
        )

        # Stack new with old
        df = concat([new_df, df], ignore_index=True)

        model, rmse = train_surrogate_model(
            level1_sets=level1_sets,
            level2_sets=split_data(df, objective),
        )

        # 2nd Breaking condition
        if rmse > rmse_obj:
            break
