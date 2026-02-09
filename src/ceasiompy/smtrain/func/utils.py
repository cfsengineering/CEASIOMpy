"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports
import shutil
import joblib
import numpy as np
import pandas as pd

from pathlib import Path
from numpy import ndarray
from pandas import DataFrame
from pydantic import BaseModel
from smt.applications import MFK
from scipy.optimize import (
    Bounds,
    OptimizeResult,
)
from smt.surrogate_models import (
    KRG,
    RBF,
)
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.su2run import MODULE_NAME as SU2RUN
from ceasiompy.smtrain import (
    LEVEL_ONE,
    LEVEL_TWO,
    LEVEL_THREE,
    AEROMAP_FEATURES,
)


# Classes

class TrainingSettings(BaseModel):
    sm_models: list[str]
    objective: str
    direction: str
    n_samples: int
    fidelity_level: str
    data_repartition: float


class GeomBounds(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    bounds: Bounds
    param_names: list[str]


class DataSplit(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    columns: list[str]
    x_train: ndarray
    y_train: ndarray

    x_val: ndarray
    y_val: ndarray

    x_test: ndarray
    y_test: ndarray

    @property
    def x_all(self) -> ndarray:
        return np.concatenate([self.x_train, self.x_val, self.x_test], axis=0)

    @property
    def y_all(self) -> ndarray:
        return np.concatenate([self.y_train, self.y_val, self.y_test], axis=0)


# Functions

def domain_converter(
    t: float | ndarray,
    from_domain: tuple[float, float],
    to_domain: tuple[float, float],
) -> float | ndarray:
    a, b = from_domain[0], from_domain[1]
    c, d = to_domain[0], to_domain[1]

    # Convert accordingly from bounds
    if a == b:
        converted = (to_domain[0] + to_domain[1]) / 2.0
    else:
        converted = ((c - d) * t + (a * d - b * c)) / (a - b)

    if isinstance(t, ndarray):
        if t.ndim != 1:
            raise ValueError('domain_converter only supports 1D numpy arrays.')
        return converted
    return float(converted)


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
    geom_bounds: GeomBounds,
    training_settings: TrainingSettings,
) -> None:
    # Save Best Low Fidelity Geometry Configuration from Training Data
    geom_cols = geom_bounds.param_names
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
