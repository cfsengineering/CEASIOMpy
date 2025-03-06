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
from skopt.space import Real, Categorical


log = get_logger()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def check_nan_inf(*arrays):
    for i, arr in enumerate(arrays):
        if np.isnan(arr).any():
            print(f"Array {i} contiene NaN")
        if np.isinf(arr).any():
            print(f"Array {i} contiene Inf")


def Kriging(
    param_space, X_train, X_test, X_val, y_train, y_test, y_val, n_calls=50, random_state=42
):
    """Train Kriging model using Bayesian optimization."""

    check_nan_inf(X_train, X_test, X_val, y_train, y_test, y_val)

    def objective(params):
        theta0, corr, poly, opt, nugget, rho_regr, lambda_penalty = params

        model = KRG(theta0=[theta0], corr=corr, poly=poly, hyper_opt=opt, nugget=nugget)
        model.set_training_values(X_train, y_train)
        model.train()

        rmse = compute_rms_error(model, X_val, y_val)
        y_var = model.predict_variances(X_val)
        penalty = np.mean(y_var)  # da valutare la normalizzazione: / (np.std(y_var) + 1e-8)

        return rmse + lambda_penalty * penalty

    start_time = time.time()
    result = gp_minimize(objective, param_space, n_calls=n_calls, random_state=random_state)
    total_time = time.time() - start_time

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

    model = KRG(
        theta0=[best_params[0]],
        corr=best_params[1],
        poly=best_params[2],
        hyper_opt=best_params[3],
        nugget=best_params[4],
    )
    model.set_training_values(X_train, y_train)
    model.train()

    rmse_test = compute_rms_error(model, X_test, y_test)
    log.info(f"Final RMSE on test set: {rmse_test:.6f}")

    return model


def MF_Kriging(
    fidelity_level,
    datasets,
    param_space,
    X_train,
    X_test,
    X_val,
    y_train,
    y_test,
    y_val,
    n_calls=30,
    random_state=42,
):
    """Train a multi-fidelity Kriging model with 2 or 3 fidelity levels."""

    X_lf, y_lf, _ = datasets["first_dataset_path"]
    if fidelity_level == 3:
        X_mf, y_mf, _ = datasets["second_dataset_path"]

    def objective(params):
        theta0, corr, poly, opt, nugget, rho_regr, lambda_penalty = params

        model = MFK(
            theta0=[theta0], corr=corr, poly=poly, hyper_opt=opt, nugget=nugget, rho_regr=rho_regr
        )
        model.set_training_values(X_lf, y_lf, name=0)
        if fidelity_level == 3:
            model.set_training_values(X_mf, y_mf, name=1)
        model.set_training_values(X_train, y_train)
        model.train()

        rmse = compute_rms_error(model, X_val, y_val)
        y_var = model.predict_variances(X_val)
        penalty = np.mean(y_var)  # da valutare la normalizzazione: / (np.std(y_var) + 1e-8)

        return rmse + lambda_penalty * penalty

    start_time = time.time()
    result = gp_minimize(objective, param_space, n_calls=n_calls, random_state=random_state)
    total_time = time.time() - start_time

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

    model = MFK(
        theta0=[best_params[0]],
        corr=best_params[1],
        poly=best_params[2],
        hyper_opt=best_params[3],
        nugget=best_params[4],
        rho_regr=best_params[5],
    )
    model.set_training_values(X_lf, y_lf, name=0)
    if fidelity_level == 3:
        model.set_training_values(X_mf, y_mf, name=1)
    model.set_training_values(X_train, y_train)
    model.train()

    rmse_test = compute_rms_error(model, X_test, y_test)
    log.info(f"Final RMSE on test set: {rmse_test:.6f}")

    return model


def make_predictions(model, X, y=None):
    """Make predictions"""

    y_pred = model.predict_values(X)
    var = model.predict_variances(X)

    if y is not None:
        log.info("Kriging, rms err: " + str(compute_rms_error(model, X, y)))

    # Valori di theta
    print("theta values", model.optimal_theta)

    return y_pred, var


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
