"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This module sets up and solves an optimisation problem or runs a design of
experiement with specified inputs and outputs that are parsed from a CSV file.

Python version: >=3.7

| Author: Vivien Riolo
| Creation: 2020-06-15

Todo:
    * Vector inputs or multiple objectives
    * Implement discrete variable with another solver
    * Find a way to avoid the first run

"""

import os
from pathlib import Path
import shutil
from re import split as splt
import numpy as np
import openmdao.api as om
from tigl3 import geometry  # Called within eval() function

import ceasiompy.SMUse.smuse as smu
import ceasiompy.Optimisation.func.tools as tls
import ceasiompy.Optimisation.func.optimfunctions as opf
import ceasiompy.CPACSUpdater.cpacsupdater as cpud
import ceasiompy.Optimisation.func.dictionnary as dct

from cpacspy.cpacspy import CPACS
from cpacspy.utils import PARAMS, COEFS
from cpacspy.cpacsfunctions import (
    add_float_vector,
    create_branch,
    get_value,
    open_tixi,
)

from ceasiompy.utils.ceasiompyutils import (
    copy_module_to_module,
    get_results_directory,
    run_subworkflow,
)
import ceasiompy.utils.moduleinterfaces as mif

from ceasiompy.utils.xpath import OPTWKDIR_XPATH, OPTIM_XPATH


from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

# =============================================================================
#   GLOBAL VARIABLES
# =============================================================================

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())

mod = []
counter = 0
# skf = False
geom_dict = {}
optim_var_dict = {}
Rt = opf.Routine()
am_dict = {}

# =============================================================================
#   CLASSES
# =============================================================================


class Geom_param(om.ExplicitComponent):
    """Classe to define the geometric parameters"""

    def setup(self):
        """Setup inputs only for the geometry"""
        for name, infos in geom_dict.items():
            if name in optim_var_dict:
                self.add_input(name, val=infos[1][0])

    def compute(self, inputs, outputs):
        """Update the geometry of the CPACS"""
        cpacs_path = mif.get_tooloutput_file_path(Rt.modules[-1])
        cpacs_path_out = mif.get_toolinput_file_path(Rt.modules[0])

        for name, infos in geom_dict.items():
            infos[1].append(inputs[name][0])
        cpud.update_cpacs_file(cpacs_path, cpacs_path_out, geom_dict)


class ModuleComp(om.ExplicitComponent):
    """Class to define each module in the problem as an independent component"""

    def __init__(self):
        """Add the module name that corresponds to the object being created"""
        om.ExplicitComponent.__init__(self)
        self.module_name = mod

    def setup(self):
        """Setup inputs and outputs"""
        declared = []
        spec = mif.get_specs_for_module(self.module_name)

        # Inputs
        for entry in spec.cpacs_inout.inputs:
            if entry.var_name in declared:
                log.info("Already declared")
            elif entry.var_name in optim_var_dict:
                var = optim_var_dict[entry.var_name]
                if entry.var_name in optim_var_dict:
                    self.add_input(entry.var_name, val=var[1][0])
                    declared.append(entry.var_name)

        if declared == []:
            self.add_input(self.module_name + "_in")
        declared = []

        # Outputs
        # To remove
        # is_skf = (self.module_name == 'SkinFriction')

        for entry in spec.cpacs_inout.outputs:
            # Replace special characters from the name of the entry and checks for accronyms
            entry.var_name = tls.change_var_name(entry.var_name)

            if entry.var_name in declared:
                log.info("Already declared")
            elif entry.var_name in optim_var_dict:
                var = optim_var_dict[entry.var_name]
                self.add_output(entry.var_name, val=var[1][0])
                declared.append(entry.var_name)
            elif (
                "aeromap" in entry.var_name and self.module_name == last_am_module
            ):  # == 'PyTornado':  #not skf^is_skf:
                # Condition to avoid any conflict with skinfriction
                for name in PARAMS:
                    if name in optim_var_dict:
                        var = optim_var_dict[name]
                        self.add_input(name, val=var[1][0])
                        declared.append(entry.var_name)
                for name in COEFS:
                    if name in optim_var_dict:
                        var = optim_var_dict[name]
                        if tls.is_digit(var[1][0]):
                            self.add_output(name, val=var[1][0])
                        else:
                            self.add_output(name)
                        declared.append(entry.var_name)

        if declared == []:
            self.add_output(self.module_name + "_out")

    def compute(self, inputs, outputs):
        """Launches the module"""

        # Updating inputs in CPACS file
        cpacs_path = mif.get_toolinput_file_path(self.module_name)
        tixi = open_tixi(cpacs_path)
        for name in inputs:
            if name in optim_var_dict:
                xpath = optim_var_dict[name][4]
                # Change only the first vector value for aeromap param
                if name in PARAMS:
                    size = tixi.getVectorSize(xpath)
                    v = list(tixi.getFloatVector(xpath, size))
                    v.pop(0)
                    v.insert(0, inputs[name])
                    tixi.updateFloatVector(xpath, v, size, "%g")
                else:
                    add_float_vector(tixi, xpath, inputs[name])
        tixi.save(cpacs_path)

        # Running the module
        run_subworkflow([self.module_name])

        # Feeding CPACS file results to outputs
        cpacs_path = mif.get_tooloutput_file_path(self.module_name)
        tixi = open_tixi(cpacs_path)
        for name in outputs:
            if name in optim_var_dict:
                xpath = optim_var_dict[name][4]
                if name in COEFS:
                    val = get_value(tixi, xpath)
                    if isinstance(val, str):
                        val = val.split(";")
                        outputs[name] = val[0]
                    else:
                        outputs[name] = val
                else:
                    outputs[name] = get_value(tixi, xpath)

        # Copy CPACS to input folder of next module
        index = Rt.modules.index(self.module_name) + 1
        if index != len(Rt.modules):
            cpacs_path = mif.get_toolinput_file_path(Rt.modules[index])
        else:
            cpacs_path = mif.get_toolinput_file_path(Rt.modules[0])
        tixi.save(cpacs_path)


class SmComp(om.ExplicitComponent):
    """Uses a surrogate model to make a prediction"""

    def setup(self):
        """Setup inputs and outputs"""
        # Take CPACS file from the optimisation
        cpacs_path = mif.get_toolinput_file_path("SMUse")
        tixi = open_tixi(cpacs_path)
        self.Model = smu.load_surrogate(tixi)
        tixi.save(cpacs_path)

        df = self.Model.df
        df.set_index("Name", inplace=True)
        for name in df.index:
            if df.loc[name, "type"] == "obj":
                self.add_output(name)
            elif df.loc[name, "type"] == "des":
                self.add_input(name)

        self.xd = df.loc[[name for name in df.index if df.loc[name, "type"] == "des"]]
        self.yd = df.loc[[name for name in df.index if df.loc[name, "type"] == "obj"]]

    def compute(self, inputs, outputs):
        """Make a prediction"""
        xp = []
        for name in self.xd.index:
            xp.append(inputs[name][0])

        xp = np.array([xp])
        yp = self.Model.sm.predict_values(xp)

        for i, name in enumerate(self.yd.index):
            outputs[name] = yp[0][i]

        # Write the inouts to the CPACS
        cpacs_path = mif.get_toolinput_file_path("SMUse")
        tixi = open_tixi(cpacs_path)
        smu.write_inouts(self.xd, xp, tixi)
        smu.write_inouts(self.yd, yp, tixi)
        cpacs_path_out = mif.get_tooloutput_file_path("SMUse")
        tixi.save(cpacs_path_out)


class Objective(om.ExplicitComponent):
    """Class to compute the objective function(s)"""

    def setup(self):
        """Setup inputs and outputs"""
        declared = []
        for obj in Rt.objective:
            var_list = splt("[+*/-]", obj)
            for v in var_list:
                if v not in declared:
                    self.add_input(v)
                    declared.append(v)
            self.add_output("Objective function " + obj)

    def compute(self, inputs, outputs):
        """Compute the objective expression"""
        global counter
        counter += 1
        cpacs_path = mif.get_tooloutput_file_path(Rt.modules[-1])

        # Save the CPACS file for this iteration
        if counter % Rt.save_iter == 0:
            loc = optim_dir_path + "/Geometry/" + "iter_{}.xml".format(counter)
            shutil.copy(cpacs_path, loc)
            log.info("Copy current CPACS to " + optim_dir_path)

        # Add new variables to dictionnary
        cpacs = CPACS(cpacs_path)

        dct.update_dict(cpacs.tixi, optim_var_dict)

        # Save the whole aeromap if needed
        if Rt.use_aeromap:
            dct.update_am_dict(cpacs, Rt.aeromap_uid, am_dict)

        # Change local wkdir for the next iteration
        # TODO: ......

        for obj in Rt.objective:
            var_list = splt("[+*/-]", obj)
            for v in var_list:
                if not v.isdigit() and v != "":
                    exec('{} = inputs["{}"]'.format(v, v))
            result = eval(obj)

            if Rt.minmax == "min":
                outputs["Objective function " + obj] = result
            else:
                outputs["Objective function " + obj] = -result

        cpacs.save_cpacs(cpacs_path, overwrite=True)
        copy_module_to_module(Rt.modules[-1], "out", Rt.modules[0], "in")


# =============================================================================
#   FUNCTIONS
# =============================================================================

# TODO: Remove this when the new optimisation routine is ready
# def create_routine_folder():
#     """Create the working dicrectory of the routine.

