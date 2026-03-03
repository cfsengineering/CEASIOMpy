"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Scripts for plotting the results
"""

# Imports

import math
import secrets
import plotly.graph_objects as go

from pathlib import Path
from pandas import DataFrame

from ceasiompy.staticstability import AXES


# Constants
AXIS_PLOT_CFG = {
    "longitudinal": {
        "x_col": "alpha",
        "group_col": "beta",
        "group_label": "beta",
        "y_col": "cms",
        "tangent_col": "cma",
        "title": "Longitudinal Stability Plot with tangent",
        "x_title": "Angle of Attack (deg)",
        "y_title": "Pitch Moment",
        "hover_inject": "SideSlip Angle (deg): %{customdata[1]}<br>",
    },
    "directional": {
        "x_col": "beta",
        "group_col": "alpha",
        "group_label": "alpha",
        "y_col": "cml",
        "tangent_col": "cnb",
        "title": "Directional Stability Plot with tangent",
        "x_title": "Angle of Sideslip (deg)",
        "y_title": "Yaw Moment",
        "hover_inject": "Angle of Attack (deg): %{customdata[0]}<br>",
    },
    "lateral": {
        "x_col": "beta",
        "group_col": "alpha",
        "group_label": "alpha",
        "y_col": "cmd",
        "tangent_col": "clb",
        "title": "Lateral Stability Plot with tangent",
        "x_title": "Angle of Sideslip (deg)",
        "y_title": "Roll Moment",
        "hover_inject": "Angle of Attack (deg): %{customdata[0]}<br>",
    },
}


# Methods

def _generate_random_color() -> str:
    """Generate a random color in hexadecimal format."""
    return f"#{secrets.randbelow(0xFFFFFF + 1):06x}"


def _set_html_plot(axis: str, stab_df: DataFrame, results_dir: Path) -> tuple[Path, dict]:
    axis_cfg = AXIS_PLOT_CFG[axis]

    # Access where to store the plot
    plot_path = Path(results_dir, f"staticstability_{axis}_plot.html")

    # Create a color map for different categories
    unique_combinations = stab_df[["alt", "mach", axis_cfg["group_col"]]].drop_duplicates()

    # Create the unique color map from the unique random colours
    color_map = {tuple(row): _generate_random_color() for row in unique_combinations.values}

    # Assign colors based on altitude, mach, and beta
    stab_df["color"] = stab_df.apply(
        lambda row: color_map[(row["alt"], row["mach"], row[axis_cfg["group_col"]])],
        axis=1,
    )

    return plot_path, color_map


# Functions

def plot_stability(stab_df: DataFrame, results_dir: Path) -> None:
    """
    Adds a stability plot for the Tangent case.
    """
    for axis in AXES:
        axis_cfg = AXIS_PLOT_CFG[axis]
        plot_path, color_map = _set_html_plot(
            axis=axis,
            stab_df=stab_df,
            results_dir=results_dir,
        )

        # Initial plot
        fig = go.Figure()

        # Add traces for each unique combination
        for pair_idx, (combination, group) in enumerate(
            stab_df.groupby(["alt", "mach", axis_cfg["group_col"]])
        ):
            color = color_map[combination]
            scatter_x = []
            scatter_y = []
            axis_label = axis_cfg["group_label"]
            legend_group_name = (
                f"Alt: {combination[0]}, Mach: {combination[1]}, {axis_label}: {combination[2]}"
            )
            legend_rank_base = pair_idx * 2
            tangent_legend_added = False

            for _, row in group.iterrows():
                scatter_x.append(row[axis_cfg["x_col"]])
                scatter_y.append(row[axis_cfg["y_col"]])
                alpha = row[axis_cfg["x_col"]]
                cms = row[axis_cfg["y_col"]]
                cma = row[axis_cfg["tangent_col"]]
                tangent_x = [alpha - 0.1, alpha + 0.1]
                tangent_y = [cms - 0.1 * cma, cms + 0.1 * cma]
                fig.add_trace(
                    go.Scatter(
                        x=tangent_x,
                        y=tangent_y,
                        mode="lines",
                        line=dict(color=color),
                        legendgroup=legend_group_name,
                        name=f"{legend_group_name} - tangent",
                        legendrank=legend_rank_base,
                        showlegend=not tangent_legend_added,
                    )
                )
                tangent_legend_added = True

            scatter = go.Scatter(
                x=scatter_x,
                y=scatter_y,
                mode="markers",
                marker=dict(color=color),
                legendgroup=legend_group_name,
                legendrank=legend_rank_base + 1,
                customdata=group[["alpha", "beta", "alt", "mach"]].to_numpy(),
                hovertemplate=(
                    "Alt: %{customdata[2]}<br>"
                    "Mach: %{customdata[3]}<br>"
                    + axis_cfg["hover_inject"]
                    + f"{axis_cfg['x_title']}: %{{x}}<br>"
                    f"{axis_cfg['y_title']}: %{{y}}"
                    "<extra></extra>"
                ),
                name=f"{legend_group_name} - points",
            )
            fig.add_trace(scatter)

        legend_rows = math.ceil(len(color_map))
        legend_bottom_margin = max(90, 40 + legend_rows * 24)

        fig.update_layout(
            title=axis_cfg["title"],
            xaxis_title=axis_cfg["x_title"],
            yaxis_title=axis_cfg["y_title"],
            margin=dict(l=90, r=40, t=80, b=legend_bottom_margin),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="left",
                x=0.0,
                entrywidthmode="fraction",
                entrywidth=0.5,
                traceorder="normal",
            ),
        )
        fig.update_xaxes(automargin=True, title_standoff=18)
        fig.update_yaxes(automargin=True, title_standoff=18)

        # Save the plot as an HTML file
        fig.write_html(plot_path)
