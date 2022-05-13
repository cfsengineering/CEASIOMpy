"""
CEASIOMpy: Conceptual Aircraft Design Software.

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function library for the optimisation module.

Python version: >=3.7

| Author: Vivien Riolo
| Creation: 2020-04-10

Todo:

    *

"""


# =================================================================================================
#   IMPORTS
# =================================================================================================


from pathlib import Path
from re import split

import pandas as pd
from ceasiompy.Optimisation.func.dictionnary import init_geom_var_dict
from ceasiompy.Optimisation.func.tools import (
    add_bounds,
    add_type,
    change_var_name,
    is_digit,
    launch_external_program,
)
from ceasiompy.SMUse.smuse import load_surrogate
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import get_all_module_specs
from ceasiompy.utils.commonxpath import OPTIM_XPATH, SMUSE_XPATH
from cpacspy.cpacsfunctions import get_value_or_default
from cpacspy.utils import COEFS, PARAMS_COEFS

log = get_logger()

MODULE_DIR = Path(__file__).parent
CSV_PATH = Path(MODULE_DIR, "Variable_library.csv")

# Parameters that can not be used as problem variables
BANNED_ENTRIES = [
    "wing",
    "delete_old_wkdirs",
    "check_extract_loads",  # Not relevant
    "cabin_crew_nb",  # Is an input in range and an output in weightconv
    "MASS_CARGO",  # Makes the programm crash for unkknown reasons
]

objective = []
var = {"Name": [], "type": [], "init": [], "min": [], "max": [], "xpath": []}


# =================================================================================================
#   CLASS
# =================================================================================================


class Routine:
    """Setup the routine to launch in Openmdao."""

    def __init__(self):
        """Define default main parameters."""

        # Choice of routine type : DOE or Optimisation
        self.type = "OPTIM"
        self.date = ""
        self.modules = []

        # Problem setup
        self.minmax = "min"  # Minimize or maximise the objective function
        self.objective = ["cl"]

        # Driver choice
        self.driver = "COBYLA"

        # When to save the CPACS
        self.save_iter = 1
        self.max_iter = 200
        self.tol = 1e-3

        # DoE
        self.doedriver = "Uniform"
        self.samplesnb = 3
        self.doe_file = ""

        # User specified configuration file path
        self.user_config = Path(MODULE_DIR, "files", "Default_config.csv")
        self.aeromap_uid = "-"
        self.use_aeromap = False

        # Counter
        self.counter = 0

        # Optimisation directory
        self.optim_dir = None

        # Variable dictionary
        self.geom_dict = {}
        self.optim_var_dict = {}
        self.am_dict = {}

        self.last_am_module = ""

        self.wkflow_dir = None

    def get_user_inputs(self, tixi):
        """Take user inputs from the GUI."""

        # Problem setup
        objectives = get_value_or_default(tixi, OPTIM_XPATH + "/objective", "cl")
        self.objective = split(";|,", objectives)
        self.minmax = get_value_or_default(tixi, OPTIM_XPATH + "/minmax", "max")

        # Global parameters
        self.driver = get_value_or_default(tixi, OPTIM_XPATH + "/parameters/driver", "COBYLA")
        self.max_iter = int(get_value_or_default(tixi, OPTIM_XPATH + "/iterationNB", 200))
        self.tol = float(get_value_or_default(tixi, OPTIM_XPATH + "/tolerance", 1e-3))
        self.save_iter = int(get_value_or_default(tixi, OPTIM_XPATH + "/saving/perIter", 1))

        # Specific DoE parameters
        self.doedriver = get_value_or_default(
            tixi, OPTIM_XPATH + "/parameters/DoE/driver", "Uniform"
        )
        self.samplesnb = int(
            get_value_or_default(tixi, OPTIM_XPATH + "/parameters/DoE/sampleNB", 3)
        )

        # User specified configuration file path
        self.user_config = str(get_value_or_default(tixi, OPTIM_XPATH + "/Config/filepath", "-"))

        fix_cl = get_value_or_default(
            tixi, "/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/fixedCL", "no"
        )
        if fix_cl == "YES":
            tixi.updateTextElement(OPTIM_XPATH + "/aeroMapUID", "aeroMap_fixedCL_SU2")
            self.aeromap_uid = "aeroMap_fixedCL_SU2"
        else:
            self.aeromap_uid = str(get_value_or_default(tixi, OPTIM_XPATH + "/aeroMapUID", "-"))

        self.use_aeromap = get_value_or_default(tixi, OPTIM_XPATH + "/Config/useAero", False)


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def gen_doe_csv(user_config):
    """Generate adequate csv with user-defined csv.

    For a DoE where a CSV file is provided by the user, the format must be
    adapted to the one that will be read by the OpenMDAO DoE tool. Here it is
    ensured that the format is correct.

    Args:
        user_config (Path): Path to user configured file.

    Returns:
        doe_csv (Path): Path to reformated file.

    """

    df = pd.read_csv(user_config)
    # Check if the name, type and at least one point are present.
    log.info(df[["Name", "type", "0"]])

    # Get only design variables
    df = df[df["type"] == "des"]

    # Get only name and columns with point values
    col = [i for i in df.columns if i.isdigit()]
    col.insert(0, "Name")

    df = df[col]
    df.set_index("Name")
    df = df.T

    doe_csv = Path(user_config.parent, "/DoE_points.csv")
    df.to_csv(doe_csv, header=False, index=False)

    return doe_csv


