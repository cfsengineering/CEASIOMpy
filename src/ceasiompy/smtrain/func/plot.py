"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions related to plotting in SMTrain.

"""

# Imports

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
from plotly.graph_objects import (
    Figure,
    Scatter,
)

from ceasiompy import log


# Methods

def _add_split_trace(
    fig: Figure,
    model: KRG | MFK | RBF,
    split: DataSplit,
    label: str,
    color: str,
) -> float:
    model_prediction = model.predict_values(split.x_test)
    rmse_loss = compute_rmse(
        sm=model,
        xe=split.x_test,
        ye=split.y_test,
    )
    fig.add_trace(
        Scatter(
            x=split.y_test.ravel(),
            y=model_prediction.ravel(),
            mode="markers",
            marker=dict(color=color, opacity=0.5),
            name=label,
        )
    )
    return rmse_loss


def plot_validation(
    model: KRG | MFK | RBF,
    results_dir: Path,
    level1_split: DataSplit,
    level2_split: DataSplit | None,
    training_settings: TrainingSettings,
) -> None:
    """
    Generates a Predicted vs Actual plot for model validation on the Test Set.
    """
    typename = get_model_typename(model)
    filename = "test_plot_" + training_settings.objective + ".html"

    y_test_range = [
        min(
            level1_split.y_test.min(),
            level2_split.y_test.min() if level2_split is not None else level1_split.y_test.min(),
        ),
        max(
            level1_split.y_test.max(),
            level2_split.y_test.max() if level2_split is not None else level1_split.y_test.max(),
        ),
    ]

    fig = Figure()

    rmse_level1 = _add_split_trace(
        fig=fig,
        model=model,
        split=level1_split,
        label="Level 1",
        color="blue",
    )
    log.info(f"{typename} (Level 1): {rmse_level1=}")
    title_rmse = f"RMSE L1: {rmse_level1}"

    if level2_split is not None:
        rmse_level2 = _add_split_trace(
            fig=fig,
            model=model,
            split=level2_split,
            label="Level 2",
            color="orange",
        )
        log.info(f"{typename} (Level 2): {rmse_level2=}")
        title_rmse += f", RMSE L2: {rmse_level2}"

    fig.add_trace(
        Scatter(
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
            f"<br><sup>{title_rmse}</sup>"
        ),
        xaxis_title=f"Actual {training_settings.objective}",
        yaxis_title=f"Predicted {training_settings.objective}",
    )
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)

    fig.write_html(Path(results_dir, filename))
