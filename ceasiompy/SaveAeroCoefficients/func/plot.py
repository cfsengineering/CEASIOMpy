"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Plot Aerodynamic coefficients from CPACS v3 aeroMaps

| Author: Leon Deligny
| Creation: 27 march 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import matplotlib
import numpy as np
import matplotlib.pyplot as plt

from ceasiompy.SaveAeroCoefficients.func.utils import (
    write_legend,
    subplot_options,
)

from pathlib import Path
from typing import List

from ceasiompy import log

# =================================================================================================
#   BACKEND SETTING
# =================================================================================================

if os.environ.get('DISPLAY', '') == "":
    matplotlib.use('Agg')
else:
    matplotlib.use('TkAgg')

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def plot(wkdir: Path, groupby_list: List, title: str, aeromap, criterion) -> None:
    fig, axs = plt.subplots(2, 3)
    fig.suptitle(title, fontsize=14)
    fig.set_figheight(8)
    fig.set_figwidth(15)
    fig.subplots_adjust(left=0.06)
    axs[0, 1].axhline(y=0.0, color="k", linestyle="-")  # Line at Cm=0

    for value, grp in aeromap.loc[criterion].groupby(groupby_list):
        legend = write_legend(groupby_list, value)

        # Convert data to NumPy arrays before plotting
        angle_of_attack = np.array(grp["angleOfAttack"])
        cl = np.array(grp["cl"])
        cd = np.array(grp["cd"])
        cms = np.array(grp["cms"])
        cl_cd = cl / cd

        axs[0, 0].plot(angle_of_attack, cl, "x-", label=legend)
        axs[1, 0].plot(angle_of_attack, cd, "x-")
        axs[0, 1].plot(angle_of_attack, cms, "x-")
        axs[1, 1].plot(angle_of_attack, cl_cd, "x-")
        axs[0, 2].plot(cd, cl, "x-")
        axs[1, 2].plot(cl, cl_cd, "x-")

    subplot_options(axs[0, 0], "CL", "AoA")
    subplot_options(axs[1, 0], "CD", "AoA")
    subplot_options(axs[0, 1], "Cm", "AoA")
    subplot_options(axs[1, 1], "CL/CD", "AoA")
    subplot_options(axs[0, 2], "CL", "CD")
    subplot_options(axs[1, 2], "CL/CD", "CL")
    fig.legend(loc="upper right")

    fig_name = title.replace(" ", "").replace("=", "") + ".png"
    fig_path = Path(wkdir, fig_name)
    plt.savefig(fig_path)
    log.info(f"Figure saved at: {fig_path}")


# ==============================================================================
#    MAIN
# ==============================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
