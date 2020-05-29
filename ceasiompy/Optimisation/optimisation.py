"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Python version: >=3.6

| Author: Aidan jungo
| Creation: 2020-24-02
| Last modifiction: 2020-06-04

TODO:

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
import ceasiompy.utils.workflowfunctions as wkf
import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.moduleinterfaces as mi
import ceasiompy.utils.optimfunctions as opf
import ceasiompy.Optimisation.func.dictionnary as dct
import ceasiompy.Optimisation.func.tools as tls

from ceasiompy.CPACSUpdater.cpacsupdater import update_cpacs_file

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

# =============================================================================
#   GLOBAL VARIABLES
# =============================================================================

Rt = opf.Routine()
counter = 0

# =============================================================================
#   CLASSES
# =============================================================================


class objective_function(om.ExplicitComponent):
    """Class to define function and variables for openmdao."""

    def setup(self):
        """Create function inputs and outputs."""
        # Add inputs
        for name, (val_type, listval, minval, maxval, getcommand, setcommand) in optim_var_dict.items():
            # Normal case
            if val_type == 'des' and listval[0] not in ['-', 'True', 'False']:
                self.add_input(name, val=listval[0])
            # Boolean case
            # elif val_type == 'des' and listval[0] in ['True', 'False']:
            #     if listval[0] == 'True':
            #         self.add_discrete_input(name, val=1)
            #     else:
            #         self.add_discrete_input(name, val=0)

        # Add outputs
        self.add_output(Rt.objective)

        # Finite difference all partials.
        self.declare_partials('*', '*', method='exact')

    def compute(self, inputs, outputs):
        """Launch subroutine to compute objective function."""
        # Add new variable value to the list in the dictionnay
        for name, (val_type, listval, minval, maxval, getcommand, setcommand) in optim_var_dict.items():
            # Normal case
            if val_type == 'des' and listval[-1] not in ['-', 'True', 'False']:
                listval.append(inputs[name][0])
            # Boolean case
            # elif val_type == 'des' and listval[-1] in ['True', 'False']:
            #     if listval[-1] == 'True':
            #         listval.append(1)
            #     else:
            #         listval.append(0)

        # Evaluate the function to optimize
        outputs[Rt.objective] = one_iteration()


