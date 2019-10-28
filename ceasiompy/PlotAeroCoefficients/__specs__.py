#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, AIRCRAFT_XPATH

cpacs_inout = CPACSInOut()

#===== Input =====

cpacs_inout.add_input(
    var_name='x',
    default_value=None,
    unit='1',
    descr='Fuselage scaling on x axis',
    xpath=AIRCRAFT_XPATH + '/model/fuselages/fuselage/transformation   \
                                /scaling/x',
)

cpacs_inout.add_input(
    var_name='y',
    default_value=None,
    unit='1',
    descr='Fuselage scaling on x axis',
    xpath=AIRCRAFT_XPATH + '/model/fuselages/fuselage/transformation   \
                                /scaling/y',
)

cpacs_inout.add_input(
    var_name='z',
    default_value=None,
    unit='1',
    descr='Fuselage scaling on x axis',
    xpath=AIRCRAFT_XPATH + '/model/fuselages/fuselage/transformation   \
                                /scaling/z',
)

# ===== Output =====

# cpacs_inout.add_output(
#         var_name='output',
#         default_value=None,
#         unit='1',
#         descr='Description of the output',
#         xpath=CEASIOM_XPATH + '/...',
#         )
