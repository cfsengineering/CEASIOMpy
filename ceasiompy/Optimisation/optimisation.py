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


from pathlib import Path
from re import split

import numpy as np
import openmdao.api as om
from ceasiompy.CPACSUpdater.cpacsupdater import update_cpacs_file
from ceasiompy.Optimisation.func.dictionnary import (
    add_am_to_dict,
    create_aeromap_dict,
    update_am_dict,
    update_dict,
)
from ceasiompy.Optimisation.func.optimfunctions import (
    Routine,
    create_variable_library,
    gen_doe_csv,
)
from ceasiompy.Optimisation.func.tools import change_var_name, is_digit, plot_results, save_results
from ceasiompy.SMUse.smuse import load_surrogate, write_inouts
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import run_module
from ceasiompy.utils.moduleinterfaces import (
    get_specs_for_module,
    get_toolinput_file_path,
    get_tooloutput_file_path,
)
from ceasiompy.utils.commonxpath import OPTIM_XPATH
from cpacspy.cpacsfunctions import add_float_vector, get_value, open_tixi
from cpacspy.cpacspy import CPACS
from cpacspy.utils import COEFS, PARAMS

# Do not remove: Called within eval() function
from tigl3 import geometry

log = get_logger()

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name

Rt = Routine()


# =================================================================================================
#   CLASSES
# =================================================================================================


class Geom_param(om.ExplicitComponent):
    """Classe to define the geometric parameters"""

    def setup(self):
        """Setup inputs only for the geometry"""

        for name, infos in Rt.geom_dict.items():
            if name in Rt.optim_var_dict:
                self.add_input(name, val=infos[1][0])

    def compute(self, inputs, outputs):
        """Update the geometry of the CPACS"""

        log.info(f"Start optimisation iteration: {Rt.counter}")

        # Update the geometry dictionary
        for name, infos in Rt.geom_dict.items():
            infos[1].append(inputs[name][0])

        if Rt.counter == 0:

            # For the first iteration, update the CPACS file from previous module
            cpacs_in = str(Rt.modules[0].cpacs_in)
            cpacs_out = str(Rt.modules[0].cpacs_out)
            update_cpacs_file(cpacs_in, cpacs_out, Rt.geom_dict)

        else:

            for m, module in enumerate(Rt.modules):

                # Increment name of output CPACS file
                Rt.modules[m].cpacs_out = Path(
                    Rt.modules[m].cpacs_out.parents[0],
                    "iter_" + str(Rt.counter).rjust(2, "0") + ".xml",
                )

                if m == 0:

                    # Use output of the last module of the previous iteration as input
                    Rt.modules[m].cpacs_in = Rt.modules[-1].cpacs_out

                    # Update the geometry of the CPACS file
                    cpacs_in = str(Rt.modules[m].cpacs_in)
                    cpacs_out = str(Rt.modules[m].cpacs_out)
                    update_cpacs_file(cpacs_in, cpacs_out, Rt.geom_dict)

                    # # The first module of the loop must update its output where the input
                    # # was saved because it has been updated by "update_cpacs_file" function.
                    # Rt.modules[m].cpacs_in = Rt.modules[m].cpacs_out

                else:

                    # Increment name of input CPACS file
                    Rt.modules[m].cpacs_in = Path(
                        Rt.modules[m].cpacs_in.parents[0],
                        "iter_" + str(Rt.counter).rjust(2, "0") + ".xml",
                    )

        Rt.counter += 1


