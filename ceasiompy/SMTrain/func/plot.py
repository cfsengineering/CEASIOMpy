"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to plotting in SMTrain.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import matplotlib.pyplot as plt

from ceasiompy.SMTrain.func.predictions import make_predictions

from pathlib import Path
from numpy import ndarray
from smt.applications import MFK
from smt.surrogate_models import KRG
from typing import (
    Dict,
    Union,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def plot_validation(
    model: Union[KRG, MFK],
    sets: Dict,
    label: str,
    result_dir: Path,
) -> None:
    """
    Generates a Predicted vs Actual plot for model validation.
    """
    y_test: ndarray
    x_test, y_test = sets["x_test"], sets["y_test"]
    y_test_range = [y_test.min(), y_test.max()]
    predictions, _ = make_predictions(model, x_test, y_test)

    fig = plt.figure(figsize=(6, 6))
    plt.scatter(y_test, predictions, color="blue", alpha=0.5)
    plt.plot(y_test_range, y_test_range, "r--", lw=2)
    plt.title(f"Predicted vs Actual {label}")
    plt.xlabel(f"Actual {label}")
    plt.ylabel(f"Predicted {label}")
    plt.grid()
    plt.savefig(Path(result_dir, "validation_plot_" + label + ".png"))
    plt.close(fig)
