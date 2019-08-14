"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/ModuleTemplate/moduletemplate.py'

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2019-08-14
| Last modifiction: 2019-08-14
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
from ceasiompy.ModuleTemplate.moduletemplate import MyClass, sum_funcion, get_fuselage_scaling

log = get_logger(__file__.split('.')[0])

# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH = MODULE_DIR + '/ToolInput/simpletest_cpacs.xml'
CPACS_OUT_PATH = MODULE_DIR + '/ToolOutput/ToolOutput.xml'


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def test_MyClass():
    """Test Class 'MyClass' """

    TestClass = MyClass()

    assert TestClass.var_a == 1.1
    assert TestClass.var_b == 2.2
    assert TestClass.var_c == 0.0

    TestClass.add_my_var()
    assert TestClass.var_c == approx(3.3)


def test_sum_funcion():
    """Test function 'sum_funcion' """

    # Test Raise ValueError
    with pytest.raises(ValueError):
        sum_funcion(5.5,4.4)

    # Test 'sum_funcion' normal use
    assert sum_funcion(5,4.4) == approx(9.4)


def test_get_fuselage_scaling():
    """Test function 'get_fuselage_scaling' """

    x,y,z = get_fuselage_scaling(CPACS_IN_PATH,CPACS_OUT_PATH)

    assert x == approx(1)
    assert y == approx(0.5)
    assert z == approx(0.5)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Test ModuleTemplate')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
