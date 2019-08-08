"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

    Test the function 'lib/utils/standardatmosphere.py'

    Works with Python 2.7/3.4
    Author : Aidan Jungo
    Creation: 2018-10-05
    Last modifiction: 2019-08-07

    TODO:  -
           -

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys

import pytest
from pytest import approx

from lib.utils.ceasiomlogger import get_logger
from lib.utils.standardatmosphere import get_atmosphere, plot_atmosphere

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def test_get_atmosphere_error():
    """Test if 'get_atmosphere' raise an error when altitude is outside
       range (0-84000m) """

    with pytest.raises(ValueError):
        get_atmosphere(-10)

    with pytest.raises(ValueError):
        get_atmosphere(85000)

def test_get_atmosphere_0m():
    """Test atmosphere values at 0m (sea level)"""

    atm = get_atmosphere(0)

    assert atm.temp == 288.15
    assert atm.pres == 101325.0
    assert atm.dens == 1.225
    assert atm.visc == approx(1.81205671028e-05)
    assert atm.sos == approx(340.294)
    assert atm.re_len_ma == approx(23004811)
    assert atm.grav == 9.80665


def test_get_atmosphere_10000m():
    """Test atmosphere values at 10000m """

    atm = get_atmosphere(10000)

    assert atm.temp == approx(223.15)
    assert atm.pres == approx(26436.267593807635)
    assert atm.dens == approx(0.4127065373832877)
    assert atm.visc == approx(1.468841666984977e-05)
    assert atm.sos == approx(299.463)
    assert atm.re_len_ma == approx(8414143)
    assert atm.grav == approx(9.775937052994681)


def test_get_atmosphere_84000m():
    """Test atmosphere values at 84000m (max from standard atmosphere)"""

    atm = get_atmosphere(84000)

    assert atm.temp == approx(188.65)
    assert atm.pres == approx(0.4359809588843071)
    assert atm.dens == approx(8.050981206963134e-06)
    assert atm.visc == approx(1.2693534953091123e-05)
    assert atm.sos == approx(275.34263714506693)
    assert atm.re_len_ma == approx(174.6383812958875)
    assert atm.grav == approx(9.553079513419783)

#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running Test Standard Atmosphere')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
