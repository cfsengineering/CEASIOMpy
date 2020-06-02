#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH, CEASIOM_XPATH

# ===== RCE integration =====

RCE = {
    "name": "ModuleTemplate",
    "description": "This is a template module",
    "exec": "pwd\npython moduletemplate.py",
    "author": "Neil Armstrong",
    "email": "neil@nasa.gov",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = True

# ----- Input -----

cpacs_inout.add_input(
    var_name='Objective function',
    var_type=str,
    default_value='cl/cd',
    unit='-',
    descr='Objective function of the optimisation problem',
    xpath=CEASIOM_XPATH+'/Optimisation/objective',
    gui=include_gui,
    gui_name='Objective',
    gui_group='Objective function',
)

cpacs_inout.add_input(
    var_name='minmax',
    var_type=list,
    default_value=['min','max'],
    unit='-',
    descr='Objective function of the optimisation problem',
    xpath=CEASIOM_XPATH+'/Optimisation/minmax',
    gui=include_gui,
    gui_name='Optimisation goal',
    gui_group='Global settings'
)

cpacs_inout.add_input(
    var_name='Driver',
    var_type=list,
    default_value=['COBYLA'],
    unit='-',
    descr='Choose the driver to run the routine with',
    xpath=CEASIOM_XPATH+'/Optimisation/parameters/driver',
    gui=include_gui,
    gui_name='Driver',
    gui_group='Global settings'
)

cpacs_inout.add_input(
    var_name='iterations',
    var_type=int,
    default_value=200,
    unit='-',
    descr='Number of iterations to do',
    xpath=CEASIOM_XPATH+'/Optimisation/iterationNB',
    gui=include_gui,
    gui_name='Max number of iterations',
    gui_group='Global settings'
)

cpacs_inout.add_input(
    var_name='Tolerance',
    var_type=float,
    default_value=1e-3,
    unit='-',
    descr='Tolerance criterion',
    xpath=CEASIOM_XPATH+'/Optimisation/tolerance',
    gui=include_gui,
    gui_name='Tolerance',
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
    var_name='file_saving',
    var_type=int,
    default_value=1,
    unit='iteration',
    descr='Save file every X iteration',
    xpath=CEASIOM_XPATH+'/Optimisation/saving/perIter',
    gui=include_gui,
    gui_name='Saving geometry every',
    gui_group='Global settings'
)


cpacs_inout.add_input(
    var_name='DoEDriver',
    var_type=list,
    default_value=['Uniform','Fullfactorial'],
    unit='-',
    descr='Choose the type of sample generator',
    xpath=CEASIOM_XPATH+'/Optimisation/parameters/DoE/driver',
    gui=include_gui,
    gui_name='Driver (DoE)',
    gui_group='DoE settings (if required)'
)

cpacs_inout.add_input(
    var_name='sample_generator',
    var_type=int,
    default_value=3,
    unit='-',
    descr='Choose the driver to run the routine with',
    xpath=CEASIOM_XPATH+'/Optimisation/parameters/DoE/sampleNB',
    gui=include_gui,
    gui_name='Sample number',
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

    # Rt.doetype = 'uniform'
    # Rt.samplesnb = 3
    # Rt.user_config = '..//Optimisation/defvar2.csv'