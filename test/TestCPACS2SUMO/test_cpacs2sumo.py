"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

    Test the module CPACS2SUMO (lib/CPACS2SUMO/cpacs2sumo.py')

    Works with Python 2.7/3.4
    Author : Aidan Jungo
    Creation: 2018-10-26
    Last modifiction: 2018-11-14

    TODO:  - Finish this test module
           - Explaine the test procedure with "Load overlay geometry"

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import unittest

from lib.CPACS2SUMO.cpacs2sumo import convert_cpacs_to_sumo
from lib.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   CLASSES
#==============================================================================


class CPACS2SUMO(unittest.TestCase):
    """
    Unit test of Tixi Function from the module 'cpacsfunctions.py'

    ATTRIBUTES
    (unittest)            unittest.TestCase

    METHODS
    test_euler2fix        Test 'test_euler2fix' function
    test_fix2euler        Test 'test_fix2euler' function

    """

    def test_cpacs2sumo(self):
        """Test convertion of several CPACS file into SUMO file"""

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

            check = input("OK? ")

        # TODO: relate assert to the answer from user (check)
        self.assertEqual(0.0, 0.0)


#==============================================================================
#   FUNCTIONS
#==============================================================================


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running Test CPACS2SUMO module')
    unittest.main()
