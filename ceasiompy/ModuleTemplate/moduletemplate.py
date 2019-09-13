"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

Python version: >=3.6

| Author: Name
| Creation: YEAR-MONTH-DAY
| Last modifiction: YEAR-MONTH-DAY

TODO:

    * Things to improve ...
    * Things to add ...
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import numpy
import matplotlib

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           add_uid, create_branch, copy_branch,\
                                           get_value, get_value_or_default,    \
                                           aircraft_name
from ceasiompy.utils.mathfunctions import euler2fix, fix2euler
from ceasiompy.utils.standardatmosphere import get_atmosphere, plot_atmosphere
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================

class MyClass:
    """
    Description of the class

    Attributes:
        var_a (float): Argument a [unit]
        var_b (float): Argument b [unit]

    .. seealso::

        See some other source

    """

    def __init__(self, a=1.1, b=2.2):
        self.var_a = a
        self.var_b = b
        self.var_c = 0.0

    def add_my_var(self):
        """This methode will sum up var_a and var_b in var_c"""

        self.var_c = self.var_a + self.var_b


#==============================================================================
#   FUNCTIONS
#==============================================================================

def sum_funcion(arg1, arg2):
    """ Function to clacluate ...

    Function 'sum_funcion' return the tolal of arg1 and arg2, after it convert
    arg1 into an float.

    Source:
       * Reference paper or book, with author and date

    Args:
        arg1 (interger):  Argument 1 [unit]
        arg2 (float): Argument 2 [unit]

    Returns:
        total (float): Output1 [unit]

    .. warning::

        Example of warning
    """

    if not isinstance(arg1, int):
        raise ValueError('arg1 is not an integer')

    total = float(arg1) + arg2

    return total


def get_fuselage_scaling(cpacs_path, cpacs_out_path):
    """Function to get fuselage scaling along x,y,z axis.

    Function 'get_fuselage_scaling' return the value of the scaling for the
    fuselage. (This is an example function just to show usaga of CPACS and tixi)

    Source:
        * Reference paper or book, with author and date

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file

    Returns:
        Tuple with fuselage scaling

        * x (float): Scaling on x [-]
        * y (float): Scaling on y [-]
        * z (float): Scaling on z [-]
    """

    # Open TIXI handle
    tixi = open_tixi(cpacs_path)

    # Create xpaths
    FUSELAGE_XPATH = '/cpacs/vehicles/aircraft/model/fuselages/fuselage'
    SCALING_XPATH = '/transformation/scaling'

    x_fus_scaling_xpath = FUSELAGE_XPATH + SCALING_XPATH + '/x'
    y_fus_scaling_xpath = FUSELAGE_XPATH + SCALING_XPATH + '/y'
    z_fus_scaling_xpath = FUSELAGE_XPATH + SCALING_XPATH + '/z'

    # Get values
    x = get_value(tixi, x_fus_scaling_xpath)
    y = get_value(tixi, y_fus_scaling_xpath)
    z = get_value(tixi, z_fus_scaling_xpath)

    # Log
    log.info('Fuselage x scaling is : ' + str(x))
    log.info('Fuselage y scaling is : ' + str(y))
    log.info('Fuselage z scaling is : ' + str(z))

    # Close TIXI handle and save the CPACS file
    close_tixi(tixi, cpacs_out_path)

    return x, y, z

#==============================================================================
#    MAIN
#==============================================================================


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = MODULE_DIR + '/ToolInput/ToolInput.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'

    # Call the function which check if imputs are well define
    check_cpacs_input_requirements(cpacs_path)

    # Define other inputs value
    my_value1 = 6
    my_value2 = 5.5

    # Call 'sum_function'
    my_total = sum_funcion(my_value1, my_value2)
    log.info('My total is equal to: ' + str(my_total))

    # Call a function which use CPACS inputs
    x, y, z = get_fuselage_scaling(cpacs_path, cpacs_out_path)
    log.info('Value x,y,z as been calculated')
    log.info('x = ' + str(x))
    log.info('y = ' + str(y))
    log.info('z = ' + str(z))

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
