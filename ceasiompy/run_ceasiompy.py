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

# =================================================================================================
#   IMPORTS
# =================================================================================================

import ceasiompy.__init__

import os
import sys

from pathlib import Path
from ceasiompy.WorkflowCreator.workflowcreator import create_wf_gui
from ceasiompy.utils.workflowclasses import Workflow

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_NAME = os.path.basename(os.getcwd())
LIB_DIR = os.path.dirname(ceasiompy.__init__.__file__)


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def print_help():

    print("\nUsage: python run_ceasiompy.py [-h] [-gui] [-cfg my_path/Configfile.cfg] ")

    print("\nThis is this help of the CEASIOMpy.")

    print("\nOptional arguments:")
    print("\n-h\tshow this help message and exit")
    print("-gui\tlaunch a graphical user inter to create a workflow and run it.")
    print("-cfg\trun a workflow from configuration file.")

    print("\nNo argument correspond to the [-gui] option.\n")


# =================================================================================================
#    MAIN
# =================================================================================================


def main():

    log.info("========== Start of " + os.path.basename(__file__) + " ==========")

    # If no argument create run the GUI
    if len(sys.argv) == 1:

        workflow = create_wf_gui()
        workflow.write_config_file()

    elif len(sys.argv) == 2:

        if sys.argv[1] == "-gui":

            workflow = create_wf_gui()
            workflow.write_config_file()

        else:
            print_help()
            sys.exit()

    elif len(sys.argv) == 3:

        if sys.argv[1] == "-cfg":

            workflow = Workflow()
            workflow.from_config_file(Path(sys.argv[2]))

        else:
            print_help()
            sys.exit()

    else:
        print_help()
        sys.exit()

    # Set and run the workflow
    workflow.set_workflow()
    workflow.run_workflow()

    log.info("=========== End of " + os.path.basename(__file__) + " ===========")


if __name__ == "__main__":

    main()