class ModuleComp(om.ExplicitComponent):
    """Class to define each module in the problem as an independent component"""

    def __init__(self, module):
        """Add the module name that corresponds to the object being created"""
        om.ExplicitComponent.__init__(self)
        self.module_name = module.name

    def setup(self):
        """Setup inputs and outputs"""
        declared = []
        spec = get_specs_for_module(self.module_name)

        # Inputs
        for entry in spec.cpacs_inout.inputs:
            if entry.var_name in declared:
                log.info("Already declared")
            elif entry.var_name in Rt.optim_var_dict:
                var = Rt.optim_var_dict[entry.var_name]
                if entry.var_name in Rt.optim_var_dict:
                    self.add_input(entry.var_name, val=var[1][0])
                    declared.append(entry.var_name)

        if declared == []:
            self.add_input(self.module_name + "_in")
        declared = []

        for entry in spec.cpacs_inout.outputs:
            # Replace special characters from the name of the entry and checks for accronyms
            entry.var_name = change_var_name(entry.var_name)

            if entry.var_name in declared:
                log.info("Already declared")
            elif entry.var_name in Rt.optim_var_dict:
                var = Rt.optim_var_dict[entry.var_name]
                self.add_output(entry.var_name, val=var[1][0])
                declared.append(entry.var_name)
            elif (
                "aeromap" in entry.var_name and self.module_name == Rt.last_am_module
            ):  # == 'PyTornado':  #not skf^is_skf:
                # Condition to avoid any conflict with skinfriction
                for name in PARAMS:
                    if name in Rt.optim_var_dict:
                        var = Rt.optim_var_dict[name]
                        self.add_input(name, val=var[1][0])
                        declared.append(entry.var_name)
                for name in COEFS:
                    if name in Rt.optim_var_dict:
                        var = Rt.optim_var_dict[name]
                        if is_digit(var[1][0]):
                            self.add_output(name, val=var[1][0])
                        else:
                            self.add_output(name)
                        declared.append(entry.var_name)

        if declared == []:
            self.add_output(self.module_name + "_out")

    def compute(self, inputs, outputs):
        """Launches the module"""

        module = [m for m in Rt.modules if m.name == self.module_name][0]

        # Updating inputs in CPACS file
        cpacs_path = str(module.cpacs_in)
        tixi = open_tixi(cpacs_path)
        for name in inputs:
            if name in Rt.optim_var_dict:
                xpath = Rt.optim_var_dict[name][4]
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
        run_module(module, Rt.wkflow_dir, Rt.counter)

        # Feeding CPACS file results to outputs
        tixi = open_tixi(str(module.cpacs_out))
        for name in outputs:
            if name in Rt.optim_var_dict:
                xpath = Rt.optim_var_dict[name][4]
                if name in COEFS:
                    val = get_value(tixi, xpath)
                    if isinstance(val, str):
                        val = val.split(";")
                        outputs[name] = val[0]
                    else:
                        outputs[name] = val
                else:
                    outputs[name] = get_value(tixi, xpath)


class SmComp(om.ExplicitComponent):
    """Uses a surrogate model to make a prediction"""

    def __init__(self, module):
        """Add the module name that corresponds to the object being created"""
        om.ExplicitComponent.__init__(self)
        self.module_name = module.name

    def setup(self):
        """Setup inputs and outputs"""

        module = [m for m in Rt.modules if m.name == self.module_name][0]

        # Take CPACS file from the optimisation
        cpacs_path = str(module.cpacs_in)
        tixi = open_tixi(cpacs_path)
        self.Model = load_surrogate(tixi)
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

        module = [m for m in Rt.modules if m.name == self.module_name][0]

        # Write the inouts to the CPACS
        tixi = open_tixi(str(module.cpacs_in))
        write_inouts(self.xd, xp, tixi)
        write_inouts(self.yd, yp, tixi)
        tixi.save(str(module.cpacs_out))


class Objective(om.ExplicitComponent):
    """Class to compute the objective function(s)"""

    def setup(self):
        """Setup inputs and outputs"""
        declared = []
        for obj in Rt.objective:
            var_list = split("[+*/-]", obj)
            for v in var_list:
                if v not in declared:
                    self.add_input(v)
                    declared.append(v)
            self.add_output("Objective function " + obj)

    def compute(self, inputs, outputs):
        """Compute the objective expression"""

        # Add new variables to dictionnary
        cpacs = CPACS(Rt.modules[-1].cpacs_out)

        update_dict(cpacs.tixi, Rt.optim_var_dict)

        # Save the whole aeromap if needed
        if Rt.use_aeromap:
            update_am_dict(cpacs, Rt.aeromap_uid, Rt.am_dict)

        for obj in Rt.objective:
            var_list = split("[+*/-]", obj)
            for v in var_list:
                if not v.isdigit() and v != "":
                    exec('{} = inputs["{}"]'.format(v, v))
            result = eval(obj)

            if Rt.minmax == "min":
                outputs["Objective function " + obj] = result
            else:
                outputs["Objective function " + obj] = -result


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


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

    if Rt.type == "OPTIM":
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
    elif Rt.type == "DOE":
        if Rt.doedriver == "Uniform":
            driver_type = om.UniformGenerator(num_samples=Rt.samplesnb)
        elif Rt.doedriver == "LatinHypercube":
            driver_type = om.LatinHypercubeGenerator(samples=Rt.samplesnb)
        elif Rt.doedriver == "FullFactorial":
            driver_type = om.FullFactorialGenerator(levels=Rt.samplesnb)
        elif Rt.doedriver == "CSVGenerated":
            file = gen_doe_csv(Rt.user_config)
            driver_type = om.CSVGenerator(file)
        prob.driver = om.DOEDriver(driver_type)
        prob.driver.options["run_parallel"] = True
        prob.driver.options["procs_per_model"] = 1
    else:
        log.error("Type of optimisation not recognize!!!")

    #  Attaching a recorder and a diagramm visualizer ##
    prob.driver.recording_options["record_inputs"] = True
    prob.driver.add_recorder(om.SqliteRecorder(str(Rt.optim_dir) + "/circuit.sqlite"))
    prob.driver.add_recorder(om.SqliteRecorder(str(Rt.optim_dir) + "/Driver_recorder.sql"))