#     Create a folder in which all CEASIOMpy runs and routine parameters will be
#     saved. This architecture may change in the future. For now the architecture
#     of the folder is as such :

#     > CEASIOMpy_Run_XX-XX-XX
#         -> Optim
#             --> Geometry
#             --> Runs
#                 ---> Run_XX-XX-XX
#         -> Optim2
#             |
#         -> OptimX
#         -> DoE

#     Args:
#         None.

#     """

#     global optim_dir_path, Rt

#     # Create the main working directory
#     tixi = open_tixi(opf.CPACS_OPTIM_PATH)

#     wkdir = get_results_directory("Optimisation")

#     optim_dir_path = os.path.join(wkdir, Rt.type)
#     Rt.date = wkdir[-19:]

#     # Save the path to the directory in the CPACS
#     if tixi.checkElement(OPTWKDIR_XPATH):
#         tixi.removeElement(OPTWKDIR_XPATH)
#     create_branch(tixi, OPTWKDIR_XPATH)
#     tixi.updateTextElement(OPTWKDIR_XPATH, optim_dir_path)

#     # Add subdirectories
#     if not os.path.isdir(optim_dir_path):
#         os.mkdir(optim_dir_path)
#         os.mkdir(optim_dir_path + "/Geometry")
#         os.mkdir(optim_dir_path + "/Runs")
#     else:
#         index = 2
#         optim_dir_path = optim_dir_path + str(index)
#         while os.path.isdir(optim_dir_path):
#             index += 1
#             optim_dir_path = optim_dir_path.split(Rt.type)[0] + Rt.type + str(index)
#         os.mkdir(optim_dir_path)
#         os.mkdir(optim_dir_path + "/Geometry")
#         os.mkdir(optim_dir_path + "/Runs")
#     tixi.updateTextElement(OPTWKDIR_XPATH, optim_dir_path)

