"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Tool to create workflow for CEASIOMpy (without using RCE)

Python version: >=3.6

| Author: Aidan jungo
| Creation: 2019-11-05
| Last modification: 2019-12-20

TODO:

    * Write the doc
    * This module is still a bit tricky to use, it will be simplified in the future
    * Use a class instead of 'optim_var_dict' dictionnay???
    * How to pass 'module_optim' as argument
    * Crete a Design of Experiment functions

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import shutil

import ceasiompy.utils.workflowfunctions as wkf
import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.Optimisation.optimisation import optimize

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

import ceasiompy.__init__
LIB_DIR = os.path.dirname(ceasiompy.__init__.__file__)

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':
    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = mi.get_toolinput_file_path(MODULE_NAME)
    cpacs_path_out = mi.get_tooloutput_file_path(MODULE_NAME)

    # Create a new wkdir
    tixi =  cpsf.open_tixi(cpacs_path)
    wkdir = ceaf.get_wkdir_or_create_new(tixi)
    cpsf.close_tixi(tixi,cpacs_path)


    ####### USER INPUT ########
    # Available Module:

    # Settings: 'SettingsGUI'
    # Geometry and mesh: 'CPACSCreator','CPACS2SUMO','SUMOAutoMesh'
    # Weight and balance: 'WeightConventional','WeightUnconventional','BalanceConventional','BalanceUnconventional'
    # Aerodynamics: 'CLCalculator','PyTornado','SkinFriction','PlotAeroCoefficients','SU2Run'
    # Mission analysis: 'Range'

    # Copy-Paste the module you want to execute, they will be run in order
    module_pre = ['SettingsGUI','WeightConventional','PyTornado','Range'] #['SettingsGUI','CPACS2SUMO','SUMOAutoMesh','SU2Run','PyTornado','SkinFriction','CLCalculator','PlotAeroCoefficients','Range']

    module_optim = ['WeightConventional','PyTornado', 'Range']
    module_post = []

    optim =  True
    doe = False

    # Choose the parameter to optimize
    optim_target = "mtom"

    # Pre Workflow (only run once)------------------------
    wkf.run_subworkflow(module_pre,cpacs_path)

    # Optim Workflow ------------------------------------
    if optim:
        wkf.copy_module_to_module(module_pre[-1],'out','CPACSUpdater','in')
        optimize(module_optim)

        # Post optim -------------------------------
        if module_post:
            wkf.copy_module_to_module('CPACSUpdater','out',module_post[0],'in')
            wkf.run_subworkflow(module_post)
            shutil.copy(mi.get_tooloutput_file_path(module_post[-1]),cpacs_path_out)
        else:
            shutil.copy(mi.get_tooloutput_file_path(module_optim[-1]),cpacs_path_out)

    elif doe:
        pass

    else:
        shutil.copy(mi.get_tooloutput_file_path(module_pre[-1]),cpacs_path_out)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
