"""
CEASIOMpy: Conceptual Aircraft Design Software

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

from pathlib import Path
from numpy import ndarray
from pandas import DataFrame
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)
from scipy.optimize import OptimizeResult
from typing import (
    List,
    Dict,
    Tuple,
    Union,
)

from ceasiompy import log
from ceasiompy.SMTrain.func import LH_SAMPLING_DATA
from ceasiompy.SU2Run import MODULE_NAME as SU2RUN_NAME
from ceasiompy.SMTrain import (
    LEVEL_ONE,
    LEVEL_TWO,
    LEVEL_THREE,
    AEROMAP_FEATURES,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def concatenate_if_not_none(list_arrays: List[Union[ndarray, None]]) -> ndarray:
    """
    Concatenates arrays in the list that are not None.
    """
    # Filter out None values
    valid_arrays = [arr for arr in list_arrays if arr is not None]
    # If no valid arrays, raise an error or return an empty array
    if not valid_arrays:
        raise ValueError("All arrays are None. Cannot concatenate.")

    return np.concatenate(valid_arrays, axis=0)


def collect_level_data(
    level_sets: Union[Dict[str, ndarray], None],
) -> Tuple[Union[ndarray, None], ...]:
    if level_sets is None:
        return None, None, None, None, None, None
    else:
        return unpack_data(level_sets)


def get_columns(objective: str) -> List[str]:
    aeromap_features = AEROMAP_FEATURES.copy()
    return aeromap_features + [objective]


def generate_su2_wkdir(iteration: int) -> None:
    """
    Generate unique SU2 working directory using iteration
    """
    wkdir_su2 = Path(SU2RUN_NAME) / f"SU2_{iteration}"
    wkdir_su2.mkdir(parents=True, exist_ok=True)


def create_aeromap_from_varpts(
    cpacs: CPACS,
    results_dir: Path,
    high_variance_points: Union[str, None],
) -> AeroMap:

    # Select dataset based on high-variance points or LHS sampling
    if high_variance_points is None:
        aeromap_uid = LH_SAMPLING_DATA
    else:
        aeromap_uid = "new_points"
    dataset_path = results_dir / f"{aeromap_uid}.csv"

    if not dataset_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    # Remove existing aeromap if present
    if cpacs.tixi.uIDCheckExists(aeromap_uid):
        cpacs.delete_aeromap(aeromap_uid)

    # Create and save new aeromap from the dataset
    aeromap = cpacs.create_aeromap_from_csv(dataset_path)
    if not aeromap:
        raise ValueError(f"Failed to create aeromap '{aeromap_uid}'.")

    aeromap.save()
    log.info(f"Selected aeromap: {aeromap_uid}")

    return aeromap


def log_params(result: OptimizeResult) -> None:
    params = result.x
    log.info(f"Theta0: {params[0]}")
    log.info(f"Correlation: {params[1]}")
    log.info(f"Polynomial: {params[2]}")
    log.info(f"Optimizer: {params[3]}")
    log.info(f"Nugget: {params[4]}")
    log.info(f"Rho regressor: {params[5]}")
    log.info(f"Penalty weight (λ): {params[6]}")
    log.info(f"Lowest RMSE obtained: {result.fun:.6f}")


def unpack_data(
    sets: Dict[str, ndarray],
) -> Tuple[ndarray, ndarray, ndarray, ndarray, ndarray, ndarray]:
    # Extract training, validation, and test sets
    x_train, x_val, x_test = sets["x_train"], sets["x_val"], sets["x_test"]
    y_train, y_val, y_test = sets["y_train"], sets["y_val"], sets["y_test"]
    return check_nan_inf(x_train, x_val, x_test, y_train, y_val, y_test)


def level_to_str(level: int) -> str:
    if level == 1:
        return LEVEL_ONE
    elif level == 2:
        return LEVEL_TWO
    else:
        return LEVEL_THREE


def str_to_level(fidelity_level: str) -> int:
    if fidelity_level == LEVEL_ONE:
        return 1
    elif fidelity_level == LEVEL_TWO:
        return 2
    else:
        return 3


def filter_constant_columns(
    df: DataFrame,
    input_columns: List,
) -> Tuple[DataFrame, Dict]:
    """
    Removes input columns that have a single unique value
    and stores their values separately.

    Args:
        df (DataFrame): DataFrame containing the dataset.
        input_columns (list): List of input column names to check.

    Returns:
        - df_filtered (DataFrame): Filtered dataFrame without constant columns.
        - removed_columns (Dict): Removed columns with their constant values.
    """

    columns_to_keep = [col for col in input_columns if df[col].nunique() > 1]
    removed_columns = {col: df[col].iloc[0] for col in input_columns if col not in columns_to_keep}

    if removed_columns:
        log.info(f"Removing constant columns: {list(removed_columns.keys())}")

    return df[columns_to_keep], removed_columns


def check_nan_inf(*arrays: Tuple[ndarray, ...]) -> Tuple[ndarray, ...]:
    """
    Checks for NaN or infinite values in the given arrays.

    Args:
        *arrays: Variable number of numpy arrays to check.
    """
    for i, arr in enumerate(arrays, start=1):
        if np.isnan(arr).any():
            log.warning(f"Array at position {i} contains NaN values and will be excluded.")
        if np.isinf(arr).any():
            log.warning(f"Array at position {i} contains infinite values and will be excluded.")
    return arrays


def get_val_fraction(train_fraction: float) -> float:
    if not (0 < train_fraction < 1):
        log.warning(
            f"Invalid data_repartition value: {train_fraction}." "It should be between 0 and 1."
        )
        train_fraction = max(0.1, min(train_fraction, 0.9))

    # Convert from "% of train" to "% of test"
    test_val_fraction = 1 - train_fraction
    return test_val_fraction