class constraint(om.ExplicitComponent):
    """Class to define the constraints or target that are not design variables."""

    def setup(self):
        """Create function inputs and outputs."""
        # Add output
        for name, (val_type, listval, minval, maxval, getcommand, setcommand) in optim_var_dict.items():
            # Normal case
            if val_type == 'const' and listval[0] not in ['-', 'True', 'False']:
                self.add_output(name, val=listval[0])
            # Boolean case
            # elif val_type == 'const' and listval[0] in ['True', 'False']:
            #     if listval[0] == 'True':
            #         self.add_discrete_output(name, val=1)
            #     else:
            #         self.add_discrete_output(name, val=0)

    def compute(self, inputs, outputs):
        """Retrieve values of constraints."""
        for name, (val_type, listval, minval, maxval, getcommand, setcommand) in optim_var_dict.items():
            # Normal case
            if val_type == 'const' and listval[-1] not in ['-', 'True', 'False']:
                outputs[name] = listval[-1]
            # Boolean case
            # elif val_type == 'const' and listval[-1] in ['True', 'False']:
            #     if listval[-1] == 'True':
            #         outputs[name] = 1
            #     else:
            #         outputs[name] = 0

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
    # Build the model
    prob = om.Problem()
    model = prob.model

    # Build model components
    indeps = model.add_subsystem('indeps', om.IndepVarComp())
    model.add_subsystem('objective', objective_function())
    model.add_subsystem('const', constraint())

    # Choose between optimizer or driver
    if Rt.type == 'DoE':
        if Rt.doetype.lower() == 'uniform':
            driver = prob.driver = om.DOEDriver(om.UniformGenerator(num_samples=Rt.samplesnb))
        elif Rt.doetype.lower() == 'fullfactorial':
            # 2->9 3->81
            driver = prob.driver = om.DOEDriver(om.FullFactorialGenerator(Rt.samplesnb))
    elif Rt.type == 'Optim':
        driver = prob.driver = om.ScipyOptimizeDriver()
        driver.options['optimizer'] = Rt.driver
        driver.options['maxiter'] = int(Rt.max_iter)
        driver.options['tol'] = Rt.tol
        if Rt.driver == 'COBYLA':
            driver.opt_settings['catol'] = 0.06

    # Connect problem components to model components

    # Design variable and constrains
    for name, (val_type, listval, minval, maxval, getcommand, setcommand) in optim_var_dict.items():
        if listval[0] not in ['-','True', 'False']:
            norm = round(np.log10(abs(float(listval[0]))+1)+1)
            if val_type == 'des':
                indeps.add_output(name, listval[0], ref=norm, ref0=0)
                model.connect('indeps.'+name, 'objective.'+name)
                model.add_design_var('indeps.'+name, lower=minval, upper=maxval)
            elif val_type == 'const':
                model.add_constraint('const.'+name, ref=norm, lower=minval, upper=maxval)
        # Boolean
        # else:
        #     if val_type == 'des':
        #         indeps.add_discrete_output(name, int(eval(listval[0])))
        #         model.connect('indeps.'+name, 'objective.'+name)
        #         model.add_design_var('indeps.'+name)
        #     elif val_type == 'const':
        #         model.add_constraint('const.'+name)

    # Objective function
    model.add_objective('objective.{}'.format(Rt.objective))

    # Recorder
    path = optim_dir_path
    driver.add_recorder(om.SqliteRecorder(path + '/Driver_recorder.sql'))

    # Run
    prob.setup()
    prob.run_driver()
    prob.cleanup()

    # Results
    log.info('=========================================')
    log.info('min = ' + str(prob['objective.{}'.format(Rt.objective)]))

    for name, (val_type, listval, minval, maxval, getcommand, setcommand) in optim_var_dict.items():
        if val_type == 'des':
            log.info(name + ' = ' + str(prob['indeps.'+name]) + '\n Min :' + str(minval) + ' Max : ' + str(maxval))

    log.info('Variable history :')

    for name, (val_type, listval, minval, maxval, getcommand, setcommand) in optim_var_dict.items():
        if val_type == 'des':
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

    # To delete coef from previous iter
    if tls.get_aeromap_path(Rt.modules) != 'None':
        xpath = tls.get_aeromap_path(Rt.modules)
        aeromap_uid = cpsf.get_value(tixi, xpath + '/aeroMapUID')
        Coef = apmf.get_aeromap(tixi, aeromap_uid)
        apmf.delete_aeromap(tixi, aeromap_uid)
        apmf.create_empty_aeromap(tixi, aeromap_uid, 'test_optim')
        apmf.save_parameters(tixi, aeromap_uid, Coef)
        cpsf.close_tixi(tixi, cpacs_path)

    # Update the CPACS file with the parameters contained in optim_var_dict
    update_cpacs_file(cpacs_path, cpacs_out_path, optim_var_dict)

    # Save the CPACS file
    if counter % Rt.save_iter == 0:
        file_copy_from = mi.get_tooloutput_file_path('CPACSUpdater')
        shutil.copy(file_copy_from, optim_dir_path+'/Geometry/'+'iter_{}.xml'.format(counter))

    # Run optimisation sub workflow
    wkf.copy_module_to_module('CPACSUpdater', 'out', Rt.modules[0], 'in')
    wkf.run_subworkflow(Rt.modules)
    wkf.copy_module_to_module(Rt.modules[-1], 'out', 'CPACSUpdater', 'in')

    # Extract results
    cpacs_results_path = mi.get_tooloutput_file_path(Rt.modules[-1])
    log.info('Results will be extracted from:' + cpacs_results_path)
    tixi = cpsf.open_tixi(cpacs_results_path)
    dct.update_dict(tixi, optim_var_dict)

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
        if not v.isdigit() and v != '':
            exec('{} = optim_var_dict["{}"][1][-1]'.format(v, v))

    result = eval(Rt.objective)
    log.info('Objective function {} : {}'.format(Rt.objective, result))
    # Evaluate objective function expression

    if Rt.minmax == 'min':
        return -result
    else:
        return result


def routine_setup(modules, routine_type, modules_pre=[]):
    """
    Set up optimisation.

    Retrieve the list of modules to use in the optimization
    loop and launches the optimization process.

    """
    log.info('----- Start of Optimisation module -----')

    global Rt, optim_var_dict, optim_dir_path
    cpacs_path = mi.get_toolinput_file_path('Optimisation')

    # Setup parameters of the routine
    Rt.type = routine_type
    Rt.modules = modules
    Rt.date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    # Create Optim folder for results
    tixi = cpsf.open_tixi(cpacs_path)
    wkdir = ceaf.get_wkdir_or_create_new(tixi)
    optim_dir_path = os.path.join(wkdir, Rt.type)
    if not os.path.isdir(optim_dir_path):
        os.mkdir(optim_dir_path)
        os.mkdir(optim_dir_path+'/Geometry')

    # Adds the initial parameters
    opf.first_run(cpacs_path, modules, modules_pre)
    Rt.get_user_inputs(cpacs_path)

    # Create dictionnary
    optim_var_dict = opf.create_variable_library(Rt, tixi, modules)

    # Copy to CPACSUpdater to pass to next modules
    wkf.copy_module_to_module('Optimisation', 'in', 'CPACSUpdater', 'in')

    # Display routine info
    log.info('------ Problem description ------')
    log.info('Routine type : {}'.format(routine_type))
    log.info('Objective function : {}'.format(Rt.objective))
    log.info('Variable recap')
    [log.info('{} : {}'.format(k, t[0])) for k, t in optim_var_dict.items()]

    run_routine()

    log.info('----- End of Optimisation module -----')


if __name__ == '__main__':
    # Specify parameters already implemented in the SettingsGUI

    log.info('This module is run automatically.')
