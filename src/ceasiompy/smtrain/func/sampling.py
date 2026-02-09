"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Sampling strategies for SMTrain.
"""

# Imports

import numpy as np

from copy import deepcopy
from sklearn.model_selection import train_test_split
from ceasiompy.smtrain.func.utils import get_val_fraction

from pathlib import Path
from numpy import ndarray
from pandas import DataFrame
from smt.applications import MFK
from smt.sampling_methods import LHS
from smt.surrogate_models import (
    RBF,
    KRG,
)
from ceasiompy.smtrain.func.utils import DataSplit
from ceasiompy.smtrain.func.config import (
    GeomBounds,
    TrainingSettings,
)

from ceasiompy import log
from ceasiompy.smtrain import AEROMAP_FEATURES


# Functions

def lh_sampling_geom(
    geom_bounds: GeomBounds,
    n_samples: int,
    random_state: int = 42,
) -> DataFrame:
    """
    Generate a Latin Hypercube Sampling (LHS) dataset within specified variable ranges.
    Uses the Enhanced Stochastic Evolutionary (ESE) criterion
    to generate a diverse set of samples within given variable limits.
    """
    log.info(f"Generating LHS sampling for {n_samples=}")
    xlimits = np.stack(
        arrays=[geom_bounds.bounds.lb, geom_bounds.bounds.ub],
        axis=1,
    ).astype(float)

    sampling = LHS(
        xlimits=xlimits,
        criterion="ese",
        random_state=random_state,
    )
    samples = sampling(n_samples)

    # Maintain constant variables with fixed ranges
    fixed_cols = [idx for idx, (low, high) in enumerate(xlimits) if low == high]
    for idx in fixed_cols:
        samples[:, idx] = xlimits[idx, 0]

    # Save sampled dataset
    # output_file_path = results_dir / ...
    # sampled_df.to_csv(output_file_path, index=False)
    # log.info(f"LHS dataset saved in {output_file_path}")

    return DataFrame({
        name: samples[:, idx]
        for idx, name in enumerate(geom_bounds.param_names)
    })


def new_points(
    x_array: ndarray,
    model,
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


def get_high_variance_points(
    model: KRG | MFK,
    level1_split: DataSplit,
) -> DataFrame:
    """
    Select points with high predictive variance from a normalized dataset.
    Returns a DataFrame of the selected rows (same columns as the input).
    """

    # You are not training on x_val and x_test so might as well add them
    x = np.concatenate(
        arrays=[level1_split.x_train, level1_split.x_val, level1_split.x_test],
        axis=0,
    )

    # Predict variance for each row
    y_var_flat = np.asarray(model.predict_variances(x)).flatten()
    finite_mask = np.isfinite(y_var_flat)
    if not np.any(finite_mask):
        log.error("All variance predictions are infinite.")
        return DataFrame()

    y_var = y_var_flat.copy()
    y_var[~finite_mask] = -np.inf

    n = len(y_var)
    sorted_indices = np.argsort(y_var)[::-1]  # Descending variance

    # Robust threshold: max(90th percentile, Q3 + 1.5 * IQR)
    finite_vals = y_var[finite_mask]
    q1, q3 = np.quantile(finite_vals, [0.25, 0.75])
    iqr = q3 - q1
    q90 = np.quantile(finite_vals, 0.90)
    threshold = max(q90, q3 + 1.5 * iqr)

    high_idx = [idx for idx in sorted_indices if y_var[idx] >= threshold]

    # Ensure at least a small fraction is selected
    min_points = max(1, int(np.ceil(0.05 * n)))
    n_high_idx = len(high_idx)
    if n_high_idx < min_points:
        high_idx = list(sorted_indices[:min_points])

    log.info(
        f"Selected {n_high_idx} high-variance points using threshold {threshold:.6g}."
    )
    return DataFrame(x[high_idx], columns=level1_split.columns)


def get_loo_points(
    model: RBF,
    level1_split: DataSplit,
) -> DataFrame:
    """
    Generate new sampling points based on LOO error for RBF models.
    Returns a DataFrame with the same columns as ranges_gui.
    """
    x = level1_split.x_all
    y = level1_split.y_all

    n_samples = x.shape[0]
    if n_samples < 3:
        log.warning("Not enough samples for LOO.")
        return DataFrame()

    loo_error = np.full(n_samples, np.nan, dtype=float)

    for i in range(n_samples):
        x_loo = np.delete(x, i, axis=0)
        y_loo = np.delete(y, i, axis=0)
        try:
            model_loo = deepcopy(model)
            model_loo.set_training_values(x_loo, y_loo)
            model_loo.train()
            y_pred_i = model_loo.predict_values(x[i].reshape(1, -1)).ravel()[0]
            loo_error[i] = abs(y_pred_i - y[i])
        except Exception as e:
            log.warning(f"LOO failed at idx {i}: {e}")
            loo_error[i] = np.nan

    finite_mask = np.isfinite(loo_error)
    if not np.any(finite_mask):
        log.error("All LOO evaluations failed.")
        return DataFrame()

    loo_err = loo_error.copy()
    loo_err[~finite_mask] = -np.inf

    n = len(loo_err)
    sorted_indices = np.argsort(loo_err)[::-1]

    # Robust threshold: max(90th percentile, Q3 + 1.5 * IQR)
    finite_vals = loo_err[finite_mask]
    q1, q3 = np.quantile(finite_vals, [0.25, 0.75])
    iqr = q3 - q1
    q90 = np.quantile(finite_vals, 0.90)
    threshold = max(q90, q3 + 1.5 * iqr)

    high_idx = [idx for idx in sorted_indices if loo_err[idx] >= threshold]

    # Ensure at least a small fraction is selected
    min_points = max(1, int(np.ceil(0.05 * n)))
    if len(high_idx) < min_points:
        high_idx = list(sorted_indices[:min_points])

    columns = level1_split.columns
    if len(columns) != x.shape[1]:
        log.warning(
            "Column count mismatch for LOO points "
            f"({len(columns)} columns vs {x.shape[1]} features). "
            "Truncating columns to match feature count."
        )
        columns = columns[: x.shape[1]]

    log.info(
        f"Selected {len(high_idx)} high-LOO points using threshold {threshold:.6g}."
    )
    return DataFrame(x[high_idx], columns=columns)


def split_data(
    data_frame: DataFrame,
    training_settings: TrainingSettings,
    random_state: int = 42,
) -> DataSplit:
    """
    Splits dataframe into training, validation, and test sets based on the specified proportions.
    """
    # Unpack
    objective = training_settings.objective
    data_repartition = training_settings.data_repartition

    x = data_frame.drop(columns=[objective]).to_numpy()
    y = data_frame[objective].to_numpy()

    # Split into train and test/validation
    x_train: ndarray
    x_test: ndarray
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=get_val_fraction(data_repartition),
        random_state=random_state,
    )

    if x_test.shape[0] < 1:
        raise ValueError(
            f"Not enough samples for validation and test with {data_repartition=}"
            f"At least 1 samples is needed for test: avaiable {x_test.shape[0]}"
            f"Try to add some points or change '% of training data'"
        )

    log.info(f"Train size: {x_train.shape[0]}, Test+Validation size: {x_test.shape[0]}")

    # Split into validation and test
    x_val: ndarray
    x_val, x_test, y_val, y_test = train_test_split(
        x_test,
        y_test,
        test_size=0.5,                  # Take half (this way val ~= test)
        random_state=random_state,
    )

    if x_val.shape[0] < 1:
        raise ValueError(
            f"Not enough samples for validation and test with {data_repartition=}"
            f"At least 1 samples is needed for test: avaiable {x_val.shape[0]}"
            f"Try to add some points or change '% of training data'"
        )

    log.info(f"Validation size: {x_val.shape[0]}, Test size: {x_test.shape[0]}")

    return DataSplit(
        x_train=x_train,
        y_train=y_train,
        x_val=x_val,
        y_val=y_val,
        x_test=x_test,
        y_test=y_test,
        columns=data_frame.columns,
    )
