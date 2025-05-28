"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Scripts for plotting the results

| Author: Leon Deligny
| Creation: 2025-01-27

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import secrets

from pathlib import Path
from pandas import DataFrame
import plotly.graph_objects as go

from typing import (
    Dict,
    Tuple,
)

from ceasiompy.StaticStability import AXES

# =================================================================================================
#   CONSTANTS
# =================================================================================================

X_Y_DICT = {
    "longitudinal_x": "aoa",
    "longitudinal_x_prime": "aos",
    "longitudinal_x_prime_short": "AoS",
    "longitudinal_y": "cms",
    "longitudinal_tangent": "cma",
    "directional_x": "aos",
    "directional_x_prime": "aoa",
    "directional_x_prime_short": "AoA",
    "directional_y": "cml",
    "directional_tangent": "cnb",
    "lateral_x": "aos",
    "lateral_x_prime": "aoa",
    "lateral_x_prime_short": "AoA",
    "lateral_y": "cmd",
    "lateral_tangent": "clb",
}

TITLES_DICT = {
    "longitudinal_title": "Longitudinal Stability Plot with tangent",
    "longitudinal_x_title": "Angle of Attack (deg)",
    "longitudinal_y_title": "Pitch Moment",
    "directional_title": "Directional Stability Plot with tangent",
    "directional_x_title": "Angle of Sideslip (deg)",
    "directional_y_title": "Yaw Moment",
    "lateral_title": "Lateral Stability Plot with tangent",
    "lateral_x_title": "Angle of Sideslip (deg)",
    "lateral_y_title": "Roll Moment (deg)",
}

LR_TITLES_DICT = {
    "longitudinal_title": "Longitudinal Stability Plot with Linear Regression",
    "longitudinal_x_title": "Angle of Attack (deg)",
    "longitudinal_y_title": "Pitch Moment",
    "directional_title": "Directional Stability Plot with Linear Regression",
    "directional_x_title": "Angle of Sideslip (deg)",
    "directional_y_title": "Yaw Moment",
    "lateral_title": "Lateral Stability Plot with Linear Regression",
    "lateral_x_title": "Angle of Sideslip (deg)",
    "lateral_y_title": "Roll Moment (deg)",
}

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def generate_random_color() -> str:
    """
    Generate a random color in hexadecimal format.

    Returns:
        str: A string representing a random color in hexadecimal format.

    """

    return f"#{secrets.randbelow(0xFFFFFF + 1):06x}"


def set_html_plot(results_dir: Path, df: DataFrame, axis: str) -> Tuple[Path, Dict]:
    # Access where to store the plot
    plot_path = Path(results_dir, f"Stability_{axis}_plot.html")

    # Create a color map for different categories
    unique_combinations = df[["alt", "mach", f"{X_Y_DICT[f'{axis}_x_prime']}"]].drop_duplicates()

    color_map = {tuple(row): generate_random_color() for row in unique_combinations.values}

    # Assign colors based on altitude, mach, and AoS
    df["color"] = df.apply(
        lambda row: color_map[
            (row["alt"], row["mach"], row[f"{X_Y_DICT[f'{axis}_x_prime']}"])
        ],
        axis=1,
    )

    return plot_path, color_map


