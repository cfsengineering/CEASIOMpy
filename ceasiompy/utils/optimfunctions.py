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

"""


# ==============================================================================
#   IMPORTS
# ==============================================================================
import os
import sys

import pandas as pd

import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.moduleinterfaces as mif
import ceasiompy.utils.workflowfunctions as wkf
import ceasiompy.Optimisation.func.dictionnary as dct
import ceasiompy.Optimisation.func.tools as tls
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

banned_entries = ['wing','delete_old_wkdirs','check_extract_loads']

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
        self.objective = 'cl'

        # Driver choice
        self.driver = "COBYLA"

        # When to save the CPACS
        self.save_iter = 1
        self.max_iter = 200
        self.tol = 1e-3

        # DoE
        self.doedriver = 'uniform'
        self.samplesnb = 3

        # User specified configuration file path
        self.user_config = '../Optimisation/Default_config.csv'

    def get_user_inputs(self, cpacs_path):
        """Take user inputs from the GUI."""
        tixi = cpsf.open_tixi(CPACS_OPTIM_PATH)

        # Problem setup
        self.objective = cpsf.get_value_or_default(tixi, OPTIM_XPATH+'objective', 'cl')
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
        self.user_config = cpsf.get_value_or_default(tixi, OPTIM_XPATH+'Config/filepath', '../Optimisation/Default_config.csv')

        cpsf.close_tixi(tixi, CPACS_OPTIM_PATH)

# ==============================================================================
#   FUNCTIONS
# ==============================================================================

def first_run(module_list, modules_pre_list=[]):
    """
    Run subworkflow once for the optimisation problem.

    This function runs a first loop to ensure that all problem variables
    are created an can be fed to the optimisation setup program.

    Parameters
    ----------
    module_list : List
        List of modules.
    module_pre_list : List
        List of modules that were run in a previous workflow.
    Returns
    -------
    NONE.

    """
    # Check if aeromap results already exists, else run workflow
    global XPATH
    global XPATH_PRE

    log.info('Launching initialization workflow')

    XPATH = tls.get_aeromap_path(module_list)
    if 'PyTornado' in modules_pre_list or 'SU2Run' in modules_pre_list:
        XPATH_PRE = tls.get_aeromap_path(modules_pre_list)
    else:
        XPATH_PRE = XPATH

    # Settings needed for CFD calculation
    if 'Optimisation' not in modules_pre_list:
        module_list.insert(0, 'Optimisation')
    if 'SettingsGUI' not in module_list or 'SettingsGUI' not in modules_pre_list:
        module_list.insert(0, 'SettingsGUI')

    # First iteration to create aeromap results if no pre-workflow
    if XPATH != XPATH_PRE or modules_pre_list == []:
        wkf.copy_module_to_module('Optimisation', 'in', module_list[0], 'in')
        wkf.run_subworkflow(module_list)
        wkf.copy_module_to_module(module_list[-1], 'out', 'Optimisation', 'in')

    # SettingsGUI only needed at the first iteration
    if 'SettingsGUI' in module_list:
        module_list.pop(module_list.index('SettingsGUI'))

    # Optimisation parameters only needed for the first run
    module_list.pop(module_list.index('Optimisation'))


def get_normal_param(tixi, value_name, entry, outputs):
    """
    Add a variable to the optimisation dictionnary.

    It is checked if the variable has a user-specified initial value, else it
    will assign a default value or the variable will be excluded from the
    problem.

    Parameters
    ----------
    tixi : Tixi3 handler

    value_name : string.
        Name of the parameter.
    entry :

    Returns
    -------
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
    if not tls.is_digit(value):
        log.info('Not a digital value')
        value = '-'
    elif entry.var_type == bool:
        log.info('Boolean, yet not implemented')
        value = '-'

    log.info('Value : {}'.format(value))
    # Ignores values that are not int or float
    # TODO : implement the list
    if value != '-':
        value = str(value)
        tixi.updateTextElement(xpath, value)

        var['Name'].append(entry.var_name)
        var['init'].append(value)
        var['xpath'].append(xpath)

        tls.add_type(entry, outputs, objective, var)
        tls.add_bounds(entry.var_name, value, var)
        log.info('Added to variable file')


