"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/CLCalculator/clcalculator.py'

Python version: >=3.6


| Author : Aidan Jungo
| Creation: 2019-07-24
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
from ceasiompy.CLCalculator.clcalculator import calculate_cl, get_cl

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def test_calculate_cl():
    """Test function 'calculate_cl' """

    ref_area = 122
    alt = 12000
    mach = 0.78
    mass = 50000
    load_fact = 1.0

    cl = calculate_cl(ref_area,alt,mach,mass,load_fact)

    assert cl == approx(0.48602439823924726)

def test_get_cl():
    """Test function 'get_cl' """

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    CPACS_IN_PATH = MODULE_DIR + '/ToolInput/D150_AGILE_Hangar_v3.xml'
    CPACS_OUT_PATH = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    get_cl(CPACS_IN_PATH,CPACS_OUT_PATH)

    tixi = open_tixi(CPACS_OUT_PATH)
    cl_xpath = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/targetCL'

    cl_to_check = tixi.getDoubleElement(cl_xpath)
    assert cl_to_check == approx(0.794788)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running Test CL Calulator')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
