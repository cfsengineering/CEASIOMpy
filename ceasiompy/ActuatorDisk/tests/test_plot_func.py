"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/ActuatorDisk/actuatordisk.py'

Python version: >=3.8

| Author : Giacomo Benedetti
| Creation: 2022-11-03

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ceasiompy.ActuatorDisk.func.optimalprop import thrust_calculator
from ceasiompy.ActuatorDisk.func.plot_func import function_plot
from ceasiompy.utils.ceasiompyutils import get_results_directory, remove_file_type_in_dir


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_plot_exist():
    results_dir = get_results_directory("ActuatorDisk")
    interference_plot_path = Path(results_dir, "interference_plot.png")
    ct_cp_distr_plot_path = Path(results_dir, "ct_cp_distr.png")

    (
        _,
        _,
        _,
        _,
        r,
        dCt_optimal,
        dCp,
        non_dimensional_radius,
        optimal_axial_interference_factor,
        optimal_rotational_interference_factor,
        prandtl,
        correction_function,
    ) = thrust_calculator(37, 0.15, 2.5146, 0.2, 2.81487, 190.5488, True, 6, 33)

    function_plot(
        r,
        dCt_optimal,
        dCp,
        non_dimensional_radius,
        optimal_axial_interference_factor,
        optimal_rotational_interference_factor,
        prandtl,
        correction_function,
    )

    assert ct_cp_distr_plot_path.exists()
    assert interference_plot_path.exists()

    remove_file_type_in_dir(results_dir, [".png"])
