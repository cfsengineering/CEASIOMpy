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

from numpy import ndarray
from pandas import DataFrame
from typing import (
    List,
    Dict,
    Tuple,
)

from ceasiompy import log
from ceasiompy.SMTrain import (
    LEVEL_ONE,
    LEVEL_TWO,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def level_to_str(level: int) -> str:
    if level == 1:
        return LEVEL_ONE
    else:
        return LEVEL_TWO


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


def check_nan_inf(*arrays) -> None:
    """
    Checks for NaN or infinite values in the given arrays.

    Args:
        *arrays: Variable number of numpy arrays to check.
    """
    for i, arr in enumerate(arrays):
        arr: ndarray
        if np.isnan(arr).any():
            raise ValueError(f"Array {i} contains NaN values.")
        if np.isinf(arr).any():
            raise ValueError(f"Array {i} contains infinite values.")


def get_val_fraction(train_fraction: float) -> float:
    if not (0 < train_fraction < 1):
        log.warning(
            f"Invalid data_repartition value: {train_fraction}."
            "It should be between 0 and 1."
        )
        train_fraction = max(0.1, min(train_fraction, 0.9))

    # Convert from "% of train" to "% of test"
    test_val_fraction = 1 - train_fraction
    return test_val_fraction


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
