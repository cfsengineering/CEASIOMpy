#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Python version: >=3.6

| Author: Aidan jungo
| Creation: 2020-24-02
| Last modifiction: 2020-24-02

TODO:
    
    * Write optimization module
"""

import openmdao.api as om
from numpy import arange
from matplotlib.pyplot import plot, show

import ceasiompy.utils.workflowfunctions as wkf #NEW
import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.CPACSUpdater.cpacsupdater import update_cpacs_file

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

#==============================================================================
#   DICTIONNARY
#==============================================================================

follower = {"Counter":0,"designVar":[],"optimVar":[]}

optim_var_dict = {}
# optim_var_dict[var1] = ('name',[init],min,max,'CPACSUpdater_command')
optim_var_dict['var1'] = ('SPAN',[30],25,45,'wings.get_wing(1).set_half_span_keep_ar(var1)')
optim_var_dict['var2'] = ('length',[62.96542953094896],60,65,'fuselage.set_length(var2)')
#optim_var_dict['var3'] = ('width',[6],5.2,7,'fuselage.set_max_width(var3)')
#optim_var_dict['var4'] = ('wing_sweep',[27],20,30,'wings.get_wing(1).set_sweep(var4)')
#optim_var_dict['var3'] = ('AR_htp',[5],4,8,'wings.get_wing(2).set_arkeep_area(var3)')
#optim_var_dict['var4'] = ('AR_vtp',[5],4,8,'wings.get_wing(3).set_arkeep_area(var4)')
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

class constraint(om.ExplicitComponent):
    """
    Class to define the constraints or target that are not explicit design variables
    """
    
    def setup(self):
        
        #Add output
        self.add_output('passengers', val=440)
        
    def compute(self, inputs, outputs):
        
        outputs['passengers'] = get_val()
        
#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_val():
    """
    Function to retrieve values that are not in the optim_var_dict (ex range, passenger, etc)
    
    TODO : Implement the general case
    """

    cpacs_results_path = mi.get_tooloutput_file_path(module_optim[-1])
    tixi = cpsf.open_tixi(cpacs_results_path)

    passnb = cpsf.get_value(tixi,'/cpacs/toolspecific/CEASIOMpy/weight/passengers/passNb')
    return passnb

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
    prob.driver.options['optimizer'] =  'COBYLA'#'SLSQP'

    # Variables
    for key, (name, listval, minval, maxval, command) in optim_var_dict.items():

        # Output, Connections and Design variables
        indeps.add_output(key, listval[0])
        prob.model.connect('indeps.'+key, 'myfunc.'+key)
        prob.model.add_design_var('indeps.'+key, lower=minval, upper=maxval)


    # Objective function
    prob.model.add_objective('myfunc.f_xy')

    #passnb = 440
    # define the component whose output will be constrained
    prob.model.add_subsystem('const', constraint())
    prob.model.add_constraint('const.passengers', upper=450, lower=440)

    # Run
    prob.setup()
    prob.run_driver()


    # Results (TODO: improve)
    log.info('=========================================')
    log.info('min = ' + str(prob['myfunc.f_xy']))
    
    iterations = arange(0,follower["Counter"])

    plot(iterations, follower["optimVar"])
    show()

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

    follower["Counter"] += 1
    print('\n','\n',follower['designVar'],'\n',follower['optimVar'],'\n','\n')
    
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
    rng = cpsf.get_value(tixi,'/cpacs/toolspecific/CEASIOMpy/ranges/rangeMaxP/rangeDescription/range')
    pl = cpsf.get_value(tixi,'/cpacs/toolspecific/CEASIOMpy/ranges/rangeMaxP/rangeDescription/payload')

    aeromap_uid = cpsf.get_value(tixi,SU2_XPATH+ '/aeroMapUID')
    Coef = apmf.get_aeromap(tixi,aeromap_uid)

    cl = Coef.cl[0]
    cd = Coef.cd[0]
    cm = Coef.cms[0]

    log.info('=========================')
    for key, (name, listval, minval, maxval, command) in optim_var_dict.items():
        #log.info(name,': ',listval[-1])
        follower["designVar"].append(listval[-1])

    log.info('Cl/Cd: ' + str(cl/cd))
    log.info('Cl: ' + str(cl))
    log.info('Cd: ' + str(cd))
    log.info('Cd: ' + str(cm))
    log.info('MTOM:' + str(mtom))
    log.info('(Cl)/MTOM:' + str(cl/mtom))
    log.info('=========================')

    follower["optimVar"].append(get_val())
    # TODO: add option to choose what will be returned
    # return -mtom
    # return -cl
    # return cd
    # return -cl/cd
    return -rng/pl
    # return -cl/cd/mtom
    # return -cl/mtom
    # minus sign because it only minimize the function


def optimize(modules):
    """
    Function that retrieves the list of modules to use in the optimization loop and launches the optimization process
    """

    global module_optim
    module_optim = modules
    run_optimizer()


