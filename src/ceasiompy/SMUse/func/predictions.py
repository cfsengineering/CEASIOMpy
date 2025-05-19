"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from smt.utils.misc import compute_rmse

from pandas import DataFrame
from smt.applications import MFK
from smt.surrogate_models import KRG
from typing import (
    Dict,
    Union,
)

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def make_predictions(
    datasets: Dict[str, DataFrame],
    model: Union[KRG, MFK],
) -> Dict[str, Dict]:
    predictions_dict = {}

    # Iterate through all datasets in the dictionary
    for dataset_name, prediction_dataset in datasets.items():
        x_pred = prediction_dataset.to_numpy()
        y_pred = model.predict_values(x_pred)
        rmse = compute_rmse(model, x_pred, y_pred)
        log.info(f"RMSE for {dataset_name}: {rmse}")

        predictions_dict[dataset_name] = {
            "predictions": y_pred,
            "rmse": rmse
        }

    return predictions_dict
