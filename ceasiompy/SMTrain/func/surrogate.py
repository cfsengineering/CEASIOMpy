"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Manage Kriging and MF_Kriging algorithms + make predictions.


Python version: >=3.8

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:

    *Improve Bayesian optimization
    *Understand better poly from SMT (sometimes gives some problems)

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger
import numpy as np
import time
from smt.surrogate_models import KRG
from smt.applications import MFK
from smt.utils.misc import compute_rms_error
from skopt import gp_minimize


log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def check_nan_inf(*arrays):
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


def Kriging(
    param_space, sets, n_calls=50, random_state=42
):  # changing the number of iteration (n_calls) speeds up the solution (low limit = 10)
    """
    Trains a Kriging model using Bayesian optimization.

    Args:
        param_space (list): List of parameter ranges for Bayesian optimization.
        sets (dict): Dictionary containing training, validation, and test datasets.
        n_calls (int, optional): Number of iterations for Bayesian optimization. Defaults to 50.
        random_state (int, optional): Random seed for reproducibility. Defaults to 42.

    Returns:
        tuple: Trained Kriging model and RMSE on the test set.
    """

    # Extract training, validation, and test sets
    X_train, X_val, X_test = sets["X_train"], sets["X_val"], sets["X_test"]
    y_train, y_val, y_test = sets["y_train"], sets["y_val"], sets["y_test"]

    # Check for NaN or infinite values in the datasets
    check_nan_inf(X_train, X_test, X_val, y_train, y_test, y_val)

    def objective(params):
        theta0, corr, poly, opt, nugget, _, lambda_penalty = params

        # Initialize and train the Kriging model
        model = KRG(theta0=[theta0], corr=corr, poly=poly, hyper_opt=opt, nugget=nugget)
        model.set_training_values(X_train, y_train)
        model.train()

        # Compute RMSE on validation set
        rmse = compute_rms_error(model, X_val, y_val)

        # Compute variance-based penalty term
        y_var = model.predict_variances(X_val)
        penalty = np.mean(y_var)  # da valutare la normalizzazione: / (np.std(y_var) + 1e-8)

        return rmse + lambda_penalty * penalty

    # Perform Bayesian optimization
    start_time = time.time()
    result = gp_minimize(objective, param_space, n_calls=n_calls, random_state=random_state)
    total_time = time.time() - start_time

    # Retrieve and log the best hyperparameters
    best_params = result.x
    log.info("Best hyperparameters found:")
    log.info(f"Theta0: {best_params[0]}")
    log.info(f"Correlation: {best_params[1]}")
    log.info(f"Polynomial: {best_params[2]}")
    log.info(f"Optimizer: {best_params[3]}")
    log.info(f"Nugget: {best_params[4]}")
    log.info(f"Penalty weight (λ): {best_params[5]}")
    log.info(f"Lowest RMSE obtained: {result.fun:.6f}")
    log.info(f"Total optimization time: {total_time:.2f} seconds ({total_time / 60:.2f} minutes)")

    # Train the final Kriging model with optimal parameters
    model = KRG(
        theta0=[best_params[0]],
        corr=best_params[1],
        poly=best_params[2],
        hyper_opt=best_params[3],
        nugget=best_params[4],
    )

    model.set_training_values(X_train, y_train)
    model.train()

    # Compute RMSE on test set
    rmse_test = compute_rms_error(model, X_test, y_test)

    log.info("===================================================================================")
    log.info("")
    log.info(f"Final RMSE on test set: {rmse_test:.6f}")
    log.info("")
    log.info("===================================================================================")

    return model, rmse_test


def MF_Kriging(
    fidelity_level,
    datasets,
    param_space,
    sets,
    n_calls=30,  # number of iterations, if it change speeds up the solution (low limit = 10)
    random_state=42,
):
    """
    Trains a multi-fidelity Kriging model with 2 or 3 fidelity levels.

    Args:
        fidelity_level (str): Fidelity level ('Two levels' or 'Three levels').
        datasets (dict): Dictionary containing datasets for different fidelity levels.
        param_space (list): List of parameter ranges for Bayesian optimization.
        sets (dict): Dictionary containing training, validation, and test datasets.
        n_calls (int, optional): Number of iterations for Bayesian optimization. Defaults to 35.
        random_state (int, optional): Random seed for reproducibility. Defaults to 42.

    Returns:
        tuple: Trained multi-fidelity Kriging model and RMSE on the test set.
    """

    if fidelity_level != "Two levels" and fidelity_level != "Three levels":
        raise ValueError("fidelity_level must be 2 or 3.")

    # Extract training, validation, and test sets
    X_train, X_val, X_test = sets["X_train"], sets["X_val"], sets["X_test"]
    y_train, y_val, y_test = sets["y_train"], sets["y_val"], sets["y_test"]

    # Extract datasets for different fidelity levels
    X_lf, y_lf, _, _, _ = datasets["level_1"]
    X_mf, y_mf = datasets["level_2"][:2] if fidelity_level == "Three levels" else (None, None)

    # Define the objective function for Bayesian optimization
    def objective(params):
        # try:
        theta0, corr, poly, opt, nugget, rho_regr, lambda_penalty = params

        # Initialize and train the multi-fidelity Kriging model
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
        model.set_training_values(X_train, y_train)
        model.train()

        # Compute RMSE on validation set
        rmse = compute_rms_error(model, X_val, y_val)

        # Compute variance-based penalty term
        y_var = model.predict_variances(X_val)
        penalty = np.mean(y_var)

        return rmse + lambda_penalty * penalty

        # except Exception as e:
        #     log.error("Error in objective function:", e)
        #     return np.inf  # Restituisce un valore molto alto per evitare blocchi

    # Perform Bayesian optimization
    start_time = time.time()
    result = gp_minimize(objective, param_space, n_calls=n_calls, random_state=random_state)
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

    # Train the multi-fidelity Kriging model with optimal parameters
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
    model.set_training_values(X_train, y_train)
    model.train()

    # Compute RMSE on test set
    rmse_test = compute_rms_error(model, X_test, y_test)

    log.info("===================================================================================")
    log.info("")
    log.info(f"Final RMSE on test set: {rmse_test:.6f}")
    log.info("")
    log.info("===================================================================================")

    return model, rmse_test


def make_predictions(model, X, y=None):
    """
    Makes predictions using the trained Kriging model.

    Args:
        model (object): Trained Kriging model.
        X (np.ndarray): Input data for prediction.
        y (np.ndarray, optional): True values for RMSE computation. Defaults to None.

    Returns:
        tuple: Predicted values and variance.
    """

    y_pred = model.predict_values(X)
    var = model.predict_variances(X)

    if y is not None:
        log.info("Kriging, rms err: " + str(compute_rms_error(model, X, y)))

    # Theta values
    print("theta values", model.optimal_theta)

    return y_pred, var


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
