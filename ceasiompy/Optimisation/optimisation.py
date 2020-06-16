"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Python version: >=3.6

| Author: Aidan jungo
| Creation: 2020-24-02
| Last modifiction: 2020-06-04

Todo:
    * Investigate the implementation of discrete values and booleans
    * Standalone module to be implemented
    * Aeromap

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
import ceasiompy.CPACSUpdater.cpacsupdater as cpud

from ceasiompy.CPACSUpdater.cpacsupdater import update_cpacs_file

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])


# =============================================================================
#   GLOBAL VARIABLES
# =============================================================================

Rt = opf.Routine()
counter = 0

# =============================================================================
#   CLASSES
# =============================================================================
class aeromap_results(om.ExplicitComponent):
    """Class to define objective function in the subgroup of the aeromap case."""

    def setup(self):
        """Create inputs/outputs"""
        tixi = cpsf.open_tixi(opf.CPACS_OPTIM_PATH)
        xpath = tls.get_aeromap_path(Rt.modules)
        aeromap_uid = cpsf.get_value(tixi, xpath + '/aeroMapUID')
        Coef = apmf.get_aeromap(tixi, aeromap_uid)

        coef_dict = Coef.to_dict()
        for name, value in coef_dict.items():
            if name in ['mach','alt','aoa','aos']:
                self.add_input(name, val=value)
            else:
                self.add_output(name, val=value)

    def compute(self, inputs, outputs):
        """Search for best value of the objective function."""

        tixi = cpsf.open_tixi(cpacs_path)
        xpath = tls.get_aeromap_path(Rt.modules)
        aeromap_uid = cpsf.get_value(tixi, xpath + '/aeroMapUID')
        Coef = apmf.get_aeromap(tixi, aeromap_uid)

        coef_dict = Coef.to_dict()
        for name, (val_type, listval, minval, maxval, getcommand, setcommand) in optim_var_dict.items():
            # Normal case
            if val_type == 'des' and name in ['mach','alt','aoa','aos']:
                listval.append(inputs[name][0])
            elif val_type == 'des' and listval[-1] not in ['-', 'True', 'False']:
                listval.append(inputs[name][0])


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
        """Retrieve values of constraints from CPACS file."""
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

    Parameters
    ----------
    None.

    Returns
    -------
    None.

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
        if Rt.doedriver.lower() == 'uniform':
            driver = prob.driver = om.DOEDriver(om.UniformGenerator(num_samples=Rt.samplesnb))
        elif Rt.doedriver.lower() == 'fullfactorial':
            driver = prob.driver = om.DOEDriver(om.FullFactorialGenerator(Rt.samplesnb))
        elif Rt.doedriver.lower() == 'latinhypercube':
            driver = prob.driver = om.DOEDriver(om.LatinHypercubeGenerator(Rt.samplesnb))
    elif Rt.type == 'Optim':
        driver = prob.driver = om.ScipyOptimizeDriver()
        driver.options['optimizer'] = Rt.driver
        driver.options['maxiter'] = Rt.max_iter
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
    driver.add_recorder(om.SqliteRecorder(optim_dir_path + '/Driver_recorder.sql'))

    # Run
    prob.setup()
    prob.run_driver()
    prob.cleanup()

    # Results
    wkf.copy_module_to_module('CPACSUpdater', 'in', 'Optimisation', 'out')
    tls.save_results(opf.CSV_PATH, optim_dir_path, optim_var_dict)
    tls.read_results(optim_dir_path, Rt.type)
    tls.display_results(prob, optim_var_dict, Rt)


