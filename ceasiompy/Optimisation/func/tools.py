"""
CEASIOMpy: Conceptual Aircraft Design Software.

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This module contains the tools used to create an adequate dictionnary.

Python version: >=3.6

| Author : Vivien Riolo
| Creation: 2020-05-26
| Last modification: 2020-05-26

TODO
----
    * Solve the accronym problematic

"""

#==============================================================================
#   IMPORTS
#==============================================================================
import numpy as np
import openmdao.api as om
import matplotlib.pyplot as plt

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   FUNCTIONS
#==============================================================================

def gen_plot(dic, objective=False, constrains=False):
    """
    Generate plots.

    Parameters
    ----------
    dic : dictionnary
        Can contain the constraints, design or objective variables.
    objective : Boolean, optional
        Checks if the objective variables are passed. The default is False.
    constrains : Boolean, optional
        Checks if the objective variables are passed. The default is False.

    TODO:
        *Find an adequate way of representation of the variables 
        (normalized ? If yes, how ?)
        
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
    Read sql file and calls the function to generate the plots

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
        plt.figure()
        r = 0
        c = 1
        cols_per_row = 5
        nbR = len(obj.keys()) + len(des.keys()) / cols_per_row
        nbC = cols_per_row
        for keyo, valo in obj.items():
            plt.ylabel(keyo)
            for key, val in des.items():
                plt.subplot(nbR, nbC, c+r*nbC)
                plt.scatter(val, valo)
                plt.xlabel(key)
                if c == 1:
                    plt.ylabel(keyo)
                c += 1
                if c >= cols_per_row:
                    r += 1
                    c = 1
            c = 1
            r += 1

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

    Check the modules that will be run in the optimisation routine to specify
    the path to the correct aeromap in the CPACS file.
    
    Parameters
    ----------
    module_list : List

    Returns
    -------
    xpath : String
    """
    PYTORNADO_XPATH = '/cpacs/toolspecific/pytornado'

    SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'
    # SKINFRICTION_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/skinFriction/aeroMapToCalculate'

    for module in module_list:
        if module == 'SU2Run':
            log.info('Found SU2 analysis')
            xpath = SU2_XPATH
        elif module == 'PyTornado':
            log.info('Found PyTornado analysis')
            xpath = PYTORNADO_XPATH
        else:
            xpath = 'None'
    return xpath


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
        except:
            return False


def accronym(name):
    """
    Return accronym of a name. (EXPERIMENTAL)
    
    In order to detect the values specified by the user as accronyms, the 
    complete name of a variable is decomposed and the first letter of
    each word is taken.
    
    Ex : 'maximal take off mass' -> 'mtom'
    
    TODO : see how it can be made more robust as some names have the same
    accronym

    Parameters
    ----------
    name : string
        name of a variable.

    Returns
    -------
    None.

    """
    full_name = name.split('_')
    accro = ''
    for word in full_name:
        if word.lower() in ['nb']:
            accro += word
        else:
            accro += word[0]
    log.info('Accronym : ' + accro)
    return accro


def add_bounds_and_type(name, objective, value, var):
    """
    Add upper and lower bound, plus the variable type.

    20% of the initial value is added and substracted to create the 
    boundaries.
    The type of the variable (boundary, constraint, objective function)
    is also specified.
    
    Parameters
    ----------
    name : string
        Name of a variable.
    objective : list
        List of variable names or accronyms appearing in the objective function
    value : 

    Returns
    -------
    None.

    """
    # var_accro = accronym(name)
    accro = 'XXX'
    if name in objective or accro in objective:
        log.info("{} in objective function expression.".format(name))
        log.info(objective)
        var['type'].append('obj')
        lower = '-'
        upper = '-'
    else:
        var['type'].append('des')
        if value in ['False', 'True']:
            lower = '-'
            upper = '-'
        elif value.isdigit():
            value = int(value)
            lower = round(value-abs(0.2*value))
            upper = round(value+abs(0.2*value))
            if lower == upper:
                lower -= 1
                upper += 1
        else:
            value = float(value)
            lower = round(value-abs(0.2*value))
            upper = round(value+abs(0.2*value))
            if lower == upper:
                lower -= 1.0
                upper += 1.0

    var['min'].append(lower)
    var['max'].append(upper)
