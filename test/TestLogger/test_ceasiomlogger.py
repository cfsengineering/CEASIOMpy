"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    Test  for 'ceasiomlogger.py' function

    Works with Python 2.7/3.4
    Author : Aidan Jungo
    Creation: 2018-09-27
    Last modifiction: YEAR-MONTH-DAY

    TODO:  -
           -

"""

#===============================================================================
#   IMPORTS
#===============================================================================

import os
import sys
import unittest

from lib.utils.ceasiomlogger import get_logger

# Delete the log file if exist, to simplify the test
if os.path.exists('testlogger.log'):
    os.remove('testlogger.log')

# Set logger name and create a logger with this name
logger_name = __file__.split('.')[0]
log = get_logger(logger_name)
logger_file_name = logger_name + '.log'

#===============================================================================
#   CLASSES
#===============================================================================

class LoggerTest(unittest.TestCase):
    """
    Description of the class

    ATTRIBUTES
    (interger)      arg1            -- Argument 1 [unit]
    (float)         arg2            -- Argument 2 [unit]

    METHODS
    test_logger            Description
    """

    def test_logger(self):
        """Test if ceasiompy logger return the correct lines on the
           log file.
        """

        # Use the 5 log level
        log.debug('Test debug')
        log.info('Test info')
        log.warning('Test warning')
        log.error('Test error')
        log.critical('Test critical')

        # Open and read (last five line of) the logfile
        with open(logger_file_name) as file:
            data = file.readlines()
        last_lines = data[-5:]

        # Set default line for each level
        debug_line_default = 'DEBUG - Test debug'
        info_line_default = 'INFO - Test info'
        warning_line_default = 'WARNING - Test warning'
        error_line_default = 'ERROR - Test error'
        critical_line_default = 'CRITICAL - Test critical'

        # Check if default line of each level are in the logfile
        self.assertIn(debug_line_default, last_lines[0])
        self.assertIn(info_line_default, last_lines[1])
        self.assertIn(warning_line_default, last_lines[2])
        self.assertIn(error_line_default, last_lines[3])
        self.assertIn(critical_line_default, last_lines[4])


#===============================================================================
#   FUNCTIONS
#===============================================================================


#===============================================================================
#    MAIN
#===============================================================================

if __name__ == '__main__':

    unittest.main()