def get_normal_param(tixi, entry, outputs):
    """Add a variable to the optimisation dictionnary.

    It is checked if the variable has a user-specified initial value, else it
    will assign a default value or the variable will be excluded from the
    problem.

    Args:
        tixi (Tixi3 handle): Handle of the current CPACS file.
        entry (object): Current parameter object.

    """

    value = "-"
    xpath = entry.xpath
    def_val = entry.default_value

    if not def_val:
        if entry.var_type in [float, int]:
            def_val = 0.0
        else:
            def_val = "-"

    if entry.var_name not in BANNED_ENTRIES:
        value = get_value_or_default(tixi, xpath, def_val)
        if entry.var_type == int:
            value = int(value)

    if not is_digit(value):
        log.info("Not a digital value")
        value = "-"
    elif entry.var_type == bool:
        log.info("Boolean, not implemented yet")
        value = "-"

    # Ignores values that are not int or float
    if value != "-":
        value = str(value)
        tixi.updateTextElement(xpath, value)

        var["init"].append(value)
        var["xpath"].append(xpath)
        var["Name"].append(entry.var_name)

        add_type(entry, outputs, objective, var)
        add_bounds(value, var)
        log.info("Value : {}".format(value))
        log.info("Added to variable file")


def get_aero_param(tixi):
    """Add the aeromap variables to the optimisation dictionnary.

    Takes the variables of the aeromap that is used.
    It is checked if the variable has a user-specified initial value, else it
    will assign a default value or the variable will be excluded from the
    problem.

    Args:
        tixi (Tixi3 handle): Handle of the current CPACS file.

    """

    # TODO: This function could probalbly be (partrly) replace by cpacspy

    log.info("Default aeromap parameters will be set")

    aeromap_uid = tixi.getTextElement(OPTIM_XPATH + "/aeroMapUID")
    xpath = tixi.uIDGetXPath(aeromap_uid) + "/aeroPerformanceMap/"

    for name in PARAMS_COEFS:
        xpath_param = xpath + name

        value = str(tixi.getDoubleElement(xpath_param))

        var["Name"].append(name)
        var["init"].append(value)
        var["xpath"].append(xpath_param)

        add_type(name, COEFS, objective, var)
        add_bounds(value, var)


