"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Sampling strategies for SMTrain.
"""

# Imports

import numpy as np
import pandas as pd

from copy import deepcopy
from sklearn.model_selection import train_test_split
from ceasiompy.smtrain.func.utils import get_val_fraction

from pathlib import Path
from numpy import ndarray
from typing import Protocol
from pandas import DataFrame
from smt.applications import MFK
from smt.sampling_methods import LHS
from smt.surrogate_models import KRG

from ceasiompy import log
from ceasiompy.smtrain import AEROMAP_FEATURES
from ceasiompy.smtrain.func import (
    AEROMAP_SELECTED_CSV,
    LH_SAMPLING_DATA_GEOMETRY_CSV,
)


class VariancePredictor(Protocol):
    """Protocol describing the variance prediction capability required by new_points."""

    def predict_variances(self, x_array: ndarray) -> ndarray:
        ...

# Functions


def lh_sampling(
    n_samples: int,
    ranges: dict,
    results_dir: Path,
    random_state: int = 42,
) -> Path | None:
    """
    Generate a Latin Hypercube Sampling (LHS) dataset within specified variable ranges.
    Uses the Enhanced Stochastic Evolutionary (ESE) criterion
    to generate a diverse set of samples within given variable limits.

    Args:
        n_samples (int): Number of samples to generate.
        ranges (dict):
            dictionary specifying the variable ranges in the format:
            { "variable_name": (min_value, max_value) }.
        results_dir (Path): Where the sampled dataset will be saved.
        random_state (int = 42): Seed for random number generation to ensure reproducibility.
    """
    if n_samples < 2:
        log.info(
            "Can not apply LHS on strictly less than 2 samples. "
            "Will use data from ceasiompy.db."
        )
        return None

    xlimits = np.array(list(ranges.values()))

    sampling = LHS(xlimits=xlimits, criterion="ese", random_state=random_state)
    samples = sampling(n_samples)

    # Maintain constant variables with fixed ranges
    fixed_cols = [idx for idx, (low, high) in enumerate(xlimits) if low == high]
    for idx in fixed_cols:
        samples[:, idx] = xlimits[idx, 0]

    sampled_dict = {key: samples[:, idx] for idx, key in enumerate(ranges.keys())}

    # Post-process sampled data to apply precision constraints
    for key in sampled_dict:
        if key == "range_of_altitude":
            sampled_dict[key] = np.round(sampled_dict[key]).astype(int)  # Convert to int
        elif key in ["range_of_mach", "range_of_aoa", "range_of_aos"]:
            sampled_dict[key] = np.round(sampled_dict[key] / 0.01) * 0.01  # Round to nearest 0.01

    # Save sampled dataset
    sampled_df = DataFrame(sampled_dict)
    output_file_path = results_dir / AEROMAP_SELECTED_CSV
    sampled_df.to_csv(output_file_path, index=False)
    log.info(f"LHS dataset saved in {output_file_path}")

    return output_file_path


def lh_sampling_geom(
    n_samples: int,
    ranges: dict[str, tuple[float, float]],
    random_state: int = 42,
) -> DataFrame:
    """
    Generate a Latin Hypercube Sampling (LHS) dataset within specified variable ranges.
    Uses the Enhanced Stochastic Evolutionary (ESE) criterion
    to generate a diverse set of samples within given variable limits.

    Args:
        n_samples (int): Number of samples to generate.
        ranges (dict):
            dictionary specifying the variable ranges in the format:
            { "variable_name": (min_value, max_value) }.
        random_state (int = 42): Seed for random number generation to ensure reproducibility.
    """
    xlimits = np.array(list(ranges.values()))

    sampling = LHS(xlimits=xlimits, criterion="ese", random_state=random_state)
    samples = sampling(n_samples)

    # Maintain constant variables with fixed ranges
    fixed_cols = [idx for idx, (low, high) in enumerate(xlimits) if low == high]
    for idx in fixed_cols:
        samples[:, idx] = xlimits[idx, 0]

    sampled_dict = {key: samples[:, idx] for idx, key in enumerate(ranges.keys())}

    # Save sampled dataset
    # output_file_path = results_dir / LH_SAMPLING_DATA_GEOMETRY_CSV
    # sampled_df.to_csv(output_file_path, index=False)
    # log.info(f"LHS dataset saved in {output_file_path}")

    return DataFrame(sampled_dict)


def new_points(
    x_array: ndarray,
    model: VariancePredictor,
    results_dir: Path,
    high_var_pts: list,
) -> DataFrame | None:
    """
    Selects new sampling points based on variance predictions from a surrogate model.

    This function identifies high-variance points from the `level_1` dataset for adaptive sampling.
    In the first iteration, it selects the top 6 points with the highest variance. In subsequent
    iterations, it picks the next highest variance point not previously selected.

    Args:
        datasets (dict): Contains different fidelity datasets (expects 'level_1').
        model (object): Surrogate model used to predict variance.
        result_dir (Path): Directory where the selected points CSV file will be saved.
        high_variance_points (list): list of previously selected high-variance points.

    Returns:
        DataFrame containing the newly selected points.
        Or None if all high-variance points have already been chosen.
    """

    # Compute variance prediction
    y_var_flat = np.asarray(model.predict_variances(x_array)).flatten()
    sorted_indices = np.argsort(y_var_flat)[::-1]  # Sort indices by variance (descending)

    # First iteration: generate boundary points
    output_file_path = results_dir / "new_points.csv"
    if not high_var_pts:
        log.info("First iteration: selecting the first 7 highest variance points.")
        selected_points = [tuple(x_array[idx]) for idx in sorted_indices[:7]]
        high_var_pts.extend(selected_points)
        sampled_df = DataFrame(selected_points, columns=AEROMAP_FEATURES)
        sampled_df.to_csv(output_file_path, index=False)
        return sampled_df

    log.info("Selecting next highest variance point.")

    # Convert list of points to a set for fast lookup
    high_variance_set = set(tuple(p) for p in high_var_pts)

    for idx in sorted_indices:
        new_point = tuple(x_array[idx])
        if new_point not in high_variance_set:
            high_var_pts.append(new_point)
            sampled_df = DataFrame([new_point], columns=AEROMAP_FEATURES)
            sampled_df.to_csv(output_file_path, index=False)
            return sampled_df

    log.warning("No new points found, all have been selected.")
    return None


def new_points_geom(
    x_array: ndarray,
    model: KRG | MFK,
    results_dir: Path,
    high_var_pts: list,
    ranges_gui: DataFrame,
) -> DataFrame | None:
    """
    Selects new sampling points based on variance predictions from a surrogate model.

    This function identifies high-variance points from the `level_1` dataset for adaptive sampling.
    In the first iteration, it selects the top 6 points with the highest variance. In subsequent
    iterations, it picks the next highest variance point not previously selected.

    Args:
        datasets (dict): Contains different fidelity datasets (expects 'level_1').
        model (object): Surrogate model used to predict variance.
        result_dir (Path): Directory where the selected points CSV file will be saved.
        high_variance_points (list): list of previously selected high-variance points.

    Returns:
        DataFrame containing the newly selected points.
        Or None if all high-variance points have already been chosen.
    """

    # Compute variance prediction
    y_var_flat = np.asarray(model.predict_variances(x_array)).flatten()
    sorted_indices = np.argsort(y_var_flat)[::-1]  # Sort indices by variance (descending)
    parameters_selected = list(ranges_gui.keys())
    # First iteration: generate boundary points
    output_file_path = results_dir / "new_points.csv"
    if not high_var_pts:
        log.info("First iteration: selecting the first 7 highest variance points.")
        selected_points = [tuple(x_array[idx]) for idx in sorted_indices[:7]]
        high_var_pts.extend(selected_points)
        sampled_df = DataFrame(selected_points, columns=parameters_selected)
        sampled_df.to_csv(output_file_path, index=False)
        return sampled_df

    log.info("Selecting next highest variance point.")

    # Convert list of points to a set for fast lookup
    high_variance_set = set(tuple(p) for p in high_var_pts)

    for idx in sorted_indices:
        new_point = tuple(x_array[idx])
        if new_point not in high_variance_set:
            high_var_pts.append(new_point)
            sampled_df = DataFrame([new_point], columns=parameters_selected)
            sampled_df.to_csv(output_file_path, index=False)
            return sampled_df

    log.warning("No new points found, all have been selected.")
    return None


def new_points_RBF(
    x_array: ndarray,
    y_array: ndarray,
    model: KRG | MFK,
    ranges_gui: DataFrame,
    n_local: int = 3,
    perturb_scale: float = 0.05,
    poor_pts: list = None
) -> DataFrame | None:
    """
    Generate new sampling points based on LOO error for RBF models.
    Returns a DataFrame with the same columns as ranges_gui.
    """

    X = np.asarray(x_array)
    y = np.asarray(y_array).ravel()
    n_samples, n_dim = X.shape

    parameters_selected = ranges_gui['Parameter'].tolist()

    if poor_pts is None:
        poor_pts = []

    if X.shape[0] < 3:
        log.warning("Not enough samples for LOO.")
        return None

    # --------------------------------------------------
    # STEP 1 — Compute LOO error
    # --------------------------------------------------
    loo_error = np.zeros(n_samples)
    for i in range(n_samples):
        X_loo = np.delete(X, i, axis=0)
        y_loo = np.delete(y, i, axis=0)
        try:
            model_loo = deepcopy(model)
            model_loo.set_training_values(X_loo, y_loo)
            model_loo.train()
            y_pred_i = model_loo.predict_values(X[i].reshape(1, -1)).ravel()[0]
            loo_error[i] = abs(y_pred_i - y[i])
        except Exception as e:
            log.warning(f"LOO failed at idx {i}: {e}")
            loo_error[i] = np.nan

    if np.all(np.isnan(loo_error)):
        log.error("All LOO evaluations failed.")
        return None

    # --------------------------------------------------
    # STEP 2 — Select worst points
    # --------------------------------------------------
    n_bad = 6
    bad_idx = np.argsort(loo_error)[-n_bad:]
    X_bad = X[bad_idx]

    # --------------------------------------------------
    # STEP 3 — Local perturbations
    # --------------------------------------------------
    X_new_list = []
    for x in X_bad:
        for _ in range(n_local):
            delta = perturb_scale * (np.random.rand(n_dim) - 0.5)
            x_new = x + delta
            # avoid duplicating points already in poor_pts
            if tuple(x_new) not in poor_pts:
                X_new_list.append(x_new)
                poor_pts.append(tuple(x_new))

    if not X_new_list:
        log.warning("No new poor-prediction points generated after perturbation.")
        return None

    X_new = np.array(X_new_list)
    sampled_df = pd.DataFrame(X_new, columns=parameters_selected)

    log.info(f"Generated {len(sampled_df)} new poor-prediction points.")
    return sampled_df


def split_data(
    df: DataFrame,
    objective: str,
    train_fraction: float = 0.7,
    test_fraction_within_split: float = 0.3,
    random_state: int = 42,
) -> dict[str, ndarray]:
    """
    Splits dataframe into training, validation, and test sets based on the specified proportions.
    """

    x = df.drop(columns=[objective]).to_numpy()
    y = df[objective].to_numpy()

    # Split into train and test/validation
    x_train: ndarray
    x_test: ndarray
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=get_val_fraction(train_fraction),
        random_state=random_state,
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
    x_val, x_test, y_val, y_test = train_test_split(
        x_test,
        y_test,
        test_size=test_fraction_within_split,
        random_state=random_state,
    )

    if x_val.shape[0] < 1:
        raise ValueError(
            f"Not enough samples for validation and test with {train_fraction=}"
            f"At least 1 samples is needed for test: avaiable {x_val.shape[0]}"
            f"Try to add some points or change '% of training data'"
        )

    log.info(f"Validation size: {x_val.shape[0]}, Test size: {x_test.shape[0]}")

    return {
        "x_train": x_train,
        "x_val": x_val,
        "x_test": x_test,
        "y_train": y_train,
        "y_val": y_val,
        "y_test": y_test,
    }
