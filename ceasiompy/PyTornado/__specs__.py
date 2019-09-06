#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH

cpacs_inout = CPACSInOut()

REFS_XPATH = AIRCRAFT_XPATH + '/model/reference'
WING_XPATH = AIRCRAFT_XPATH + '/model/wings'

#===== Input =====

cpacs_inout.add_input(
    var_name='x_CG',
    default_value=None,
    unit='m',
    descr='Centre of gravity (x-coordinate)',
    cpacs_path=REFS_XPATH + '/point/x'
)

cpacs_inout.add_input(
    var_name='y_CG',
    default_value=None,
    unit='m',
    descr='Centre of gravity (y-coordinate)',
    cpacs_path=REFS_XPATH + '/point/x'
)

cpacs_inout.add_input(
    var_name='z_CG',
    default_value=None,
    unit='m',
    descr='Centre of gravity (z-coordinate)',
    cpacs_path=REFS_XPATH + '/point/x'
)

cpacs_inout.add_input(
    var_name='area',
    default_value=None,
    unit='m^2',
    descr='Reference area for force and moment coefficients',
    cpacs_path=REFS_XPATH + '/area'
)

cpacs_inout.add_input(
    var_name='length',
    default_value=None,
    unit='m',
    descr='Reference length for force and moment coefficients',
    cpacs_path=REFS_XPATH + '/length'
)

cpacs_inout.add_input(
    var_name='wing',
    default_value=None,
    unit='-',
    descr='Aircraft lifting surface',
    cpacs_path=WING_XPATH,
)

# ===== Output =====

# cpacs_inout.add_output(
#     var_name='output',
#     default_value=None,
#     unit='1',
#     descr='Description of the output',
#     cpacs_path=CEASIOM_XPATH + '/...',
# )

RCE = {
    "name": "PyTornado",
    "description": "Wrapper module for PyTornado",
    "exec": "pwd\npython runpytornado.py",
    "author": "Aaron Dettmann",
    "email": "dettmann@kth.se",
}

XPATH_PYTORNADO = '/cpacs/toolspecific/pytornado'

GUI_SETTINGS = {
    'Aero map name': ['', str, None, XPATH_PYTORNADO + '/aeroMapUID', 'Name of the aero map to evaluate'],
    'Chordwise panels': [10, int, '1', XPATH_PYTORNADO + '/vlm_autopanels_c', 'Number of chordwise panels'],
    'Spanwise panels': [5, int, '1', XPATH_PYTORNADO + '/vlm_autopanels_s', 'Number of spanwise panels'],
    'Show plot lattice': [False, bool, None, XPATH_PYTORNADO + '/plot/lattice/show', 'Show lattice plot?'],
    'Save plot lattice': [False, bool, None, XPATH_PYTORNADO + '/plot/lattice/save', 'Save lattice plot?'],
}