#     tixi.save(opf.CPACS_OPTIM_PATH)


def driver_setup(prob):
    """Change settings of the driver

    Here the type of the driver has to be selected, wether it will be an
    optimisation driver or a DoE driver. In both cases there are multiple
    options to choose from to tune the driver.
    Two recorders are then attached to the driver for results and N2 plotting.

    Args:
        prob (om.Problem object) : Instance of the Problem class that is used
        to define the current routine.

    """

    if Rt.type == "Optim":
        # TBD : Genetic algorithm
        # if len(Rt.objective) > 1 and False:
        #     log.info("""More than 1 objective function, the driver will
        #              automatically be set to NSGA2""")
        #     prob.driver = om.pyOptSparseDriver() # multifunc driver : NSGA2
        #     prob.driver.options['optimizer'] = 'NSGA2'
        #     prob.driver.opt_settings['PopSize'] = 7
        #     prob.driver.opt_settings['maxGen'] = Rt.max_iter
        # else:
        prob.driver = om.ScipyOptimizeDriver()
        prob.driver.options["optimizer"] = Rt.driver
        prob.driver.options["maxiter"] = Rt.max_iter
        prob.driver.options["tol"] = Rt.tol
        prob.driver.options["disp"] = True
    elif Rt.type == "DoE":
        if Rt.doedriver == "Uniform":
            driver_type = om.UniformGenerator(num_samples=Rt.samplesnb)
        elif Rt.doedriver == "LatinHypercube":
            driver_type = om.LatinHypercubeGenerator(samples=Rt.samplesnb)
        elif Rt.doedriver == "FullFactorial":
            driver_type = om.FullFactorialGenerator(levels=Rt.samplesnb)
        elif Rt.doedriver == "CSVGenerated":
            file = opf.gen_doe_csv(Rt.user_config)
            driver_type = om.CSVGenerator(file)
        prob.driver = om.DOEDriver(driver_type)
        prob.driver.options["run_parallel"] = True
        prob.driver.options["procs_per_model"] = 1
    else:
        log.error("Type of optimisation not recognize!!!")

    #  Attaching a recorder and a diagramm visualizer ##
    prob.driver.recording_options["record_inputs"] = True
    prob.driver.add_recorder(om.SqliteRecorder(str(optim_dir_path) + "/circuit.sqlite"))
    prob.driver.add_recorder(om.SqliteRecorder(str(optim_dir_path) + "/Driver_recorder.sql"))


