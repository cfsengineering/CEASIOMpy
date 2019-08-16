#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH, CEASIOM_XPATH

cpacs_inout = CPACSInOut()

#===== Input =====

cpacs_inout.add_input(
    var_name='ref_len',
    default_value=None,
    unit='m',
    descr='Reference length of the aircraft',
    cpacs_path=AIRCRAFT_XPATH + '/model/reference/length',
)

cpacs_inout.add_input(
    var_name='ref_area',
    default_value=None,
    unit='m^2',
    descr='Reference area of the aircraft',
    cpacs_path=AIRCRAFT_XPATH + '/model/reference/area',
)

cpacs_inout.add_input(
    var_name='cruise_alt',
    default_value=12000,
    unit='m',
    descr='Aircraft cruise altitude',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/cruise_alt',
)

cpacs_inout.add_input(
    var_name='cruise_mach',
    default_value=0.78,
    unit='1',
    descr='Aircraft cruise Mach number',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/cruise_mach',
)

cpacs_inout.add_input(
    var_name='target_cl',
    default_value='1.0',
    unit='1',
    descr='Value of CL to achieve to have a level flight with the given conditions',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/targetCL',
)

cpacs_inout.add_input(
    var_name='fixed_cl',
    default_value='NO',
    unit='-',
    descr='FIXED_CL_MODE parameter for SU2',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/fixedCL',
)

cpacs_inout.add_input(
    var_name='max_iter',
    default_value='10',
    unit='-',
    descr='Maximum number of iterations performed by SU2',
    cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/settings/maxIter',
)



# ===== Output =====

# cpacs_inout.add_output(
#     var_name='output',
#     default_value=None,
#     unit='1',
#     descr='Description of the output',
#     cpacs_path=CEASIOM_XPATH + '/...',
# )
