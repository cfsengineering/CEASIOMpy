"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Script to plot the FEM mesh and VLM panels used in the aeroelastic computations,
and plot the shape of the deformed wing. It helps to see if the geometry was
accurately captured and if the meshes are fine.

Python version: >=3.8

| Author: Romain Gauthier
| Creation: 2024-06-19

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import matplotlib.pyplot as plt

from pathlib import Path

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def plot_fem_mesh(wing_df, centerline_df, wkdir):
    """
    Saves a plot of the VLM and FEM meshes in the x-y and y-z planes.

    Args:
        wing_df (pandas dataframe): dataframe containing the VLM nodes.
        centerline_df (pandas dataframe): dataframe containing the FEM nodes.
        wkdir (Path): path to the directory to save the plot.

    """

    fig, axs = plt.subplots(1, 2)
    axs[0].plot(centerline_df["y"], centerline_df["x"], "-o", label="FEM nodes", color="r",
                ms=1)
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


def plot_deformed_wing(centerline_df, undeformed_df, wkdir):
    """
    Saves a plot of the deformed and undeformed shapes of the wing.

    Args:
        centerline_df (DataFrame): Contains nodes of the deformed wing.
        undeformed_df (DataFrame): Contains nodes of the initial wing.
        wkdir (Path): Path to the directory to save the plot.
    """
    fig, axs = plt.subplots()
    axs.plot(centerline_df['y_new'],
             centerline_df['z_new'],
             '-o',
             label='Deformed wing',
             linewidth=2,
             color='r')

    axs.plot(undeformed_df["y"], undeformed_df["z"], '-o', label="Undeformed wing", linewidth=2)
    axs.set_xlabel('$y$ [m]')
    axs.set_ylabel('$z$ [m]', rotation=0)
    axs.set_title('Wing shape in y-z plane')
    axs.legend()
    # plt.axis('equal')

    # for index, row in centerline_df.iterrows():
    #     y, z = row['y'], row['z']
    #     Fy, Fz = row['Fy'], row['Fz']
    #     axs.quiver(y, z, Fy, Fz, angles='uv', scale=10, color='k', width=0.003)

    fig.tight_layout()
    fig.savefig(Path(wkdir, "deformed_wing.png"))


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
