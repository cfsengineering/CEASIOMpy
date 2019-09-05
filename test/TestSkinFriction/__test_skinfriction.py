"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/SkinFriction/skinfriction.py'

Python version: >=3.6


| Author : Aidan Jungo
| Creation: 2019-07-17
| Last modifiction: 2019-08-07
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys

import pytest
from pytest import approx

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi, get_value
from ceasiompy.SkinFriction.skinfriction import get_largest_wing_dim, \
                                          estimate_skin_friction_coef, \
                                          add_skin_friction

log = get_logger(__file__.split('.')[0])

# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH = MODULE_DIR + '/ToolInput/D150_AGILE_Hangar_v3.xml'
CPACS_OUT_PATH = MODULE_DIR + '/ToolOutput/ToolOutput.xml'


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def test_get_largest_wing_dim():
    """Test function 'get_largest_wing_dim' """

    tixi = open_tixi(CPACS_IN_PATH)
    tigl = open_tigl(tixi)

    wing_area_max, wing_span_max = get_largest_wing_dim(tixi,tigl)

    assert wing_area_max == approx(122.32551815387066)
    assert wing_span_max == approx(33.915185246594945)


def test_estimate_skin_friction_coef():
    """Test function 'estimate_skin_friction_coef' """

    # Test 1
    wetted_area = 1
    wing_area = 1
    wing_span = 1
    mach = 1
    alt = 1

    cd0 = estimate_skin_friction_coef(wetted_area,wing_area,wing_span,mach,alt)

    assert cd0 == approx(0.005320707210958961)

    # Test 2, with "real values"
    tixi = open_tixi(CPACS_IN_PATH)
    tigl = open_tigl(tixi)
    analysis_xpath = '/cpacs/toolspecific/CEASIOMpy/geometry/analysis'
    wetted_area = get_value(tixi,analysis_xpath + '/wettedArea')
    wing_area, wing_span = get_largest_wing_dim(tixi,tigl)
    mach = 0.78
    alt = 12000

    cd0 = estimate_skin_friction_coef(wetted_area,wing_area,wing_span,mach,alt)

    assert cd0 == approx(0.01998328842386761)


def test_add_skin_friction():
    """Test function 'add_skin_friction' """

    # TODO: improve this function to test everything

    add_skin_friction(CPACS_IN_PATH, CPACS_OUT_PATH)

    tixi = open_tixi(CPACS_OUT_PATH)
    cd0_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/skinFriction/cd0'
    cd0_to_check = tixi.getDoubleElement(cd0_xpath)

    assert cd0_to_check == approx(0.01998328842386761)

#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Test SkinFriction')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
