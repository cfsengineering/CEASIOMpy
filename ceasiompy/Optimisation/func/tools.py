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
    * Write the module

"""

#==============================================================================
#   IMPORTS
#==============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   FUNCTIONS
#==============================================================================


def get_aeromap_path(module_list):
    """
    Return xpath of selected aeromap.

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
    Return accronym of a name.

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


def add_bounds(name, objective, value, var):
    """
    Add upper and lower bound, plsu the variable type.

    Returns
    -------
    None.

    """
    # var_accro = accronym(name)
    var_accro = ''
    if name in objective or var_accro in objective:
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