def get_sm_vars(tixi):
    """Retrieves variable in the case of a surrogate.

    In the case of a surrogate model being used, the entries are retrieved from
    the dataframe that is saved in the SM file.

    Args:
        tixi (Tixi3 handler): Tixi handle of the CPACS file.

    """

    Model = load_surrogate(tixi)
    df = Model.df.rename(columns={"Unnamed: 0": "Name"})
    df.set_index("Name", inplace=True)

    for name in df.index:
        name = change_var_name(name)
        if name not in var["Name"] and df.loc[name]["setcmd"] == "-":
            var["Name"].append(name)
            var["type"].append(df.loc[name]["type"])

            xpath = df.loc[name]["getcmd"]
            var["xpath"].append(xpath)

            value = str(tixi.getDoubleElement(xpath))
            var["init"].append(value)

            add_bounds(value, var)
        else:
            log.warning("Variable already exists")
            log.info(name + " will not be added to the variable file")


def get_module_vars(tixi, specs):
    """Retrieve input and output variables of a module.

    Gets all the inputs and outputs of a module based on its __spec__ file,
    and decides for each parameter if it can be added to the problem or not.

    Returns:
        tixi (Tixi3 handler): Tixi handle of the CPACS file.
        specs (class): Contains the modules inputs and outputs specifications.

    """

    aeromap = True
    inouts = specs.cpacs_inout.inputs + specs.cpacs_inout.outputs
    for entry in inouts:
        xpath = entry.xpath
        if xpath.endswith("/"):
            xpath = xpath[:-1]
        value_name = xpath.split("/")[-1]

        log.info("----------------------------")
        log.info("Name : " + entry.var_name)

        # Change the name of the entry if it's a valid accronym (ex: mtom) or
        # if it has a special sign (ex: ranges[0])
        entry.var_name = change_var_name(entry.var_name)

        log.info(xpath)
        log.info(value_name)

        # Check validity of variable
        if entry.var_name == "":
            log.error("Empty name, not a valid variable name")
        elif entry.var_name in var["Name"]:
            log.warning("Variable already exists")
            log.info(entry.var_name + " will not be added to the variable file")

        # Aeromap variable
        elif value_name == "aeroPerformanceMap" and aeromap:
            aeromap = False
            get_aero_param(tixi)
        # Normal case
        else:
            get_normal_param(tixi, entry, specs.cpacs_inout.outputs)


def generate_dict(df):
    """Generate dictionary from a dataframe.

    Convert a dataframe to a dictionary and modifies the dictionary in order to
    have all the necessary keys to

    Args:
        df (DataFrame): Contains all the variable. Used to passs from a csv to a dict

    Returns:
        optim_var_dict (dict): Used to pass the variables to the openMDAO setup.

    """

    df.dropna(axis=0, subset=["type", "getcmd"], inplace=True)
    if "min" not in df.columns:
        df["min"] = "-"
    if "max" not in df.columns:
        df["max"] = "-"

    defined_dict = df.to_dict("index")

    # Transform to a convenient form of dict
    optim_var_dict = {}
    for key, subdict in defined_dict.items():
        if subdict["initial value"] in ["False", "True", "-"] or subdict["type"] == "obj":
            optim_var_dict[key] = (
                subdict["type"],
                [subdict["initial value"]],
                "-",
                "-",
                subdict["getcmd"],
                subdict["setcmd"],
            )
        else:
            optim_var_dict[key] = (
                subdict["type"],
                [float(subdict["initial value"])],
                subdict["min"],
                subdict["max"],
                subdict["getcmd"],
                subdict["setcmd"],
            )
    return optim_var_dict


