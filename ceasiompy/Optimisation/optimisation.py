#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Python version: >=3.6

| Author: Vivien Riolo
| Creation: 2020-24-02
| Last modifiction: 2020-24-02

TODO:
    
    * Write optimization module
    * Implement it to the workflow module
"""

import openmdao.api as om
import ceasiompy.utils.workflowfunctions as wkf #NEW

import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.CPACSUpdater.cpacsupdater import update_cpacs_file

from ceasiompy.utils.workflowfunctions import optim_var_dict
from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

#==============================================================================
#   CLASSES
#==============================================================================

class objective_function(om.ExplicitComponent):
    """
    Class to define function and variables for openmdao.
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

def run_optimizer():
    """Function to run optimisation with openmdao.

    Function 'run_optimizer' is used to define the optimisation problem for
    openmdao. The different parameter to define variables are pass through a
    global dictionnay (for now).

    Source:
        * http://openmdao.org/twodocs/versions/latest/getting_started/index.html

    """

    # Build the model
    prob = om.Problem()

    indeps = prob.model.add_subsystem('indeps', om.IndepVarComp())
    prob.model.add_subsystem('myfunc', objective_function())

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
    """Function to evaluate the value to optimize.

    Function 'one_optim_iter' will exectute in order all the module contained
    in '...' and extract the ... value from the last CPACS file, this value will
    be returned to the optimizer
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

    # Run optimisation sub workflow
    wkf.copy_module_to_module('CPACSUpdater','out',module_optim[0],'in')
    wkf.run_subworkflow(module_optim)
    wkf.copy_module_to_module(module_optim[-1],'out','CPACSUpdater','in')

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


def optimize(modules):
    """
    Function that retrieves the list of modules to use in the optimization loop and launches the optimization process
    """
    
    global module_optim
    module_optim = modules
    run_optimizer()


