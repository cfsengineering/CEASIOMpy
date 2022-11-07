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

    axial_interference_factor = axial_interference_function(0.12, 0.5)

    assert axial_interference_factor == approx(0.01994, rel=1e-2)


def test_check_output():

    renard_thrust_coeff, power_coeff, thrust_over_density, efficiency = thrust_calculator(
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
    assert power_coeff == approx(0.974, rel=1e-2)
    assert thrust_over_density == 45000
    assert efficiency == approx(0.7699, rel=1e-2)


def test_file_generation():

    actuator_disk_path = Path("ActuatorDisk.dat")
    assert actuator_disk_path.exists()

    with actuator_disk_path.open("r") as f:
        lines = f.readlines()
    assert lines[0] == "# Automatic generated actuator disk input data file\n"


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test ActuatorDisk")
    print("To run test use the following command:")
    print(">> pytest -v")
