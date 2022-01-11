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
from ceasiompy.utils.ceasiompyfunctions import WorkflowOptions, create_dir_structure
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
    """ Run the complete Worflow

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
    

    
# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":
    
    log.info("========== Start of " + os.path.basename(__file__) + " ==========")
    
    cpacs_path_out = mi.get_tooloutput_file_path(MODULE_NAME)

    no_arg = True

    if len(sys.argv) > 1:
        if sys.argv[1] == "-gui":
            no_arg = False

            Opt = create_wf_gui()

        elif sys.argv[1] == "-cfg":

            if len(sys.argv) > 2:
                cfg_file = sys.argv[2]
                if os.path.isfile(cfg_file):
                    no_arg = False
                else:
                    print(" ")
                    print("The path you use as argument is not a file!")
                    print(" ")
                    sys.exit()
            else:
                print(" ")
                print("No configuration file!")
                print('If you use the option "-cfg" to run this module,')
                print("you must specifiy the path to the config file!")
                print(" ")
                sys.exit()

            Opt = WorkflowOptions()

            Opt.from_config_file(cfg_file)
            Opt.working_dir = Path(cfg_file).parent.absolute()

        else:
            print(" ")
            print("Invalid argument!")
            print("You can use the option -gui to run this module with a user interface.")
            print("You can use the option -cfg to run this module with a configuration file.")
            print(" ")
            sys.exit()

    # To run a workflow without gui or config file
    if no_arg:

        Opt = WorkflowOptions()

        # Available Module:
        # Settings: 'SettingsGUI'
        # Geometry and mesh:
        #       'CPACSCreator','CPACS2SUMO','SUMOAutoMesh'
        # Weight and balance:
        #       'WeightConventional','WeightUnconventional',
        #       'BalanceConventional','BalanceUnconventional'
        # Aerodynamics:
        #       'CLCalculator','PyTornado','SkinFriction','PlotAeroCoefficients',
        #       'SU2MeshDef','SU2Run'
        # Mission analysis: 'Range','StabilityStatic'
        # Surrogate modelling: 'SMTrain', 'SMUse'

        Opt.module_pre = ["PyTornado", "SkinFriction"]
        Opt.module_optim = []
        Opt.module_post = []
        Opt.optim_method = "None"  # DoE, Optim, None

    create_dir_structure(Opt)

    # # Run the workflow
    # run_workflow(Opt)
    
    log.info("=========== End of " + os.path.basename(__file__) + " ===========")