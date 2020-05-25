"""
CEASIOMpy: Conceptual Aircraft Design Software.

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Tool to create workflow for CEASIOMpy (without using RCE)

Python version: >=3.6

| Author: Vivien Riolo
| Creation: 2020-04-10
| Last modification: 2020-04-10

Todo:
----
    * Write the doc
    * This module is still a bit tricky to use, it will be simplified in the future
    * Use a class instead of 'optim_var_dict' dictionnary???
    * How to pass 'module_optim' as argument
    * Create a Design of Experiment functions

"""


# ==============================================================================
#   IMPORTS
# ==============================================================================
import os
import sys
import numpy as np
import openmdao.api as om
import pandas as pd

import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.moduleinterfaces as mif
import ceasiompy.Optimisation.func.dictionnary as dct

import matplotlib.pyplot as plt
from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])


# ==============================================================================
#   GLOBALS
# ==============================================================================
var = {}
objective = ''
# CPACS_OPTIM_PATH = '../PyTornado/ToolOutput/ToolOutput.xml'
CPACS_OPTIM_PATH = '../Optimisation/ToolInput/ToolInput.xml'
CSV_PATH = '../Optimisation/Variable_library.csv'


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

        # User specified configuration file path
        self.user_config = ''


# ==============================================================================
#   FUNCTIONS
# ==============================================================================
def gen_plot(dic, objective=False, constrains=False):
    """
    Generate plots.

    Parameters
    ----------
    dic : TYPE
        DESCRIPTION.
    objective : TYPE, optional
        DESCRIPTION. The default is False.
    constrains : TYPE, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    None.

    """
    iterations = len(dic)

    plt.figure()
    if objective:
        for key, lst in dic.items():
            iterations = np.arange(len(lst))
            plt.plot(iterations, -lst+lst[0], label=key)
            plt.legend()
    elif constrains:
        for key, lst in dic.items():
            if 'const' in key:
                iterations = np.arange(len(lst))
                plt.plot(iterations, lst-lst[0], label=key)
                plt.legend()
    else:
        for key, lst in dic.items():
            iterations = np.arange(len(lst))
            plt.plot(iterations, lst-lst[0], label=key)
            plt.legend()


def read_results(optim_dir_path, routine_type):
    """
    Read sql file.

    Returns
    -------
    None.

    """
    # Read recorded options
    path = optim_dir_path
    cr = om.CaseReader(path + '/Driver_recorder.sql')
    # driver_cases = cr.list_cases('driver') (If  multiple recorders)

    cases = cr.get_cases()

    # Initiates dictionnaries
    case1 = cr.get_case(0)
    obj = case1.get_objectives()
    des = case1.get_design_vars()
    const = case1.get_constraints()

    for case in cases[1::]:
        for key, val in case.get_objectives().items():
            obj[key] = np.append(obj[key], val)

        for key, val in case.get_design_vars().items():
            des[key] = np.append(des[key], val)

        for key, val in case.get_constraints().items():
            if 'const' in key:
                const[key] = np.append(const[key], val)

    # Datapoints for DoE
    if routine_type.upper() == 'DOE':
        fig=plt.figure()
        l = 0
        c = 1
        cols_per_row = 5
        nbL = len(obj.keys()) + len(des.keys())%cols_per_row
        nbC = cols_per_row

        for keyo, valo in obj.items():
            plt.ylabel(keyo)
            for key, val in des.items():
                plt.subplot(nbL, nbC, c+l*nbC)
                plt.scatter(val, valo)
                plt.xlabel(key)
                if c==1:
                    plt.ylabel(keyo)
                c += 1
                if c > cols_per_row:
                    l += 1
                    c = 1
            c = 1
            l += 1

    # Iterative evolution for Optim
    gen_plot(obj, objective=True)
    gen_plot(des)
    gen_plot(const, constrains=True)

    # 3D plot
    # fig = plt.figure()
    # ax = fig.gca(projection='3d')
    # ax.scatter(des['indeps.wing2_span'],des['indeps.wing1_span'],-obj['objective.cl'])

    plt.show()


def get_aeromap_path(module_list):
    """
    Return xpath of selected aeromap.

    Parameters
    ----------
    module_list : List
        DESCRIPTION.

    Returns
    -------
    xpath : String
        DESCRIPTION.

    """
    PYTORNADO_XPATH = '/cpacs/toolspecific/pytornado'
    SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'
    # SKINFRICTION_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/skinFriction/aeroMapToCalculate'
    for module in module_list:
        if module == 'SU2Run':
            log.info('Found SU2 analysis')
            xpath = SU2_XPATH
            return xpath
        elif module == 'PyTornado':
            log.info('Found PyTornado analysis')
            xpath = PYTORNADO_XPATH
            return xpath
        else:
            xpath = 'None'
    return xpath


