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
    * This module is still a bit tricky to use, it will be simplified in the future
    * Use a class instead of 'optim_var_dict' dictionnary???

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
var = {}
objective = ''

CPACS_OPTIM_PATH = '../Optimisation/ToolInput/ToolInput.xml'
CSV_PATH = '../Optimisation/Variable_library.csv'

OPTIM_XPATH = '/cpacs/toolspecific/CEASIOMpy/Optimisation/'
AEROMAP_XPATH = '/cpacs/vehicles/aircraft/model/analyses/aeroPerformance'

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

# ==============================================================================
#   FUNCTIONS
# ==============================================================================

def first_run(cpacs_path, module_list, modules_pre_list=[]):
    """
    Create dictionnaries for the optimisation problem.
    
    This function runs a first loop to ensure that all problem variables
    are created an can be fed to the optimisation setup program. 

    Parameters
    ----------
    cpacs_path : String
        Path to the CPACS file.
    module_list : List
        List of modules.

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

    # If settingsGUI only needed at the first iteration
    if 'SettingsGUI' in module_list:
        module_list.pop(module_list.index('SettingsGUI'))
    # Optimisation parameters only needed for the first run
    module_list.pop(module_list.index('Optimisation'))

def get_normal(tixi, value_name, entry):
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
    xpath_parent = xpath[:-(len(value_name)+1)]
    def_val = entry.default_value
    type_val = entry.var_type

    # Check if the path exists, else create it
    if not tixi.checkElement(xpath):
        log.info('Branch does not exist')
        cpsf.create_branch(tixi, xpath_parent)
        tixi.addTextElement(xpath_parent, value_name, '-')
        value = '-'
        log.info('Created branch')
        user_val = None
    else:
        user_val = tixi.getTextElement(xpath)

    # Check if a default value can be addded
    if def_val is not None:
        log.info('Default value found'+str(def_val))
        if type_val is bool:
            log.info('Boolean value will be added')
            value = str(def_val)
        elif not tls.isDigit(def_val):
            value = '-'
            log.info('Not a number, "-" will be added')
        else:
            log.info('Float value will be added')
            value = str(def_val)

    # Check if user input is given
    elif user_val is not None:
        log.info('User value found : '+str(user_val))
        if type_val is bool:
            log.info('Boolean value will be added')
            value = str(user_val)
        elif not tls.isDigit(user_val):
            value = '-'
            log.info('Not a number, "-" will be added')
        else:
            log.info('Float value will be added')
            value = str(user_val)
    else:
        log.info('No default value, "-" will be added')
        value = '-'

    # Ignores values that are not int, float or bool
    # TODO : implement the list
    if value != '-':
        tixi.updateTextElement(xpath, value)

        var['Name'].append(entry.var_name)
        var['init'].append(value)
        var['xpath'].append(xpath)

        tls.add_bounds_and_type(entry.var_name, objective, value, var)
        log.info('Added to variable file')


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
            log.info('Default aeromap parameters will be set')

            # Get name of aeromap that is used
            am_nb = tixi.getNumberOfChilds(AEROMAP_XPATH)
            am_uid = tixi.getTextElement(tls.get_aeromap_path([module_name])+'/aeroMapUID')
            log.info('Aeromap \"{}\" will be used for the variables.'.format(am_uid))
            
            # Search the aeromap index in the CPACS file if there are more
            if am_nb > 1:
                log.info('More than 1 aeromap, by defaut the first one will be used')
                for i in range(1,am_nb+1):
                    uid = tixi.getTextAttribute(AEROMAP_XPATH+'/aeromap[{}]'.format(i),'uID')
                    if uid == am_uid:
                        am_index = '[{}]'.format(i)
            else:
                am_index = '[1]'

            for name in ['altitude', 'machNumber', 'angleOfAttack', 'angleOfSideslip',
                         'cl', 'cd', 'cs', 'cml', 'cmd', 'cms']:
                var['Name'].append(name)
                xpath_param = xpath.replace('[i]', am_index)+'/'+name

                value = str(tixi.getDoubleElement(xpath_param))
                var['init'].append(value)

                var['xpath'].append(xpath_param)

                tls.add_bounds_and_type(name, objective, value, var)

        # Normal case
        else:
            get_normal(tixi, value_name, entry)


def generate_dict(df, user_config=''):
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
    
    # Use user-specified CSV or create a new one
    if user_config == '':
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
        log.info('Variable library file has been saved')
        df = pd.read_csv(CSV_PATH, index_col=0)
    else:
        df = pd.read_csv(user_config, index_col=0)

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


def create_variable_library(Rt, tixi='', module_list=[]):
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

    tixi : Tixi3 handler
        
    module_list : list
        List of the modules that are included in the optimisation loop.
    
    Returns
    -------
    optim_var_dict : dict
        Dictionnary with all optimisation parameters

    """
    global objective, var
    objective = Rt.objective
    var = {'Name': [], 'type': [], 'init': [], 'min': [], 'max': [], 'xpath': []}

    if tixi == '':
        tixi = cpsf.open_tixi(CPACS_OPTIM_PATH)

    if Rt.user_config == '' or Rt.user_config == '-':
        log.info('No configuration file specified, a default file will be generated')
        for mod_name, specs in mif.get_all_module_specs().items():
            if specs is not None and mod_name in module_list:
                get_variables(tixi, specs, mod_name)

        # Add the default values for the variables
        # df['uID'] = var['uID']
        df = pd.DataFrame(columns=['Name'], data=var['Name'])
        df['type'] = var['type']
        df['initial value'] = var['init']
        df['min'] = var['min']
        df['max'] = var['max']
        df['getpath'] = var['xpath']

        # Add geometry parameters as design variables (only design type for the moment)
        geom_var = dct.init_design_var_dict(tixi)
        for key, (var_name, [init_value], lower_bound, upper_bound, setcmd, getcmd) in geom_var.items():
            new_row = {'Name': var_name, 'type': 'des', 'initial value': init_value,
                       'min': lower_bound, 'max': upper_bound, 'getpath': getcmd,
                       'setpath': setcmd}
            df = df.append(new_row, ignore_index=True)

        tixi.save(CPACS_OPTIM_PATH)
        tixi.close()
        optim_var_dict = generate_dict(df)
    else:
        df = pd.DataFrame
        log.info('Configuration file specified, will be used')
        optim_var_dict = generate_dict(df, Rt.user_config)

    return optim_var_dict


if __name__ == '__main__':

    log.info('-------------------------------------------------')
    log.info('Not a standalone module. Nothing will be executed')
    log.info('-------------------------------------------------')
