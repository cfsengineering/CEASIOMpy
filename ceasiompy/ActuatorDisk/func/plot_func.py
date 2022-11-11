"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This the function created by University of Naples Federico II and adepted for Ceasiompy to generate
a file .dat with thrust coefficient distribution

Python version: >=3.8

| Author: Giacomo Benedetti
| Creation: 2022-11-03

TODO:

"""
# =================================================================================================
#   IMPORTS
# =================================================================================================

import pylab as pl
from ceasiompy.utils.ceasiompyutils import get_results_directory
from pathlib import Path

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def function_plot(
    r,
    dCt_optimal,
    dCp,
    non_dimensional_radius,
    optimal_axial_interference_factor,
    optimal_rotational_interference_factor,
    prandtl,
    correction_function,
):
    "Function to save plot in result folder"

    results_dir = get_results_directory("ActuatorDisk")
    interference_plot_path = Path(results_dir, "interference_plot.png")
    ct_cp_distr_plot_path = Path(results_dir, "ct_cp_distr.png")
    prandtl_correction_plot_path = Path(results_dir, "prandtl_correction_plot.png")

    f1 = pl.figure(1)
    pl.plot(r, dCt_optimal, "r", markersize=4, label="$\\frac{dCT}{d\overline{r}}$")
    pl.plot(r, dCp, "k", markersize=4, label="$\\frac{dCP}{d\overline{r}}$")
    pl.grid(True)
    pl.legend(numpoints=3)
    pl.xlabel("$\overline{r}$")
    pl.ylabel("$dC_t$,  $dC_p$")
    pl.title("Load Distribution")

    f1.savefig(ct_cp_distr_plot_path)

    f2 = pl.figure(2)
    pl.plot(
        non_dimensional_radius,
        optimal_axial_interference_factor,
        "r",
        markersize=4,
        label="$a$",
    )
    pl.plot(
        non_dimensional_radius,
        optimal_rotational_interference_factor,
        "k",
        markersize=4,
        label="$a^1$",
    )
    pl.grid(True)
    pl.legend(numpoints=3)
    pl.xlabel("$\chi$")
    pl.ylabel("$a$, $a^1$")
    pl.title("Interference Factors")
    if prandtl:
        f3 = pl.figure(3)
        pl.plot(r, correction_function, "k", markersize=4)
        pl.grid(True)
        pl.xlabel("$\overline{r}$")
        pl.ylabel("$F(\overline{r})$")
        pl.title("Tip Loss Prandtl Correction Function")
        f3.savefig(prandtl_correction_plot_path)

    f2.savefig(interference_plot_path)
