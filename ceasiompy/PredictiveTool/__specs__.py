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
    xpath=CEASIOM_XPATH+'/SurrogateModel/objective',
    gui=include_gui,
    gui_name='Objective',
    gui_group='Global settings',
)

cpacs_inout.add_input(
    var_name='file',
    var_type=str,
    default_value='Aeromap_generated.csv',
    unit='-',
    descr='File that summarises the inputs and outputs to train the model with',
    xpath=CEASIOM_XPATH+'/SurrogateModel/file',
    gui=include_gui,
    gui_name='File',
    gui_group='Global settings'
)

cpacs_inout.add_input(
    var_name='Aeromap only',
    var_type=bool,
    default_value='False',
    unit='-',
    descr="""Indicate wether or not the parameters are all contained in an aeromap, in which case
    the workflow only has to be run once.""",
    xpath=CEASIOM_XPATH+'/SurrogateModel/AeroMapOnly',
    gui=include_gui,
    gui_name='Aeromap specific',
    gui_group='Global settings'
)

cpacs_inout.add_input(
    var_name='modules',
    var_type=list,
    default_value='-',
    unit='-',
    descr='List of modules to run',
    gui=False,
)

cpacs_inout.add_input(
    var_name='DoEDriver',
    var_type=list,
    default_value=['Uniform','Fullfactorial', 'LatinHypercube', 'PlackettBurman'],
    unit='-',
    descr='Choose the type of sample generator',
    xpath=CEASIOM_XPATH+'/SurrogateModel/DoE/driver',
    gui=include_gui,
    gui_name='Driver (DoE)',
    gui_group='DoE settings (if required)'
)

cpacs_inout.add_input(
    var_name='sample_generator',
    var_type=int,
    default_value=3,
    unit='-',
    descr='Needed to indicate the number of samples to be generated',
    xpath=CEASIOM_XPATH+'/Optimisation/parameters/DoE/sampleNB',
    gui=include_gui,
    gui_name='Sample # parameter',
    gui_group='DoE settings (if required)'
)

cpacs_inout.add_input(
    var_name='Configuration file path',
    var_type='pathtype',
    default_value='../Optimisation/Default_config.csv',
    unit='1',
    descr='Absolute path to the CSV file',
    xpath=CEASIOM_XPATH + '/Optimisation/Config/filepath',
    gui=True,
    gui_name='CSV file path',
    gui_group='Configuration',
)

# ----- Output -----

# cpacs_inout.add_output(
#     var_name='output',
#     default_value='-',
#     unit='1',
#     descr='Description of the output',
#     xpath='/cpacs/toolspecific/CEASIOMpy/test/myOutput',
# )
