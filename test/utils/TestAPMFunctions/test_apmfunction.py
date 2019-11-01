"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test all the function for 'lib/utils/apmfunctions.py'

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2019-08-27
| Last modifiction: 2019-11-01

TODO:

    * Create test functions when apmfunctions are finalised

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import shutil

import pytest
from pytest import raises

from tixi3.tixi3wrapper import Tixi3Exception
from tigl3.tigl3wrapper import Tigl3Exception

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                     add_uid, get_value, get_value_or_default, \
                                     create_branch, copy_branch, aircraft_name,\
                                     add_float_vector, get_float_vector,       \
                                     add_string_vector, get_string_vector

from ceasiompy.utils.apmfunctions import AeroCoefficient, get_aeromap_uid_list,\
                                         create_empty_aeromap, check_aeromap,  \
                                         save_parameters, save_coefficients,   \
                                         get_aeromap, merge_aeroMap,           \
                                         aeromap_from_csv, aeromap_to_csv,     \
                                         delete_aeromap

log = get_logger(__file__.split('.')[0])

# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH = os.path.join(MODULE_DIR,'ToolInput','simpletest_cpacs.xml')
CPACS_OUT_PATH = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

#==============================================================================
#   CLASSES
#==============================================================================

# Test AeroCoefficient Class ???

#==============================================================================
#   FUNCTIONS
#==============================================================================

# def test_create_empty_aeromap():
#     """Test the function 'create_empty_aeromap'"""
#
#     # Create TIXI handles for a valid CPACS file
#     tixi_handle = open_tixi(CPACS_IN_PATH)


# def test_get_aeromap_uid_list():
#     """Test the function 'get_aeromap_uid_list'"""
#
#     # Create TIXI handles for a valid CPACS file
#     tixi = open_tixi(CPACS_IN_PATH)
#
#     # Raise error for an invalid CPACS path
#     with pytest.raises(ValueError):
#         get_aeromap_uid_list(tixi, xpath)

def test_aeromap_from_csv():
    """Test the function 'aeromap_from_csv'"""

    tixi = open_tixi(CPACS_IN_PATH)

    aeromap_uid = 'test_aeromap'
    csv_path = 'ToolInput/Aeromap_test.csv'
    aeromap_from_csv(tixi, aeromap_uid, csv_path)

    AeroCoef = get_aeromap(tixi, aeromap_uid)

    assert AeroCoef.get_count() == 24

    for i in range(12):
        assert AeroCoef.alt[i] == 0
    for j in range(12,24):
        print(i)
        assert AeroCoef.alt[j] == 12000

    # Is is useful to test all the value?


# def test_check_aeromap():
    """ Test the function 'check_aeromap'"""


# def test_get_aeromap ():
    """ Test the function 'get_aeromap'"""


# def test_save_parameters():
    """ Test the function 'save_parameters'"""


# def test_save_coefficients():
    """ Test the function 'save_coefficients'"""


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running Test APM Functions')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
    log.info('or')
    log.info('>> pytest -vs  (for more details)')
