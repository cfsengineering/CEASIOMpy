"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions from 'lib/utils/mathfunctions.py'

| Author : Aidan Jungo
| Creation: 2018-10-19

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pytest import approx
from ceasiompy.utils.mathsfunctions import (
    euler2fix,
    fix2euler,
)

from ceasiompy.utils.generalclasses import Point

from ceasiompy import log

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_euler2fix():
    """Test convertion from Euler angles to fix angles"""

    euler_angle = Point()

    euler_angle.x = 0
    euler_angle.y = 0
    euler_angle.z = 0
    fix_angle = euler2fix(euler_angle)

    assert fix_angle.x == approx(0.0)
    assert fix_angle.y == approx(0.0)
    assert fix_angle.z == approx(0.0)

    euler_angle.x = 135
    euler_angle.y = 99
    euler_angle.z = -30
    fix_angle = euler2fix(euler_angle)
    assert fix_angle.x == approx(98.045944)
    assert fix_angle.y == approx(-14.5532525)
    assert fix_angle.z == approx(83.4377462)

    euler_angle.x = 50
    euler_angle.y = 32
    euler_angle.z = 65
    fix_angle = euler2fix(euler_angle)
    assert fix_angle.x == approx(64.580333)
    assert fix_angle.y == approx(-33.388795)
    assert fix_angle.z == approx(49.2418955)


def test_fix2euler():
    """Test convertion from fix angles to Euler angles"""

    fix_angle = Point()

    # Test by doing both transformation
    fix_angle.x = 30.23
    fix_angle.y = -85.52
    fix_angle.z = -10.98
    euler_angle = fix2euler(fix_angle)
    fix_angle2 = euler2fix(euler_angle)

    assert fix_angle.x == approx(fix_angle2.x)
    assert fix_angle.y == approx(fix_angle2.y)
    assert fix_angle.z == approx(fix_angle2.z)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Running Test Math Functions")
    log.info("To run test use the following command:")
    log.info(">> pytest -v")
