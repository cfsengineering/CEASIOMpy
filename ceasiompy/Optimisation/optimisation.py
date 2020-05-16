"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Python version: >=3.6

| Author: Aidan jungo
| Creation: 2020-24-02
| Last modifiction: 2020-06-04

TODO:

    * Class instead of dictionnary ?
    * Add/modify the optimisation parameters
"""

# =============================================================================
#   IMPORTS
# =============================================================================

import os
import datetime
import openmdao.api as om
import numpy as np
import shutil

from re import split as splt
from ceasiompy.Optimisation.func.dictionnary import init_dict, update_res_var_dict
import ceasiompy.utils.workflowfunctions as wkf
import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.moduleinterfaces as mi
import ceasiompy.utils.optimfunctions as opf

from ceasiompy.CPACSUpdater.cpacsupdater import update_cpacs_file

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

# =============================================================================
#   GLOBAL VARIABLES
# =============================================================================

Rt = opf.Routine
counter = 0

# =============================================================================
#   CLASSES
# =============================================================================


class objective_function(om.ExplicitComponent):
    """Class to define function and variables for openmdao."""

    def setup(self):
        """Create function inputs and outputs."""
        # Add inputs
        for key, (name, listval, minval, maxval, setcommand, getcommand) in design_var_dict.items():
            self.add_input(key, val=listval[0])

        # Add outputs
        self.add_output(Rt.objective)

        # Finite difference all partials.
        self.declare_partials('*', '*', method='exact')

    def compute(self, inputs, outputs):
        """Launch subroutine to compute objective function."""
        # Add new variable value to the list in the dictionnay
        for key, (name, listval, minval, maxval, setcommand, getcommand) in design_var_dict.items():
            listval.append(inputs[key][0])

        # Evaluate the function to optimize
        outputs[Rt.objective] = one_iteration()


class constraint(om.ExplicitComponent):
    """Class to define the constraints or target that are not design variables."""

    def setup(self):
        """Create function inputs and outputs."""
        # Add output
        for key, (name, listval, lower_bound, upper_bound, getcommand) in res_var_dict.items():
            self.add_output(name, val=listval[0])

    def compute(self, inputs, outputs):
        """Retrieve values of constraints."""
        for key, (name, listval, lower_bound, upper_bound, getcmd) in res_var_dict.items():
            outputs[name] = listval[-1]

        # outputs['passengers'] = get_val()

# =============================================================================
#   FUNCTIONS
# =============================================================================


def run_routine():
    """
    Run optimisation with openmdao.

    Function 'run_routine' is used to define the optimisation problem for
    openmdao. The different parameter to define variables are passed through a
    global dictionnay (for now).

    Source:
        *http://openmdao.org/twodocs/versions/latest/getting_started/index.html

    """
    # sInitialize dictionnaries
    # init_dict()

    # Build the model
    prob = om.Problem()
    model = prob.model

    # Build model components
    indeps = model.add_subsystem('indeps', om.IndepVarComp())
    model.add_subsystem('objective', objective_function())
    model.add_subsystem('const', constraint())

    # Choose between optimizer or driver
    if Rt.type == 'DoE':
        if Rt.doetype == 'uniform':
            driver = prob.driver = om.DOEDriver(om.UniformGenerator(num_samples=Rt.samplesnb))
        elif Rt.doetype == 'fullfact':
            # 2->9 3->81
            driver = prob.driver = om.DOEDriver(om.FullFactorialGenerator(Rt.samplesnb))
    elif Rt.type == 'Optim':
        driver = prob.driver = om.ScipyOptimizeDriver()
        # SLSQP,COBYLA,shgo,TNC
        driver.options['optimizer'] = Rt.driver
        # driver.options['maxiter'] = 20
        driver.options['tol'] = 1e-2
        if Rt.driver == 'COBYLA':
            driver.opt_settings['catol'] = 0.06


    # Connect problem components to model components

    # Design variable
    for key, (name, listval, minval, maxval, setcommand, getcommand) in design_var_dict.items():
        norm = int(np.log10(abs(listval[0])+1)+1)
        indeps.add_output(key, listval[0], ref=norm, ref0=0)
        model.connect('indeps.'+key, 'objective.'+key)
        model.add_design_var('indeps.'+key, lower=minval, upper=maxval)

    # Constraints
    for key, (name, listval, minval, maxval, getcommand) in res_var_dict.items():
        # Select only one constrain
        if name in Rt.constraints:
            norm = int(np.log10(abs(listval[0])+1)+1)
            model.add_constraint('const.'+name, ref=norm, lower=-0.25, upper=0.25)

    # Objective function
    model.add_objective('objective.{}'.format(Rt.objective))

    # Recorder
    path  = optim_dir_path
    driver.add_recorder(om.SqliteRecorder(path + '/Driver_recorder.sql'))

    # Run
    prob.setup()
    prob.run_driver()
    prob.cleanup()

    # Results
    log.info('=========================================')
    log.info('min = ' + str(prob['objective.{}'.format(Rt.objective)]))

    for key, (name, listval, minval, maxval, setcommand, getcommand) in design_var_dict.items():
        log.info(name + ' = ' + str(prob['indeps.'+key]) + '\n Min :' + str(minval) + ' Max : ' + str(maxval))

    log.info('Variable history')
    for key, (name, listval, minval, maxval, setcommand, getcommand) in design_var_dict.items():
        log.info(name + ' => ' + str(listval))

    log.info('=========================================')

    # Generate plots, maybe make a dynamic plot
    opf.read_results(optim_dir_path, Rt.type)


def one_iteration():
    """
    Compute the objective function.

    Function 'one_iteration' will exectute in order all the module contained
    in '...' and extract the ... value from the last CPACS file, this value will
    be returned to the optimizer CPACSUpdater....

    """
    global counter
    counter += 1

    # Create the parameter in CPACS with 'CPACSUpdater' module
    cpacs_path = mi.get_toolinput_file_path('CPACSUpdater')
    cpacs_out_path = mi.get_tooloutput_file_path('CPACSUpdater')

    tixi = cpsf.open_tixi(cpacs_path)
    wkdir_path = ceaf.create_new_wkdir(Rt.date)
    WKDIR_XPATH = '/cpacs/toolspecific/CEASIOMpy/filesPath/wkdirPath'
    tixi.updateTextElement(WKDIR_XPATH, wkdir_path)

    # TODO: improve this part! (maybe move somewhere else)
    # To delete coef from previous iter
    if opf.get_aeromap_path(Rt.modules) != 'None':
        xpath = opf.get_aeromap_path(Rt.modules)
        aeromap_uid = cpsf.get_value(tixi, xpath + '/aeroMapUID')
        Coef = apmf.get_aeromap(tixi, aeromap_uid)
        apmf.delete_aeromap(tixi, aeromap_uid)
        apmf.create_empty_aeromap(tixi, aeromap_uid, 'test_optim')
        apmf.save_parameters(tixi, aeromap_uid, Coef)
        cpsf.close_tixi(tixi, cpacs_path)

    # Update the CPACS file with the parameters contained in design_var_dict
    update_cpacs_file(cpacs_path, cpacs_out_path, design_var_dict)

    # Save the CPACS file
    if counter % 1 == 0:
        file_copy_from = mi.get_tooloutput_file_path('CPACSUpdater')
        shutil.copy(file_copy_from, optim_dir_path+'/Geometry/'+'iter_{}.xml'.format(counter))

    # Run optimisation sub workflow
    wkf.copy_module_to_module('CPACSUpdater', 'out', Rt.modules[0], 'in')
    wkf.run_subworkflow(Rt.modules)
    wkf.copy_module_to_module(Rt.modules[-1], 'out', 'CPACSUpdater', 'in')

    # Extract results  TODO: improve this part
    cpacs_results_path = mi.get_tooloutput_file_path(Rt.modules[-1])
    log.info('Results will be extracted from:' + cpacs_results_path)
    tixi = cpsf.open_tixi(cpacs_results_path)

    # Update the constraints values
    update_res_var_dict(tixi)
    return compute_obj()


def compute_obj():
    """
    Interpret the objective variable command.

    Get all the values needed to compute the objective function and
    evaluates its expression.

    Returns
    -------
    None.

    """
    # Get variable keys from objective function string
    var_list = splt('[+*/-]', Rt.objective)

    # Create local variable and assign value
    for v in var_list:
        if not v.isdigit():
            exec('{} = res_var_dict["{}"][1][-1]'.format(v, v))

    result = eval(Rt.objective)
    log.info('Objective function {} : {}'.format(Rt.objective, result))
    # Evaluate objective function expression
    return -result


def routine_setup(modules, routine_type, modules_pre=[]):
    """
    Set up optimisation.

    Retrieve the list of modules to use in the optimization
    loop and launches the optimization process.

    """
    log.info('----- Start of Optimisation module -----')
    global Rt, design_var_dict, res_var_dict, optim_dir_path

    # Setup parameters of the routine
    Rt.type = routine_type
    Rt.modules = modules
    Rt.driver = 'COBYLA'
<<<<<<< HEAD
    Rt.objective = 'cl'
=======
    Rt.objective = 'cl/cd'
>>>>>>> 0432dc169a3578c01b80e6dbdb1980e2f497b180
    # Rt.design_vars =
    Rt.constraints = []
    Rt.date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    Rt.doetype = 'uniform'
    Rt.samplesnb = 3

    cpacs_path = mi.get_toolinput_file_path('Optimisation')

    # Create Optim folder for results
    tixi = cpsf.open_tixi(cpacs_path)
    wkdir = ceaf.get_wkdir_or_create_new(tixi)
    optim_dir_path = os.path.join(wkdir,Rt.type)
    if not os.path.isdir(optim_dir_path):
        os.mkdir(optim_dir_path)
        os.mkdir(optim_dir_path+'/Geometry')

    # Initiates dictionnaries
    res_var_dict, design_var_dict = init_dict(cpacs_path, modules, modules_pre)

    # Copy to CPACSUpdater to pass to next modules
    wkf.copy_module_to_module('Optimisation', 'in', 'CPACSUpdater', 'in')

    # Display routine info
    log.info('------ Problem description ------')
    log.info('Routine type : {}'.format(routine_type))
    log.info('Objective function : {}'.format(Rt.objective))
    [log.info('Design variables : {}'.format(k)) for k in design_var_dict.keys()]
    [log.info('constraints : {}'.format(k)) for k in res_var_dict.keys()]

    run_routine()

    log.info('----- End of Optimisation module -----')


if __name__ == '__main__':
    # Specify parameters already implemented in the SettingsGUI
    module_list = ['WeightConventional','PyTornado']
    rt_type = 'Optim'

    routine_setup(module_list, rt_type)
