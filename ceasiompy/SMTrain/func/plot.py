"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to plotting in SMTrain.

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import matplotlib.pyplot as plt

from pathlib import Path
from smt.applications import MFK
from smt.surrogate_models import KRG
from typing import (
    Dict,
    Union,
)

from ceasiompy.SMTrain.func.predictions import make_predictions

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

    x_test = sets["x_test"]
    y_test = sets["y_test"]

    predictions, _ = make_predictions(model, x_test, y_test)

    fig = plt.figure(figsize=(6, 6))
    plt.scatter(y_test, predictions, color="blue", alpha=0.5)
    plt.plot(
        [y_test.min(), y_test.max()],
        [y_test.min(), y_test.max()],
        "r--",
        lw=2,
    )
    plt.title(f"Predicted vs Actual {label}")
    plt.xlabel(f"Actual {label}")
    plt.ylabel(f"Predicted {label}")
    plt.grid()

    fig_name = "validation_plot_" + label + ".png"
    fig_path = Path(result_dir, fig_name)
    plt.savefig(fig_path)
    plt.close(fig)
