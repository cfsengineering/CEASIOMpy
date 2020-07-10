"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This module sets up and solves an optimisation problem or runs a design of
experiement with specified inputs and outputs that are parsed from a CSV file.

Python version: >=3.6

| Author: Vivien Riolo
| Creation: 2020-06-15
| Last modification: 2020-06-22

Todo:
    * List inputs or multiple objectives
    * Discrete variables : find elegant solution of implementation

"""
import os
import shutil
import numpy as np
import openmdao.api as om
from tigl3 import geometry # Called within eval() function
from re import split as splt

import ceasiompy.utils.optimfunctions as opf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.moduleinterfaces as mif
import ceasiompy.utils.workflowfunctions as wkf
import ceasiompy.utils.ceasiompyfunctions as ceaf

import ceasiompy.SMUse.smuse as smu
import ceasiompy.Optimisation.func.tools as tls
import ceasiompy.CPACSUpdater.cpacsupdater as cpud
import ceasiompy.Optimisation.func.dictionnary as dct

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

# =============================================================================
#   GLOBAL VARIABLES
# =============================================================================

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())

# =============================================================================
#   CLASSES
# =============================================================================

class geom_param(om.ExplicitComponent):
    """ Classe to define the geometric parameters"""

    def setup(self):
        """ Setup inputs only for the geometry"""
        for name, (val_type, listval, minval, maxval,
                   setcommand, getcommand) in geom_dict.items():
            if name in optim_var_dict:
                self.add_input(name, val=listval[0])


    def compute(self, inputs, outputs):
        """Update the geometry of the CPACS"""
        cpacs_path = mif.get_tooloutput_file_path(Rt.modules[-1])
        cpacs_path_out = mif.get_toolinput_file_path(Rt.modules[0])

        for name, (val_type, listval, minval, maxval,
                   setcommand, getcommand) in geom_dict.items():
            listval.append(inputs[name][0])
        cpud.update_cpacs_file(cpacs_path, cpacs_path_out, geom_dict)


class moduleComp(om.ExplicitComponent):
    """ Class to define each module in the problem as an independent component"""

    def __init__(self):
        """Add the module name that corresponds to the object being created"""
        om.ExplicitComponent.__init__(self)
        self.module_name = mod


    def setup(self):
        """ Setup inputs and outputs"""
        spec =  mif.get_specs_for_module(self.module_name)

        #Inputs
        for entry in spec.cpacs_inout.inputs:
            if entry.var_name in optim_var_dict:
                var = optim_var_dict[entry.var_name]
                # if entry.var_type == int:
                #     self.add_discrete_input(entry.var_name, val = var[1][0])
                # else:
                self.add_input(entry.var_name, val=var[1][0])
            elif entry.var_name not in ['']:
                self.add_input(entry.var_name)

        # Outputs
        for entry in spec.cpacs_inout.outputs:
            if entry.var_name in optim_var_dict:
                var = optim_var_dict[entry.var_name]
                # if entry.var_type == int:
                #     self.add_discrete_output(entry.var_name, val=var[1][0])
                # else:
                self.add_output(entry.var_name, val=var[1][0])
            elif 'aeromap' in entry.var_name:
                # Condition to avoid conflict with skinfriction
                is_skf = (self.module_name == 'SkinFriction')
                if (skf and is_skf) or (not skf and not is_skf):
                    for name in ['altitude', 'machNumber',
                                  'angleOfAttack', 'angleOfSideslip']:
                        if name in optim_var_dict:
                            var = optim_var_dict[name]
                            self.add_input(name, val=var[1][0])
                    for name in ['cl', 'cd', 'cs', 'cml', 'cmd', 'cms']:
                        if name in optim_var_dict:
                            var = optim_var_dict[name]
                            if tls.is_digit(var[1][0]):
                                self.add_output(name, val=var[1][0])
                            else:
                                self.add_output(name)
            else:
                self.add_output(entry.var_name)


    def compute(self, inputs, outputs):
        """Launches the module"""

        # Updating inputs in CPACS file
        cpacs_path = mif.get_toolinput_file_path(self.module_name)
        tixi = cpsf.open_tixi(cpacs_path)
        for name in inputs:
            if name in optim_var_dict:
                xpath = optim_var_dict[name][4]
                cpsf.add_float_vector(tixi, xpath, inputs[name])
        cpsf.close_tixi(tixi, cpacs_path)

        # Running the module
        wkf.run_subworkflow([self.module_name])

        # Feeding CPACS file restults to outputs
        cpacs_path = mif.get_tooloutput_file_path(self.module_name)
        tixi = cpsf.open_tixi(cpacs_path)
        for name in outputs:
            if name in optim_var_dict:
                xpath = optim_var_dict[name][4]
                outputs[name] = cpsf.get_value(tixi, xpath)

        # Copy CPACS to input folder of next module
        index = Rt.modules.index(self.module_name)+1
        if index != len(Rt.modules):
            cpacs_path = mif.get_toolinput_file_path(Rt.modules[index])
        else:
            cpacs_path = mif.get_toolinput_file_path(Rt.modules[0])
        cpsf.close_tixi(tixi, cpacs_path)


class surrogate_model(om.ExplicitComponent):
    """Uses a surrogate model to make a prediction"""

    def setup(self):
        """Setup inputs and outputs"""
        # Take CPACS file from the optimisation
        cpacs_path = mif.get_toolinput_file_path(MODULE_NAME)
        tixi = cpsf.open_tixi(cpacs_path)
        file = cpsf.get_value_or_default(tixi, smu.PREDICT_XPATH+'modelFile', '')
        cpsf.close_tixi(tixi, cpacs_path)

        self.Model = smu.load_surrogate(file)

        df = self.Model.df
        df.set_index('Name')
        for name in df.index :
            if df[name]['type'] == 'obj':
                self.add_output(name)
            elif df[name]['type'] == 'des':
                self.add_input(name)

    def compute(self, inputs, outputs):
        """Make a prediction"""

        df = self.Model.df
        x = df.loc[[i for i,v in enumerate(df['type']) if v == 'des']]
        for name in x['Name']:
            x.append(inputs[name])

        x = np.array([x])
        yp = self.Model.sm.predict_values(x)
        y = df.loc[[i for i, v in enumerate(df['type']) if v == 'obj']]
        y.set_index('Name')
        smu.write_outputs(y, yp)
        for i, name in enumerate(y.index):
            outputs[name] = yp[0][i]


class objective(om.ExplicitComponent):
    """Class to compute the objective function(s)"""

    def setup(self):
        """ Setup inputs and outputs"""
        declared = []
        for obj in Rt.objective:
            var_list = splt('[+*/-]', obj)
            for var in var_list:
                if var not in declared:
                    self.add_input(var)
                    declared.append(var)
            self.add_output('Objective function '+obj)


    def compute(self, inputs, outputs):
        """Compute the objective expression"""
        global counter
        counter += 1
        cpacs_path = mif.get_tooloutput_file_path(Rt.modules[-1])

        # Save the CPACS file for this iteration
        if counter%Rt.save_iter == 0:
            loc = optim_dir_path+'/Geometry/'+'iter_{}.xml'.format(counter)
            shutil.copy(cpacs_path, loc)

        # Add new variables to dictionnary
        tixi = cpsf.open_tixi(cpacs_path)
        dct.update_dict(tixi, optim_var_dict)

        # Change local wkdir for the next iteration
        tixi.updateTextElement(opf.WKDIR_XPATH,ceaf.create_new_wkdir(optim_dir_path))

        for obj in Rt.objective:
            var_list = splt('[+*/-]', obj)
            for v in var_list:
                if not v.isdigit() and v != '':
                    exec('{} = inputs["{}"]'.format(v, v))
            result = eval(obj)

            if Rt.minmax == 'min':
                outputs['Objective function '+obj] = -result
            else:
                outputs['Objective function '+obj] = result

        cpsf.close_tixi(tixi, cpacs_path)


# =============================================================================
#   FUNCTIONS
# =============================================================================

def create_routine_folder():
    """Create the working dicrectory of the routine.

    Create a folder in which all CEASIOMpy runs and routine parameters will be
    saved. This architecture may change in the future.

    Args:
        None.

    Returns:
        None.

    """
    global optim_dir_path, Rt

    # Create the main working directory
    tixi = cpsf.open_tixi(opf.CPACS_OPTIM_PATH)
    wkdir = ceaf.get_wkdir_or_create_new(tixi)
    optim_dir_path = os.path.join(wkdir, Rt.type)
    Rt.date = wkdir[-19:]

    # Save the path to the directory in the CPACS
    if tixi.checkElement(opf.OPTWKDIR_XPATH):
        tixi.removeElement(opf.OPTWKDIR_XPATH)
    cpsf.create_branch(tixi, opf.OPTWKDIR_XPATH)
    tixi.updateTextElement(opf.OPTWKDIR_XPATH,optim_dir_path)

    # Add subdirectories
    if not os.path.isdir(optim_dir_path):
        os.mkdir(optim_dir_path)
        os.mkdir(optim_dir_path+'/Geometry')
        os.mkdir(optim_dir_path+'/Runs')
    else:
        index = 2
        optim_dir_path = optim_dir_path + str(index)
        while os.path.isdir(optim_dir_path):
            index += 1
            optim_dir_path = optim_dir_path.split(Rt.type)[0]+Rt.type+str(index)
        os.mkdir(optim_dir_path)
        os.mkdir(optim_dir_path+'/Geometry')
        os.mkdir(optim_dir_path+'/Runs')
    tixi.updateTextElement(opf.OPTWKDIR_XPATH,optim_dir_path)

    cpsf.close_tixi(tixi, opf.CPACS_OPTIM_PATH)


def driver_setup(prob):
    """Change settings of the driver

    Here the type of the driver has to be selected, wether it will be an
    optimisation driver or a DoE driver. In both cases there are multiple
    options to choose from to tune the driver.
    Two recorders are then attached to the driver for results and N2 plotting.

    Args:
        prob (om.Problem object) : Instance of the Problem class that is used
        to define the current routine.

    Returns:
        None.

    """
    if Rt.type == 'Optim':
        # TBD
        # if len(Rt.objective) > 1 and False:
        #     log.info("""More than 1 objective function, the driver will
        #              automatically be set to NSGA2""")
        #     prob.driver = om.pyOptSparseDriver() # multifunc driver : NSGA2
        #     prob.driver.options['optimizer'] = 'NSGA2'
        #     prob.driver.opt_settings['PopSize'] = 7
        #     prob.driver.opt_settings['maxGen'] = Rt.max_iter
        # else:
        prob.driver = om.ScipyOptimizeDriver()
        prob.driver.options['optimizer'] = Rt.driver
        prob.driver.options['maxiter'] = Rt.max_iter
        prob.driver.options['tol'] = Rt.tol
        prob.driver.options['disp'] = True
    else:
        if Rt.doedriver == 'Uniform':
            driver_type = om.UniformGenerator(num_samples=Rt.samplesnb)
        elif Rt.doedriver == 'LatinHypercube':
            driver_type = om.LatinHypercubeGenerator(samples=Rt.samplesnb)
        elif Rt.doedriver == 'FullFactorial':
            driver_type = om.FullFactorialGenerator(levels=Rt.samplesnb)
        prob.driver = om.DOEDriver(driver_type)
        prob.driver.options['run_parallel'] = True
        prob.driver.options['procs_per_model'] = 1

    ## Attaching a recorder and a diagramm visualizer ##
    prob.driver.recording_options['record_inputs'] = True
    prob.driver.add_recorder(om.SqliteRecorder(optim_dir_path+'/circuit.sqlite'))
    prob.driver.add_recorder(om.SqliteRecorder(optim_dir_path+'/Driver_recorder.sql'))


