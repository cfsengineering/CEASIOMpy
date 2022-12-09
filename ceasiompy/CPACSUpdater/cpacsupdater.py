"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Update geometry of a CPACS file for simple modification or optimisation

Python version: >=3.8

| Author: Aidan Jungo
| Creation: 2019-11-11

TODO:

    * This module is still a bit tricky to use, it will be simplified in the future

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.ceasiomlogger import get_logger

from ceasiompy.utils.moduleinterfaces import (
    check_cpacs_input_requirements,
    get_toolinput_file_path,
)

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def update_cpacs_file(cpacs_path, cpacs_out_path, optim_var_dict):
    """Function to update a CPACS file with value from the optimiser

    This function sets the new values of the design variables given by
    the routine driver to the CPACS file, using the Tigl and Tixi handler.

    Source:
        * See CPACSCreator api function,

    Args:
        cpacs_path (Path): Path to CPACS file to update
        cpacs_out_path (Path):Path to the updated CPACS file
        optim_var_dict (dict): Dictionary containing all the variable
                               value/min/max and command to modify a CPACS file

    """

    cpacs = CPACS(cpacs_path)
    log.info(f"{cpacs_path} will be updated.")

    # Object seems to be unused, but are use in "eval" function
    wings = cpacs.aircraft.get_wings()
    fuselage = cpacs.aircraft.get_fuselages().get_fuselage(1)

    # Perform update of all the variable contained in 'optim_var_dict'
    for name, variables in optim_var_dict.items():

        # Unpack the variables
        val_type, listval, _, _, getcommand, setcommand = variables

        if val_type == "des" and listval[0] not in ["-", "True", "False"]:

            if setcommand not in ["-", ""]:

                # Define variable (var1,var2,..)
                locals()[str(name)] = listval[-1]

                # Update value by using tigl configuration
                if ";" in setcommand:  # if more than one command on the line
                    command_split = setcommand.split(";")
                    for setcommand in command_split:
                        eval(setcommand)
                else:
                    eval(setcommand)
            else:

                # Update value directly in the CPACS file
                xpath = getcommand
                cpacs.tixi.updateTextElement(xpath, str(listval[-1]))

    # aircraft.write_cpacs(aircraft.get_uid())
    cpacs.save_cpacs(str(cpacs_out_path))

    log.info(f"{cpacs_out_path} has been saved.")
    log.info("----- Start of CPACSUpdater -----")


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    check_cpacs_input_requirements(cpacs_path)
    update_cpacs_file(cpacs_path, cpacs_out_path, variable_to_update)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = get_tooloutput_file_path(MODULE_NAME)

    main(cpacs_path, cpacs_out_path)


# Other functions which could be useful
# help(aircraft)
# help(wings)
# help(fuselage)
# help(wings.get_wing(1).get_section(1))
# uid = wings.get_wing(1).get_section(2).get_uid()
# help(wings.get_wing(1).get_positioning_transformation(uid))
# wings.get_wing(1).get_section(2).set_rotation(geometry.CTiglPoint(40,40,-4))
# airfoil = wings.get_wing(1).get_section(1).get_section_element(1).get_airfoil_uid()
# help(airfoil)
# wings.get_wing(1).get_section(1).get_section_element(1).set_airfoil_uid('NACA0006')
# scal = wings.get_wing(1).get_section(1).get_section_element(1).get_scaling()
# help(wings.get_wing(1).get_section(2))
