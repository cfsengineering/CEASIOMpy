#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, CEASIOM_XPATH, AIRCRAFT_XPATH

cpacs_inout = CPACSInOut()

# ===== Input =====

cpacs_inout.add_input(
    var_name='mtom',
    default_value=None,
    unit='kg',
    descr='MTOM (maybe another mass shoud be used, more representative for cruise mass?)',
    cpacs_path=AIRCRAFT_XPATH + '/model/analyses/massBreakdown/designMasses/mTOM/mass',
)

cpacs_inout.add_input(
    var_name='cruise_mach',
    default_value=0.78,
    unit='-',
    descr='Aircraft cruise Mach number',
    cpacs_path=CEASIOM_XPATH + '/ranges/cruiseMach',
)

cpacs_inout.add_input(
    var_name='cruise_alt',
    default_value=12000,
    unit='m',
    descr='Aircraft cruise altitude',
    cpacs_path=CEASIOM_XPATH + '/ranges/cruiseAltitude',
)

cpacs_inout.add_input(
    var_name='load_fact',
    default_value=1.05,
    unit='1',
    descr='Load Factor',
    cpacs_path=CEASIOM_XPATH + '/ranges/loadFactor',
)

cpacs_inout.add_input(
    var_name='ref_area',
    default_value=None,
    unit='m^2',
    descr='Reference area',
    cpacs_path=AIRCRAFT_XPATH + '/model/reference/area',
)

# ===== Output =====

# cpacs_inout.add_output(
#         var_name='TODO',
#         default_value='TODO',
#         unit='TODO',
#         descr='TODO',
#         cpacs_path='TODO',
#         )
