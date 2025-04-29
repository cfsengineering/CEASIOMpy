"""
Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:
    *Improve loop and AVL and SU2 settings
"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from ceasiompy.SMTrain.func.utils import get_val_fraction
from ceasiompy.SMTrain.func.surrogate import make_predictions

from pathlib import Path
from numpy import ndarray
from pandas import DataFrame
from smt.applications import MFK
from smt.surrogate_models import KRG
from smt.sampling_methods import LHS
from typing import (
    Dict,
    List,
    Union,
)

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def new_doe(
    datasets: Dict,
    model: Union[KRG, MFK],
    fraction_of_new_samples: int,
    result_dir: Path,
):
    """
    Generate a new set of suggested sampling points based on model uncertainty.

    This function selects the highest uncertainty points from the dataset with
    the highest fidelity level and suggests them for additional sampling.

    Args:
        datasets (Dict):
            Contains datasets for different fidelity levels.
            Expected format: { "fidelity_X": (X, y, df_filt, rmv_col, df) }.
        model: Trained surrogate model used for making predictions.
        fraction_of_new_samples (float):
            Determines the number of new samples by dividing
            the dataset size by this value.
        result_dir (Path): Where new dataset will be saved.

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
        df: DataFrame
        df_filt: DataFrame
        rmv_col: Dict
        x, _, df_filt, rmv_col, df = datasets[highest_fidelity_level]
    except ValueError:
        raise ValueError(
            f"Dataset structure for {highest_fidelity_level} is incorrect."
            f"Expected tuple (X, y, df_filt, rmv_col, df)."
        )

    _, y_var = make_predictions(model, x)

    y_var_flat = np.asarray(y_var).flatten()
    sorted_indices = np.argsort(y_var_flat)[::-1]  # Sort in descending order
    n_new_samples = max(1, len(x) // fraction_of_new_samples)  # Ensure at least one sample
    top_n_indices = sorted_indices[:n_new_samples]
    top_X: ndarray = x[top_n_indices]

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
    output_file_path = result_dir / "suggested_points.csv"
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
        ranges (Dict):
            Dictionary specifying the variable ranges in the format:
            { "variable_name": (min_value, max_value) }.
        results_dir (Path): Where the sampled dataset will be saved.
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
    sampled_df = DataFrame(sampled_dict)
    output_file_path = results_dir / "lh_sampling_dataset.csv"
    sampled_df.to_csv(output_file_path, index=False)
    log.info(f"LHS dataset saved in {output_file_path}")

    return output_file_path


def new_points(
    datasets: Dict,
    model: Union[KRG, MFK],
    results_dir: Path,
    high_variance_points: List,
) -> Union[DataFrame, None]:
    """
    Selects new sampling points based on variance predictions from a surrogate model.

    This function identifies high-variance points from the `level_1` dataset for adaptive sampling.
    In the first iteration, it selects the top 6 points with the highest variance. In subsequent
    iterations, it picks the next highest variance point not previously selected.

    Args:
        datasets (Dict): Contains different fidelity datasets (expects 'level_1').
        model (object): Surrogate model used to predict variance.
        result_dir (Path): Directory where the selected points CSV file will be saved.
        high_variance_points (List): List of previously selected high-variance points.

    Returns:
        DataFrame containing the newly selected points.
        Or None if all high-variance points have already been chosen.
    """

    # Retrieve the first fidelity dataset
    first_dataset = datasets["level_1"]
    df: DataFrame
    x, _, df, _, _ = first_dataset  # Unpack dataset

    # Compute variance prediction
    _, y_var = make_predictions(model, x)
    y_var_flat = np.asarray(y_var).flatten()
    sorted_indices = np.argsort(y_var_flat)[::-1]  # Sort indices by variance (descending)

    output_file_path = results_dir / "new_points.csv"
    columns = df.columns

    # First iteration: generate boundary points
    if not high_variance_points:
        log.info("First iteration: selecting the first 6 highest variance points.")
        selected_points = [tuple(x[idx]) for idx in sorted_indices[:6]]
        high_variance_points.extend(selected_points)
        sampled_df = DataFrame(selected_points, columns=columns)
        sampled_df.to_csv(output_file_path, index=False)
        return sampled_df

    log.info("Selecting next highest variance point.")

    # Convert list of points to a set for fast lookup
    high_variance_set = set(tuple(p) for p in high_variance_points)

    for idx in sorted_indices:
        new_point = tuple(x[idx])
        if new_point not in high_variance_set:
            high_variance_points.append(new_point)
            sampled_df = DataFrame([new_point], columns=columns)
            sampled_df.to_csv(output_file_path, index=False)
            return sampled_df

    log.warning("No new points found, all have been selected.")
    return None


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