def add_subsystems(prob, ivc):
    """Add subsystems to problem.

    All subsystem classes are added to the problem model.

    Args:
        prob (om.Problem object): Current problem that is being defined
        ivc (om.IndepVarComp object): Independent variables of the problem

    """

    global mod, geom_dict
    geom = Geom_param()
    obj = Objective()

    # Independent variables
    prob.model.add_subsystem("indeps", ivc, promotes=["*"])

    # Geometric parameters
    mod = [Rt.modules[0], Rt.modules[-1]]
    geom_dict = {k: v for k, v in optim_var_dict.items() if v[5] != "-"}
    if geom_dict:
        prob.model.add_subsystem("Geometry", geom, promotes=["*"])

    # Find last module to use an aeromap
    am_module = ["SU2Run", "PyTornado", "SkinFriction"]
    global last_am_module
    last_am_module = ""
    for name in Rt.modules:
        if name in am_module:
            last_am_module = name

    # Modules
    for n, name in enumerate(Rt.modules):
        if name == "SMUse":
            prob.model.add_subsystem(name, SmComp(), promotes=["*"])
        else:
            mod = name
            spec = mif.get_specs_for_module(name)
            if spec.cpacs_inout.inputs or spec.cpacs_inout.outputs:
                prob.model.add_subsystem(name, ModuleComp(), promotes=["*"])

    # Objectives
    prob.model.add_subsystem("objective", obj, promotes=["*"])


def add_parameters(prob, ivc):
    """Add problem parameters.

    In this function all the problem parameters, namely the constraints,
    design variables and objective functions, are added to the problem model,
    with their respective boundaries if they are given.

    Args:
        prob (om.Problem object): Current problem that is being defined
        ivc (om.IndepVarComp object): Independent variables of the problem

    """

    # Defining constraints and linking design variables to the ivc
    for name, (
        val_type,
        listval,
        minval,
        maxval,
        getcommand,
        setcommand,
    ) in optim_var_dict.items():
        if val_type == "des" and listval[-1] not in ["True", "False", "-"]:
            if tls.is_digit(minval) and tls.is_digit(maxval):
                prob.model.add_design_var(name, lower=float(minval), upper=float(maxval))
            elif tls.is_digit(minval):
                prob.model.add_design_var(name, lower=float(minval))
            elif tls.is_digit(maxval):
                prob.model.add_design_var(name, upper=float(maxval))
            else:
                prob.model.add_design_var(name)
            ivc.add_output(name, val=listval[-1])
        elif val_type == "const":
            if tls.is_digit(minval) and tls.is_digit(maxval):
                prob.model.add_constraint(name, lower=float(minval), upper=float(maxval))
            elif tls.is_digit(minval):
                prob.model.add_constraint(name, lower=float(minval))
            elif tls.is_digit(maxval):
                prob.model.add_constraint(name, upper=float(maxval))
            else:
                prob.model.add_constraint(name)

    # Adding the objective functions, multiple objectives TBD in SciPyOpt
    # for o in Rt.objective:
    #     prob.model.add_objective('Objective function '+o)
    prob.model.add_objective("Objective function " + Rt.objective[0])


