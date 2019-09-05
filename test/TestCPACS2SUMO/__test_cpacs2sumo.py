"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test the module CPACS2SUMO (lib/CPACS2SUMO/cpacs2sumo.py')

Python version: >=3.6


| Author : Aidan Jungo
| Creation: 2018-10-26
| Last modifiction: 2019-08-07

TODO:

    * Finish this test module
    * Explaine the test procedure with "Load overlay geometry"

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import unittest

import pytest

from ceasiompy.CPACS2SUMO.cpacs2sumo import convert_cpacs_to_sumo
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

yes_list = ['YES','Yes','yes','Y','y','1']

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def test_cpacs2sumo():
    """Test convertion of several CPACS file into SUMO file. This function has
       some manual testing to performed, it must be completed with more
       explanations."""

    # CEASIOMPY_DIR
    CPACS_TEST_FOLDER = os.getcwd() + '/../CPACSfiles/'
    SUMO_OUTPUT_PATH = os.getcwd() \
                       + '/../../lib/CPACS2SUMO/ToolOutput/ToolOutput.smx'

    # Get list of CPACS file to test
    cpacs_test_list = os.listdir(CPACS_TEST_FOLDER)

    # For each CPACS file, convert it, using "convert_cpacs_to_sumo", then
    # open it in SUMO to see the results and compare it with the STEP file.
    for cpacs_file in cpacs_test_list:
        cpacs_path = CPACS_TEST_FOLDER + cpacs_file
        print("========")
        print(cpacs_path)
        convert_cpacs_to_sumo(cpacs_path)
        os.system('sumo ' + SUMO_OUTPUT_PATH)

        # TODO: Export step file from cpacs and explain the procedure
        answer = input("Is this file seems OK? ")
        assert answer in yes_list


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running Test CPACS2SUMO module')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
