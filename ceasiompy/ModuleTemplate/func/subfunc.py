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

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================



#==============================================================================
#   FUNCTIONS
#==============================================================================

def my_subfunc(arg_a, arg_b):
    """ Function to clacluate ...

    Function 'my_subfunc' is a subfunction of ModuleTemplate which returns...

    Source:
       * Reference paper or book, with author and date

    Args:
        arg_a (str):  Argument 1
        arg_a (str): Argument 2

    Returns:
        new_arg (str): Output argument

    .. warning::

        Example of warning
    """

    new_arg = arg_a + ' and ' + arg_b

    return new_arg


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')
