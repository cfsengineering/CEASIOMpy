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

from ceasiompy.ActuatorDisk.func.optimalprop import optimal_prop
from ceasiompy.ActuatorDisk.func.optimalprop import axial_interference_factor_distribution


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

    axial_interference_factor = axial_interference_factor_distribution(0.12, 0.5)

    assert axial_interference_factor == approx(0.0237)


def test_check_output():

    renard_thrust_coeff, power_coeff, thrust_over_density, efficiency = optimal_prop(
        10,
        0.5,
        1.5,
        0.2,
        1.5,
        150,
        True,
        2,
    )

    assert renard_thrust_coeff == 0.5
    assert power_coeff == approx(0.974)
    assert thrust_over_density == 45000
    assert efficiency == approx(0.7699)


def test_file_generation():

    actuator_disk_path = "../ActuatorDisk.dat"
    exist_actuator_disk_path = Path.exists(actuator_disk_path)
    assert exist_actuator_disk_path == True


def test_value_generation():

    actuator_disk_path = "../ActuatorDisk.dat"
    a = Path.read_text(actuator_disk_path)
    assert a == a


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test ActuatorDisk")
    print("To run test use the following command:")
    print(">> pytest -v")
