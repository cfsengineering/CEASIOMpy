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


def test_axial_interference():

    lagrangian_molt = np.array([0.3, 0.12, 0.05])
    adimensional_radius = np.array([0.25, 0.5, 0.75])

    calc_axial_interference = np.array([0.01699, 0.01994, 0.01689])

    axial_interference_factor = axial_interference_function(lagrangian_molt, adimensional_radius)

    assert all(axial_interference_factor) == all(calc_axial_interference)


def test_check_output():

    stations = np.array([20, 20, 20, 20, 20, 20, 20, 20])
    total_thrust_coefficient = np.array([0.5, 0.8, 1, 1.2, 1.5, 0.2, 0.15])
    radius = np.array([1.5, 1.5, 1.2, 1.4, 2, 1.4, 1.4, 1.7])
    hub_radius = np.array([0.2, 0.15, 0.1, 0.1, 0.2, 0.1, 0.1, 0.2])
    advanced_ratio = np.array([1.5, 2, 1.8, 1.6, 1.8, 1.4, 1.3, 1.7])
    free_stream_velocity = np.array([150, 190, 180, 140, 190, 130, 130, 160])
    prandtl = np.array([True, True, True, True, True, True, True, True])
    blade_nb = np.array([2, 3, 3, 2, 8, 2, 2, 6])

    calc_renard_thrust_coeff = np.array(
        [0.5, 0.8, 1, 1.2, 1.5, 0.2, (approx(0.15, rel=1e-2)), 1.3]
    )
    calc_power_coeff = np.array(
        [
            (approx(0.9621, rel=1e-2)),
            (approx(2.1758, rel=1e-2)),
            (approx(2.7597, rel=1e-2)),
            (approx(3.4587, rel=1e-2)),
            (approx(5.4348, rel=1e-2)),
            (approx(0.313, rel=1e-2)),
            (approx(0.2139, rel=1e-2)),
            (approx(3.9936, rel=1e-2)),
        ]
    )
    calc_thrust_over_density = np.array(
        [
            (approx(45000, rel=1e-2)),
            (approx(64980, rel=1e-2)),
            (approx(57600, rel=1e-2)),
            (approx(72030, rel=1e-2)),
            (approx(267407.41, rel=1e-2)),
            (approx(13520, rel=1e-2)),
            (approx(11760, rel=1e-2)),
            (approx(133120, rel=1e-2)),
        ]
    )
    calc_efficiency = np.array(
        [
            (approx(0.7794, rel=1e-2)),
            (approx(0.7354, rel=1e-2)),
            (approx(0.6523, rel=1e-2)),
            (approx(0.5551, rel=1e-2)),
            (approx(0.4968, rel=1e-2)),
            (approx(0.8945, rel=1e-2)),
            (approx(0.9115, rel=1e-2)),
            (approx(0.5534, rel=1e-2)),
        ]
    )

    for i in range(7):

        (renard_thrust_coeff, power_coeff, thrust_over_density, efficiency) = thrust_calculator(
            stations[i],
            total_thrust_coefficient[i],
            radius[i],
            hub_radius[i],
            advanced_ratio[i],
            free_stream_velocity[i],
            prandtl[i],
            blade_nb[i],
        )

        assert renard_thrust_coeff == calc_renard_thrust_coeff[i]
        assert power_coeff == calc_power_coeff[i]
        assert thrust_over_density == calc_thrust_over_density[i]
        assert efficiency == calc_efficiency[i]


def test_file_generation():

    thrust_calculator(20, 0.5, 1.5, 0.15, 1.5, 150, True, 2)

    results_dir = get_results_directory("ActuatorDisk")
    actuator_disk_dat_path = Path(results_dir, "ActuatorDisk.dat")
    assert actuator_disk_dat_path.exists()

    with actuator_disk_dat_path.open("r") as f:
        lines = f.readlines()

    assert lines[0] == "# Automatic generated actuator disk input data file\n"


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test ActuatorDisk")
    print("To run test use the following command:")
    print(">> pytest -v")
