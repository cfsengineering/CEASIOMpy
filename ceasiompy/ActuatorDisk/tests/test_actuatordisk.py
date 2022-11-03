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

import os
import pytest
from ceasiompy.ActuatorDisk.func.optimalprop import optimal_prop
from ceasiompy.ActuatorDisk.actuatordisk import write_actuator_disk
from ceasiompy.utils.ceasiompyutils import get_results_directory

from pytest import approx

MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(MODULE_DIR, "ToolInput", "simpletest_cpacs.xml")
CPACS_OUT_PATH = Path(MODULE_DIR, "ToolOutput", "ToolOutput.xml")


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


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


# def test_sum_funcion():
#    """Test function 'sum_funcion'"""
#
#    # Test Raise ValueError
#    with pytest.raises(ValueError):
#        sum_funcion(5.5, 4.4)
#
#    # Test 'sum_funcion' normal use
#    assert sum_funcion(5, 4.4) == approx(9.4)
#
#
# def test_get_fuselage_scaling():
#    """Test function 'get_fuselage_scaling'"""
#
#    x, y, z = get_fuselage_scaling(CPACS_IN_PATH, CPACS_OUT_PATH)
#
#    assert x == approx(1)
#    assert y == approx(0.5)
#    assert z == approx(0.5)
#
#
# def test_subfunc():
#    """Test subfunction 'my_subfunc'"""
#
#    a = "a"
#    b = "b"
#
#    res = my_subfunc(a, b)
#
#    assert res == "a and b"


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test ActuatorDisk")
    print("To run test use the following command:")
    print(">> pytest -v")
