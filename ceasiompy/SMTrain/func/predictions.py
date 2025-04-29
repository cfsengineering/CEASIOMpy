"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Make predictions with model and array of inputs x.
"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from smt.utils.misc import compute_rmse

from numpy import ndarray
from smt.applications import MFK
from smt.surrogate_models import KRG
from typing import (
    Tuple,
    Union,
)

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def make_predictions(
    model: Union[KRG, MFK],
    x: ndarray,
    y: Union[ndarray, None] = None,
) -> Tuple[ndarray, ndarray]:
    """
    Makes predictions using the trained kriging model.
    Args:
        model (object): Trained kriging model.
        x (ndarray): Input data for prediction.
        y (ndarray = None): True values for RMSE computation.
    Returns:
        Predicted values and variance.
    """

    y_pred = model.predict_values(x)
    var = model.predict_variances(x)

    if y is not None:
        log.info(f"kriging, rms err: {compute_rmse(model, x, y)}")

    log.info(f"Theta values: {model.optimal_theta}")

    return y_pred, var
