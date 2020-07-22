"""
CEASIOMpy: Conceptual Aircraft Design Software.

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function library for the optimisation module.

Python version: >=3.6

| Author: Vivien Riolo
| Creation: 2020-04-10
| Last modification: 2020-04-10

Todo:
----
    * Check how to open the csv file depending on the user program

"""


# ==============================================================================
#   IMPORTS
# ==============================================================================
import os

from re import split
import pandas as pd

import ceasiompy.SMUse.smuse as smu
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.moduleinterfaces as mif
import ceasiompy.utils.workflowfunctions as wkf
import ceasiompy.Optimisation.func.tools as tls
import ceasiompy.Optimisation.func.dictionnary as dct

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])


# ==============================================================================
#   GLOBALS
# ==============================================================================

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_OPTIM_PATH = mif.get_toolinput_file_path('Optimisation')
CSV_PATH = MODULE_DIR+'/Variable_library.csv'

WKDIR_XPATH = '/cpacs/toolspecific/CEASIOMpy/filesPath/wkdirPath'
OPTWKDIR_XPATH = '/cpacs/toolspecific/CEASIOMpy/filesPath/optimPath'
OPTIM_XPATH = '/cpacs/toolspecific/CEASIOMpy/Optimisation/'
AEROMAP_XPATH = '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance'
SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

# Parameters that can not be used as problem variables
banned_entries = ['wing', 'delete_old_wkdirs', 'check_extract_loads', # Not relevant variables
                  'cabin_crew_nb', # Is an input in range and an output in weightconv
                  'MASS_CARGO' # Strange behaviour to be fixed
                  ]

objective = []
var = {'Name':[], 'type':[], 'init':[], 'min':[], 'max':[], 'xpath':[]}

# ==============================================================================
#   CLASS
# ==============================================================================
class Routine:
    """Setup the routine to launch in Openmdao."""

    def __init__(self):
        """Define default main parameters."""
        # Choice of routine type : DOE or Optimisation
        self.type = "Optim"
        self.date = ""
        self.modules = []

        # Problem setup
        self.minmax = 'min' # Minimize or maximise the objective function
        self.objective = ['cl']

        # Driver choice
        self.driver = "COBYLA"

        # When to save the CPACS
        self.save_iter = 1
        self.max_iter = 200
        self.tol = 1e-3

        # DoE
        self.doedriver = 'uniform'
        self.samplesnb = 3
        self.doe_file = ''

        # User specified configuration file path
        self.user_config = '../Optimisation/Default_config.csv'
        self.aeromap_uid = '-'
        self.use_aeromap = False

    def get_user_inputs(self, tixi):
        """Take user inputs from the GUI."""

        # Problem setup
        objectives = cpsf.get_value_or_default(tixi, OPTIM_XPATH+'objective', 'cl')
        self.objective = split(';|,', objectives)
        self.minmax = cpsf.get_value_or_default(tixi, OPTIM_XPATH+'minmax', 'max')

        # Global parameters
        self.driver = cpsf.get_value_or_default(tixi, OPTIM_XPATH+'parameters/driver', 'COBYLA')
        self.max_iter = int(cpsf.get_value_or_default(tixi, OPTIM_XPATH+'iterationNB', 200))
        self.tol = float(cpsf.get_value_or_default(tixi, OPTIM_XPATH+'tolerance', 1e-3))
        self.save_iter = int(cpsf.get_value_or_default(tixi, OPTIM_XPATH+'saving/perIter', 1))

        # Specific DoE parameters
        self.doedriver = cpsf.get_value_or_default(tixi, OPTIM_XPATH+'parameters/DoE/driver', 'uniform')
        self.samplesnb = int(cpsf.get_value_or_default(tixi, OPTIM_XPATH+'parameters/DoE/sampleNB', 3))

        # User specified configuration file path
        self.user_config = str(cpsf.get_value_or_default(tixi, OPTIM_XPATH+'Config/filepath', '-'))
        self.aeromap_uid = str(cpsf.get_value_or_default(tixi, OPTIM_XPATH+'aeroMapUID', '-'))

        self.use_aeromap = cpsf.get_value_or_default(tixi, OPTIM_XPATH+'Config/useAero', False)

# ==============================================================================
#   FUNCTIONS
# ==============================================================================

