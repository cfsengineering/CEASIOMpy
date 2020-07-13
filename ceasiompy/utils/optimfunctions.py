"""
CEASIOMpy: Conceptual Aircraft Design Software.

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function library for the optimisation module

Python version: >=3.6

| Author: Vivien Riolo
| Creation: 2020-04-10
| Last modification: 2020-04-10

Todo:
----
    * Write the doc
    * Check how to open the csv file depending on the user program

"""


# ==============================================================================
#   IMPORTS
# ==============================================================================
import os
import sys

import pandas as pd

import ceasiompy.SMUse.smuse as smu
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.moduleinterfaces as mif
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.workflowfunctions as wkf
import ceasiompy.Optimisation.func.dictionnary as dct
import ceasiompy.Optimisation.func.tools as tls

from re import split as splt
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
banned_entries = ['wing','delete_old_wkdirs','check_extract_loads', # Not relevant variables
                  'cabin_crew_nb' # Is an input in range and an output in weightconv
                  ]
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
        self.use_aeromap = False
        self.aeromap_uid = '-'

    def get_user_inputs(self, cpacs_path):
        """Take user inputs from the GUI."""
        tixi = cpsf.open_tixi(CPACS_OPTIM_PATH)

        # Problem setup
        objectives = cpsf.get_value_or_default(tixi, OPTIM_XPATH+'objective', 'cl')
        self.objective = splt(';|,',objectives)
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
        self.use_aeromap = cpsf.get_value_or_default(tixi, OPTIM_XPATH+'Config/useAero', '-')
        self.aeromap_uid = str(cpsf.get_value_or_default(tixi, OPTIM_XPATH+'Config/aeroMapUID', '-'))

        cpsf.close_tixi(tixi, CPACS_OPTIM_PATH)

# ==============================================================================
#   FUNCTIONS
# ==============================================================================

def first_run(module_list, modules_pre_list=[]):
    """Run subworkflow once for the optimisation problem.

    This function runs a first loop to ensure that all problem variables
    are created an can be fed to the optimisation setup program.

    Args:
        module_list (lst) : List of modules to run.
        module_pre_list (lst) : List of modules that were run in a previous
        workflow.

    Returns:
        None.

    """
    log.info('Launching initialization workflow')

    # Settings needed for CFD calculation
    if 'Optimisation' not in modules_pre_list:
        module_list.insert(0, 'Optimisation')
    if 'SettingsGUI' not in module_list:
        module_list.insert(0, 'SettingsGUI')

    # First iteration to create aeromap results if no pre-workflow
    wkf.copy_module_to_module('Optimisation', 'in', module_list[0], 'in')
    wkf.run_subworkflow(module_list)
    wkf.copy_module_to_module(module_list[-1], 'out', 'Optimisation', 'in')

    # SettingsGUI only needed at the first iteration
    if 'SettingsGUI' in module_list:
        module_list.remove('SettingsGUI')

    # Optimisation parameters only needed for the first run
    module_list.remove('Optimisation')


def change_var_name(name):
    """Modify the variable name

    Checks for special characters and replaces them with '_' which can be taken
    as a variable name for the OpenMDAO problem.

    Args:
        name (str): variable name.

    Returns:
        new_name (str): new variable_name.

    """
    log.info('Check variable name {}'.format(name))
    for s in name:
        if s in ['[',']']:
            name = name.replace(s,'_')
    log.info('Variable name was change to {}'.format(name))

    return name


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
        df[['Name','type',0]]

        # Get only design variables
        df = df.loc[[i for i,v in enumerate(df['type']) if v == 'des']]

        # Get only name and columns with point values
        l = [i for i in df.columns if i.isdigit()]
        l.insert(0,'Name')
        df = df[l]

        df = df.T

    except:
        pass
    doe_csv = os.path.split(user_config)[0]+'DoE_points.csv'

    df.to_csv(doe_csv, header=False, index=False)

    return doe_csv


def get_normal_param(tixi, value_name, entry, outputs):
    """Add a variable to the optimisation dictionnary.

    It is checked if the variable has a user-specified initial value, else it
    will assign a default value or the variable will be excluded from the
    problem.

    Args:
        tixi (Tixi3 handle): Handle of the current CPACS file.
        value_name (str): Name of the parameter.
        entry (object): Current parameter object.

    Returns:
        None.

    """
    log.info('Type : '+str(entry.var_type))
    xpath = entry.xpath
    def_val = entry.default_value
    value = '-'

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

    log.info('Value : {}'.format(value))
    # Ignores values that are not int or float
    if value != '-':
        value = str(value)
        tixi.updateTextElement(xpath, value)

        var['Name'].append(entry.var_name)
        var['init'].append(value)
        var['xpath'].append(xpath)

        tls.add_type(entry, outputs, objective, var)
        tls.add_bounds(entry.var_name, value, var)
        log.info('Added to variable file')


