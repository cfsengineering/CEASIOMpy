"""
Created on Tue Feb 25 15:59:13 2020

@author: Aidan Jungo

Module containing the utilitary functions for the workflowcreator and optimization modules

TODO:
    - Investigate why the stp models are not or badly exported
    - Add the function to make a caption
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import subprocess
import shutil
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

import ceasiompy.__init__
LIB_DIR = os.path.dirname(ceasiompy.__init__.__file__)

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'


#==============================================================================
#   DICTIONNARY
#==============================================================================
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

    if not module_to_run:
        log.info('No module to run in "Pre-module"')
        return 0

    submodule_list = mi.get_submodule_list()

    for module in module_to_run:
        if module not in submodule_list:
            raise ValueError('No module named "' + module + '"!')

    # Copy the cpacs file in the first module
    if cpacs_path_in:
        shutil.copy(cpacs_path_in,mi.get_toolinput_file_path(module_to_run[0]))

    log.info('The following modules will be executed: ' + str(module_to_run))

    for m, module in enumerate(module_to_run):

        log.info('\n######################################################################################')
        log.info('Run module: ' + module)
        log.info('######################################################################################\n')

        # Go to the module directory
        module_path = os.path.join(LIB_DIR,module)
        print('\n Going to ',module_path,'\n')
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
