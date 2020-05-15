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
    * Use a class instead of 'optim_var_dict' dictionnay???
    * How to pass 'module_optim' as argument
    * Create a Design of Experiment functions

"""


# ==============================================================================
#   IMPORTS
# ==============================================================================

import numpy as np
import openmdao.api as om

import matplotlib.pyplot as plt
from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])
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
        self.objective = 'cl'
        self.constraints = []
        self.design_vars = {}

        # Driver choice
        self.driver = "COBYLA"


# ==============================================================================
#   FUNCTIONS
# ==============================================================================

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
    # SKINFRICTION_xPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/skinFriction/aeroMapToCalculate'
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
        for keyo, valo in obj.items():
            for key, val in des.items():
                fig, ax = plt.subplots()
                plt.scatter(val, valo)

    # Iterative evolution for Optim
    gen_plot(obj, objective=True)
    gen_plot(des)
    gen_plot(const, constrains=True)

    # 3D plot
    # fig = plt.figure()
    # ax = fig.gca(projection='3d')
    # ax.scatter(des['indeps.wing2_span'],des['indeps.wing1_span'],-obj['objective.cl'])

    plt.show()