def get_aero_param(tixi, module_name):
    """Add the aeromap variables to the optimisation dictionnary.

    Takes the variables of the aeromap that is used.
    It is checked if the variable has a user-specified initial value, else it
    will assign a default value or the variable will be excluded from the
    problem.

    Args:
        tixi (Tixi3 handle): Handle of the current CPACS file.
        value_name (str): Name of the parameter.
        entry (object): Current parameter object.

    Returns:
        None.

    """
    log.info('Default aeromap parameters will be set')

    # Get name of aeromap that is used
    am_uid = apmf.get_current_aeromap_uid(tixi, [module_name])
    log.info('Aeromap \"{}\" will be used for the variables.'.format(am_uid))

    # Search the aeromap index in the CPACS file if there are more
    am_list = apmf.get_aeromap_uid_list(tixi)
    for i, uid in enumerate(am_list):
        if uid == am_uid:
            am_index = '[{}]'.format(i+1)
    xpath = apmf.AEROPERFORMANCE_XPATH + '/aeroMap' + am_index + '/aeroPerformanceMap/'

    outputs = ['cl', 'cd', 'cs', 'cml', 'cmd', 'cms']
    inputs = ['altitude', 'machNumber', 'angleOfAttack', 'angleOfSideslip']

    inputs.extend(outputs)
    for name in inputs:
        xpath_param = xpath+name
        value = str(tixi.getDoubleElement(xpath_param))

        var['Name'].append(name)
        var['init'].append(value)
        var['xpath'].append(xpath_param)

        tls.add_type(name, outputs, objective, var)
        tls.add_bounds(name, value, var)


def get_variables(tixi, specs, module_name):
    """Retrieve input and output variables of a module.

    Gets all the inputs and outputs of a module based on its __spec__ file,
    and decides for each parameter if it can be added to the problem or not,
    depending on its.
    In the case of a surrogate model being used, the entries are retrieved from
    the dataframe that is saved in the SM file.

    Returns:
        tixi (Tixi3 handler): Tixi handle of the CPACS file.
        specs (class): Contains the modules inputs and outputs specifications.

    Returns:
        None.

    """
    aeromap = True
    inouts = specs.cpacs_inout.inputs + specs.cpacs_inout.outputs
    if module_name == 'SMUse':
        Model = smu.load_surrogate(CPACS_OPTIM_PATH)
        df = Model.df.rename(columns={'Unnamed: 0':'Name'})
        df.set_index('Name', inplace=True)
        for name in df.index:
            if name not in var['Name'] and df.loc[name]['setcmd'] == '-':
                var['Name'].append(name)
                xpath = df.loc[name]['getcmd']
                value = str(tixi.getDoubleElement(xpath))
                var['xpath'].append(xpath)
                var['init'].append(value)
                var['type'].append(df.loc[name]['type'])
                tls.add_bounds(name, value, var)
            else:
                log.warning('Variable already exists')
                log.info(name+' will not be added to the variable file')
    else:
        for entry in inouts:
            xpath = entry.xpath
            if xpath.endswith('/'):
                xpath = xpath[:-1]
            value_name = xpath.split('/')[-1]

            log.info('----------------------------')
            log.info('Name : '+entry.var_name)
            if 'range' in entry.var_name or 'payload' in entry.var_name:
                entry.var_name = change_var_name(entry.var_name)
            log.info(xpath)
            log.info(value_name)

            # Check validity of variable
            if entry.var_name == '':
                log.error('Not a valid variable name')
            elif entry.var_name in var['Name']:
                log.warning('Variable already exists')
                log.info(entry.var_name+' will not be added to the variable file')

            # Aeromap variable
            elif value_name == 'aeroPerformanceMap' and aeromap:
                aeromap = False
                get_aero_param(tixi, module_name)
            # Normal case
            else:
                get_normal_param(tixi, value_name, entry, specs.cpacs_inout.outputs)


def generate_dict(df):
    """Write all variables in a CSV file or use a predefined file.

    Args:
        df (DataFrame): Contains all the variable. Used to passs from a csv to a dict

    Returns:
        optim_var_dict (dict): Used to pass the variables to the openMDAO setup.

    """
    df.dropna(axis=0,subset=['type','getcmd'],inplace=True)
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
                                   subdict['min'], subdict['max'],
                                   subdict['getcmd'], subdict['setcmd'])
        else:
            optim_var_dict[key] = (subdict['type'], [float(subdict['initial value'])],
                                   subdict['min'], subdict['max'],
                                   subdict['getcmd'], subdict['setcmd'])
    return optim_var_dict


