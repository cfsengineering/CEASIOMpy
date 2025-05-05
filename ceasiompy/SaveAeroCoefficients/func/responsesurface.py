"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This function enables to create the Response Surface of a Surrogate Model created with SMTrain.
Also the scatter points of the training datasets could be plotted

| Author: Giacomo Gronda
| Creation: 2025-03-20

TODO:
    *Compatibility with SMTrain loop
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from cpacspy.cpacsfunctions import get_value
from ceasiompy.SMUse.func.config import load_surrogate
from ceasiompy.SMTrain.func.predictions import make_predictions
from ceasiompy.utils.ceasiompyutils import get_aeromap_list_from_xpath

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.SaveAeroCoefficients import AEROMAP_FEATURES
from ceasiompy.utils.commonxpaths import (
    RS_XPATH,
    PLOT_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def plot_response_surface(cpacs: CPACS, results_dir: Path) -> None:
    """
    Generates and visualizes the response surface
    of an aerodynamic coefficient using a surrogate model.

    Notes:
        - The function extracts variables for the X and Y axes, along with two constant parameters.
        - It generates a grid of input values and makes predictions using the surrogate model.
        - The resulting surface plot is saved as an image in the results directory.
    """

    tixi = cpacs.tixi

    # Load the trained surrogate modeland metadata
    model, coefficient, removed_columns = load_surrogate(cpacs)

    # Ensure removed_columns is a list
    if not isinstance(removed_columns, list):
        log.warning("removed_columns is not a list, setting to empty list.")
        removed_columns = []

    # Extract X-axis variable and limits
    x = get_value(tixi, RS_XPATH + "/VariableOnX/Variable")
    x_low_limit = get_value(tixi, RS_XPATH + "/VariableOnX/LowLimit")
    x_high_limit = get_value(tixi, RS_XPATH + "/VariableOnX/HighLimit")

    # Extract y-axis variable and limits
    y = get_value(tixi, RS_XPATH + "/VariableOnY/Variable")
    y_low_limit = get_value(tixi, RS_XPATH + "/VariableOnY/LowLimit")
    y_high_limit = get_value(tixi, RS_XPATH + "/VariableOnY/HighLimit")

    # Extract two constant variables
    c1 = get_value(tixi, RS_XPATH + "/FirstConstantVariable")
    c1_value = get_value(tixi, RS_XPATH + "/FirstConstantVariableValue")

    c2 = get_value(tixi, RS_XPATH + "/SecondConstantVariable")
    c2_value = get_value(tixi, RS_XPATH + "/SecondConstantVariableValue")

    # Generate a grid of X and Y values
    x_grid = np.linspace(x_low_limit, x_high_limit, 50)
    y_grid = np.linspace(y_low_limit, y_high_limit, 50)
    X, Y = np.meshgrid(x_grid, y_grid)

    # Build the input matrix for model prediction
    input_data = np.column_stack([(
        X.ravel()
        if col == x
        else (
            Y.ravel()
            if col == y
            else np.full(X.size, c1_value) if col == c1 else np.full(X.size, c2_value)
        ))
        for col in AEROMAP_FEATURES
        if col not in removed_columns
    ])

    # Retrieve aeromaps for scatter plot
    aeromap_for_scatter_xpath = PLOT_XPATH + "/aeroScatter"
    aeromap_uid_list = get_aeromap_list_from_xpath(cpacs, aeromap_for_scatter_xpath)

    # Initialize a list to store DataFrames with aerodynamic map data
    aeromap_df_list = []
    for aeromap_uid in aeromap_uid_list:
        aeromap_df = cpacs.get_aeromap_by_uid(aeromap_uid).df
        aeromap_df["uid"] = aeromap_uid
        aeromap_df_list.append(aeromap_df)

    # Combine all aerodynamic maps into a single DataFrame
    full_aeromap_df = pd.concat(aeromap_df_list, ignore_index=True)

    # Make predictions using the surrogate model
    pred_values = model.predict_values(input_data)

    Z = pred_values.reshape(X.shape)

    # Create the 3D plot
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8)

    # Define markers and colors for scatter points
    scatter_markers = ["o", "X", "s"]
    scatter_colors = ["r", "b", "g"]

    # Loop through each aeromap UID and overlay scatter points
    for idx, aeromap_uid in enumerate(aeromap_uid_list):
        aeromap_filtered = full_aeromap_df[full_aeromap_df["uid"] == aeromap_uid]

        # Apply filtering based on constant variables
        aeromap_filtered = aeromap_filtered[
            (aeromap_filtered[c1] == c1_value) & (aeromap_filtered[c2] == c2_value)
        ]

        log.info(f"Processing aeromap: {aeromap_uid}")

        if not aeromap_filtered.empty:
            x_scatter = aeromap_filtered[x].values
            y_scatter = aeromap_filtered[y].values
            coeff_scatter = aeromap_filtered[coefficient].values

            marker = scatter_markers[idx % len(scatter_markers)]
            color = scatter_colors[idx % len(scatter_colors)]
            ax.scatter(
                x_scatter, y_scatter, coeff_scatter, c=color, marker=marker, label=aeromap_uid
            )

    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_xlim(ax.get_xlim()[::-1])
    ax.set_ylim(ax.get_ylim()[::-1])
    ax.set_zlabel(f"{coefficient}")
    ax.set_title(f"Response Surface for {c1} = {c1_value} and {c2} = {c2_value}")
    ax.view_init(elev=25, azim=45)
    ax.legend()

    # Save the plot as an image in the results directory
    plt.savefig(Path(results_dir, "response_surface_" + x + "_vs_" + y + ".png"))
    plt.close(fig)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
