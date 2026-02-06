"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to plotting in SMTrain.

"""

# Imports

import plotly.graph_objects as go

from smt.utils.misc import compute_rmse
from ceasiompy.smtrain.func.utils import get_model_typename

from pathlib import Path
from smt.applications import MFK
from ceasiompy.smtrain.func.utils import DataSplit
from ceasiompy.smtrain.func.config import TrainingSettings
from smt.surrogate_models import (
    KRG,
    RBF,
)

from ceasiompy import log


# Functions

def plot_validation(
    model: KRG | MFK | RBF,
    results_dir: Path,
    level1_split: DataSplit,
    training_settings: TrainingSettings,
) -> None:
    """
    Generates a Predicted vs Actual plot for model validation.
    """

    y_test_range = [level1_split.y_test.min(), level1_split.y_test.max()]
    typename = get_model_typename(model)

    # Model Prediction on Test Set
    model_prediction = model.predict_values(level1_split.x_test)

    # RMSE(y_test, model(x_test))
    rmse_loss = compute_rmse(
        sm=model,
        xe=level1_split.x_test,
        ye=level1_split.y_test,
    )

    log.info(f"{typename}: {rmse_loss=}")

    # Create figure
    y_test_values = level1_split.y_test.ravel()
    y_pred_values = model_prediction.ravel()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=y_test_values,
            y=y_pred_values,
            mode="markers",
            marker=dict(color="blue", opacity=0.5),
            name="Prediction",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=y_test_range,
            y=y_test_range,
            mode="lines",
            line=dict(color="red", dash="dash", width=2),
            name="Ideal",
        )
    )

    fig.update_layout(
        title=(
            f"{typename}: Predicted vs Actual of {training_settings.objective}"
            f"<br><sup>RMSE error on the test set {rmse_loss}</sup>"
        ),
        xaxis_title=f"Actual {training_settings.objective}",
        yaxis_title=f"Predicted {training_settings.objective}",
    )
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)

    fig.write_html(Path(results_dir, "test_plot_" + training_settings.objective + ".html"))