def get_default_df(module_list):
    """Generate dataframe with all inouts.

    Generates a dataframe containing all the variables that could be found in
    each module and that could be used as a parameter for an optimisation or
    DoE routine.

    Args:
        module_list (lst): list of modules to execute in the routine.

    Returns:
        df (Dataframe): Dataframe with all the module variables.

    """
    tixi = cpsf.open_tixi(CPACS_OPTIM_PATH)
    if 'SMUse' in module_list and cpsf.get_value_or_default(tixi, smu.SMUSE_XPATH+'AeroMapOnly', False):
        get_aero_param(tixi, 'SMUse')
    else:
        for mod_name, specs in mif.get_all_module_specs().items():
            if specs and mod_name in module_list:
                get_variables(tixi, specs, mod_name)
    cpsf.close_tixi(tixi, CPACS_OPTIM_PATH)

    # Add the default values for the variables
    df = pd.DataFrame(columns=['Name'], data=var['Name'])
    df['type'] = var['type']
    df['initial value'] = var['init']
    df['min'] = var['min']
    df['max'] = var['max']
    df['getcmd'] = var['xpath']

    # Add geometry parameters as design variables (only design type for the moment)
    tixi = cpsf.open_tixi(CPACS_OPTIM_PATH)
    geom_var = dct.init_geom_var_dict(tixi)
    for key, (var_name, [init_value], lower_bound, upper_bound, setcmd, getcmd) in geom_var.items():
        new_row = {'Name': var_name, 'type': 'des', 'initial value': init_value,
                   'min': lower_bound, 'max': upper_bound, 'getcmd': getcmd,
                   'setcmd': setcmd}
        df = df.append(new_row, ignore_index=True)

    df.sort_values(by=['type','Name'], axis=0, ignore_index=True,
                   ascending=[False, True], inplace=True)
    return df


def create_variable_library(Rt, optim_dir_path):
    """Create a dictionnary and a CSV file containing all variables that appear
    in the module list.

    The CSV files lists all the inputs and outputs of each module with :
    * An initial value
    * An upper and lower bound
    * The commands to get and modify the value of the parameter in the CPACS file
    * The variable type : Constraint, Design variable, Objective function component

    Args:
        Rt (class): Contains all the parameters of the current routine.
        optim_dir_path (str): Path to the working directory.

    Returns:
        optim_var_dict (dct): Dictionnary with all optimisation parameters.

    """
    global objective, var
    objective = []
    CSV_PATH = optim_dir_path+'/Variable_library.csv'
    var = {'Name':[], 'type':[], 'init':[], 'min':[], 'max':[], 'xpath':[]}

    for obj in Rt.objective:
        objective.extend(splt('[+*/-]',obj))

    if not os.path.isfile(Rt.user_config):
        log.info('No configuration file found, default one will be generated')
        df = get_default_df(Rt.modules)

        # Save and open CSV file
        df.to_csv(CSV_PATH, index=False, na_rep='-')
        log.info('Variable library file has been generated')
        log.info('Variable library file will opened to be modified')

        OS = sys.platform
        log.info('Identified OS : '+OS)
        if OS == 'linux':
            os.system('libreoffice ' + CSV_PATH)
        elif OS == 'win32':
            os.system('Start excel.exe ' + CSV_PATH.replace('/', '\\'))
        elif OS == 'darwin':
            os.system('Numbers ' + CSV_PATH)

        input('Press ENTER to continue...')
        log.info('Variable library file has been saved at '+CSV_PATH)
        df = pd.read_csv(CSV_PATH, index_col=0, skip_blank_lines=True)
        optim_var_dict = generate_dict(df)
    else:
        log.info('Configuration file found, will be used')
        df = pd.read_csv(Rt.user_config, index_col=0)
        optim_var_dict = generate_dict(df)

        tixi = cpsf.open_tixi(CPACS_OPTIM_PATH)
        dct.update_dict(tixi, optim_var_dict)
        cpsf.close_tixi(tixi, CPACS_OPTIM_PATH)

    return optim_var_dict


if __name__ == '__main__':

    log.info('|-------------------------------------------------|')
    log.info('|Not a standalone module. Nothing will be executed|')
    log.info('|-------------------------------------------------|')