def create_om_problem(prob):
    """Create a model for an optimisation problem or a DoE.

    Args:
        prob (om.Problem object): Current problem that is being defined

    Returns:
        None.

    """
    ivc = om.IndepVarComp()

    # Add subsystems to problem ##
    add_subsystems(prob, ivc)

    # Defining problem parameters ##
    add_parameters(prob, ivc)

    # Setting up the problem options ##
    driver_setup(prob)

    # Setup the model hierarchy for OpenMDAO ##
    prob.setup()


def generate_results(prob):
    """Create all results from the routine.

    Extract the data that has been retrieved by OpenMDAO and use them to
    generate, plot and save results.

    Args:
        prob (om.Problem object): Current problem that is being defined

    """

    if Rt.use_aeromap and Rt.type == "DoE":
        dct.add_am_to_dict(optim_var_dict, am_dict)

    # Generate N2 scheme ##
    om.n2(optim_dir_path + "/circuit.sqlite", optim_dir_path + "/circuit.html", False)

    # Recap of the problem inputs/outputs ##
    prob.model.list_inputs()
    prob.model.list_outputs()

    # Results processing ##
    tls.plot_results(optim_dir_path, "", optim_var_dict)

    tls.save_results(optim_dir_path, optim_var_dict)

    copy_module_to_module(Rt.modules[-1], "out", "Optimisation", "out")


def routine_launcher(optim_method, module_optim, wkflow_dir):
    """Run an optimisation routine or DoE using the OpenMDAO library.

    This function launches the setup for the routine by setting up the problem
    with the OpenMDAO component, creating of reading a file containing all the
    problem parameters and launching the driver. It also specifies where to
    save the case recordings and launches the results plotting at the end of
    the routine.

    Args:
        optim_method (str): Optimisation method to be used
        module_optim (list): list of modules (ModuleToRun object) in the optimisation loop

    """

    global optim_var_dict, am_dict, Rt

    Rt.type = optim_method
    Rt.modules = [module.name for module in module_optim]

    # TODO: Remove this when the new optimisation routine is ready
    # Initialize CPACS file and problem dictionary ##
    # create_routine_folder()
    # opf.first_run(Rt)

    # TODO: change that, from which module should it comes?
    # CPACS_OPTIM_PATH = mif.get_toolinput_file_path("Optimisation")

    # Cpacs from the ouput of the last module
    cpacs_path = str(module_optim[-1].cpacs_out)

    cpacs = CPACS(cpacs_path)

    Rt.get_user_inputs(cpacs.tixi)

    global optim_dir_path  # TODO change that
    optim_dir_path = Path(wkflow_dir, "Results", optim_method)
    optim_dir_path.mkdir(parents=True, exist_ok=True)

    optim_var_dict = opf.create_variable_library(Rt, cpacs.tixi, optim_dir_path)
    am_dict = dct.create_aeromap_dict(cpacs, Rt.aeromap_uid, Rt.objective)

    # TODO: Where to save new file
    tmp_cpacs = Path(wkflow_dir, "temp.xml")
    cpacs.save_cpacs(str(tmp_cpacs), overwrite=True)

    module_optim[0].cpacs_in = tmp_cpacs

    # Instantiate components and subsystems ##
    prob = om.Problem()
    create_om_problem(prob)

    # Run the model ##
    prob.run_driver()

    generate_results(prob)


# =================================================================================================
#    MAIN
# =================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + os.path.basename(__file__) + " -----")

    tixi = open_tixi(cpacs_path)

    log.info("Impose the aeromap of the optimisation to all other modules")

    try:
        am_uid = get_value(tixi, OPTIM_XPATH + "/aeroMapUID")
    except ValueError:
        raise ValueError("No aeromap found in the file")

    log.info("Aeromap " + am_uid + " will be used")

    tixi.save(cpacs_out_path)

    log.info("----- End of " + os.path.basename(__file__) + " -----")


if __name__ == "__main__":

    cpacs_path = mif.get_toolinput_file_path("Optimisation")
    cpacs_out_path = mif.get_tooloutput_file_path("Optimisation")

    main(cpacs_path, cpacs_out_path)
