"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/SkinFriction/skinfriction.py'

Python version: >=3.6


| Author : Aidan Jungo
| Creation: 2019-07-17
| Last modifiction: 2021-10-13
"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import sys

import pytest
from pytest import approx

from cpacspy.cpacspy import CPACS

from ceasiompy.SkinFriction.skinfriction import estimate_skin_friction_coef, add_skin_friction

# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH = os.path.join(MODULE_DIR, "D150_simple_SkinFriction_test.xml")
CPACS_OUT_PATH = os.path.join(MODULE_DIR, "D150_simple_skinfriction_test_output.xml")

# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def test_estimate_skin_friction_coef():
    """Test function 'estimate_skin_friction_coef'"""

    # {cd0:[wetted_area,wing_area,wing_span,mach,alt]}
    test_dict = {
        0.005308238904488722: [1, 1, 1, 1, 1],
        0.021046702729598663: [701.813, 100, 20, 0.78, 12000],
        0.00655: [1, 1, 1, 0, 0],
    }

    for cd0, inputs in test_dict.items():
        assert cd0 == approx(estimate_skin_friction_coef(*inputs))


def test_add_skin_friction():
    """Test function 'add_skin_friction'"""

    # User the function to add skin frictions
    add_skin_friction(CPACS_IN_PATH, CPACS_OUT_PATH)

    # Read the aeromap with the skin friction added in the output cpacs file
    cpacs = CPACS(CPACS_OUT_PATH)
    apm_sf = cpacs.get_aeromap_by_uid("test_apm_SkinFriction")

    # Expected values
    cl_list_expected = [0.1, 0.102944, 0.1, 0.102944]
    cd_list_expected = [0.0269518, 0.0266942, 0.0266942, 0.0264406]
    cs_list_expected = [0.001, 0.001, 0.00394364, 0.00394364]

    assert all([a == approx(b, rel=1e-4) for a, b in zip(apm_sf.get("cl"), cl_list_expected)])
    assert all([a == approx(b, rel=1e-4) for a, b in zip(apm_sf.get("cd"), cd_list_expected)])
    assert all([a == approx(b, rel=1e-4) for a, b in zip(apm_sf.get("cs"), cs_list_expected)])

    # Remove the output cpacs file if exist
    if os.path.exists(CPACS_OUT_PATH):
        os.remove(CPACS_OUT_PATH)


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Test SkinFriction")
    print("To run test use the following command:")
    print(">> pytest -v")
