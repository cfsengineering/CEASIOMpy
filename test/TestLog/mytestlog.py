"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    Test funtion for the CEASIOMpy logger

    Works with Python 2.7/3.4
    Author : Aidan Jungo
    Creation: 2018-09-27
    Last modifiction: YEAR-MONTH-DAY

    TODO:  - Add the real test
           -

"""

#===============================================================================
#   IMPORTS
#===============================================================================

import os
import sys

print(os.getcwd)

sys.path.append('../../')
from lib.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

#===============================================================================
#   CLASSES
#===============================================================================


#===============================================================================
#   FUNCTIONS
#===============================================================================

def test_5log_level():
    """ Function to clacluate

    Function 'test_5log_level' use all the 5 level of log.

    Source : -

    INPUT
    -

    OUTPUT
    -

    """

    log.debug('Test debug')
    log.info('Test info')
    log.warning('Test warning')
    log.error('test error')
    log.critical('test critical')


#===============================================================================
#    MAIN
#===============================================================================

if __name__ == '__main__':

    test_5log_level()
