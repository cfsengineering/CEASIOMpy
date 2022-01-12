"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Main module of CEASIOMpy to launch workflow by different way.

Python version: >=3.7

| Author: Aidan Jungo
| Creation: 2022-01-06

Todo:
    * All

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import ceasiompy.__init__

import os
import sys
import shutil

import datetime
from pathlib import Path

from ceasiompy.WorkflowCreator.workflowcreator import create_wf_gui
import ceasiompy.utils.moduleinterfaces as mi
import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.workflowfunctions as wkf
from cpacspy.cpacsfunctions import open_tixi
from ceasiompy.Optimisation.optimisation import routine_launcher
from ceasiompy.utils.ceasiompyfunctions import WorkflowOptions
from ceasiompy.utils.configfiles import ConfigFile

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_NAME = os.path.basename(os.getcwd())


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def run_workflow(Opt):
    """Run the complete Worflow

    Args:
        Opt (class): Cl
        cpacs_out_path (str): Path to the output CPACS file
        module_list (list): List of module to inclue in the GUI

    """

    # Copy ToolInput.xml in ToolInput dir if not already there
    # cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
    cpacs_path = "../test_files/CPACSfiles/D150_simple.xml"
    Opt.cpacs_path = os.path.abspath(cpacs_path)
    # if not os.path.abspath(Opt.cpacs_path) == os.path.abspath(cpacs_path):
    #     shutil.copy(Opt.cpacs_path, cpacs_path)
    #     Opt.cpacs_path = os.path.abspath(cpacs_path)

    # Create a new wkdir
    tixi = open_tixi(Opt.cpacs_path)
    wkdir = ceaf.get_wkdir_or_create_new(tixi)
    tixi.save(Opt.cpacs_path)

    # Write the config file in the working dir
    Opt.write_config_file(wkdir)

    # Copy ToolInput in the Working directory
    shutil.copy(Opt.cpacs_path, os.path.join(wkdir, "Input.xml"))

    # Run Pre-otimisation workflow
    if Opt.module_pre:
        wkf.run_subworkflow(Opt.module_pre, Opt.cpacs_path)

        if not Opt.module_optim and not Opt.module_post:
            shutil.copy(mi.get_tooloutput_file_path(Opt.module_pre[-1]), cpacs_path_out)

    # Run Optimisation workflow
    if Opt.module_optim:

        if Opt.module_pre:
            wkf.copy_module_to_module(Opt.module_pre[-1], "out", "Optimisation", "in")
        else:
            wkf.copy_module_to_module("WorkflowCreator", "in", "Optimisation", "in")

        if Opt.optim_method:
            routine_launcher(Opt)
        else:
            log.warning("No optimization method has been selected!")
            log.warning("The modules will be run as a simple workflow")
            wkf.run_subworkflow(Opt.module_optim)

        if not Opt.module_post:
            shutil.copy(mi.get_tooloutput_file_path(Opt.module_optim[-1]), cpacs_path_out)

    # Run Post-optimisation workflow
    if Opt.module_post:

        if Opt.module_optim:
            wkf.copy_module_to_module(Opt.module_optim[-1], "out", Opt.module_post[0], "in")
        elif Opt.module_pre:
            wkf.copy_module_to_module(Opt.module_pre[-1], "out", Opt.module_post[0], "in")
        else:
            wkf.copy_module_to_module("WorkflowCreator", "in", Opt.module_post[0], "in")

        # wkf.copy_module_to_module('CPACSUpdater','out',Opt.module_post[0],'in')  usefuel?
        wkf.run_subworkflow(Opt.module_post)
        shutil.copy(mi.get_tooloutput_file_path(Opt.module_post[-1]), cpacs_path_out)

    # Copy ToolInput in the Working directory
    shutil.copy(cpacs_path_out, os.path.join(wkdir, "Output.xml"))


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

    cpacs_path_out = mi.get_tooloutput_file_path(MODULE_NAME)

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
    Opt.create_dir_structure()
    # run_workflow(Opt)

    log.info("=========== End of " + os.path.basename(__file__) + " ===========")
