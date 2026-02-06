"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports
import shutil
import numpy as np
import pandas as pd
from pathlib import Path
from numpy import ndarray
from pandas import DataFrame
from pydantic import BaseModel
from smt.applications import MFK
from scipy.optimize import OptimizeResult
from ceasiompy.smtrain.func.parameter import Parameter
from ceasiompy.smtrain.func.config import TrainingSettings
from smt.surrogate_models import (
    KRG,
    RBF,
)
from cpacspy.cpacspy import (
    CPACS,
    AeroMap,
)

from ceasiompy import log
from ceasiompy.smtrain.func import AEROMAP_SELECTED
from ceasiompy.pyavl import MODULE_NAME as PYAVL
from ceasiompy.su2run import MODULE_NAME as SU2RUN
from ceasiompy.smtrain import (
    LEVEL_ONE,
    LEVEL_TWO,
    LEVEL_THREE,
    AEROMAP_FEATURES,
)


# Classes

class DataSplit(BaseModel):
    columns: list[str]
    x_train: ndarray
    y_train: ndarray

    x_val: ndarray
    y_val: ndarray

    x_test: ndarray
    y_test: ndarray


# Functions

def save_model(
    model: KRG | MFK | RBF,
    columns: list[str],
    results_dir: Path,
    training_settings: TrainingSettings,
) -> None:
    """
    Save trained surrogate model.
    """
    suffix = get_model_typename(model)
    model_path = results_dir / f"sm_{suffix}.pkl"

    with open(model_path, "wb") as file:
        joblib.dump(
            value={
                "model": model,
                "columns": columns,
                "objective": training_settings.objective,
            },
            filename=file,
        )
    log.info(f"Model saved to {model_path}")


def store_best_geom_from_training(
    dataframe: DataFrame,
    cpacs_list: list[CPACS],
    lh_sampling: DataFrame,
    results_dir: Path,
    params_ranges: list[Parameter],
    training_settings: TrainingSettings,
) -> None:
    # Save Best Low Fidelity Geometry Configuration from Training Data
    geom_cols = [p.name for p in params_ranges]
    objective = training_settings.objective
    mean_obj_by_geom = (
        dataframe.groupby(geom_cols, dropna=False)[objective]
        .mean()
        .reset_index()
    )

    # Store best geometry (CPACS, Configuration)
    best_geom_dir = results_dir / "best_geometry"
    best_geom_dir.mkdir(exist_ok=True)
    best_geometry_idx = mean_obj_by_geom[objective].idxmax()
    best_geometries_df = mean_obj_by_geom.loc[[best_geometry_idx]]
    best_geometries_df.to_csv(f"{best_geom_dir}/best_geom_config.csv", index=False)

    # Save associated CPACS file for the best geometry
    best_geom_values = best_geometries_df[geom_cols].iloc[0].values
    mask = (lh_sampling[geom_cols] == best_geom_values).all(axis=1)
    if not mask.any():
        raise ValueError("Could not match best geometry to a CPACS file. Skipping copy.")

    best_cpacs_idx = int(mask.idxmax())
    best_cpacs_path = cpacs_list[best_cpacs_idx].cpacs_file
    shutil.copyfile(
        best_cpacs_path,
        best_geom_dir / f"best_geom_{best_cpacs_idx + 1:03d}.xml",
    )


def get_columns(objective: str) -> list[str]:
    aeromap_features = AEROMAP_FEATURES.copy()
    return aeromap_features + [objective]


def generate_su2_wkdir(iteration: int) -> None:
    """
    Generate unique SU2 working directory using iteration
    """
    wkdir_su2 = Path(SU2RUN) / f"SU2_{iteration}"
    wkdir_su2.mkdir(parents=True, exist_ok=True)


def create_aeromap_from_varpts(
    cpacs: CPACS,
    results_dir: Path,
    high_variance_points: str | None,
) -> AeroMap:

    # Select dataset based on high-variance points or LHS sampling
    if high_variance_points is None:
        aeromap_uid = AEROMAP_SELECTED
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


def log_params_krg(result: OptimizeResult) -> None:
    params = result.x
    log.info(f"Theta0: {params[0]}")
    log.info(f"Correlation: {params[1]}")
    log.info(f"Polynomial: {params[2]}")
    log.info(f"Optimizer: {params[3]}")
    log.info(f"Nugget: {params[4]}")
    log.info(f"Rho regressor: {params[5]}")
    log.info(f"Penalty weight (λ): {params[6]}")
    log.info(f"Lowest RMSE obtained: {result.fun:.6f}")


def log_params_rbf(result: OptimizeResult) -> None:
    params = result.x
    log.info(f"d0 (scaling): {params[0]:.3f}")
    log.info(f"poly_degree: {params[1]}")
    log.info(f"reg (regularization): {params[2]:.2e}")
    log.info(f"Lowest RMSE obtained: {result.fun:.6f}")


def unpack_data(
    sets: dict[str, ndarray],
) -> tuple[ndarray, ndarray, ndarray, ndarray, ndarray, ndarray]:
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
    input_columns: list,
) -> tuple[DataFrame, dict]:
    """
    Removes input columns that have a single unique value
    and stores their values separately.

    Args:
        df (DataFrame): DataFrame containing the dataset.
        input_columns (list): list of input column names to check.

    Returns:
        - df_filtered (DataFrame): Filtered dataFrame without constant columns.
        - removed_columns (dict): Removed columns with their constant values.
    """

    columns_to_keep = [col for col in input_columns if df[col].nunique() > 1]
    removed_columns = {col: df[col].iloc[0] for col in input_columns if col not in columns_to_keep}

    if removed_columns:
        log.info(f"Removing constant columns: {list(removed_columns.keys())}")

    return df[columns_to_keep], removed_columns


def check_nan_inf(*arrays: tuple[ndarray, ...]) -> tuple[ndarray, ...]:
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
    return 1 - train_fraction


def get_model_typename(model: KRG | MFK | RBF) -> str:
    return model.__class__.__name__.lower()


def num_flight_conditions(alt, mach, aoa, aos):
    return max(len(alt), len(mach), len(aoa), len(aos))


def num_geom_params(df_geom):
    return df_geom.shape[1]


def drop_constant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove columns with constant values (no variance).
    """
    return df.loc[:, df.nunique(dropna=False) > 1]
