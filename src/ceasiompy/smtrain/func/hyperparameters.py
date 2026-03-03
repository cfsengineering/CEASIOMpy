"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to the training of the surrogate model.
"""

# Imports
import numpy as np

from ceasiompy.smtrain.func.utils import DataSplit
from skopt.space import (
    Real,
    Categorical,
)

from ceasiompy import log


# Functions

def get_hyperparam_space_rbf(
    level1_split: DataSplit,
    level2_split: DataSplit | None = None,
    level3_split: DataSplit | None = None,
) -> list:
    """
    Get Hyper-parameters space, determined by the training set.
    """
    arrays = [level1_split.x_train]
    if level2_split is not None:
        arrays.append(level2_split.x_train)
    if level3_split is not None:
        arrays.append(level3_split.x_train)

    x_train = np.concatenate(arrays, axis=0)
    n_samples, n_features = x_train.shape
    r = n_samples / 3**n_features

    if 0.8 <= r < 1:
        return [
            Real(1, 25, name="d0"),
            Categorical([-1], name="poly_degree"),
            Real(1e-15, 1e-8, name="reg"),
        ]
    elif 0.3 <= r < 0.8:
        return [
            Real(1, 250, name="d0"),
            Categorical([-1], name="poly_degree"),
            Real(1e-15, 1e-8, name="reg"),
        ]
    elif 0.0 <= r < 0.3:
        return [
            Real(1, 1000, name="d0"),
            Categorical([-1], name="poly_degree"),
            Real(1e-15, 1e-8, name="reg"),
        ]
    else:
        return [
            Real(1, 10, name="d0"),
            Categorical([-1], name="poly_degree"),
            Real(1e-15, 1e-8, name="reg"),
        ]


def get_hyperparam_space_kriging(
    level1_split: DataSplit,
    level2_split: DataSplit | None = None,
    level3_split: DataSplit | None = None,
) -> list[str]:
    """
    Get Hyper-parameters space from the different fidelity datasets.
    Uniquely determined by the training set x_train.
    """

    # Concatenate only non-None arrays
    arrays = [level1_split.x_train]
    if level2_split is not None:
        arrays.append(level2_split.x_train)
    if level3_split is not None:
        arrays.append(level3_split.x_train)

    x_train = np.concatenate(arrays, axis=0)
    n_samples, n_features = x_train.shape

    # Determine allowed polynomial regression types based on sample count
    if n_samples > ((n_features + 1) * (n_features + 2) / 2):
        poly_options = ["constant", "linear", "quadratic"]
        x = (n_features + 1) * (n_features + 2) / 2
        log.info(f"Training points (n_samples): {x}<{n_samples} -> poly_options: {poly_options}")
    elif n_samples > (n_features + 2):
        poly_options = ["constant", "linear"]
        x = (n_features + 1) * (n_features + 2) / 2
        y = n_features + 2
        log.info(
            f"Training points (n_samples): {y}<{n_samples}<={x} -> poly_options: {poly_options}"
        )
    elif n_samples > 2:
        poly_options = ["constant"]
        y = n_features + 2
        log.info(f"Training points (n_samples): {n_samples}<={y} -> poly_options: {poly_options}")
    else:
        raise Warning(
            f"Number of training points must be greater than 2, current size: {n_samples}"
        )

    return [
        Real(0.0001, 10, name="theta0"),
        Categorical(["abs_exp", "squar_exp", "matern52", "matern32"], name="corr"),
        Categorical(poly_options, name="poly"),
        Categorical(["Cobyla", "TNC"], name="opt"),
        Real(1e-12, 1e-4, name="nugget"),
        Categorical(poly_options, name="rho_regr"),
        Real(0.1, 1, name="lambda_penalty"),
    ]
