"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Manage kriging and mf_kriging algorithms + make predictions.

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:
    *Improve Bayesian optimization
    *Understand better poly from SMT (sometimes gives some problems)
"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import time
import numpy as np

from numpy import ndarray
from smt.applications import MFK
from smt.surrogate_models import KRG
from scipy.optimize import OptimizeResult
from typing import (
    List,
    Dict,
    Tuple,
    Union,
    Literal,
    Callable,
)

from skopt import gp_minimize
from smt.utils.misc import compute_rmse

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def check_nan_inf(*arrays) -> None:
    """
    Checks for NaN or infinite values in the given arrays.

    Args:
        *arrays: Variable number of numpy arrays to check.
    """
    for i, arr in enumerate(arrays):
        if np.isnan(arr).any():
            raise ValueError(f"Array {i} contains NaN values.")
        if np.isinf(arr).any():
            raise ValueError(f"Array {i} contains infinite values.")


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
    sets: Dict,
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

    # Extract training, validation, and test sets
    x_train, x_val, x_test = sets["x_train"], sets["x_val"], sets["x_test"]
    y_train, y_val, y_test = sets["y_train"], sets["y_val"], sets["y_test"]

    # Check for NaN or infinite values in the datasets
    check_nan_inf(x_train, x_test, x_val, y_train, y_test, y_val)

    def objective(params) -> float:
        """
        Needs to have params as an argument (gp_minimize restriction).
        """
        theta0, corr, poly, opt, nugget, _, lambda_penalty = params

        # Initialize and train the kriging model
        model = KRG(theta0=[theta0], corr=corr, poly=poly, hyper_opt=opt, nugget=nugget)
        model.set_training_values(x_train, y_train)
        model.train()
        loss = (
            compute_rmse(model, x_val, y_val)
            + lambda_penalty * np.mean(model.predict_variances(x_val))
        )

        return loss

    best_params = optimize_hyper_parameters(objective, param_space, n_calls, random_state)

    # Assess kriging model on the optimal parameters
    model = KRG(
        theta0=[best_params[0]],
        corr=best_params[1],
        poly=best_params[2],
        hyper_opt=best_params[3],
        nugget=best_params[4],
    )

    model.set_training_values(x_train, y_train)
    model.train()

    rmse_test = compute_rmse(model, x_test, y_test)
    log.info(f"Final RMSE on test set: {rmse_test:.6f}")

    return model, rmse_test


def mf_kriging(
    fidelity_level: Literal["Two levels", "Three levels"],
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

    # Extract training, validation, and test sets
    x_train, x_val, x_test = sets["x_train"], sets["x_val"], sets["x_test"]
    y_train, y_val, y_test = sets["y_train"], sets["y_val"], sets["y_test"]
    check_nan_inf(x_train, x_val, x_test, y_train, y_val, y_test)

    # Extract datasets for different fidelity levels
    X_lf, y_lf, _, _, _ = datasets["level_1"]
    X_mf, y_mf = datasets["level_2"][:2] if fidelity_level == "Three levels" else (None, None)

    def objective(params) -> float:
        theta0, corr, poly, opt, nugget, rho_regr, lambda_penalty = params

        model = MFK(
            theta0=[theta0],
            corr=corr,
            poly=poly,
            hyper_opt=opt,
            nugget=nugget,
            rho_regr=rho_regr,
        )
        model.set_training_values(X_lf, y_lf, name=0)
        if fidelity_level == "Three levels":
            model.set_training_values(X_mf, y_mf, name=1)
        model.set_training_values(x_train, y_train)
        model.train()

        loss = (
            compute_rmse(model, x_val, y_val)
            + lambda_penalty * np.mean(model.predict_variances(x_val))
        )
        return loss

    best_params = optimize_hyper_parameters(objective, param_space, n_calls, random_state)

    # Assess multi-fidelity kriging model on the optimal parameters
    model = MFK(
        theta0=[best_params[0]],
        corr=best_params[1],
        poly=best_params[2],
        hyper_opt=best_params[3],
        nugget=best_params[4],
        rho_regr=best_params[5],
    )
    model.set_training_values(X_lf, y_lf, name=0)
    if fidelity_level == "Three levels":
        model.set_training_values(X_mf, y_mf, name=1)

    model.set_training_values(x_train, y_train)
    model.train()

    rmse_test = compute_rmse(model, x_test, y_test)
    log.info(f"Final RMSE on test set: {rmse_test:.6f}")

    return model, rmse_test


def make_predictions(
    model: Union[KRG, MFK],
    x: ndarray,
    y: Union[ndarray, None] = None,
) -> Tuple[ndarray, ndarray]:
    """
    Makes predictions using the trained kriging model.

    Args:
        model (object): Trained kriging model.
        X (ndarray): Input data for prediction.
        y (ndarray = None): True values for RMSE computation.

    Returns:
        Predicted values and variance.
    """

    y_pred = model.predict_values(x)
    var = model.predict_variances(x)

    if y is not None:
        log.info(f"kriging, rms err: {compute_rmse(model, x, y)}")

    log.info(f"Theta values: {model.optimal_theta}")

    return y_pred, var


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