def add_subsystems(prob, ivc):
    """Add subsystems to problem.

    All subsystem classes are added to the problem model.

    Args:
        prob (om.Problem object): Current problem that is being defined
        ivc (om.IndepVarComp object): Independent variables of the problem

    """

    geom = Geom_param()
    obj = Objective()

    # Independent variables
    prob.model.add_subsystem("indeps", ivc, promotes=["*"])

    # Geometric parameters
    Rt.geom_dict = {k: v for k, v in Rt.optim_var_dict.items() if v[5] != "-"}
    if Rt.geom_dict:
        prob.model.add_subsystem("Geometry", geom, promotes=["*"])

    # Loop throuth Modules
    for module in Rt.modules:

        if module.name in ["SU2Run", "PyTornado", "SkinFriction"]:
            Rt.last_am_module = module.name

        if module.name == "SMUse":
            prob.model.add_subsystem(module.name, SmComp(module), promotes=["*"])
        else:
            spec = get_specs_for_module(module.name)
            if spec.cpacs_inout.inputs or spec.cpacs_inout.outputs:
                prob.model.add_subsystem(module.name, ModuleComp(module), promotes=["*"])

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
    ) in Rt.optim_var_dict.items():
        if val_type == "des" and listval[-1] not in ["True", "False", "-"]:
            if is_digit(minval) and is_digit(maxval):
                prob.model.add_design_var(name, lower=float(minval), upper=float(maxval))
            elif is_digit(minval):
                prob.model.add_design_var(name, lower=float(minval))
            elif is_digit(maxval):
                prob.model.add_design_var(name, upper=float(maxval))
            else:
                prob.model.add_design_var(name)
            ivc.add_output(name, val=listval[-1])
        elif val_type == "const":
            if is_digit(minval) and is_digit(maxval):
                prob.model.add_constraint(name, lower=float(minval), upper=float(maxval))
            elif is_digit(minval):
                prob.model.add_constraint(name, lower=float(minval))
            elif is_digit(maxval):
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

    if Rt.use_aeromap and Rt.type == "DOE":
        add_am_to_dict(Rt.optim_var_dict, Rt.am_dict)

    # Generate N2 scheme
    # TODO: should be uncommented
    # om.n2(Path(Rt.optim_dir, "circuit.sqlite"), Path(Rt.optim_dir, "circuit.html"), False)

    # Recap of the problem inputs/outputs
    prob.model.list_inputs()
    prob.model.list_outputs()

    # Results processing
    plot_results(Rt.optim_dir, "", Rt.optim_var_dict)
    save_results(Rt.optim_dir, Rt.optim_var_dict)


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

    Rt.type = optim_method
    Rt.modules = module_optim
    Rt.wkflow_dir = wkflow_dir

    # Cpacs from the ouput of the last module
    cpacs_path = str(Rt.modules[0].cpacs_in)

    cpacs = CPACS(cpacs_path)

    Rt.get_user_inputs(cpacs.tixi)

    Rt.optim_dir = Path(wkflow_dir, "Results", optim_method)
    Rt.optim_dir.mkdir(parents=True, exist_ok=True)

    Rt.optim_var_dict = create_variable_library(Rt, cpacs.tixi, Rt.optim_dir)
    Rt.am_dict = create_aeromap_dict(cpacs, Rt.aeromap_uid, Rt.objective)

    # Instantiate components and subsystems ##
    prob = om.Problem()
    create_om_problem(prob)

    # Run the model ##
    prob.run_driver()

    generate_results(prob)


# =====================================================================================================================
#    MAIN
# =====================================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    tixi = open_tixi(cpacs_path)

    log.info("Impose the aeromap of the optimisation to all other modules")

    try:
        am_uid = get_value(tixi, OPTIM_XPATH + "/aeroMapUID")
    except ValueError:
        raise ValueError("No aeromap found in the file")

    log.info("Aeromap " + am_uid + " will be used")

    tixi.save(cpacs_out_path)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path("Optimisation")
    cpacs_out_path = get_tooloutput_file_path("Optimisation")

    main(cpacs_path, cpacs_out_path)
