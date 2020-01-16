"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Tool to create workflow for CEASIOMpy (without using RCE)

Python version: >=3.6

| Author: Aidan jungo
| Creation: 2019-11-05
| Last modifiction: 2019-12-20

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
import sys
import math
import numpy
import subprocess
import matplotlib
import shutil

import openmdao.api as om
import importlib
import matplotlib
import matplotlib.pyplot as plt

import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.CPACSUpdater.cpacsupdater import update_cpacs_file

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

import ceasiompy.__init__
LIB_DIR = os.path.dirname(ceasiompy.__init__.__file__)

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

#==============================================================================
#   CLASSES
#==============================================================================

class Function(om.ExplicitComponent):
    """
    Class to denifine function and variables for openmdao.
    """

    def setup(self):

        # Add inputs
        for key, (name, listval, minval, maxval, command) in optim_var_dict.items():
            self.add_input(key, val=listval[0])

        # Add outputs
        self.add_output('f_xy', val=17.0)

        # Finite difference all partials.
        self.declare_partials('*', '*', method='fd')


    def compute(self, inputs, outputs):

        # Add new variable value to the list in the dictionnay
        for key, (name, listval, minval, maxval, command) in optim_var_dict.items():
            listval.append(inputs[key][0])

        # Evaluate the function to optimize
        outputs['f_xy'] = one_optim_iter()


#==============================================================================
#   FUNCTIONS
#==============================================================================


def copy_module_to_module(module_from, io_from, module_to, io_to):
    """ Transfer CPACS file from one module to another.

    Function 'copy_module_to_module' copy the CPACS file form ToolInput or
    ToolOutput of 'module_from' to ToolInput or ToolOutput of 'module_to'

    Args:
        module_from (str): Name of the module the CPACS file is copy from
        io_from (str): "in" or "out", for ToolInput or ToolOutput
        module_to (str): Name of the module where the CPACS file will be copy
        io_to (str): "in" or "out", for ToolInput or ToolOutput
    """

    in_list = ['in','In','IN','iN','input','Input','INPUT','ToolInput','toolinput']

    if io_from in in_list:
        file_copy_from = mi.get_toolinput_file_path(module_from)
    else: # 'out' or anything else ('out' by default)
        file_copy_from = mi.get_tooloutput_file_path(module_from)
    log.info('Copy CPACS from:'+ file_copy_from)

    if io_to in in_list:
        file_copy_to = mi.get_toolinput_file_path(module_to)
    else: # 'out' or anything else ('out' by default)
        file_copy_to = mi.get_tooloutput_file_path(module_to)

    log.info('Copy CPACS to:'+ file_copy_to)

    shutil.copy(file_copy_from,file_copy_to)


def run_subworkflow(module_to_run,cpacs_path_in='',cpacs_path_out=''):
    """Function to run a list of module in order.

    Function 'run_subworkflow' will exectute in order all the module contained
    in 'module_to_run' list. Every time the resuts of one module (generaly CPACS
    file) will be copied as input for the next module.


    Args:
        module_to_run (list): List of mododule to run (in order)
        cpacs_path_in (str): Path of the CPACS file use, if not already in the
                             ToolInput folder of the first submodule
        cpacs_path_out (str): Path of the output CPACS file use, if not already
                              in the ToolInput folder of the first submodule

    """

    submodule_list = mi.get_submodule_list()

    for module in module_to_run:
        if module not in submodule_list:
            raise ValueError('No module named "' + module + '"!')

    # Copy the cpacs file in the first module
    if cpacs_path_in:
        shutil.copy(cpacs_path_in,mi.get_toolinput_file_path(module_to_run[0]))

    log.info('The following module will be execute: ' + str(module_to_run))

    for m, module in enumerate(module_to_run):

        log.info('\n######################################################################################')
        log.info('Run module: ' + module)
        log.info('######################################################################################\n')

        # Go to the module directory
        module_path = os.path.join(LIB_DIR,module)
        os.chdir(module_path)

        # Copy CPACS file from previous module to this one
        if m > 0:
            copy_module_to_module(module_to_run[m-1],'out',module,'in')

        # Find the python file to run
        for file in os.listdir(module_path):
            if file.endswith('.py'):
                if not file.startswith('__'):
                    main_python = file

        # Run the module
        error = subprocess.call(['python',main_python])
        if error:
            raise ValueError('An error ocured in the module '+ module)

    # Copy the cpacs file in the first module
    if cpacs_path_out:
        shutil.copy(mi.get_tooloutput_file_path(module_to_run[-1]),cpacs_path_out)


