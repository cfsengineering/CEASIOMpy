"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to the loss computation of the surrogate model.

"""

# Imports

import numpy as np

from smt.utils.misc import compute_rmse

from numpy import ndarray
from smt.applications import MFK
from ceasiompy.smtrain.func.utils import DataSplit
from smt.surrogate_models import (
    KRG,
    RBF,
)

# Methods

def _compute_loss(
    model: KRG | MFK,
    lambda_penalty: float,
    x_: ndarray,
    y_: ndarray,
) -> float:
    return compute_rmse(model, x_, y_) + lambda_penalty * np.mean(model.predict_variances(x_))


# Functions

def compute_rbf_loss(
    params: tuple,
    x_: ndarray,
    y_: ndarray,
    level1_split: DataSplit,
    level2_split: DataSplit | None = None,
    level3_split: DataSplit | None = None,
) -> tuple[RBF, float]:
    model = RBF(
        d0=params[0],
        poly_degree=int(params[1]),
        reg=params[2],
        print_global=False,
    )
    model.set_training_values(
        xt=level1_split.x_train,
        yt=level1_split.y_train,
    )
    if level2_split is not None:
        model.set_training_values(
            xt=level2_split.x_train,
            yt=level2_split.y_train,
            name=2,
        )

    if level3_split is not None:
        model.set_training_values(
            xt=level3_split.x_train,
            yt=level3_split.y_train,
            name=3,
        )

    model.train()
    return model, _compute_loss(
        x_=x_,
        y_=y_,
        model=model,
        lambda_penalty=params[6],
    )


def compute_kriging_loss(
    params: tuple,
    x_: ndarray,
    y_: ndarray,
    level1_split: DataSplit,
    level2_split: DataSplit | None = None,
    level3_split: DataSplit | None = None,
) -> tuple[KRG | MFK, float]:
    """
    Returns model and the loss for this model on the x_, y_ set.
    """
    if level2_split is None and level3_split is None:
        model = KRG(
            theta0=[params[0]],
            corr=str(params[1]),  # Important to convert to str format
            poly=params[2],
            hyper_opt=params[3],
            nugget=params[4],
        )
    else:
        model = MFK(
            theta0=[params[0]],
            corr=str(params[1]),
            poly=params[2],
            hyper_opt=params[3],
            nugget=params[4],
            rho_regr=params[5],
        )

    model.set_training_values(
        xt=level1_split.x_train,
        yt=level1_split.y_train,
    )
    if level2_split is not None:
        model.set_training_values(
            xt=level2_split.x_train,
            yt=level2_split.y_train,
            name=2,
        )
    if level3_split is not None:
        model.set_training_values(
            xt=level3_split.x_train,
            yt=level2_split.y_train,
            name=3,
        )

    model.train()
    return model, _compute_loss(
        x_=x_,
        y_=y_,
        model=model,
        lambda_penalty=params[6],
    )