def add_subsystems(prob):
    """Add subsystems to problem.

    All subsystem classes are added to the problem model.

    Args:
        prob (om.Problem object): Current problem that is being defined
        ivc (om.IndepVarComp object): Independent variables of the problem

    Returns:
        None.

    """
    global mod, geom_dict, skf
    geom = geom_param()
    obj = objective()

    # Independent variables
    prob.model.add_subsystem('indeps', ivc, promotes=['*'])

    # Geometric parameters
    mod = [Rt.modules[0], Rt.modules[-1]]
    geom_dict = {k:v for k, v in optim_var_dict.items() if v[5]!='-'}
    if geom_dict:
        prob.model.add_subsystem('Geometry', geom, promotes=['*'])

    # Deal with the SkinFriction case
    skf = False
    if 'SkinFriction' in Rt.modules:
        skf = True

    # Modules
    for name in Rt.modules:
        mod = name
        spec = mif.get_specs_for_module(name)
        if spec.cpacs_inout.inputs or spec.cpacs_inout.outputs:
            prob.model.add_subsystem(name, moduleComp(), promotes=['*'])

    # Objectives
    prob.model.add_subsystem('objective', obj, promotes=['*'])


def add_parameters(prob):
    """Add problem parameters.

    In this function all the problem parameters, namely the constraints,
    design variables and objective functions, are added to the problem model.

    Args:
        prob (om.Problem object): Current problem that is being defined
        ivc (om.IndepVarComp object): Independent variables of the problem

    Returns:
        None.
    """
    # Defining constraints and linking design variables to the ivc
    for name, (val_type, listval, minval, maxval,
               getcommand, setcommand) in optim_var_dict.items():
        if val_type == 'des' and listval[0] not in ['True','False', '-']:
            prob.model.add_design_var(name, lower=minval, upper=maxval)
            ivc.add_output(name, val=listval[0])
        elif val_type == 'const':
            prob.model.add_constraint(name, lower=minval, upper=maxval)

    # Adding the objective functions, multiple objectives TBD in SciPyOpt
    # for o in Rt.objective:
    #     prob.model.add_objective('Objective function '+o)
    prob.model.add_objective('Objective function '+Rt.objective[0])


