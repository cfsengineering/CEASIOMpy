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


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def compute_loss(
    params: Tuple,
    model_type: str,
    x_train: ndarray,
    y_train: ndarray,
    x_: ndarray,
    y_: ndarray,
) -> Tuple[Union[KRG, MFK], float]:
    """
    Returns model and the loss for this model on the x_, y_ set.
    """
    if model_type == "KRG":
        model = KRG(
            theta0=[params[0]],
            corr=params[1],
            poly=params[2],
            hyper_opt=params[3],
            nugget=params[4],
        )
    else:
        model = MFK(
            theta0=[params[0]],
            corr=params[1],
            poly=params[2],
            hyper_opt=params[3],
            nugget=params[4],
            rho_regr=params[5],
        )
    model.set_training_values(x_train, y_train)
    model.train()
    rmse = (
        compute_rmse(model, x_, y_) + params[6] * np.mean(model.predict_variances(x_))
    )
    return model, rmse