def add_stability_plot_tangent(results_dir: Path, df: DataFrame) -> None:
    """
    Adds a stability plot for the Tangent case.
    """
    for axis in AXES:
        plot_path, color_map = set_html_plot(results_dir, df, axis)

        # Initial plot
        fig = go.Figure()

        # Add traces for each unique combination
        for combination, group in df.groupby(["alt", "mach", f"{X_Y_DICT[f'{axis}_x_prime']}"]):
            color = color_map[combination]
            scatter_x = []
            scatter_y = []

            for _, row in group.iterrows():
                scatter_x.append(row[f"{X_Y_DICT[f'{axis}_x']}"])
                scatter_y.append(row[f"{X_Y_DICT[f'{axis}_y']}"])
                alpha = row[f"{X_Y_DICT[f'{axis}_x']}"]
                cms = row[f"{X_Y_DICT[f'{axis}_y']}"]
                cma = row[f"{X_Y_DICT[f'{axis}_tangent']}"]
                tangent_x = [alpha - 0.1, alpha + 0.1]
                tangent_y = [cms - 0.1 * cma, cms + 0.1 * cma]
                fig.add_trace(
                    go.Scatter(
                        x=tangent_x,
                        y=tangent_y,
                        mode="lines",
                        line=dict(color=color),
                        showlegend=True,
                    )
                )
            axis_label = X_Y_DICT[f"{axis}_x_prime_short"]

            scatter = go.Scatter(
                x=scatter_x,
                y=scatter_y,
                mode="markers",
                marker=dict(color=color),
                name=(
                    f"Alt: {combination[0]}, "
                    f"Mach: {combination[1]}, "
                    f"{axis_label}: {combination[2]}"
                )
            )
            fig.add_trace(scatter)

        fig.update_layout(
            title=f'{TITLES_DICT[axis + "_title"]}',
            xaxis_title=f'{TITLES_DICT[axis + "_x_title"]}',
            yaxis_title=f'{TITLES_DICT[axis + "_y_title"]}',
        )

        # Save the plot as an HTML file
        fig.write_html(plot_path)


def add_stability_plot_lr(results_dir: Path, df: DataFrame) -> None:
    """
    Adds a stability plot for Linear Regression case.
    """
    for axis in AXES:
        plot_path, color_map = set_html_plot(results_dir, df, axis)

        # Initial plot
        fig = go.Figure()

        # Add traces for each unique combination
        for combination, group in df.groupby(["alt", "mach", f"{X_Y_DICT[f'{axis}_x_prime']}"]):
            color = color_map[combination]
            scatter_x = group[f"{X_Y_DICT[f'{axis}_x']}"].tolist()
            scatter_y = group[f"{X_Y_DICT[f'{axis}_y']}"].tolist()

            # Plot the scatter points
            scatter = go.Scatter(
                x=scatter_x,
                y=scatter_y,
                mode="markers",
                marker=dict(color=color),
                name=f"Alt: {combination[0]}, Mach: {combination[1]}, "
                f"{X_Y_DICT[f'{axis}_x_prime_short']}: {combination[2]}",
            )
            fig.add_trace(scatter)

            # Plot the linear regression line
            lr_cma = group[f"lr_{X_Y_DICT[f'{axis}_tangent']}"].iloc[0]
            lr_cma_intercept = group[f"lr_{X_Y_DICT[f'{axis}_tangent']}_intercept"].iloc[0]
            line_x = [min(scatter_x), max(scatter_x)]
            line_y = [lr_cma * x + lr_cma_intercept for x in line_x]
            line = go.Scatter(
                x=line_x, y=line_y, mode="lines", line=dict(color=color), showlegend=False
            )
            fig.add_trace(line)

        fig.update_layout(
            title=f'{LR_TITLES_DICT[axis + "_title"]}',
            xaxis_title=f'{LR_TITLES_DICT[axis + "_x_title"]}',
            yaxis_title=f'{LR_TITLES_DICT[axis + "_y_title"]}',
        )

        # Save the plot as an HTML file
        fig.write_html(plot_path)


def plot_stability(results_dir: Path, df: DataFrame, tangent_bool: bool) -> None:
    """
    Generate and save stability plots for longitudinal, directional, and lateral stability.

    This function calls the add_stability_plot function
    for each type of stability (longitudinal, directional, and lateral)
    to generate and save the corresponding stability plots.

    Args:
        df (DataFrame): DataFrame containing the stability data.
        tangent_bool (bool):
            False if using slope derivatives.
            True if using Linear Regression to compute the stability derivatives.

    """

    if not tangent_bool:
        add_stability_plot_tangent(results_dir, df)
    else:
        add_stability_plot_lr(results_dir, df)
