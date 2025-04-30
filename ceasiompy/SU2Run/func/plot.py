"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Save plot in result folder of SU2 module.

| Author: Leon Deligny
| Creation: 2025-Feb-24

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import matplotlib

import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path

from ceasiompy import log

# =================================================================================================
#   BACKEND SETTING
# =================================================================================================

try:
    # Try to use TkAgg if DISPLAY is set and Tkinter is available
    if os.environ.get('DISPLAY', '') != "":
        matplotlib.use('TkAgg')
    else:
        matplotlib.use('Agg')
except Exception:
    # Fallback to Agg if TkAgg is not available or fails
    matplotlib.use('Agg')

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def save_plots(
    radial_stations: np.ndarray,
    radial_thrust_coefs: np.ndarray,
    radial_power_coefs: np.ndarray,
    non_dimensional_radius: float,
    optimal_axial_interference_factor: np.ndarray,
    optimal_rotational_interference_factor: np.ndarray,
    prandtl_correction_values: np.ndarray,
    case_dir_path: Path,
    propeller_uid: str,
) -> None:
    """
    Save plot in result folder.
    """

    current_dir = Path(case_dir_path, propeller_uid)
    current_dir.mkdir()
    interference_plot_path = Path(current_dir, "interference.png")
    ct_cp_distr_plot_path = Path(current_dir, "radial_thrust_and_power_coefficient.png")
    prandtl_correction_plot_path = Path(current_dir, "prandtl_correction.png")

    f1 = plt.figure(1)
    plt.plot(
        radial_stations,
        radial_thrust_coefs,
        "r",
        markersize=4,
        label=r"$\frac{dCT}{d\overline{r}}$",
    )
    plt.plot(
        radial_stations,
        radial_power_coefs,
        "k",
        markersize=4,
        label=r"$\frac{dCP}{d\overline{r}}$",
    )
    plt.grid(True)
    plt.legend()
    plt.xlabel(r"$\overline{r}$")
    plt.ylabel(r"$dC_t$,  $dC_p$")
    plt.title("Load Distribution")

    f1.savefig(ct_cp_distr_plot_path)
    plt.clf()

    f2 = plt.figure(2)
    plt.plot(
        non_dimensional_radius,
        optimal_axial_interference_factor,
        "r",
        markersize=4,
        label=r"$a$",
    )
    plt.plot(
        non_dimensional_radius,
        optimal_rotational_interference_factor,
        "k",
        markersize=4,
        label=r"$a^1$",
    )
    plt.grid(True)
    plt.legend(numpoints=3)
    plt.xlabel(r"$\frac{2\pi*r}{J}$")
    plt.ylabel(r"$a$, $a^1$")
    plt.title("Interference Factors")

    f2.savefig(interference_plot_path)
    plt.clf()

    f3 = plt.figure(3)
    plt.plot(radial_stations, prandtl_correction_values, "k", markersize=4)
    plt.grid(True)
    plt.xlabel(r"$\overline{r}$")
    plt.ylabel(r"$F(\overline{r})$")
    plt.title("Tip Loss Prandtl Correction Function")
    f3.savefig(prandtl_correction_plot_path)
    plt.clf()

    plot_msg = "A plot have been saved at "
    log.info(f"{plot_msg} {ct_cp_distr_plot_path}.")
    log.info(f"{plot_msg} {interference_plot_path}.")
    log.info(f"{plot_msg} {prandtl_correction_plot_path}.")

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
