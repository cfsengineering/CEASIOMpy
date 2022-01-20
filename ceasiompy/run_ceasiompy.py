"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Main module of CEASIOMpy to launch workflow by different way.

Python version: >=3.7

| Author: Aidan Jungo
| Creation: 2022-01-06

Todo:
    * 

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import ceasiompy.__init__

import os
import sys

from ceasiompy.WorkflowCreator.workflowcreator import create_wf_gui
from ceasiompy.utils.ceasiompyfunctions import WorkflowOptions

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_NAME = os.path.basename(os.getcwd())
LIB_DIR = os.path.dirname(ceasiompy.__init__.__file__)


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def print_help():

    print("\nUsage: python run_ceasiompy.py [-h] [-gui] [-cfg my_path/Configfile.cfg] ")
    print("\nThis is this help of the CEASIOMpy.")
    print("\nOptional arguments:")
    print("\n-h\tshow this help message and exit")
    print("-gui\tlaunch a graphical user inter to create a workflow and run it.")
    print("-cfg\trun a workflow from configuration file.")
    print("\nNo argument correspond to the [-gui] option.\n")


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    log.info("========== Start of " + os.path.basename(__file__) + " ==========")

    # If no argument create run the GUI
    if len(sys.argv) == 1:

        Opt = create_wf_gui()
        Opt.write_config_file()

    elif len(sys.argv) == 2:

        if sys.argv[1] == "-gui":

            Opt = create_wf_gui()
            Opt.write_config_file()

        else:
            print_help()
            sys.exit()

    elif len(sys.argv) == 3:

        if sys.argv[1] == "-cfg":

            cfg_file = sys.argv[2]

            if not os.path.isfile(cfg_file):
                raise FileNotFoundError(f"{cfg_file} has not been found!")

            if not cfg_file.endswith(".cfg"):
                raise ValueError("The CEASIOMpy configuration file must be a *.cfg file!")

            Opt = WorkflowOptions()
            Opt.from_config_file(cfg_file)

        else:
            print_help()
            sys.exit()

    else:
        print_help()
        sys.exit()

    # Run the workflow
    Opt.set_workflow()
    Opt.run_workflow()

    log.info("=========== End of " + os.path.basename(__file__) + " ===========")
