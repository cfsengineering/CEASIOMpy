#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH, CEASIOM_XPATH

# ===== RCE integration =====

RCE = {
    "name": "Predictive tool module",
    "description": "This module builds a surrogate model to make predictions on data",
    "exec": "pwd\npython prediction.py",
    "author": "Vivien Riolo",
    "email": "-",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = True

# ----- Input -----

cpacs_inout.add_input(
    var_name='Objectives',
    var_type=str,
    default_value='cl/cd,cl',
    unit='-',
    descr="""Objective function list for the surrogate model to predict \n Warning !
    The parameters name must match the ones in the CSV file !""",
    xpath=CEASIOM_XPATH+'/surrogateModel/objective',
    gui=include_gui,
    gui_name='Objective',
    gui_group='Global settings',
)

cpacs_inout.add_input(
    var_name='Aeromap',
    var_type=bool,
    default_value=False,
    unit='-',
    descr="""If only the aeromap has to be used""",
    xpath=CEASIOM_XPATH+'/surrogateModel/useAeromap',
    gui=include_gui,
    gui_name='Aeromap only',
    gui_group='Global settings',
)

cpacs_inout.add_input(
    var_name='',
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to evaluate",
    xpath=CEASIOM_XPATH + '/surrogateModel/aeroMapUID',
    gui=True,
    gui_name='__AEROMAP_SELECTION',
    gui_group='Global settings',
)

cpacs_inout.add_input(
    var_name='data_file',
    var_type='pathtype',
    default_value='-',
    descr='CSV file to be used to train a model',
    xpath=CEASIOM_XPATH+'/surrogateModel/trainFile',
    gui=include_gui,
    gui_name='Training dataset',
    gui_group='Training options'
)

cpacs_inout.add_input(
    var_name='type',
    var_type=list,
    default_value=['KRG', 'KPLSK', 'KPLS', 'RBF', 'IDW', 'LS'],
    unit='-',
    descr='Type of surrogate model to choose from',
    xpath=CEASIOM_XPATH+'/surrogateModel/modelType',
    gui=include_gui,
    gui_name='Type of surrogate',
    gui_group='Training options'
)


# ----- Output -----

# cpacs_inout.add_output(
#     var_name='output',
#     default_value='-',
#     unit='1',
#     descr='Description of the output',
#     xpath='/cpacs/toolspecific/CEASIOMpy/test/myOutput',
# )
