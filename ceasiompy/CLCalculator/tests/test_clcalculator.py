"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/CLCalculator/clcalculator.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2019-07-24

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os

import pytest
from pytest import approx

from ceasiompy.CLCalculator.clcalculator import calculate_cl, get_cl

from cpacspy.cpacsfunctions import open_tixi


# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH = os.path.join(MODULE_DIR, "D150_simple.xml")
CPACS_OUT_PATH = os.path.join(MODULE_DIR, "D150_simple_clcalulator_test.xml")

# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def test_calculate_cl():
    """Test function 'calculate_cl'"""

    ref_area = 122
    alt = 12000
    mach = 0.78
    mass = 50000
    load_fact = 1.0

    cl = calculate_cl(ref_area, alt, mach, mass, load_fact)

    assert cl == approx(0.48429196151547343)


def test_get_cl():
    """Test function 'get_cl'"""

    get_cl(CPACS_IN_PATH, CPACS_OUT_PATH)

    tixi = open_tixi(CPACS_OUT_PATH)
    cl_xpath = "/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/targetCL"

    cl_to_check = tixi.getDoubleElement(cl_xpath)
    assert cl_to_check == approx(0.791955)

    # Remove the output cpacs file if exist
    if os.path.exists(CPACS_OUT_PATH):
        os.remove(CPACS_OUT_PATH)


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Running Test CL Calulator")
    print("To run test use the following command:")
    print(">> pytest -v")
