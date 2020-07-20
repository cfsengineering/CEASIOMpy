#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH, CEASIOM_XPATH

# ===== RCE integration =====

RCE = {
    "name": "SMTrain module",
    "description": "This module generates a surrogate model",
    "exec": "pwd\npython smtrain.py",
    "author": "Vivien Riolo",
    "email": "info@cfse.ch",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = True

# ----- Input -----

cpacs_inout.add_input(
    var_name='Objectives',
    var_type=str,
    default_value='cl',
    unit='-',
    descr="""Objective function list for the surrogate model to predict \n Warning !
    The parameters name must match the ones in the CSV file !""",
    xpath=CEASIOM_XPATH+'/surrogateModel/objective',
    gui=include_gui,
    gui_name='Objective',
    gui_group='Global settings',
)

cpacs_inout.add_input(
    var_name='trainig_part',
    var_type=float,
    default_value='0.9',
    descr='Defining the percentage of the data to use to train the model in [0;1]',
    xpath=CEASIOM_XPATH+'/surrogateModel/trainingPercentage',
    gui=include_gui,
    gui_name='% of training data',
    gui_group='Global settings'
)

cpacs_inout.add_input(
    var_name='Show_validation_plots',
    var_type=bool,
    default_value=True,
    unit=None,
    descr='Choose if the validation plots must be shown or not',
    xpath=CEASIOM_XPATH+'/surrogateModel/showPlots',
    gui=include_gui,
    gui_name='Show plots',
    gui_group='Global settings',
)

cpacs_inout.add_input(
    var_name='Aeromap',
    var_type=bool,
    default_value=False,
    unit=None,
    descr="""If only the aeromap has to be used""",
    xpath=CEASIOM_XPATH+'/surrogateModel/useAeromap',
    gui=include_gui,
    gui_name='Use an aeromap',
    gui_group='Aeromap settings',
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
    gui_group='Aeromap settings',
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
    default_value=['KRG', 'KPLSK', 'KPLS', 'LS'],
    unit=None,
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