def one_iteration():
    """
    Compute the objective function.

    Function 'one_iteration' will exectute in order all the module contained
    in '...' and extract the ... value from the last CPACS file, this value will
    be returned to the optimizer CPACSUpdater....

    Parameters
    ----------
    None.

    Returns
    -------
    None.

    """
    global counter
    counter += 1

    # Create new Run folder
    tixi = cpsf.open_tixi(cpacs_path)
    wkdir_path = ceaf.create_new_wkdir(Rt.date)
    tixi.updateTextElement(opf.WKDIR_XPATH, wkdir_path)

    # Delete coef from previous iteration
    if tls.get_aeromap_path(Rt.modules) != 'None':
        xpath = tls.get_aeromap_path(Rt.modules)
        aeromap_uid = cpsf.get_value(tixi, xpath + '/aeroMapUID')
        Coef = apmf.get_aeromap(tixi, aeromap_uid)
        apmf.delete_aeromap(tixi, aeromap_uid)
        apmf.create_empty_aeromap(tixi, aeromap_uid, 'test_optim')
        apmf.save_parameters(tixi, aeromap_uid, Coef)
        cpsf.close_tixi(tixi, cpacs_path)

    # Set new variable values
    update_cpacs_file(cpacs_path, cpacs_out_path, optim_var_dict)

    # Save the CPACS file
    if counter % Rt.save_iter == 0:
        loc = '/Geometry/'+'iter_{}.xml'.format(counter)
        shutil.copy(cpacs_out_path, optim_dir_path+loc)

    # Run optimisation subworkflow
    wkf.copy_module_to_module('Optimisation', 'out', Rt.modules[0], 'in')
    wkf.run_subworkflow(Rt.modules)
    wkf.copy_module_to_module(Rt.modules[-1], 'out', 'Optimisation', 'in')

    # Extract result variables
    log.info('Results will be extracted from:' + cpacs_path)
    tixi = cpsf.open_tixi(cpacs_path)
    dct.update_dict(tixi, optim_var_dict)
    cpsf.close_tixi(tixi, cpacs_path)

    return compute_obj()


def compute_obj():
    """
    Interpret the objective variable command.

    Retrieve all the values that appear in the objective function and
    evaluates the mathematical operators that link them.

    Parameters
    ----------
    None.

    Returns
    -------
    result : float
    Objective function value

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


def create_routine_folder():
    """
    Create a folder in which all CEASIOMpy runs in the optimisation loop
    will be saved. This architecture may change in the future.

    Parameters
    ----------
    cpacs_path : str
        Path to file.

    Returns
    -------
    None.

    """
    global optim_dir_path

    tixi = cpsf.open_tixi(cpacs_path)
    wkdir = ceaf.get_wkdir_or_create_new(tixi)
    optim_dir_path = os.path.join(wkdir, Rt.type)

    if not os.path.isdir(optim_dir_path):
        os.mkdir(optim_dir_path)
        os.mkdir(optim_dir_path+'/Geometry')

    cpsf.get_value_or_default(tixi, opf.OPTWKDIR_XPATH,optim_dir_path)
    cpsf.close_tixi(tixi, cpacs_path)


def routine_setup(modules, routine_type, modules_pre=[]):
    """
    Set up optimisation.

    Retrieve the list of modules to use in the optimization
    loop and launches the optimization process.

    Parameters
    ----------
    modules : list
        Modules to run in the optimisation loop
    routine_type : str
        DoE or Optim
    modules_pre : list
        Modules that were run before the optimisation

    Returns
    -------
    None

    """
    log.info('----- Start of Optimisation module -----')

    global Rt, optim_var_dict, cpacs_path, cpacs_out_path
    cpacs_path = mi.get_toolinput_file_path('Optimisation')
    cpacs_out_path = mi.get_tooloutput_file_path('Optimisation')

    # Setup parameters of the routine
    Rt.date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    Rt.type = routine_type
    Rt.modules = modules

    create_routine_folder()

    # Adds the initial parameters
    opf.first_run(cpacs_path, modules, modules_pre)
    Rt.get_user_inputs(cpacs_path)

    optim_var_dict = opf.create_variable_library(Rt)

    # Display routine info
    log.info('------ Problem description ------')
    log.info('Routine type : {}'.format(routine_type))
    log.info('Objective function : {}'.format(Rt.objective))
    log.info('Variable recap')
    for k, t in optim_var_dict.items():
        log.info('{} : {}'.format(k, t[0]))

    run_routine()

    log.info('----- End of Optimisation module -----')


if __name__ == '__main__':

    log.info('This module must be run with the GUI for now.')
    wkf.copy_module_to_module('Optimisation', 'in', 'Optimisation', 'out')
