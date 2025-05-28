"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

| Author: Name
| Creation: day month year

TODO:

    * Things to improve ...
    * Things to add ...
"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pydantic import validate_call
from cpacspy.cpacsfunctions import get_value

from typing import Tuple
from cpacspy.cpacspy import CPACS

from ceasiompy.utils.commonxpaths import FUSELAGES_XPATH

from ceasiompy import (
    log,
    ceasiompy_cfg,
)

# =================================================================================================
#   CLASSES
# =================================================================================================


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


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


@validate_call(config=ceasiompy_cfg)
def get_fuselage_scaling(cpacs: CPACS) -> Tuple[float, float, float]:
    """Function to get fuselage scaling along x,y,z axis.

    Function 'get_fuselage_scaling' return the value of the scaling for the
    fuselage. (This is an example function just to show usage of CPACS and tixi)

    Source:
        * Reference paper or book, with author and date

    """

    tixi = cpacs.tixi

    SCALING_XPATH = "/fuselage[1]/transformation/scaling"
    x_fus_scaling_xpath = FUSELAGES_XPATH + SCALING_XPATH + "/x"
    y_fus_scaling_xpath = FUSELAGES_XPATH + SCALING_XPATH + "/y"
    z_fus_scaling_xpath = FUSELAGES_XPATH + SCALING_XPATH + "/z"

    # Get values
    x = float(get_value(tixi, x_fus_scaling_xpath))
    y = float(get_value(tixi, y_fus_scaling_xpath))
    z = float(get_value(tixi, z_fus_scaling_xpath))

    # Log
    log.info(f"Fuselage x scaling is {x}.")
    log.info(f"Fuselage y scaling is {y}.")
    log.info(f"Fuselage z scaling is {z}.")

    return (x, y, z)


@validate_call
def my_subfunc(arg_a: str, arg_b: str) -> str:
    """Function to calculate ...

    Function 'my_subfunc' is a subfunction of ModuleTemplate which returns...

    Source:
       * Reference paper or book, with author and date

    Args:
        arg_a (str): Argument 1
        arg_a (str): Argument 2

    Returns:
        new_arg (str): Output argument

    .. warning::

        Example of warning
    """

    new_arg = arg_a + " and " + arg_b

    return new_arg
