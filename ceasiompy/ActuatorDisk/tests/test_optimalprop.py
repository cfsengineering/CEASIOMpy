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
import pytest
from ceasiompy.ActuatorDisk.func.optimalprop import (
    axial_interference_function,
    prandtl_corr,
    radial_stations,
    thrust_calculator,
)
from ceasiompy.utils.ceasiompyutils import get_results_directory
from pytest import approx

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
    recive a vector with input parameter [total_thrust_coefficient, radius, hub radius,
    free_stream_velocity, prandtl, blades_number, rotational_velocity]
    the function will give an output file to compare with given result vector
    [renard_thrust_coeff, power_coeff, thrust_over_density, efficiency]

    """
    input_values = {
        "test1": [[0.5, 1.5, 0.2, 150, True, 2, 33], [0.5, 0.965, 44104.5, 0.7847]],
        "test2": [[0.8, 1.5, 0.15, 0.1, True, 3, 33], [0, 0.00744, 0, 0]],
        "test3": [[1, 1.2, 0.1, 180, False, 3, 33], [1, 3.010, 36130.40, 0.7549]],
        "test4": [[1.2, 1.4, 0.1, 140, True, 2, 33], [1.2, 3.299, 80323.24, 0.55097]],
        "test5": [[1.5, 2, 0.2, 190, True, 8, 33], [1.5, 4.6177, 418175.999, 0.4675]],
        "test6": [[0.2, 1.4, 0.1, 130, True, 2, 33], [0.2, 0.3138, 13387.20, 0.8966]],
        "test7": [[0.15, 1.4, 0.1, 130, True, 2, 33], [0.15, 0.2292, 10040.4057, 0.92068]],
        "test8": [[1.2, 1.7, 0.5107, 160, False, 6, 22], [1.199, 3.7025, 77614.39, 0.6932]],
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

    thrust_calculator(0.5, 1.5, 0.15, 150, True, 2, 33)

    assert actuator_disk_dat_path.exists()

    with actuator_disk_dat_path.open("r") as f:
        lines = f.readlines()

    assert lines[0] == "# Automatic generated actuator disk input data file using\n"
    assert lines[-1] == "1.0000000     0.0000000      0.0000000     0.0\n"


def test_adimentional_radius():
    with pytest.raises(ValueError):
        radial_stations(1, 1.1)
    np.testing.assert_almost_equal(radial_stations(1, 0.1), (np.arange(0.1, 1.02, 0.025)))
    np.testing.assert_almost_equal(radial_stations(1, 0.5), (np.arange(0.5, 1.02, 0.025)))
    np.testing.assert_almost_equal(radial_stations(1, 0.2), (np.arange(0.2, 1.02, 0.025)))


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test ActuatorDisk")
    print("To run test use the following command:")
    print(">> pytest -v")
