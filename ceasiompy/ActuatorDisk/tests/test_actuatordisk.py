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

import numpy as np
from ceasiompy.ActuatorDisk.func.optimalprop import (
    thrust_calculator,
    adimensionalize_radius,
    axial_interference_function,
)
from ceasiompy.ActuatorDisk.func.plot_func import function_plot
from ceasiompy.ActuatorDisk.func.prandtl_correction import prandtl_corr
from ceasiompy.utils.ceasiompyutils import get_results_directory
from pytest import approx
import pytest
from ceasiompy.utils.ceasiompyutils import remove_file_type_in_dir

MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(MODULE_DIR, "ToolInput", "simpletest_cpacs.xml")
CPACS_OUT_PATH = Path(MODULE_DIR, "ToolOutput", "ToolOutput.xml")
ACTUATOR_DISK_PATH = Path(MODULE_DIR, "ToolOutput")

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_axial_interference():

    lagrangian_molt = np.array([0.3, 0.12, 0.05])
    adimensional_radius = np.array([0.25, 0.5, 0.75])

    calc_axial_interference = np.array([0.01699, 0.01994, 0.01689])

    axial_interference_factor = axial_interference_function(lagrangian_molt, adimensional_radius)

    assert all(axial_interference_factor) == all(calc_axial_interference)


def test_prandtl_corr():

    r = np.arange(0.1, 1, 0.09)
    correction_values = prandtl_corr(True, 2, r, 30, 0.8, 120)

    output_values = np.array(
        [
            0.73844572,
            0.71153049,
            0.68137418,
            0.64739118,
            0.6087976,
            0.56449233,
            0.51282436,
            0.45107467,
            0.37404968,
            0.26860365,
        ]
    )
    assert correction_values == approx(output_values)


def test_check_output():
    """Test function which made different test on thrust_coefficient function, the test function
    recive a vector with input parameter [stations, total_thrust_coefficient, radius,
    hub radius, advanced_ratio, free_stream_velocity, prandtl, blades_number] the function will
    give an output file to compare with given result vector
    [renard_thrust_coeff, power_coeff, thrust_over_density, efficiency]

    """
    input_values = {
        "test1": [[20, 0.5, 1.5, 0.2, 1.5, 150, True, 2], [0.5, 0.975, 45000, 0.7688]],
        "test2": [[20, 0.8, 1.5, 0.15, 2, 190, True, 3], [0.8, 2.217, 64980, 0.7215]],
        "test3": [[20, 1, 1.2, 0.1, 1.8, 180, False, 3], [1, 2.5304, 57600, 0.7113]],
        "test4": [[20, 1.2, 1.4, 0.1, 1.6, 140, True, 2], [1.2, 3.6097, 72030, 0.5318]],
        "test5": [[20, 1.5, 2, 0.2, 1.8, 190, True, 8], [1.5, 5.9200, 267407.41, 0.4560]],
        "test6": [[20, 0.2, 1.4, 0.1, 1.4, 130, True, 2], [0.2, 0.3148, 13520, 0.8892]],
        "test7": [[20, 0.15, 1.4, 0.1, 1.3, 130, True, 2], [0.15, 0.2149, 11760, 0.9071]],
        "test8": [[20, 1.3, 1.7, 0.5107, 1.7, 160, False, 6], [1.3, 3.5762, 133120, 0.6179]],
        "test9": [
            [37, 0.15, 2.5146, 0.2, 2.81487, 190.5488, False, 6],
            [0.15, 0.4368, 17385.4054, 0.9673],
        ],
    }

    for values in input_values.values():

        (
            renard_thrust_coeff,
            power_coeff,
            thrust_over_density,
            efficiency,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
            _,
        ) = thrust_calculator(*values[0])

        assert renard_thrust_coeff == approx(values[1][0], rel=1e-3)
        assert power_coeff == approx(values[1][1], rel=1e-3)
        assert thrust_over_density == approx(values[1][2], rel=1e-3)
        assert efficiency == approx(values[1][3], rel=1e-3)


def test_file_exist():

    results_dir = get_results_directory("ActuatorDisk")
    actuator_disk_dat_path = Path(results_dir, "ActuatorDisk.dat")

    if actuator_disk_dat_path.exists():
        actuator_disk_dat_path.unlink()

    thrust_calculator(20, 0.5, 1.5, 0.15, 1.5, 150, True, 2)

    assert actuator_disk_dat_path.exists()

    with actuator_disk_dat_path.open("r") as f:
        lines = f.readlines()

    assert lines[0] == "# Automatic generated actuator disk input data file using\n"
    assert lines[-8] == "1.0000000     0.0000000      0.0000000     0.0\n"


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
    ) = thrust_calculator(37, 0.15, 2.5146, 0.2, 2.81487, 190.5488, True, 6)

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


def test_adimentional_radius():
    with pytest.raises(ValueError):
        adimensionalize_radius(1, 1.1, 11)
    np.testing.assert_almost_equal(adimensionalize_radius(1, 0.1, 11), (np.arange(0.1, 1.1, 0.1)))
    np.testing.assert_almost_equal(adimensionalize_radius(1, 0.5, 11), (np.arange(0.5, 1.05, 0.1)))
    np.testing.assert_almost_equal(
        adimensionalize_radius(1, 0.11, 11), (np.arange(0.2, 1.05, 0.1))
    )


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test ActuatorDisk")
    print("To run test use the following command:")
    print(">> pytest -v")
