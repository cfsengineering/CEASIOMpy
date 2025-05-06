"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to the loss computation of the surrogate model.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import numpy as np

from smt.utils.misc import compute_rmse

from numpy import ndarray
from smt.applications import MFK
from smt.surrogate_models import KRG
from typing import (
    Tuple,
    Union,
)

from ceasiompy.SMTrain import (
    LEVEL_ONE,
    LEVEL_TWO,
    # LEVEL_THREE,
)


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def compute_first_level_loss(
    params: Tuple,
    x_train: ndarray,
    y_train: ndarray,
    x_: ndarray,
    y_: ndarray,
) -> Tuple[KRG, float]:
    """
    Returns model and the loss for this model on the x_, y_ set.
    """
    model = KRG(
        theta0=[params[0]],
        corr=str(params[1]),  # Important to convert to str format
        poly=params[2],
        hyper_opt=params[3],
        nugget=params[4],
    )
    model.set_training_values(x_train, y_train)
    model.train()
    return model, compute_loss(model, params[6], x_, y_)


def compute_multi_level_loss(
    params: Tuple,
    x_fl_train: ndarray,
    y_fl_train: ndarray,
    x_sl_train: Union[ndarray, None],
    y_sl_train: Union[ndarray, None],
    # x_tl_train: Union[ndarray, None],
    # y_tl_train: Union[ndarray, None],
    x_: ndarray,
    y_: ndarray,
) -> Tuple[MFK, float]:
    """
    Returns model and the loss for this model on the x_, y_ set.
    """
    model = MFK(
        theta0=[params[0]],
        corr=params[1],
        poly=params[2],
        hyper_opt=params[3],
        nugget=params[4],
        rho_regr=params[5],
    )
    model.set_training_values(x_fl_train, y_fl_train, name=LEVEL_ONE)
    # if x_sl_train is not None and y_sl_train is not None:
    model.set_training_values(x_sl_train, y_sl_train, name=LEVEL_TWO)
    # if x_tl_train is not None and y_tl_train is not None:
    #     model.set_training_values(x_tl_train, y_tl_train, name=LEVEL_THREE)
    model.train()
    return model, compute_loss(model, params[6], x_, y_)


def compute_loss(
    model: Union[KRG, MFK],
    lambda_penalty: float,
    x_: ndarray,
    y_: ndarray,
) -> float:
    return compute_rmse(model, x_, y_) + lambda_penalty * np.mean(model.predict_variances(x_))
