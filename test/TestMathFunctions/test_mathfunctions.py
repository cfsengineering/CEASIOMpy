"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

    Test functions from 'lib/utils/mathfunctions.py'

    Works with Python 2.7/3.4
    Author : Aidan Jungo
    Creation: 2018-10-19
    Last modifiction: 2018-10-22

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
from lib.utils.mathfunctions import euler2fix, fix2euler

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   CLASSES
#==============================================================================


class SimpleNamespace(object):
    """ Rudimentary SimpleNamespace clone.

    Works as a record-type object, or 'struct'. Attributes can be added
    on-the-fly by assignment. Attributes are accesed using point-notation.

    https://docs.python.org/3.5/library/types.html
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        keys = sorted(self.__dict__)
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(type(self).__name__, ", ".join(items))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class MathFunctions(unittest.TestCase):
    """
    Unit test of Tixi Function from the module 'cpacsfunctions.py'

    ATTRIBUTES
    (unittest)            unittest.TestCase

    METHODS
    test_euler2fix        Test 'test_euler2fix' function
    test_fix2euler        Test 'test_fix2euler' function

    """

    def test_euler2fix(self):
        """Test convertion from Euler angles to fix angles """

        euler_angle = SimpleNamespace()

        euler_angle.x = 0
        euler_angle.y = 0
        euler_angle.z = 0
        fix_angle = euler2fix(euler_angle)
        self.assertEqual(fix_angle.x, 0.0)
        self.assertEqual(fix_angle.y, 0.0)
        self.assertEqual(fix_angle.z, 0.0)

        euler_angle.x = 50
        euler_angle.y = 32
        euler_angle.z = 65
        fix_angle = euler2fix(euler_angle)
        self.assertEqual(fix_angle.x, 49.24)
        self.assertEqual(fix_angle.y, -33.39)
        self.assertEqual(fix_angle.z, 64.58)

        euler_angle.x = -12.5
        euler_angle.y = 27
        euler_angle.z = 93
        fix_angle = euler2fix(euler_angle)
        self.assertEqual(fix_angle.x, 27.56)
        self.assertEqual(fix_angle.y, 11.12)
        self.assertEqual(fix_angle.z, 92.72)

        euler_angle.x = 90
        euler_angle.y = 90
        euler_angle.z = 90
        fix_angle = euler2fix(euler_angle)
        self.assertEqual(fix_angle.x, 90.0)
        self.assertEqual(fix_angle.y, -90.0)
        self.assertEqual(fix_angle.z, 90.0)

    def test_fix2euler(self):
        """Test convertion from fix angles to Euler angles"""

        fix_angle = SimpleNamespace()

        fix_angle.x = 0
        fix_angle.y = 0
        fix_angle.z = 0
        euler_angle = euler2fix(fix_angle)
        self.assertEqual(euler_angle.x, 0.0)
        self.assertEqual(euler_angle.y, 0.0)
        self.assertEqual(euler_angle.z, 0.0)

        fix_angle.x = 90
        fix_angle.y = 90
        fix_angle.z = 90
        euler_angle = euler2fix(fix_angle)
        self.assertEqual(euler_angle.x, 90.0)
        self.assertEqual(euler_angle.y, -90.0)
        self.assertEqual(euler_angle.z, 90.0)

        # Test by doing both transformation
        fix_angle.x = 30.23
        fix_angle.y = -85.52
        fix_angle.z = -10.98
        euler_angle = fix2euler(fix_angle)
        fix_angle2 = euler2fix(euler_angle)
        self.assertEqual(fix_angle, fix_angle2)


#==============================================================================
#   FUNCTIONS
#==============================================================================


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running Test Math Functions')
    unittest.main()
