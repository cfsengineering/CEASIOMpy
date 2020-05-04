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

from matplotlib.pyplot import plot, show, legend, figure

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
        self.constrains = {'cms': (-0.1, 0.1)}
        self.design_vars = {}

        # Driver choice
        self.driver = "COBYLA"


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

    figure()
    if objective:
        for key, lst in dic.items():
            iterations = np.arange(len(lst))
            plot(iterations, -lst+lst[0], label=key)
            legend()
    elif constrains:
        for key, lst in dic.items():
            iterations = np.arange(len(lst))
            plot(iterations, lst/lst[0], label=key)
            legend()
    else:
        for key, lst in dic.items():
            iterations = np.arange(len(lst))
            plot(iterations, lst/lst[0], label=key)
            legend()


def read_results():
    """
    Read sql file.

    Returns
    -------
    None.

    """
    # Read recorded options
    path = '../Optimisation/'
    cr = om.CaseReader(path + 'Driver_recorder.sql')
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
            const[key] = np.append(const[key], val)

    gen_plot(obj, objective=True)
    gen_plot(des)
    gen_plot(const, constrains=True)

    show()

