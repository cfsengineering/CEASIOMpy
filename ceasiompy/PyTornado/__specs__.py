#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH

cpacs_inout = CPACSInOut()

REFS_XPATH = AIRCRAFT_XPATH + '/model/reference'
WING_XPATH = AIRCRAFT_XPATH + '/model/wings'
XPATH_PYTORNADO = '/cpacs/toolspecific/pytornado'

#===== Input =====

cpacs_inout.add_input(
    var_name='',
    var_type=str,
    default_value=None,
    unit=None,
    descr="Name of the aero map to evaluate",
    cpacs_path=XPATH_PYTORNADO + '/aeroMapUID',
    gui=True,
    gui_name='Aero map name',
    gui_group=None,
)

# ----- Discretisation -----
# TO BE IMPROVED IN NEW PYTORNADO VERSION
cpacs_inout.add_input(
    var_name='',
    var_type=int,
    default_value=20,
    unit=None,
    descr="The number of chordwise VLM panels",
    cpacs_path=XPATH_PYTORNADO + '/vlm_autopanels_c',
    gui=True,
    gui_name='Number of chordwise panels',
    gui_group='Dicretisation',
)

cpacs_inout.add_input(
    var_name='',
    var_type=int,
    default_value=5,
    unit=None,
    descr="The number of spanwise VLM panels",
    cpacs_path=XPATH_PYTORNADO + '/vlm_autopanels_s',
    gui=True,
    gui_name='Number of spanwise panels',
    gui_group='Dicretisation',
)

# ----- Plots -----
for plot_name in ['lattice', 'geometry', 'results', 'matrix_downwash']:
    cpacs_inout.add_input(
        var_name='',
        var_type=bool,
        default_value=False,
        unit=None,
        descr=f"Show a {plot_name} plot (program will pause to show)",
        cpacs_path=XPATH_PYTORNADO + f'/plot/{plot_name}/show',
        gui=True,
        gui_name='Show plot',
        gui_group=f'{plot_name.capitalize()} plot',
    )

    cpacs_inout.add_input(
        var_name='',
        var_type=bool,
        default_value=False,
        unit=None,
        descr=f"Show a {plot_name} plot",
        cpacs_path=XPATH_PYTORNADO + f'/plot/{plot_name}/save',
        gui=True,
        gui_name='Save plot',
        gui_group=f'{plot_name.capitalize()} plot',
    )

    # TODO: add optional settings

# ----- Save other results -----
for save_name in ['global', 'panelwise', 'aeroperformance']:
    cpacs_inout.add_input(
        var_name='',
        var_type=bool,
        default_value=False,
        unit=None,
        descr=f"Save PyTornado '{save_name}' results",
        cpacs_path=XPATH_PYTORNADO + f'/save_results/{save_name}',
        gui=True,
        gui_name=f'Save {save_name.capitalize()}',
        gui_group=f'Save CPACS external results',
    )

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
