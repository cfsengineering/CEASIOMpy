"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

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
import math

import numpy
import matplotlib

from lib.utils.ceasiomlogger import get_logger
from lib.utils.cpacsfunctions import open_tixi, close_tixi
from lib.utils.mathfunctions import euler2fix, fix2euler
from lib.utils.standardatmosphere import get_atmosphere, plot_atmosphere

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================

class MyClass:
    """
    Description of the class

    ATTRIBUTES
    (float)         var_a            -- Argument a [unit]
    (float)         var_b            -- Argument b [unit]

    METHODS
    add_my_var      This methode will sum up var_a and var_b in var_c
    """

    def __init__(self, a=0.0, b=0.0):
        self.var_a = a
        self.var_b = b
        self.var_c = 0.0

    def add_my_var(self):
        self.var_c = self.var_a + self.var_b


#==============================================================================
#   FUNCTIONS
#==============================================================================

def sum_funcion(arg1, arg2):
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

    my_total = sum_funcion(my_value1, my_value2)
    log.info('My total is equal to: ' + str(my_total))

    log.info('Value as been calculated')
