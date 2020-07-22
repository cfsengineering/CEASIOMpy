#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH, CEASIOM_XPATH

# ===== RCE integration =====

RCE = {
    "name": "SMUse module",
    "description": "This module uses a surrogate model to make predictions on data",
    "exec": "pwd\npython smuse.py",
    "author": "Vivien Riolo",
    "email": "info@cfse.ch",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = True

# ----- Input -----

cpacs_inout.add_input(
    var_name='model_file',
    var_type='pathtype',
    default_value='-',
    descr='File that contains a trained model',
    xpath=CEASIOM_XPATH+'/surrogateModelUse/modelFile',
    gui=include_gui,
    gui_name='Model to use',
    gui_group='Prediction options'
)



cpacs_inout.add_input(
    var_name='Aeromap only',
    var_type=bool,
    default_value='False',
    unit=None,
    descr="""Indicate wether or not the parameters are all contained in an aeromap, in which case
    the workflow only has to be run once.""",
    xpath=CEASIOM_XPATH+'/surrogateModelUse/AeroMapOnly',
    gui=include_gui,
    gui_name='Aeromap only',
    gui_group='Aeromap settings'
)

cpacs_inout.add_input(
    var_name='',
    var_type=list,
    default_value=None,
    descr='To which aeroMap the model shall take andn write the entries',
    xpath=CEASIOM_XPATH + '/surrogateModelUse/aeroMapUID',
    gui=True,
    gui_name='__AEROMAP_SELECTION',
)
# ----- Output -----

# cpacs_inout.add_output(
#     var_name='output',
#     default_value='-',
#     unit='1',
#     descr='Description of the output',
#     xpath='/cpacs/toolspecific/CEASIOMpy/test/myOutput',
# )
