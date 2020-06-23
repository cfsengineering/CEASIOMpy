"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This module sets up and solves an optimisation problem with specified inputs
and outputs, read from a CSV file.

Python version: >=3.6

| Author: Vivien Riolo
| Creation: 2020-06-15
| Last modification: 2020-06-22

Todo:
    * List case / multiple objectives

"""
import os
import sys
import shutil
import datetime
import argparse
import openmdao.api as om
from tigl3 import geometry
from re import split as splt

import ceasiompy.utils.optimfunctions as opf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.moduleinterfaces as mif
import ceasiompy.utils.workflowfunctions as wkf
import ceasiompy.Optimisation.func.dictionnary as dct
import ceasiompy.Optimisation.func.tools as tls
import ceasiompy.CPACSUpdater.cpacsupdater as cpud

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

# =============================================================================
#   GLOBAL VARIABLES
# =============================================================================

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
#   CLASSES
# =============================================================================

class geom_param(om.ExplicitComponent):
    """ Classe to define  the geometric parameters"""

    def setup(self):
        """ Setup inputs only for the geometry"""
        global geom_dict
        # Create dictionnary with only the geometric parameters
        # i.e. which can be modified using the Tigl handler
        geom_dict = {k:v for k, v in optim_var_dict.items() if v[5]!='-'}

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
            if name in optim_var_dict:
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
                if var[0] == 'des':
                    self.add_input(entry.var_name, val = var[1][0])
                elif var[0] in ['const','obj']:
                    self.add_output(entry.var_name, val = var[1][0])

        # Outputs
        for entry in spec.cpacs_inout.outputs:
            if entry.var_name in optim_var_dict:
                var = optim_var_dict[entry.var_name]
                self.add_output(entry.var_name, val=var[1][0])
            elif 'aeromap' in entry.var_name:
                for name in ['altitude', 'machNumber',
                              'angleOfAttack', 'angleOfSideslip']:
                    if name in optim_var_dict:
                        var = optim_var_dict[name]
                        self.add_input(name, val=var[1][0])
                for name in ['cl', 'cd', 'cs', 'cml', 'cmd', 'cms']:
                    if name in optim_var_dict:
                        var = optim_var_dict[name]
                        self.add_output(name, val=var[1][0])
            # Add output by default as it may be an input for the next module
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


class objective(om.ExplicitComponent):
    """Take the objective values and compute the function"""

    def setup(self):
        """ Setup inputs and outputs"""
        var_list = splt('[+*/-]', Rt.objective)
        for var in var_list:
            self.add_input(var)
        self.add_output('Objective function')


    def compute(self, inputs, outputs):
        """Compute the objective expression"""
        global counter
        counter += 1
        var_list = splt('[+*/-]', Rt.objective)
        cpacs_path = mif.get_tooloutput_file_path(Rt.modules[-1])

        # Save the CPACS file for this iteration
        if counter%Rt.save_iter == 0:
            loc = optim_dir_path+'/Geometry/'+'iter_{}.xml'.format(counter)
            shutil.copy(cpacs_path, loc)

        # Add new variables to dictionnary
        tixi = cpsf.open_tixi(cpacs_path)
        dct.update_dict(tixi, optim_var_dict)

        # Change local wkdir for the next iteration
        tixi.updateTextElement(opf.WKDIR_XPATH,ceaf.create_new_wkdir(Rt.date))

        for v in var_list:
            if not v.isdigit() and v != '':
                exec('{} = inputs["{}"]'.format(v, v))

        result = eval(Rt.objective)
        if Rt.minmax == 'min':
            outputs['Objective function'] = -result
        else:
            outputs['Objective function'] = result

        cpsf.close_tixi(tixi, cpacs_path)


# =============================================================================
#   FUNCTIONS
# =============================================================================

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

    tixi = cpsf.open_tixi(opf.CPACS_OPTIM_PATH)
    wkdir = ceaf.create_new_wkdir()
    if not tixi.checkElement(opf.WKDIR_XPATH):
        cpsf.create_branch(tixi, WKDIR_XPATH)
    tixi.updateTextElement(opf.WKDIR_XPATH,wkdir)
    optim_dir_path = os.path.join(wkdir, Rt.type)

    if not os.path.isdir(optim_dir_path):
        os.mkdir(optim_dir_path)
    os.mkdir(optim_dir_path+'/Geometry')
    os.mkdir(optim_dir_path+'/Runs')

    # Dirty way to create a new path, may be changed
    cpsf.get_value_or_default(tixi, opf.OPTWKDIR_XPATH,optim_dir_path)

    cpsf.close_tixi(tixi, opf.CPACS_OPTIM_PATH)


def routine_launcher(Opt):
    """
    Run an optimisation routine or DoE using the OpenMDAO library.

    Parameters
    ----------
    Opt : class
        Indicates which modules to use and the routine type (Optim or DoE).

    Returns
    -------
    None.

    """
    global mod, counter, optim_var_dict, Rt

    counter = 0
    Rt = opf.Routine()
    Rt.type = Opt.optim_method
    Rt.modules = Opt.module_optim
    Rt.date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    ## Initialize CPACS file ##
    create_routine_folder()
    opf.first_run(Rt.modules)
    Rt.get_user_inputs(opf.CPACS_OPTIM_PATH)


    ## Instantiate components ##
    ivc = om.IndepVarComp()
    prob = om.Problem()
    geom = geom_param()
    obj = objective()
    optim_var_dict = opf.create_variable_library(Rt, optim_dir_path)


    ## Filling the components ##
    # Problem variables
    prob.model.add_subsystem('indeps', ivc, promotes=['*'])

    # Geometric parameters
    mod = [Rt.modules[0], Rt.modules[-1]]
    prob.model.add_subsystem('Geometry', geom, promotes=['*'])

    # Module inputs and outputs
    for name in Rt.modules:
        mod = name
        spec = mif.get_specs_for_module(name)
        if spec.cpacs_inout.inputs or spec.cpacs_inout.outputs:
                prob.model.add_subsystem(name, moduleComp(), promotes=['*'])

    # Objective function
    prob.model.add_subsystem('objective', obj, promotes=['*'])


    ## Defining problem parameters ##
    # Defining constraints and linking design variables to the ivc
    for name, (val_type, listval, minval, maxval,
               getcommand, setcommand) in optim_var_dict.items():
        if val_type == 'des' and listval[0] not in ['True','False', '-']:
            ivc.add_output(name, val=listval[0],lower=minval, upper=maxval)
            prob.model.add_design_var(name, lower=minval, upper=maxval)
        elif val_type == 'const':
            prob.model.add_constraint(name, lower=minval, upper=maxval)

    # Adding the objective function
    prob.model.add_objective('Objective function')


    ## Setting up the problem options ##
    # prob.driver = om.pyOptSparseDriver() #multifunc driver : NSGA2
    # prob.driver.options['optimizer'] = 'NSGA2'
    # prob.driver.options['Popsize'] = 50
    # prob.driver.options['maxGen'] = 50
    prob.driver = om.ScipyOptimizeDriver()
    prob.driver.options['optimizer'] = Rt.driver
    prob.driver.options['maxiter'] = Rt.max_iter
    prob.driver.options['tol'] = Rt.tol
    prob.driver.options['disp'] = True

    # Attaching a recorder and a diagramm visualizer
    prob.driver.add_recorder(om.SqliteRecorder(optim_dir_path+'/Driver_recorder.sql'))
    prob.driver.add_recorder(om.SqliteRecorder(optim_dir_path+'/circuit.sqlite'))

    # Setup the model hierarchy for OpenMDAO
    prob.setup()

    # Generate N2 model
    # om.n2(path+'/circuit.sqlite', outfile=path+'/circuit.html')

    # Run the model
    prob.run_driver()

    # Recap of the problem inputs/outputs
    prob.model.list_inputs()
    prob.model.list_outputs()

    tls.plot_results(optim_dir_path,'')


if __name__ == '__main__':

    #Creating a dummy class to pass the default arguments
    class Opt(): pass
    if len(sys.argv) > 2:
        Opt.optim_method = sys.argv[1]
        Opt.module_optim = sys.argv[2]
    else:
        Opt.optim_method = 'Optim'
        Opt.module_optim = ['WeightConventional', 'CPACS2SUMO', 'SUMOAutoMesh', 'SU2Run']
    routine_launcher(Opt)

