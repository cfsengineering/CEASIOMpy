"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to compute the wing deformation, plot the displacements and rotations,
and plot the convergence.

| Author: Romain Gauthier
| Creation: 2024-06-17
"""

# Imports

import numpy as np
import pandas as pd

from ceasiompy.aeroframe.func.utils import (
    calculate_angle,
    compute_delta_a,
)

from pathlib import Path
from numpy import ndarray
from pandas import DataFrame
from scipy.interpolate import interp1d


# Functions

def compute_deformations(
    results: Path,
    wing_df: DataFrame,
    centerline_df: DataFrame,
) -> tuple[DataFrame, DataFrame, ndarray]:
    """
    Computes the deformation at each beam node
    and translate the displacement to the VLM mesh.

    Args:
        results: FramAT results for displacement, rotations...
        wing_df: dataframe containing VLM nodes.
        centerline_df: dataframe containing beam nodes,

    Returns:
        centerline_df: updated dataframe with displacements and rotations.
        deformed_df: dataframe containing the new VLM points.
        tip_points: coordinates of the tip of the deformed wing [m].
    """

    # Interpolate displacements and rotations along the wing span
    tensors = results.get("tensors", {})
    comp_u = tensors.get("comp:U", {})
    y_plot = np.linspace(
        centerline_df["y"].min(),
        centerline_df["y"].max(),
        len(comp_u.get("uz", [])),
    )

    def interp_profile(key: str):
        return interp1d(
            y_plot,
            comp_u.get(key, np.zeros_like(y_plot)),
            kind="quadratic",
            fill_value="extrapolate",
        )(centerline_df["y"])

    for key in ["ux", "uy", "uz", "thx", "thy", "thz"]:
        centerline_df[key] = interp_profile(key)

    for coord in ["x", "y", "z"]:
        centerline_df[f"{coord}_new"] = centerline_df[coord] + centerline_df[f"u{coord}"]

    # Compute the updated values of coordinates and angles of the beam nodes
    for angle in ["thx", "thy", "thz"]:
        centerline_df[f"{angle}_new"] = centerline_df[angle]

    centerline_df["AoA_new"] += np.rad2deg(centerline_df["thy"])

    centerline_df["delta_S"] = centerline_df.apply(
        lambda row: [row["ux"], row["uy"], row["uz"]], axis=1
    )
    centerline_df["omega_S"] = centerline_df.apply(
        lambda row: [row["thx"], row["thy"], row["thz"]], axis=1
    )

    # Mapping of the displacements and rotations of the beam nodes to the associated VLM panel
    wing_df["delta_S_mapped"] = wing_df["closest_centerline_index"].map(centerline_df["delta_S"])
    wing_df["omega_S_mapped"] = wing_df["closest_centerline_index"].map(centerline_df["omega_S"])

    wing_df["delta_A"] = wing_df.apply(compute_delta_a, axis=1)
    for coord in ["x", "y", "z"]:
        wing_df[f"{coord}_new"] = wing_df.apply(
            lambda row: row[coord] + row["delta_A"]["xyz".index(coord)], axis=1
        )

    wing_df["y_new_round"] = wing_df["y_new"].apply(lambda x: round(x, 1))

    leading_edges = []
    for _, group in wing_df.groupby("y_new_round"):
        if len(group) >= 2:
            leading_edge = group.loc[group["x_new"].idxmin()]
            trailing_edge = group.loc[group["x_new"].idxmax()]

            chord_line = np.array(
                [
                    trailing_edge["x_new"] - leading_edge["x_new"],
                    trailing_edge["y_new"] - leading_edge["y_new"],
                    trailing_edge["z_new"] - leading_edge["z_new"],
                ]
            )

            horizontal_vec = np.array([1, 0, 0])

            twist_angle = calculate_angle(chord_line, horizontal_vec)

            leading_edges.append(
                (
                    leading_edge["x_new"],
                    leading_edge["y_new_round"],
                    leading_edge["z_new"],
                    leading_edge.get("chord_length", np.nan),
                    leading_edge.get("AoA", 0) + twist_angle,
                )
            )

    deformed_df = pd.DataFrame(
        leading_edges, columns=["x_leading", "y_leading", "z_leading", "chord", "AoA"]
    )

    tip_points = centerline_df.loc[centerline_df["y_new"].idxmax()][
        ["x_new", "y_new", "z_new"]
    ].to_numpy()

    return centerline_df, deformed_df, tip_points
