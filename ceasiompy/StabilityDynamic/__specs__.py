#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, CEASIOM_XPATH

STABILITY_DYNAMIC_XPATH =  '/cpacs/toolspecific/CEASIOMpy/stability/dynamic'


# ===== RCE integration =====

RCE = {
    "name": "StabilityDynamic",
    "description": "Determine if a vehicle isdynamically stable or not  ",
    "exec": "pwd\npython dynamicstability.py",
    "author": "Loïc Verdier",
    "email": "loic.verdier@epfl.ch",
}


# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()


# ===== Input =====

cpacs_inout.add_input(
    var_name='',
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to evaluate",
    xpath=STABILITY_DYNAMIC_XPATH + '/aeroMapUid',
    gui=True,
    gui_name='__AEROMAP_SELECTION',
    gui_group='Inputs',
)

cpacs_inout.add_input(
    var_name='MassConfig',
    var_type=list,
    default_value= ['mMLM', 'mMRM', 'mTOM', 'mZFM'],
    unit='[unit]',
    xpath='/cpacs/toolspecific/CEASIOMpy/stability/dynamic/MassConfiguration',
    gui=True,
    gui_name='Mass selection: ',
    gui_group='Inputs'
)

cpacs_inout.add_input(
    var_name='show_plot',
    var_type=bool,
    default_value=False,
    unit=None,
    descr='Show all plot during the stability analysis',
    xpath=STABILITY_DYNAMIC_XPATH + '/showPlots',
    gui=True,
    gui_name='Show Stbility plots',
    gui_group='Output',
)

cpacs_inout.add_input(
    var_name='save_plot',
    var_type=bool,
    default_value=False,
    unit=None,
    descr='Save all plot during the stability analysis',
    xpath=STABILITY_DYNAMIC_XPATH + '/savePlots',
    gui=True,
    gui_name='Save Stbility plots',
    gui_group='Output',
)

# ===== Output =====

cpacs_inout.add_output(
    var_name='longitudinaly_stable',
    default_value=None,
    unit='1',
    descr='Is the aircraft longitudinaly stable',
    xpath=STABILITY_DYNAMIC_XPATH+'/results/longitudinalDynamicStable',
)

cpacs_inout.add_output(
    var_name='dirrectionaly_stable',
    default_value=None,
    unit='1',
    descr='Is the aircraft dirrectionaly stable',
    xpath=STABILITY_DYNAMIC_XPATH+'/results/directionnalDynamicStable',
)


cpacs_inout.add_output(
    var_name='trim_alt_longi_list',
    default_value=None,
    unit='m',
    descr='corresponding trim altitude at which the airraft have been noticed to be longitudinaly stable',
    xpath=STABILITY_DYNAMIC_XPATH+'/trimconditions/longitudinal/altitude',
)

cpacs_inout.add_output(
    var_name='trim_mach_longi_list',
    default_value=None,
    unit='-',
    descr='corresponding trim mach at which the airraft have been noticed to be longitudinaly stable',
    xpath=STABILITY_DYNAMIC_XPATH+'/trimconditions/longitudinal/machNumber',
)

cpacs_inout.add_output(
    var_name='trim_aoa_longi_list',
    default_value=None,
    unit='deg',
    descr='corresponding trim AOA at which the airraft have been noticed to be longitudinaly stable',
    xpath=STABILITY_DYNAMIC_XPATH+'/trimconditions/longitudinal/angleOfAttack',
)

cpacs_inout.add_output(
    var_name='trim_aos_longi_list',
    default_value=None,
    unit='deg',
    descr='corresponding trim AOS at which the airraft have been noticed to be longitudinaly stable',
    xpath=STABILITY_DYNAMIC_XPATH+'/trimconditions/longitudinal/angleOfSideslip',
)

cpacs_inout.add_output(
    var_name='trim_alt_direc_list',
    default_value=None,
    unit='m',
    descr='corresponding trim altitude at which the airraft have been noticed to be directionaly stable',
    xpath=STABILITY_DYNAMIC_XPATH+'/trimconditions/directional/altitude',
)

cpacs_inout.add_output(
    var_name='trim_mach_direc_list',
    default_value=None,
    unit='-',
    descr='corresponding trim mach at which the airraft have been noticed to be directionaly stable',
    xpath=STABILITY_DYNAMIC_XPATH+'/trimconditions/directional/machNumber',
)

cpacs_inout.add_output(
    var_name='trim_aoa_direc_list',
    default_value=None,
    unit='deg',
    descr='corresponding trim AOA at which the airraft have been noticed to be directionaly stable',
    xpath=STABILITY_DYNAMIC_XPATH+'/trimconditions/directional/angleOfAttack',
)

cpacs_inout.add_output(
    var_name='trim_aos_direc_list',
    default_value=None,
    unit='deg',
    descr='corresponding trim AOA at which the airraft have been noticed to be directionaly stable',
    xpath=STABILITY_DYNAMIC_XPATH+'/trimconditions/directional/angleOfSideslip',
)