def update_dict(tixi, optim_var_dict):
    """
    Update dictionnary after a workflow

    Parameters
    ----------
    tixi : TYPE
        DESCRIPTION.
    optim_var_dict : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    for name, (val_type, listval, minval, maxval, getcommand, setcommand) in optim_var_dict.items():
        log.info(name)
        log.info(getcommand)
        if setcommand == '-':
            log.info("ADD new Val")
            new_val = tixi.getDoubleElement(getcommand)
            # Checks type of variable
            if type(new_val) == list:
                listval.append(new_val[-1])
                log.info(name + ' ' + str(new_val[-1]))
            else:
                listval.append(new_val)
                log.info(name + ' ' + str(new_val))


def isDigit(value):
    """
    Check if a string value is a float.

    Parameters
    ----------
    value : string

    Returns
    -------
    Boolean.

    """
    if type(value) is list:
        return False
    else:
        try:
            float(value)
            return True
        except ValueError:
            return False


def accronym(name):
    """
    Return accronym of a name.

    Parameters
    ----------
    name : string
        name of a variable.

    Returns
    -------
    None.

    """
    l = name.split('_')
    accro = ''
    for word in l:
        accro += word[0]
    log.info('Accronym : '+ accro)
    return accro


def get_normal(tixi, value_name, entry):
    """
    Add a variable the dictionnary

    Parameters
    ----------
    tixi : TYPE
        DESCRIPTION.
    value_name : TYPE
        DESCRIPTION.
    entry : TYPE
        DESCRIPTION.

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
        log.info('Default value found')
        log.info(def_val)
        if type_val is bool:
            log.info('Boolean value will be added')
            value = str(def_val)
        elif not isDigit(def_val):
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
        elif not isDigit(user_val):
            value = '-'
            log.info('Not a number, "-" will be added')
        else:
            log.info('Float value will be added')
            value = str(user_val)
    else:
        log.info('No default value, "-" will be added')
        value = '-'

    tixi.updateTextElement(xpath, value)

    var['Name'].append(entry.var_name)
    var['init'].append(value)
    var['xpath'].append(xpath)
    var_accro = accronym(entry.var_name)
    if entry.var_name in objective or var_accro in objective:
        var['type'].append('obj')
    else:
        var['type'].append('des')
    log.info('Added to variable file')


def get_variables(tixi, specs):
    """
    Retrieve input and output variables of a module

    Parameters
    ----------
    tixi : TYPE
        DESCRIPTION.
    specs : TYPE
        DESCRIPTION.

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
            # Get number of aeromaps
            for name in ['altitude', 'machNumber', 'angleOfAttack', 'angleOfSideslip',
                         'cl', 'cd', 'cs', 'cml', 'cmd', 'cms']:
                var['Name'].append(name)
                xpath_param = xpath.replace('[i]', '[1]')+'/'+name
                var['init'].append(tixi.getDoubleElement(xpath_param))
                # TODO Solve the aeromap problem
                var['xpath'].append(xpath_param)
                if name in objective:
                    var['type'].append('obj')
                else:
                    var['type'].append('des')

        # Normal case
        else:
            get_normal(tixi, value_name, entry)

    print(var)

def generate_dict(df, user_config=''):
    """
    Write all variables in a CSV file or use a predefined file.

    Parameters
    ----------
    df : TYPE
        DESCRIPTION.

    Returns
    -------
    optim_var_dict : TYPE
        DESCRIPTION.

    """
    if user_config == '':
        # Save and open CSV file
        # TODO : check multiplatform usage
        df.to_csv(CSV_PATH, index=False, na_rep='-')
        log.info('Variable library file has been generated')

        OS = sys.platform
        log.info('Identified OS : '+OS)
        if OS == 'linux':
            os.system('libreoffice ' + CSV_PATH)
        elif OS == 'win32':
            os.system('Start excel.exe ' + CSV_PATH)
        elif OS == 'darwin':
            os.system('Numbers ' + CSV_PATH)
        log.info('Variable library file has been saved')
        df = pd.read_csv(CSV_PATH, index_col=0)
    else:
        df = pd.read_csv(user_config, index_col=0)

    df = df.dropna()
    print(df)
    df.to_csv(CSV_PATH, index=True, na_rep='-')
    defined_dict = df.to_dict('index')

    # Transform to a convenient form of dict
    optim_var_dict = {}
    for key, subdict in defined_dict.items():
        if subdict['initial value'] in ['False', 'True', '-']:
            optim_var_dict[key] = (subdict['type'], [subdict['initial value']],
                                   subdict['min'], subdict['max'],
                                   subdict['getpath'], subdict['setpath'])
        else:
            optim_var_dict[key] = (subdict['type'], [float(subdict['initial value'])],
                                   subdict['min'], subdict['max'],
                                   subdict['getpath'], subdict['setpath'])
    return optim_var_dict


def create_variable_library(Rt, tixi='', module_list=[]):
    """
    Create .cvs file with all the variables and their xpath

    Returns
    -------
    None.

    """
    global objective, var
    objective = Rt.objective
    var = {'Name': [], 'type': [], 'init': [], 'xpath': []}

    if tixi == '':
        tixi = cpsf.open_tixi(CPACS_OPTIM_PATH)

    if Rt.user_config == '':
        log.info('No configuration file specified, a default file will be generated')
        for mod_name, specs in mif.get_all_module_specs().items():
            if specs is not None and mod_name in module_list:
                get_variables(tixi, specs)

        # Add the default values for the variables
        # df['uID'] = var['uID']
        df = pd.DataFrame(columns=['Name'], data=var['Name'])
        df['type'] = var['type']
        df['initial value'] = var['init']
        df['min'] = -1
        df['max'] = 1
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
    Rt = Routine()
    create_variable_library(Rt, module_list=['WeightConventional', 'PyTornado'])
