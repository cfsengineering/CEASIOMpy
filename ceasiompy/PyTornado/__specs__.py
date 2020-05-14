#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH

# ===== RCE integration =====

RCE = {
    "name": "PyTornado",
    "description": "Wrapper module for PyTornado",
    "exec": "pwd\npython runpytornado.py",
    "author": "Aaron Dettmann",
    "email": "dettmann@kth.se",
}

REFS_XPATH = AIRCRAFT_XPATH + '/model/reference'
WING_XPATH = AIRCRAFT_XPATH + '/model/wings'
XPATH_PYTORNADO = '/cpacs/toolspecific/pytornado'

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

#===== Input =====

cpacs_inout.add_input(
    var_name='',
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to evaluate",
    xpath=XPATH_PYTORNADO + '/aeroMapUID',
    gui=True,
    gui_name='__AEROMAP_SELECTION',
    gui_group=None,
)

cpacs_inout.add_input(
    var_name='delete_old_wkdirs',
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Delete old PyTornado working directories (if existent)",
    xpath=XPATH_PYTORNADO + '/deleteOldWKDIRs',
    gui=False,
    gui_name='Delete',
    gui_group='Delete old working directories',
)


# ----- Discretisation -----
# TO BE IMPROVED IN NEW PYTORNADO VERSION
cpacs_inout.add_input(
    var_name='',
    var_type=int,
    default_value=20,
    unit=None,
    descr="The number of chordwise VLM panels",
    xpath=XPATH_PYTORNADO + '/vlm_autopanels_c',
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
    xpath=XPATH_PYTORNADO + '/vlm_autopanels_s',
    gui=True,
    gui_name='Number of spanwise panels',
    gui_group='Dicretisation',
)

# ----- Plots -----
for plot_name in ['lattice', 'geometry', 'results', 'matrix_downwash']:
    for action in ['save', 'show']:
        cpacs_inout.add_input(
            var_name='',
            var_type=bool,
            default_value=False,
            unit=None,
            descr=f"{action.capitalize()} a {plot_name.replace('_', ' ')} plot (program will pause to show)",
            xpath=XPATH_PYTORNADO + f'/plot/{plot_name}/{action}',
            gui=True,
            gui_name=f'{action.capitalize()} plot',
            gui_group=f"{plot_name.capitalize().replace('_', ' ')} plot",
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
        xpath=XPATH_PYTORNADO + f'/save_results/{save_name}',
        gui=True,
        gui_name=f'Save {save_name.capitalize()}',
        gui_group=f'Save CPACS external results',
    )

cpacs_inout.add_input(
    var_name='check_extract_loads',
    var_type=bool,
    default_value=False,
    unit='1',
    descr='Option to extract loads from results',
    xpath=XPATH_PYTORNADO + '/save_results/extractLoads',
    gui=True,
    gui_name='Extract loads',
    gui_group=f'Save CPACS external results',
)

cpacs_inout.add_input(
    var_name='x_CG',
    default_value=None,
    unit='m',
    descr='Centre of gravity (x-coordinate)',
    xpath=REFS_XPATH + '/point/x'
)

cpacs_inout.add_input(
    var_name='y_CG',
    default_value=None,
    unit='m',
    descr='Centre of gravity (y-coordinate)',
    xpath=REFS_XPATH + '/point/x'
)

cpacs_inout.add_input(
    var_name='z_CG',
    default_value=None,
    unit='m',
    descr='Centre of gravity (z-coordinate)',
    xpath=REFS_XPATH + '/point/x'
)

cpacs_inout.add_input(
    var_name='area',
    default_value=None,
    unit='m^2',
    descr='Reference area for force and moment coefficients',
    xpath=REFS_XPATH + '/area'
)

cpacs_inout.add_input(
    var_name='length',
    default_value=None,
    unit='m',
    descr='Reference length for force and moment coefficients',
    xpath=REFS_XPATH + '/length'
)

cpacs_inout.add_input(
    var_name='wing',
    default_value=None,
    unit='-',
    descr='Aircraft lifting surface',
    xpath=WING_XPATH,
)


# ----- Output -----

cpacs_inout.add_output(
    var_name='aeromap_PyTornado',  # name to change...
    # var_type=CPACS_aeroMap, # no type pour output, would it be useful?
    default_value=None,
    unit='-',
    descr='aeroMap with aero coefficients calculated by PyTornado',
    xpath='/cpacs/vehicles/aircraft/model/analyses/aeroPerformance/aeroMap[i]/aeroPerformanceMap',
)
