"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

    Test functions for 'lib/SkinFriction/skinfriction.py'

    Works with Python 2.7/3.4
    Author : Aidan Jungo
    Creation: 2019-07-17
    Last modifiction: 2019-07-23

    TODO:  - change 'assertEqual' by something like approximately equal...???
           -

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import unittest

from lib.utils.ceasiomlogger import get_logger
from lib.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi, get_value
from lib.SkinFriction.skinfriction import get_largest_wing_dim, \
                                          estimate_skin_friction_coef, \
                                          add_skin_friction

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   CLASSES
#==============================================================================

class SkinFriction(unittest.TestCase):
    """
    Unit test of Tixi Function from the module 'skinfriction.py'

    ATTRIBUTES
    (unittest)            unittest.TestCase

    METHODS
    test_euler2fix        Test 'test_euler2fix' function
    test_fix2euler        Test 'test_fix2euler' function

    """

    # Default CPACS file to test
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    CPACS_IN_PATH = MODULE_DIR + '/ToolInput/D150_AGILE_Hangar_v3.xml'
    CPACS_OUT_PATH = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    def test_get_largest_wing_dim(self):
        """Test function 'get_largest_wing_dim' """

        tixi = open_tixi(self.CPACS_IN_PATH)
        tigl = open_tigl(tixi)

        wing_area_max, wing_span_max = get_largest_wing_dim(tixi,tigl)

        self.assertEqual(wing_area_max, 122.32551815387066)
        self.assertEqual(wing_span_max, 33.91371055721875)

    def test_estimate_skin_friction_coef(self):
        """Test function 'estimate_skin_friction_coef' """

        # Test 1
        wetted_area = 1
        wing_area = 1
        wing_span = 1
        speed = 1
        alt = 1

        cd0 = estimate_skin_friction_coef(wetted_area,wing_area,wing_span, \
                                          speed,alt)
        self.assertEqual(cd0, 0.006545561619853559)

        # Test 2, with "real values"
        tixi = open_tixi(self.CPACS_IN_PATH)
        tigl = open_tigl(tixi)
        analysis_xpath = '/cpacs/toolspecific/CEASIOMpy/geometry/analysis'
        wetted_area = get_value(tixi,analysis_xpath + '/wettedArea')
        wing_area, wing_span = get_largest_wing_dim(tixi,tigl)
        speed = 272
        alt = 12000

        cd0 = estimate_skin_friction_coef(wetted_area,wing_area,wing_span, \
                                          speed,alt)
        self.assertEqual(cd0, 0.01897576059542221)


    def test_add_skin_friction(self):
        """Test function 'add_skin_friction' """

        add_skin_friction(self.CPACS_IN_PATH, self.CPACS_OUT_PATH)

        tixi = open_tixi(self.CPACS_OUT_PATH)
        cd0_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/cd0'
        cd0_to_check = tixi.getDoubleElement(cd0_xpath)
        self.assertEqual(cd0_to_check, 0.0189758)



        #self.assertEqual(fix_angle.z, 90.0)


#==============================================================================
#   FUNCTIONS
#==============================================================================


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running Test Math Functions')
    unittest.main()
