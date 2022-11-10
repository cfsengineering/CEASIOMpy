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
from ceasiompy.ActuatorDisk.func.optimalprop import axial_interference_function
import numpy as np
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


def test_file_not_exist():

    results_dir = get_results_directory("ActuatorDisk")
    actuator_disk_dat_path = Path(results_dir, "ActuatorDisk.dat")
    assert actuator_disk_dat_path.exists() == False


def test_axial_interference():

    lagrangian_molt = np.array([0.3, 0.12, 0.05])
    adimensional_radius = np.array([0.25, 0.5, 0.75])

    calc_axial_interference = np.array([0.01699, 0.01994, 0.01689])

    axial_interference_factor = axial_interference_function(lagrangian_molt, adimensional_radius)

    assert all(axial_interference_factor) == all(calc_axial_interference)


def test_check_output():
    """Test function which made different test on thrust_coefficient function, the test function
    recive a vector with input parameter [stations, total_thrust_coefficient, radius,
    hub radius, advanced_ratio, free_stream_velocity, prandtl, blades_number] the function will
    give an output file to confront with given result vector
    [renard_thrust_coeff, power_coeff, thrust_over_density, efficiency]

    """
    input_values = {
        "test1": [[20, 0.5, 1.5, 0.2, 1.5, 150, True, 2], [0.5, 0.9621, 45000, 0.7794]],
        "test2": [[20, 0.8, 1.5, 0.15, 2, 190, True, 3], [0.8, 2.1758, 64980, 0.7354]],
        "test3": [[20, 1, 1.2, 0.1, 1.8, 180, False, 3], [1, 2.4896, 57600, 0.7230]],
        "test4": [[20, 1.2, 1.4, 0.1, 1.6, 140, True, 2], [1.2, 3.4586, 72030, 0.5551]],
        "test5": [[20, 1.5, 2, 0.2, 1.8, 190, True, 8], [1.5, 5.4348, 267407.41, 0.4968]],
        "test6": [[20, 0.2, 1.4, 0.1, 1.4, 130, True, 2], [0.2, 0.313, 13520, 0.8945]],
        "test7": [[20, 0.15, 1.4, 0.1, 1.3, 130, True, 2], [0.15, 0.2139, 11760, 0.9115]],
        "test8": [[20, 1.3, 1.7, 0.2, 1.7, 160, False, 6], [1.3, 3.4596, 133120, 0.6387]],
    }

    for test, values in input_values.items():

        (renard_thrust_coeff, power_coeff, thrust_over_density, efficiency) = thrust_calculator(
            *values[0]
        )

        assert renard_thrust_coeff == approx(values[1][0], rel=1e-2)
        assert power_coeff == approx(values[1][1], rel=1e-2)
        assert thrust_over_density == approx(values[1][2], rel=1e-1)
        assert efficiency == approx(values[1][3], rel=1e-1)


def test_file_exist():

    thrust_calculator(20, 0.5, 1.5, 0.15, 1.5, 150, True, 2)

    results_dir = get_results_directory("ActuatorDisk")
    actuator_disk_dat_path = Path(results_dir, "ActuatorDisk.dat")
    assert actuator_disk_dat_path.exists()

    with actuator_disk_dat_path.open("r") as f:
        lines = f.readlines()

    assert lines[0] == "# Automatic generated actuator disk input data file using\n"
    assert lines[-1] == "  1.0000000     0.0000000     0.0000000     0.0\n"


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test ActuatorDisk")
    print("To run test use the following command:")
    print(">> pytest -v")