def add_entries(tixi, module_list):
    """Add the entries of all the modules.

    Search all the entries that can be used as problem parameters and fills the
    variable dictionary with the valid entries.

    Args:
        tixi (Tixi3 handler): Tixi handle of the CPACS file.

    """

    use_am = get_value_or_default(tixi, SMUSE_XPATH + "/AeroMapOnly", False)
    if "SMUse" in module_list and use_am:
        get_aero_param(tixi)
    else:
        for mod_name, specs in get_all_module_specs().items():
            if specs and mod_name in module_list:
                if mod_name == "SMUse":
                    get_sm_vars(tixi)
                else:
                    get_module_vars(tixi, specs)


def initialize_df():
    """Initialize the dataframe with the entries.

    Setup a dataframe that contains all the entries that were found in the
    modules.

    """

    df = pd.DataFrame(columns=["Name"], data=var["Name"])
    df["type"] = var["type"]
    df["initial value"] = var["init"]
    df["min"] = var["min"]
    df["max"] = var["max"]
    df["getcmd"] = var["xpath"]

    return df


def add_geometric_vars(tixi, df):
    """Add geometry parameters as design variables.

    Automatically add the geometric variables as they are not included as
    module entries.

    Args:
        tixi (Tixi3 handler): Tixi handle of the CPACS file.

    """

    geom_var = init_geom_var_dict(tixi)
    for key, (
        var_name,
        [init_value],
        lower_bound,
        upper_bound,
        setcmd,
        getcmd,
    ) in geom_var.items():
        new_row = {
            "Name": var_name,
            "type": "des",
            "initial value": init_value,
            "min": lower_bound,
            "max": upper_bound,
            "getcmd": getcmd,
            "setcmd": setcmd,
        }
        df = df.append(new_row, ignore_index=True)

    df.sort_values(
        by=["type", "Name"],
        axis=0,
        ignore_index=True,
        ascending=[False, True],
        inplace=True,
    )

    return df


def get_default_df(tixi, module_list):
    """Generate dataframe with all inouts.

    Generates a dataframe containing all the variables that could be found in
    each module and that could be used as a parameter for an optimisation or
    DoE routine.

    Args:
        tixi (Tixi3 handler): Tixi handle of the CPACS file.
        module_list (lst): list of modules to execute in the routine.

    Returns:
        df (Dataframe): Dataframe with all the module variables.

    """

    # Fill the variable dictionary with all entries
    add_entries(tixi, module_list)

    df = initialize_df()

    df = add_geometric_vars(tixi, df)

    return df


def create_variable_library(Rt, tixi, optim_dir_path):
    """Create a dictionnary and a CSV file containing all variables that appear
    in the module list.

    The CSV files lists all the inputs and outputs of each module with :
    * An initial value
    * An upper and lower bound
    * The commands to get and modify the value of the parameter in the CPACS file
    * The variable type : Constraint, Design variable, Objective function component

    Args:
        Rt (class): Contains all the parameters of the current routine.
        tixi (Tixi3 handler): Tixi handle of the CPACS file.
        optim_dir_path (Path): Path to the working directory.

    Returns:
        optim_var_dict (dict): Dictionnary with all optimisation parameters.

    """

    global objective, var

    CSV_PATH = Path(optim_dir_path, "Variable_library.csv")

    for obj in Rt.objective:
        objective.extend(split("[+*/-]", obj))

    if Rt.user_config.is_file():
        log.info("Configuration file found, will be used")
        log.info(Rt.user_config)
        df = pd.read_csv(Rt.user_config, index_col=0)
        optim_var_dict = generate_dict(df)

    else:
        log.info("No configuration file found, default one will be generated")
        module_list = [module.name for module in Rt.modules]
        df = get_default_df(tixi, module_list)

        # Save and open CSV file
        df.to_csv(CSV_PATH, index=False, na_rep="-")
        log.info("Variable library file has been generated")

        launch_external_program(CSV_PATH)

        log.info(f"Variable library file has been saved at {CSV_PATH}")
        df = pd.read_csv(CSV_PATH, index_col=0, skip_blank_lines=True)
        optim_var_dict = generate_dict(df)

    return optim_var_dict


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":

    print("Nothing to execute!")