def first_run(Rt):
    """Run subworkflow once for the optimisation problem.

    This function runs a first loop to ensure that all problem variables
    are created an can be fed to the optimisation setup program.

    Args:
        Rt (Routine object): Class that contains the routine informations.

    Returns:
        None.

    """
    log.info('Launching initialization workflow')
    Rt.modules.insert(0, 'Optimisation')

    # Settings needed for CFD calculation
    added_gui = False
    if 'SettingsGUI' not in Rt.modules:
        Rt.modules.insert(0, 'SettingsGUI')
        added_gui = True

    # First iteration to create aeromap results if no pre-workflow
    wkf.copy_module_to_module('Optimisation', 'in', Rt.modules[0], 'in')
    wkf.run_subworkflow(Rt.modules)
    wkf.copy_module_to_module(Rt.modules[-1], 'out', 'Optimisation', 'in')

    # SettingsGUI only needed at the first iteration
    if 'SettingsGUI' in Rt.modules and added_gui:
        Rt.modules.remove('SettingsGUI')

    # Optimisation parameters only needed for the first run
    Rt.modules.remove('Optimisation')


def gen_doe_csv(user_config):
    """Generate adequate csv with user-defined csv.

    For a DoE where a CSV file is provided by the user, the format must be
    adapted to the one that will be read by the OpenMDAO DoE tool. Here it is
    ensured that the format is correct.

    Args:
        user_config (str): Path to user configured file.

    Returns:
        doe_csv (str): Path to reformated file.

    """

    df = pd.read_csv(user_config)

    try:
        # Check if the name, type and at least one point are present.
        log.info(df[['Name', 'type', 0]])

        # Get only design variables
        df = df.loc[[i for i, v in enumerate(df['type']) if v == 'des']]

        # Get only name and columns with point values
        l = [i for i in df.columns if i.isdigit()]
        l.insert(0, 'Name')
        df = df[l]

        df = df.T

    except:
        pass
    doe_csv = os.path.split(user_config)[0]+'DoE_points.csv'

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

    Returns:
        None.

    """

    value = '-'
    xpath = entry.xpath
    def_val = entry.default_value

    if not def_val:
        if entry.var_type in [float, int]:
            def_val = 0.0
        else:
            def_val = '-'

    if entry.var_name not in banned_entries:
        value = cpsf.get_value_or_default(tixi, xpath, def_val)
        if entry.var_type == int:
            value = int(value)

    if not tls.is_digit(value):
        log.info('Not a digital value')
        value = '-'
    elif entry.var_type == bool:
        log.info('Boolean, not implemented yet')
        value = '-'

    # Ignores values that are not int or float
    if value != '-':
        value = str(value)
        tixi.updateTextElement(xpath, value)

        var['init'].append(value)
        var['xpath'].append(xpath)
        var['Name'].append(entry.var_name)

        tls.add_type(entry, outputs, objective, var)
        tls.add_bounds(value, var)
        log.info('Value : {}'.format(value))
        log.info('Added to variable file')


def update_am_path(tixi, am_uid):
    """Replace the aeromap uID for each module.

    Update the aeromap uID that is used for by modules in the optimisation loop

    Args:
        tixi (Tixi3 handle): Handle of the current CPACS file.
        am_uid (str): uID of the aeromap that will be used by all modules.

    Return:
        None.

    """
    am_xpath = ['/cpacs/toolspecific/pytornado/aeroMapUID',
                '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/aeroMapUID',
                '/cpacs/toolspecific/CEASIOMpy/surrogateModelUse/AeroMapOnly']
    for name in am_xpath:
        if tixi.checkElement(name):
            tixi.updateTextElement(name, am_uid)
        else:
            cpsf.create_branch(tixi, name)
            tixi.updateTextElement(name, am_uid)


def get_aeromap_index(tixi, am_uid):
    """Return index of the aeromap to be used.

    With the aeromap uID, the index of this aeromap is returned if there are
    more than one in the CPACS file.

    Args:
        tixi (Tixi3 handle): Handle of the current CPACS file
        am_uid (str): uID of the aeromap that will be used by all modules.

    Returns:
        am_index (str): The index of the aeromap between brackets.

    """
    am_list = apmf.get_aeromap_uid_list(tixi)
    am_index = '[1]'
    for i, uid in enumerate(am_list):
        if uid == am_uid:
            am_index = '[{}]'.format(i+1)

    return am_index


def get_aero_param(tixi):
    """Add the aeromap variables to the optimisation dictionnary.

    Takes the variables of the aeromap that is used.
    It is checked if the variable has a user-specified initial value, else it
    will assign a default value or the variable will be excluded from the
    problem.

    Args:
        tixi (Tixi3 handle): Handle of the current CPACS file.

    Returns:
        None.

    """
    log.info('Default aeromap parameters will be set')

    am_uid = cpsf.get_value(tixi, OPTIM_XPATH+'aeroMapUID')
    am_index = get_aeromap_index(tixi, am_uid)

    log.info('Aeromap \"{}\" will be used for the variables.'.format(am_uid))

    xpath = apmf.AEROPERFORMANCE_XPATH + '/aeroMap'\
            + am_index + '/aeroPerformanceMap/'

    for name in apmf.COEF_LIST+apmf.XSTATES:
        xpath_param = xpath+name
        value = str(tixi.getDoubleElement(xpath_param))

        var['Name'].append(name)
        var['init'].append(value)
        var['xpath'].append(xpath_param)

        tls.add_type(name, apmf.COEF_LIST, objective, var)
        tls.add_bounds(value, var)


def get_smu_vars(tixi):
    """Retrieves variable in the case of a surrogate.

    In the case of a surrogate model being used, the entries are retrieved from
    the dataframe that is saved in the SM file.

    Args:
        tixi (Tixi3 handler): Tixi handle of the CPACS file.

    Returns:
        None.

    """
    Model = smu.load_surrogate(tixi)
    df = Model.df.rename(columns={'Unnamed: 0':'Name'})
    df.set_index('Name', inplace=True)

    for name in df.index:
        name = tls.change_var_name(name)
        if name not in var['Name'] and df.loc[name]['setcmd'] == '-':
            var['Name'].append(name)
            xpath = df.loc[name]['getcmd']
            value = str(tixi.getDoubleElement(xpath))
            var['xpath'].append(xpath)
            var['init'].append(value)
            var['type'].append(df.loc[name]['type'])
            tls.add_bounds(value, var)
        else:
            log.warning('Variable already exists')
            log.info(name+' will not be added to the variable file')


def get_module_vars(tixi, specs):
    """Retrieve input and output variables of a module.

    Gets all the inputs and outputs of a module based on its __spec__ file,
    and decides for each parameter if it can be added to the problem or not.

    Returns:
        tixi (Tixi3 handler): Tixi handle of the CPACS file.
        specs (class): Contains the modules inputs and outputs specifications.

    Returns:
        None.

    """
    aeromap = True
    inouts = specs.cpacs_inout.inputs + specs.cpacs_inout.outputs
    for entry in inouts:
        xpath = entry.xpath
        if xpath.endswith('/'):
            xpath = xpath[:-1]
        value_name = xpath.split('/')[-1]

        log.info('----------------------------')
        log.info('Name : '+entry.var_name)

        # Change the name of the entry if it's a valid accronym (ex: mtom) or
        # if it has a special sign (ex: ranges[0])
        entry.var_name = tls.change_var_name(entry.var_name)

        log.info(xpath)
        log.info(value_name)

        # Check validity of variable
        if entry.var_name == '':
            log.error('Empty name, not a valid variable name')
        elif entry.var_name in var['Name']:
            log.warning('Variable already exists')
            log.info(entry.var_name+' will not be added to the variable file')

        # Aeromap variable
        elif value_name == 'aeroPerformanceMap' and aeromap:
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
    df.dropna(axis=0, subset=['type', 'getcmd'], inplace=True)
    if 'min' not in df.columns:
        df['min'] = '-'
    if 'max' not in df.columns:
        df['max'] = '-'

    defined_dict = df.to_dict('index')

    # Transform to a convenient form of dict
    optim_var_dict = {}
    for key, subdict in defined_dict.items():
        if subdict['initial value'] in ['False', 'True', '-'] or subdict['type'] == 'obj':
            optim_var_dict[key] = (subdict['type'], [subdict['initial value']],
                                   '-', '-', subdict['getcmd'], subdict['setcmd'])
        else:
            optim_var_dict[key] = (subdict['type'], [float(subdict['initial value'])],
                                   subdict['min'], subdict['max'],
                                   subdict['getcmd'], subdict['setcmd'])
    return optim_var_dict


def add_entries(tixi, module_list):
    """Add the entries of all the modules.

    Search all the entries that can be used as problenm parameters.

    Args:
        tixi (Tixi3 handler): Tixi handle of the CPACS file.

    Returns:
        None.

    """
    use_am = cpsf.get_value_or_default(tixi, smu.SMUSE_XPATH+'AeroMapOnly', False)
    if 'SMUse' in module_list and use_am:
        get_aero_param(tixi)
    else:
        for mod_name, specs in mif.get_all_module_specs().items():
            if specs and mod_name in module_list:
                if mod_name == 'SMUse':
                    get_smu_vars(tixi)
                else:
                    get_module_vars(tixi, specs)


def initialize_df():
    """Initialize the dataframe with the entries.

    Setup a dataframe that contains all the entries that were found in the
    modules.

    Args:
        None

    Returns:
        None.

    """
    df = pd.DataFrame(columns=['Name'], data=var['Name'])
    df['type'] = var['type']
    df['initial value'] = var['init']
    df['min'] = var['min']
    df['max'] = var['max']
    df['getcmd'] = var['xpath']

    return df


def add_geometric_vars(tixi, df):
    """Add geometry parameters as design variables.

    The geometric variables are not included as module entries and must be
    added differently.

    Args:
        tixi (Tixi3 handler): Tixi handle of the CPACS file.

    Returns:
        None.

    """
    geom_var = dct.init_geom_var_dict(tixi)
    for key, (var_name, [init_value], lower_bound, upper_bound, setcmd, getcmd) in geom_var.items():
        new_row = {'Name': var_name, 'type': 'des', 'initial value': init_value,
                   'min': lower_bound, 'max': upper_bound, 'getcmd': getcmd,
                   'setcmd': setcmd}
        df = df.append(new_row, ignore_index=True)

    df.sort_values(by=['type', 'Name'], axis=0, ignore_index=True,
                   ascending=[False, True], inplace=True)

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
    add_entries(tixi, module_list)

    df = initialize_df()

    df = add_geometric_vars(tixi, df)

    return df


def create_am_lib(Rt, tixi):
    """Create a dictionary for the aeromap coefficients.

    Return a dictionary with all the values of the aeromap that is used during
    the routine, so that all the results of the aeromap can later be exploited.

    Args:
        Rt (class): Contains all the parameters of the current routine.
        tixi (Tixi3 handler): Tixi handle of the CPACS file.

    Returns:
        am_dict (dct): Dictionnary with all aeromap parameters.

    """
    Coef = apmf.get_aeromap(tixi, Rt.aeromap_uid)
    am_dict = Coef.to_dict()
    am_index = apmf.get_aeromap_index(tixi, Rt.aeromap_uid)

    xpath = apmf.AEROPERFORMANCE_XPATH + '/aeroMap'\
            + am_index + '/aeroPerformanceMap/'

    for name in apmf.COEF_LIST+apmf.XSTATES:
        if name in ['altitude', 'machNumber']:
            min_val = 0
            max_val = '-'
            val_type = 'des'
        if name in apmf.COEF_LIST:
            min_val = -1
            max_val = 1
            if name in Rt.objective:
                val_type = 'obj'
            else:
                val_type = 'const'
        if name in ['angleOfAttack', 'angleOfSideslip']:
            min_val = -5
            max_val = 5
            val_type = 'des'
        am_dict[name] = (val_type, am_dict[name], min_val, max_val, xpath+name, '-')

    return am_dict


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
        optim_dir_path (str): Path to the working directory.

    Returns:
        optim_var_dict (dct): Dictionnary with all optimisation parameters.

    """
    global objective, var
    CSV_PATH = optim_dir_path+'/Variable_library.csv'

    for obj in Rt.objective:
        objective.extend(split('[+*/-]', obj))

    if os.path.isfile(Rt.user_config):
        log.info('Configuration file found, will be used')
        log.info(Rt.user_config)
        df = pd.read_csv(Rt.user_config, index_col=0)
        optim_var_dict = generate_dict(df)

    else:
        log.info('No configuration file found, default one will be generated')
        df = get_default_df(tixi, Rt.modules)

        # Save and open CSV file
        df.to_csv(CSV_PATH, index=False, na_rep='-')
        log.info('Variable library file has been generated')

        tls.launch_external_program(CSV_PATH)

        log.info('Variable library file has been saved at '+CSV_PATH)
        df = pd.read_csv(CSV_PATH, index_col=0, skip_blank_lines=True)
        optim_var_dict = generate_dict(df)

    return optim_var_dict


if __name__ == '__main__':

    log.info('|-------------------------------------------------|')
    log.info('|Not a standalone module. Nothing will be executed|')
    log.info('|-------------------------------------------------|')