def get_aero_param(tixi, xpath, module_name):

    log.info('Default aeromap parameters will be set')

    # Get name of aeromap that is used
    am_nb = tixi.getNumberOfChilds(AEROMAP_XPATH)
    am_uid = tixi.getTextElement(tls.get_aeromap_path([module_name])+'/aeroMapUID')
    log.info('Aeromap \"{}\" will be used for the variables.'.format(am_uid))

    # Search the aeromap index in the CPACS file if there are more
    if am_nb > 1:
        for i in range(1,am_nb+1):
            am_xpath = AEROMAP_XPATH+'/aeromap[{}]'.format(i)
            uid = tixi.getTextAttribute(am_xpath, 'uID')
            if uid == am_uid:
                am_index = '[{}]'.format(i)
    else:
        am_index = '[1]'

    outputs = ['cl', 'cd', 'cs', 'cml', 'cmd', 'cms']
    inputs = ['altitude', 'machNumber', 'angleOfAttack', 'angleOfSideslip']
    inputs.extend(outputs)
    for name in inputs:
        xpath_param = xpath.replace('[i]', am_index)+'/'+name
        value = str(tixi.getDoubleElement(xpath_param))

        var['Name'].append(name)
        var['init'].append(value)
        var['xpath'].append(xpath_param)

        tls.add_type(name, outputs, objective, var)
        tls.add_bounds(name, value, var)


def get_variables(tixi, specs, module_name):
    """
    Retrieve input and output variables of a module

    Parameters
    ----------
    tixi : Tixi3 handler

    specs : class
        Contains the modules inputs and outputs specifications.

    Returns
    -------
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
            get_aero_param(tixi, xpath, module_name)
        # Normal case
        else:
            get_normal_param(tixi, value_name, entry, specs.cpacs_inout.outputs)



def generate_dict(df):
    """
    Write all variables in a CSV file or use a predefined file.

    Parameters
    ----------
    df : DataFrame
        Contains all the variable. Used to passs from a csv to a dict

    Returns
    -------
    optim_var_dict : dict
        Used to pass the variables to the openMDAO setup.

    """
    df = df.dropna()
    df.to_csv(CSV_PATH, index=True, na_rep='-')
    defined_dict = df.to_dict('index')

    # Transform to a convenient form of dict
    optim_var_dict = {}
    for key, subdict in defined_dict.items():
        if subdict['initial value'] in ['False', 'True', '-'] or subdict['type'] == 'obj':
            optim_var_dict[key] = (subdict['type'], [subdict['initial value']],
                                   subdict['min'], subdict['max'],
                                   subdict['getpath'], subdict['setpath'])
        else:
            optim_var_dict[key] = (subdict['type'], [float(subdict['initial value'])],
                                   float(subdict['min']), float(subdict['max']),
                                   subdict['getpath'], subdict['setpath'])
    return optim_var_dict


def get_default_df(module_list):

    tixi = cpsf.open_tixi(CPACS_OPTIM_PATH)
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
    df['getpath'] = var['xpath']

    # Add geometry parameters as design variables (only design type for the moment)
    tixi = cpsf.open_tixi(CPACS_OPTIM_PATH)
    geom_var = dct.init_design_var_dict(tixi)
    for key, (var_name, [init_value], lower_bound, upper_bound, setcmd, getcmd) in geom_var.items():
        new_row = {'Name': var_name, 'type': 'des', 'initial value': init_value,
                   'min': lower_bound, 'max': upper_bound, 'getpath': getcmd,
                   'setpath': setcmd}
        df = df.append(new_row, ignore_index=True)

    return df

def create_variable_library(Rt, optim_dir_path):
    """
    Create a dictionnary and a CSV file containing all variables that appear
    in the module list.

    The CSV files lists all the inputs and outputs of each module with :
    * An initial value
    * An upper and lower bound
    * The commands to get and modify the value of the parameter in the CPACS file
    * The variable type : Constraint, Design variable, Objective function component

    Parameters
    ----------
    Rt : Class
        Contains

    optim_dir_path : str
        Path to the working directory.

    Returns
    -------
    optim_var_dict : dict
        Dictionnary with all optimisation parameters

    """
    global objective, var, CSV_PATH
    CSV_PATH = optim_dir_path+'/Variable_library.csv'
    objective = Rt.objective
    var = {'Name':[], 'type':[], 'init':[], 'min':[], 'max':[], 'xpath':[]}

    if not os.path.isfile(Rt.user_config):
        log.info('No configuration file found, default one will be generated')
        df = get_default_df(Rt.modules)

        # Save and open CSV file
        df.to_csv(CSV_PATH, index=False, na_rep='-')
        log.info('Variable library file has been generated')

        OS = sys.platform
        log.info('Identified OS : '+OS)
        if OS == 'linux':
            os.system('libreoffice ' + CSV_PATH)
        elif OS == 'win32':
            os.system('Start excel.exe ' + CSV_PATH.replace('/', '\\'))
        elif OS == 'darwin':
            os.system('Numbers ' + CSV_PATH)

        log.info('Variable library file has been saved at '+CSV_PATH)
        df = pd.read_csv(CSV_PATH, index_col=0)
    else:
        log.info('Configuration file found, will be used')
        df = pd.read_csv(Rt.user_config, index_col=0)

    optim_var_dict = generate_dict(df)

    return optim_var_dict


if __name__ == '__main__':

    log.info('-------------------------------------------------')
    log.info('Not a standalone module. Nothing will be executed')
    log.info('-------------------------------------------------')
