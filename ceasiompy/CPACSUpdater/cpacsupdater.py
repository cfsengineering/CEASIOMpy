"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Update geometry of a CPACS file for simple modification or optimisation

Python version: >=3.7

| Author: Aidan Jungo
| Creation: 2019-11-11

TODO:

    * This module is still a bit tricky to use, it will be simplified in the future

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os

from cpacspy.cpacsfunctions import open_tixi, open_tigl, get_tigl_configuration
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def update_cpacs_file(cpacs_path, cpacs_out_path, optim_var_dict):
    """Function to update a CPACS file with value from the optimiser

    This function sets the new values of the design variables given by
    the routine driver to the CPACS file, using the Tigl and Tixi handler.

    Source:
        * See CPACSCreator api function,

    Args:
        cpacs_path (str): Path to CPACS file to update
        cpacs_out_path (str):Path to the updated CPACS file
        optim_var_dict (dict): Dictionary containing all the variable
                               value/min/max and command to modify a CPACS file

    """

    tixi = open_tixi(cpacs_path)
    tigl = open_tigl(tixi)

    aircraft = get_tigl_configuration(tigl)
    # help(aircraft)

    wings = aircraft.get_wings()
    # help(wings)

    fuselage = aircraft.get_fuselages().get_fuselage(1)
    # help(fuselage)

    # Other functions which could be useful

    # help(wings.get_wing(1).get_section(1))
    # uid = wings.get_wing(1).get_section(2).get_uid()
    # help(wings.get_wing(1).get_positioning_transformation(uid))
    # wings.get_wing(1).get_section(2).set_rotation(geometry.CTiglPoint(40,40,-4))
    # airfoil = wings.get_wing(1).get_section(1).get_section_element(1).get_airfoil_uid()
    # help(airfoil)
    # wings.get_wing(1).get_section(1).get_section_element(1).set_airfoil_uid('NACA0006')
    # scal = wings.get_wing(1).get_section(1).get_section_element(1).get_scaling()
    # help(wings.get_wing(1).get_section(2))

    # Perform update of all the variable contained in 'optim_var_dict'
    for (
        name,
        (val_type, listval, minval, maxval, getcommand, setcommand),
    ) in optim_var_dict.items():
        if val_type == "des" and listval[0] not in ["-", "True", "False"]:
            if setcommand not in ["-", ""]:
                # Define variable (var1,var2,..)
                locals()[str(name)] = listval[-1]
                # Execute the command coresponding to the variable
                if ";" in setcommand:  # if more than one command on the line
                    command_split = setcommand.split(";")
                    for setcommand in command_split:
                        eval(setcommand)
                else:
                    eval(setcommand)
            else:
                xpath = getcommand
                tixi.updateTextElement(xpath, str(listval[-1]))
    aircraft.write_cpacs(aircraft.get_uid())
    tigl.close()
    tixi.save(cpacs_out_path)


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    log.info("----- Start of " + os.path.basename(__file__) + " -----")

    cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
    cpacs_out_path = mi.get_tooloutput_file_path(MODULE_NAME)

    # Call the function which check if imputs are well define
    # mi.check_cpacs_input_requirements(cpacs_path)

    log.info("----- End of " + os.path.basename(__file__) + " -----")
