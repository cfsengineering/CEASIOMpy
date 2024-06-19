"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to...

Python version: >=3.8

| Author: Romain Gauthier
| Creation: 2024-06-17

TODO:

    * Things to improve...

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================
from scipy import interpolate
import numpy as np
import pandas as pd
from ceasiompy.utils.ceasiomlogger import get_logger
import matplotlib.pyplot as plt
from pathlib import Path

log = get_logger()

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def compute_deformations(results, wing_df, centerline_df):
    y_plot = np.linspace(centerline_df['y'].min(), centerline_df['y'].max(), len(
        results.get('tensors').get('comp:U')['uz']))
    ux_profile = interpolate.interp1d(y_plot, results.get('tensors').get(
        'comp:U')['ux'], kind='quadratic', fill_value='extrapolate')
    uy_profile = interpolate.interp1d(y_plot, results.get('tensors').get(
        'comp:U')['uy'], kind='quadratic', fill_value='extrapolate')
    uz_profile = interpolate.interp1d(y_plot, results.get('tensors').get(
        'comp:U')['uz'], kind='quadratic', fill_value='extrapolate')
    thx_profile = interpolate.interp1d(y_plot, results.get('tensors').get(
        'comp:U')['thx'], kind='quadratic', fill_value='extrapolate')
    thy_profile = interpolate.interp1d(y_plot, results.get('tensors').get(
        'comp:U')['thy'], kind='quadratic', fill_value='extrapolate')
    thz_profile = interpolate.interp1d(y_plot, results.get('tensors').get(
        'comp:U')['thz'], kind='quadratic', fill_value='extrapolate')

    centerline_df['ux'] = ux_profile(centerline_df['y'])
    centerline_df['uy'] = uy_profile(centerline_df['y'])
    centerline_df['uz'] = uz_profile(centerline_df['y'])
    centerline_df['thx'] = thx_profile(centerline_df['y'])
    centerline_df['thy'] = thy_profile(centerline_df['y'])
    centerline_df['thz'] = thz_profile(centerline_df['y'])

    centerline_df["x_new"] += centerline_df['ux']
    centerline_df["y_new"] += centerline_df['uy']
    centerline_df["z_new"] += centerline_df['uz']

    centerline_df["delta_S"] = centerline_df.apply(
        lambda row: [row['ux'], row['uy'], row['uz']], axis=1)
    centerline_df["omega_S"] = centerline_df.apply(
        lambda row: [row['thx'], row['thy'], row['thz']], axis=1)

    wing_df["delta_S_mapped"] = wing_df["closest_centerline_index"].map(centerline_df["delta_S"])
    wing_df["omega_S_mapped"] = wing_df["closest_centerline_index"].map(centerline_df["omega_S"])

    def compute_delta_A(row):
        delta_S = row["delta_S_mapped"]
        distance_vector = row["distance_vector"]
        omega_S = row["omega_S_mapped"]
        cross_product = np.cross(distance_vector, omega_S)
        return delta_S + cross_product

    wing_df["delta_A"] = wing_df.apply(compute_delta_A, axis=1)
    wing_df["x_new"] = wing_df.apply(lambda row: row["x"] + row["delta_A"][0], axis=1)
    wing_df["y_new"] = wing_df.apply(lambda row: row["y"] + row["delta_A"][1], axis=1)
    wing_df["z_new"] = wing_df.apply(lambda row: row["z"] + row["delta_A"][2], axis=1)

    wing_df["y_new_round"] = wing_df['y_new'].apply(lambda x: round(x, 8))

    def calculate_angle(v1, v2):
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        cos_theta = dot_product / (norm_v1 * norm_v2)
        angle = np.arccos(cos_theta)
        return np.degrees(angle)

    leading_edges = []
    for y_val, group in wing_df.groupby('y_new_round'):
        if len(group) >= 2:
            leading_edge = group.loc[group["x_new"].idxmin()]
            trailing_edge = group.loc[group["x_new"].idxmax()]

            chord_line = np.array([
                trailing_edge["x_new"] - leading_edge["x_new"],
                trailing_edge["y_new"] - leading_edge["y_new"],
                trailing_edge["z_new"] - leading_edge["z_new"]
            ])

            horizontal_vec = np.array([1, 0, 0])

            twist_angle = calculate_angle(chord_line, horizontal_vec)

            leading_edges.append(
                (leading_edge["x_new"], leading_edge["y_new"], leading_edge["z_new"], leading_edge["chord_length"], leading_edge["AoA"] + twist_angle))

    deformed_df = pd.DataFrame(leading_edges, columns=[
                               "x_leading", "y_leading", "z_leading", "chord", "AoA"])
    # deformed_df["x_leading"] -= deformed_df["x_leading"].min()

    max_y_new = wing_df["y_new_round"].max()
    tip_points = wing_df.query("y_new_round == @max_y_new")[["x_new", "y_new", "z_new"]].to_numpy()

    return centerline_df, deformed_df, tip_points


def plot_convergence(tip_deflection, res, wkdir):
    iter_vec = np.arange(1, len(tip_deflection) + 1, 1)
    fig, axs = plt.subplots(1, 2)
    axs[0].plot(iter_vec, tip_deflection, '-o')
    axs[0].set_xlabel('Iteration')
    axs[0].set_ylabel('$\delta_z$ [m]')
    axs[0].set_title("Wing tip deflection")

    axs[1].plot(iter_vec[1:], res[1:], '-o')
    axs[1].set_xlabel('Iteration')
    axs[1].set_ylabel('Residual')
    axs[1].set_yscale('log')
    axs[1].set_title("Residual of deflection")

    fig.tight_layout()
    fig.savefig(Path(wkdir, "deflection_convergence.png"))

    # =================================================================================================
    #    MAIN
    # =================================================================================================
if __name__ == "__main__":

    log.info("Nothing to execute!")