def routine_launcher(Opt):
    """Run an optimisation routine or DoE using the OpenMDAO library.

    This function launches the setup for the routine by setting up the problem
    with the OpenMDAO component, creating of reading a file containing all the
    problem parameters and launching the driver. It also specifies where to
    save the case recordings and launches the results plotting at the end of
    the routine.

    Args:
        Opt (class) : Indicates which modules to use and the routine type
        (Optim or DoE).

    Returns:
        None.

    """
    global counter, optim_var_dict, Rt, skf, ivc

    counter = 0
    Rt = opf.Routine()
    Rt.type = Opt.optim_method
    Rt.modules = Opt.module_optim

    ## Initialize CPACS file and problem dictionary ##
    create_routine_folder()

    opf.first_run(Rt.modules)

    Rt.get_user_inputs(opf.CPACS_OPTIM_PATH)
    optim_var_dict = opf.create_variable_library(Rt, optim_dir_path)

    ## Instantiate components and subsystems ##
    prob = om.Problem()
    ivc = om.IndepVarComp()

    ## Add subsystems to problem ##
    add_subsystems(prob)

    ## Defining problem parameters ##
    add_parameters(prob)

    ## Setting up the problem options ##
    driver_setup(prob)

    ## Setup the model hierarchy for OpenMDAO ##
    prob.setup()

    ## Run the model ##
    prob.run_driver()

    ## Generate N2 scheme ##
    om.n2(optim_dir_path+'/circuit.sqlite', optim_dir_path+'/circuit.html', False)

    ## Recap of the problem inputs/outputs ##
    prob.model.list_inputs()
    prob.model.list_outputs()

    ## Results processing ##
    tls.plot_results(optim_dir_path,'', optim_var_dict)
    tls.save_results(optim_dir_path, optim_var_dict)

    wkf.copy_module_to_module(Rt.modules[-1], 'out', 'Optimisation', 'out')


if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    wkf.run_subworkflow('WorkflowCreator')

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
