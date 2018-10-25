"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    Test the function 'lib/utils/standardatmosphere.py'

    Works with Python 2.7/3.4
    Author : Aidan Jungo
    Creation: 2018-10-05
    Last modifiction: 2018-10-08

    TODO:  -
           -

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import unittest

from lib.utils.ceasiomlogger import get_logger
from lib.utils.standardatmosphere import get_atmosphere, plot_atmosphere

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   CLASSES
#==============================================================================


class StandardAtmosphere(unittest.TestCase):
    """
    Unit test of Tixi Function from the module 'cpacsfunctions.py'

    ATTRIBUTES
    (unittest)            unittest.TestCase

    METHODS
    test_get_atmosphere_error   Test 'get_atmosphere' outside of range
    test_get_atmosphere_0m      Test 'get_atmosphere' at 0m
    test_get_atmosphere_10000m  Test 'get_atmosphere' at 10000m
    test_get_atmosphere_84000m  Test 'get_atmosphere' at 84000m

    """

    def test_get_atmosphere_error(self):
        """Test if 'get_atmosphere' raise an error when altitude is outside
           range (0-84000m) """

        with self.assertRaises(ValueError):
            get_atmosphere(-10)

        with self.assertRaises(ValueError):
            get_atmosphere(85000)

    def test_get_atmosphere_0m(self):
        """Test atmosphere values at 0m (sea level)"""

        atm = get_atmosphere(0)

        self.assertEqual(atm.temp, 288.15)
        self.assertEqual(atm.pres, 101325.0)
        self.assertEqual(atm.dens, 1.225)
        self.assertEqual(round(atm.visc, 9), round(1.81205671028e-05, 9))
        self.assertEqual(round(atm.sos, 3), 340.294)
        self.assertEqual(round(atm.re_len_ma, 0), 23004811)
        self.assertEqual(atm.grav, 9.80665)

    def test_get_atmosphere_10000m(self):
        """Test atmosphere values at 10000m """

        atm = get_atmosphere(10000)

        self.assertEqual(round(atm.temp, 2), 223.15)
        self.assertEqual(round(atm.pres, 1), 26436.3)
        self.assertEqual(round(atm.dens, 4), 0.4127)
        self.assertEqual(round(atm.visc, 9), round(1.4688e-05, 9))
        self.assertEqual(round(atm.sos, 3), 299.463)
        self.assertEqual(round(atm.re_len_ma, 0), 8414143)
        self.assertEqual(round(atm.grav, 4), 9.7759)

    def test_get_atmosphere_84000m(self):
        """Test atmosphere values at 84000m (max from standard atmosphere)"""

        atm = get_atmosphere(84000)

        self.assertEqual(atm.temp, 188.65)
        self.assertEqual(round(atm.pres, 3), 0.436)
        self.assertEqual(round(atm.dens, 6), 8e-06)
        self.assertEqual(round(atm.visc, 9), round(1.2694e-05, 9))
        self.assertEqual(round(atm.sos, 3), 275.343)
        self.assertEqual(round(atm.re_len_ma, 0), 175)
        self.assertEqual(round(atm.grav, 4), 9.5531)


#==============================================================================
#   FUNCTIONS
#==============================================================================


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running Test Standard Atmosphere')
    unittest.main()
