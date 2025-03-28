"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Small description of the script

Python version: >=3.8

| Author: Name
| Creation: D-M-Y

TODO:
    * Things to improve ...
    * Things to add ...

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pydantic import validate_call
from ceasiompy.utils.ceasiompyutils import call_main
from ceasiompy.ModuleTemplate.func.subfunc import get_fuselage_scaling

from cpacspy.cpacspy import CPACS

from ceasiompy.ModuleTemplate import MODULE_NAME

from ceasiompy import (
    log, 
    ceasiompy_cfg,
)

# Do not add function definitions here.
# If you want to define classes or functions do it in func directory.

# =================================================================================================
#    MAIN
# =================================================================================================


# You will need to have a function named main.
# CEASIOMpy will run one main per module.


# If the function takes as input a arbitrary type object,
# you need to add config=validate_cfg.
@validate_call(config=ceasiompy_cfg)
# Try to always use the validate_call decorator if your function is called only once.
# This way you can be sure that your function takes as inputs
# and gives as outputs the correct types of object.
def main(cpacs: CPACS) -> None:

    # Call a function which use CPACS inputs
    x, y, z = get_fuselage_scaling(cpacs)
    log.info("Value x, y, z have been calculated.")
    log.info("x = " + str(x))
    log.info("y = " + str(y))
    log.info("z = " + str(z))


if __name__ == "__main__":
    # By default uses D150_simple.xml at CPACS_files.
    call_main(main, MODULE_NAME)
    # If you want to run your module with a specific CPACS file,
    # you can use:
    # call_main(main, MODULE_NAME, cpacs_path = Path(path/to/cpacs.xml))
    # The saved CPACS can be found in the ToolOutput directory.