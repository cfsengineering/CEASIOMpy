"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    Small description of the script

    Works with Python 2.7/3.4
    Author : Name
    Creation: YEAR-MONTH-DAY
    Last modifiction: YEAR-MONTH-DAY

    TODO:  -
           -

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys

from lib.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================

class MyClass:
    """
    Description of the class

    ATTRIBUTES
    (interger)      arg1            -- Argument 1 [unit]
    (float)         arg2            -- Argument 2 [unit]

    METHODS
    Name            Description
    """



#==============================================================================
#   FUNCTIONS
#==============================================================================

def sum_funcion(arg1,arg2):
    """ Function to clacluate ...

    Function 'sum_funcion' return the tolal of arg1 and arg2, after it convert
    arg1 into an float.

    Source : Reference paper or book, with author and date

    ARGUMENTS
    (interger)      arg1            -- Argument 1 [unit]
    (float)         arg2            -- Argument 2 [unit]

    RETURNS
    (float)         total          -- output1 [unit]
    """

    total = float(arg1) + arg2

    return total

#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':


    log.info('Running Mymodule')

    my_value1 = 6
    my_value2 = 5.5

    my_total = sum_funcion(value1,value2)

    log.info('Value as been calculated')
