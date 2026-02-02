"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to plot the FEM mesh and VLM panels used in the aeroelastic computations,
and plot the shape of the deformed wing. It helps to see if the geometry was
accurately captured and if the meshes are fine.

| Author: Romain Gauthier
| Creation: 2024-06-19

"""

# Imports

import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from pandas import DataFrame

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def plot_fem_mesh(
    wing_df: DataFrame,
    centerline_df: DataFrame,
    wkdir: Path,
) -> None:
    """
    Saves a plot of the VLM and FEM meshes in the x-y and y-z planes.

    Args:
        wing_df (pandas dataframe): dataframe containing the VLM nodes.
        centerline_df (pandas dataframe): dataframe containing the FEM nodes.
        wkdir (Path): path to the directory to save the plot.

    """

    fig, axs = plt.subplots(1, 2)
    axs[0].plot(centerline_df["y"], centerline_df["x"], "-o", label="FEM nodes", color="r", ms=1)
    axs[0].scatter(wing_df["y"], wing_df["x"], s=1, label="wing panels", color="b")
    axs[0].set_xlabel("$y$")
    axs[0].set_ylabel("$x$")
    axs[0].axis("equal")
    axs[0].set_title("FEM nodes in $x-y$ plane")
    axs[0].legend()

    axs[1].plot(centerline_df["y"], centerline_df["z"], "-o", label="FEM nodes", color="r")
    axs[1].scatter(wing_df["y"], wing_df["z"], label="wing panels", color="b")
    axs[1].set_xlabel("$y$")
    axs[1].set_ylabel("$z$")
    axs[1].axis("equal")
    axs[1].set_title("FEM nodes in $y-z$ plane")

    fig.tight_layout()
    fig.savefig(Path(wkdir, "structural_mesh.png"))


def plot_deformed_wing(
    centerline_df: DataFrame,
    undeformed_df: DataFrame,
    wkdir: Path,
) -> None:
    """
    Saves a plot of the deformed and undeformed shapes of the wing.

    Args:
        centerline_df (DataFrame): Contains nodes of the deformed wing.
        undeformed_df (DataFrame): Contains nodes of the initial wing.
        wkdir (Path): Path to the directory to save the plot.
    """
    fig, axs = plt.subplots()
    axs.plot(
        centerline_df["y_new"],
        centerline_df["z_new"],
        "-o",
        label="Deformed wing",
        linewidth=2,
        color="r",
    )

    axs.plot(
        undeformed_df["y"],
        undeformed_df["z"],
        "-o",
        label="Undeformed wing",
        linewidth=2,
    )
    axs.set_xlabel("$y$ [m]")
    axs.set_ylabel("$z$ [m]", rotation=0)
    axs.set_title("Wing shape in y-z plane")
    axs.legend()
    # plt.axis('equal')

    # for index, row in centerline_df.iterrows():
    #     y, z = row['y'], row['z']
    #     Fy, Fz = row['Fy'], row['Fz']
    #     axs.quiver(y, z, Fy, Fz, angles='uv', scale=10, color='k', width=0.003)

    fig.tight_layout()
    fig.savefig(Path(wkdir, "deformed_wing.png"))


def plot_translations_rotations(centerline_df, wkdir):
    """
    Function to plot the displacements and rotations profiles along the span.

    Function 'plot_translations_rotations' saves a plot  of the displacements
    and rotations profiles along the span.

    Args:
        centerline_df (pandas dataframe): dataframe containing the displacements
                                          and rotations of the beam nodes.
        wkdir (Path): path to the directory to save the plot.

    """
    fig, axs = plt.subplots(3, 2, sharex=True)

    # Translations
    axs[0][0].plot(centerline_df["y"], centerline_df["ux"])
    axs[0][0].set_xlabel("$y$ [m]")
    axs[0][0].set_ylabel("$u_x$ [m]")

    axs[1][0].plot(centerline_df["y"], centerline_df["uy"])
    axs[1][0].set_xlabel("$y$ [m]")
    axs[1][0].set_ylabel("$u_y$ [m]")

    axs[2][0].plot(centerline_df["y"], centerline_df["uz"])
    axs[2][0].set_xlabel("$y$ [m]")
    axs[2][0].set_ylabel("$u_z$ [m]")

    # Rotations
    axs[0][1].plot(centerline_df["y"], np.rad2deg(centerline_df["thx"]))
    axs[0][1].set_xlabel("$y$ [m]")
    axs[0][1].set_ylabel("$\\theta_x~[^{\\circ}]$")

    axs[1][1].plot(centerline_df["y"], np.rad2deg(centerline_df["thy"]))
    axs[1][1].set_xlabel("$y$ [m]")
    axs[1][1].set_ylabel("$\\theta_y~[^{\\circ}]$")

    axs[2][1].plot(centerline_df["y"], np.rad2deg(centerline_df["thz"]))
    axs[2][1].set_xlabel("$y$ [m]")
    axs[2][1].set_ylabel("$\\theta_z~[^{\\circ}]$")

    fig.suptitle("Structural translations/rotations along the span.")
    fig.tight_layout()
    fig.savefig(Path(wkdir, "translations_rotations.png"))
    plt.close(fig)


def plot_convergence(tip_deflection, res, wkdir):
    """
    Function to plot the convergence of the aeroelastic computations.

    Function 'plot_convergence' saves a plot of the evolution of the
    wing tip deflection during the iterations, as well as a plot of
    the residual.

    Args:
        tip_deflection (list) : deflections of the mid-chord wing tip for each iteration [m].
        res (list): residual of the mid-chord wing tip for each iteration
        wkdir (Path): path to the directory to save the plot.

    """
    iter_vec = np.arange(1, len(tip_deflection) + 1, 1)
    fig, axs = plt.subplots(1, 2)
    axs[0].plot(iter_vec, tip_deflection, "-o")
    axs[0].set_xlabel("Iteration")
    axs[0].set_ylabel(r"$\delta_z$ [m]")
    axs[0].set_title("Wing tip deflection")

    axs[1].plot(iter_vec[1:], res[1:], "-o")
    axs[1].set_xlabel("Iteration")
    axs[1].set_ylabel("Residual")
    axs[1].set_yscale("log")
    axs[1].set_title("Residual of deflection")

    fig.tight_layout()
    fig.savefig(Path(wkdir, "deflection_convergence.png"))