def run_optimizer():
    """Function to run optimisation with openmdao.

    Function 'run_optimizer' is used to difine the optimisation problem for
    openmdao. The different parameter to define variables are pass through a
    global dictionnay (for now).

    Source:
        * http://openmdao.org/twodocs/versions/latest/getting_started/index.html

    """

    # Build the model
    prob = om.Problem()

    indeps = prob.model.add_subsystem('indeps', om.IndepVarComp())
    prob.model.add_subsystem('myfunc', Function())

    # Optimizer
    prob.driver = om.ScipyOptimizeDriver()
    prob.driver.options['optimizer'] = 'COBYLA' #'SLSQP'

    # Variables
    for key, (name, listval, minval, maxval, command) in optim_var_dict.items():

        # Output, Connections and Design variables
        indeps.add_output(key, listval[0])
        prob.model.connect('indeps.'+key, 'myfunc.'+key)
        prob.model.add_design_var('indeps.'+key, lower=minval, upper=maxval)

    # Objective function
    prob.model.add_objective('myfunc.f_xy')

    # Run
    prob.setup()
    prob.run_driver()


    # Results (TODO: improve and add plots)
    log.info('=========================================')
    log.info('min = ' + str(prob['myfunc.f_xy']))

    for key, (name, listval, minval, maxval, command) in optim_var_dict.items():
        log.info(name + ' = ' + str(prob['indeps.'+key]))

    log.info('Variable history')
    for key, (name, listval, minval, maxval, command) in optim_var_dict.items():
        log.info(name + ' => ' + str(listval))

    log.info('=========================================')


def one_optim_iter():
    """Function to evaluate the vaule to optimize.

    Function 'one_optim_iter' will exectute in order all the module contained
    in '...' and extract the ... value from the lase CPACS file, this value will
    be return to the optimizer
    CPACSUpdater....

    """

    # Create the parameter in CPACS with 'CPACSUpdater' module
    cpacs_path = mi.get_toolinput_file_path('CPACSUpdater')
    cpacs_out_path = mi.get_tooloutput_file_path('CPACSUpdater')

    tixi =  cpsf.open_tixi(cpacs_path)
    wkdir_path = ceaf.create_new_wkdir()
    WKDIR_XPATH = '/cpacs/toolspecific/CEASIOMpy/filesPath/wkdirPath'
    tixi.updateTextElement(WKDIR_XPATH,wkdir_path)

    # TODO: improve this part! (maybe move somewhere else)
    # To delete coef from previous iter
    aeromap_uid = cpsf.get_value(tixi,SU2_XPATH+ '/aeroMapUID')
    Coef = apmf.get_aeromap(tixi,aeromap_uid)
    apmf.delete_aeromap(tixi,aeromap_uid)
    apmf.create_empty_aeromap(tixi,aeromap_uid,'test_optim')
    apmf.save_parameters(tixi,aeromap_uid,Coef)
    cpsf.close_tixi(tixi,cpacs_path)

    # Update the CPACS file with the parameters contained in optim_var_dict
    update_cpacs_file(cpacs_path,cpacs_out_path, optim_var_dict)

    # Run optimissation sub workflow
    copy_module_to_module('CPACSUpdater','out',module_optim[0],'in')
    run_subworkflow(module_optim)
    copy_module_to_module(module_optim[-1],'out','CPACSUpdater','in')

    # Extract results  TODO: improve this part
    cpacs_results_path = mi.get_tooloutput_file_path(module_optim[-1])
    log.info('Results will be extracted from:' + cpacs_results_path)
    tixi = cpsf.open_tixi(cpacs_results_path)

    mtom = cpsf.get_value(tixi,'/cpacs/vehicles/aircraft/model/analyses/massBreakdown/designMasses/mTOM/mass')

    aeromap_uid = cpsf.get_value(tixi,SU2_XPATH+ '/aeroMapUID')
    Coef = apmf.get_aeromap(tixi,aeromap_uid)

    cl = Coef.cl[0]
    cd = Coef.cd[0]
    cm = Coef.cms[0]

    log.info('=========================')
    for key, (name, listval, minval, maxval, command) in optim_var_dict.items():
        log.info(name,': ',listval[-1])

    log.info('Cl/Cd: ' + str(cl/cd))
    log.info('Cl: ' + str(cl))
    log.info('Cd: ' + str(cd))
    log.info('Cd: ' + str(cm))
    log.info('MTOM:' + str(mtom))
    log.info('(Cl)/MTOM:' + str(cl/mtom))
    log.info('=========================')

    # TODO: add option to choose what will be returned
    # return -mtom
    # return -cl
    # return cd
    # return -cl/cd
    return -cl/cd/mtom
    # return -cl/mtom
    # minus sign because it only minimize the function


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
    # Available Moudle:

    # Settings: 'SettingsGUI'
    # Geometry and mesh: 'CPACSCreator','CPACS2SUMO','SUMOAutoMesh'
    # Weight and balance: 'WeightConventional'
    # Aerodynamics: 'CLCalculator','PyTornado','SU2Run','SkinFriction','PlotAeroCoefficients'
    # Mission analysis: 'Range'

    # Copy-Paste the module you want to execute, they will be run in order
    module_pre = ['SettingsGUI','CPACS2SUMO','SUMOAutoMesh','SU2Run','SkinFriction','PlotAeroCoefficients']

    module_optim = ['WeightConventional','PyTornado']
    module_post = []
    optim =  False
    doe = False

    # Diffine the parameter to optimize
    # TODO

    # Define variables dictionnay (for now, it is useed as a global varible to simplify)
    optim_var_dict = {}
    # optim_var_dict[var1] = ('name',[init],min,max,'CPACSUpdater_command')
    optim_var_dict['var1'] = ('SPAN',[30],20,40,'wings.get_wing(1).set_half_span_keep_ar(var1)')
    optim_var_dict['var2'] = ('wing_sweep',[10],10,25,'wings.get_wing(1).set_sweep(var2)')
    # optim_var_dict['var3'] = ('AR_htp',[5],4,8,'wings.get_wing(2).set_arkeep_area(var3)')
    # optim_var_dict['var4'] = ('AR_vtp',[5],4,8,'wings.get_wing(3).set_arkeep_area(var4)')
    # optim_var_dict['var6'] = ('sec_size1',[13.43],10.0,15.2,'wings.get_wing(1).get_section(1).get_section_element(1).get_ctigl_section_element().set_width(var6)')
    # optim_var_dict['var7'] = ('sec_size2',[13.43],10.0,15.2,'wings.get_wing(1).get_section(2).get_section_element(1).get_ctigl_section_element().set_width(var7)')
    # optim_var_dict['var8'] = ('sec_size3',[9.56],8.0,11.2,'wings.get_wing(1).get_section(3).get_section_element(1).get_ctigl_section_element().set_width(var8)')
    # optim_var_dict['var9'] = ('sec_size4',[8.35],6.0,10.2,'wings.get_wing(1).get_section(4).get_section_element(1).get_ctigl_section_element().set_width(var9)')
    # optim_var_dict['var10'] = ('sec_size5',[4.14],3.0,5.2,'wings.get_wing(1).get_section(5).get_section_element(1).get_ctigl_section_element().set_width(var10)')
    # optim_var_dict['var11'] = ('sec_size6',[2.17],1.0,3.2,'wings.get_wing(1).get_section(6).get_section_element(1).get_ctigl_section_element().set_width(var11)')
    # optim_var_dict['var12'] = ('sec_size7',[1.47],1.0,2.2,'wings.get_wing(1).get_section(7).get_section_element(1).get_ctigl_section_element().set_width(var12)')
    # optim_var_dict['var13'] = ('rot_sec2',[0],-4,4,'wings.get_wing(1).get_section(5).set_rotation(geometry.CTiglPoint(0,var13,0))')
    # optim_var_dict['var14'] = ('rot_sec3',[0],-4,4,'wings.get_wing(1).get_section(6).set_rotation(geometry.CTiglPoint(0,var14,0))')
    # optim_var_dict['var15'] = ('rot_sec4',[0],-4,4,'wings.get_wing(1).get_section(7).set_rotation(geometry.CTiglPoint(0,var15,0))')
    # optim_var_dict['var16'] = ('rot_sec5',[0],-4,4,'wings.get_wing(1).get_section(5).set_rotation(geometry.CTiglPoint(0,var16,0))')
    # optim_var_dict['var17'] = ('rot_sec6',[0],-4,4,'wings.get_wing(1).get_section(6).set_rotation(geometry.CTiglPoint(0,var17,0))')
    # optim_var_dict['var18'] = ('rot_sec7',[0],-4,4,'wings.get_wing(1).get_section(7).set_rotation(geometry.CTiglPoint(0,var18,0))')

    ###########################


    # Pre Workflow (only run once)------------------------
    run_subworkflow(module_pre,cpacs_path)

    # Optim Workflow ------------------------------------
    if optim:
        copy_module_to_module(module_pre[-1],'out','CPACSUpdater','in')
        run_optimizer()

        # Post optim -------------------------------
        if module_post:
            copy_module_to_module('CPACSUpdater','out',module_post[0],'in')
            run_subworkflow(module_post)
            shutil.copy(mi.get_tooloutput_file_path(module_post[-1]),cpacs_path_out)
        else:
            shutil.copy(mi.get_tooloutput_file_path(module_optim[-1]),cpacs_path_out)

    elif doe:
        pass

    else:
        shutil.copy(mi.get_tooloutput_file_path(module_pre[-1]),cpacs_path_out)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
