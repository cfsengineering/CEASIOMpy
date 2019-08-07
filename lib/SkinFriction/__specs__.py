#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib.utils.moduleinterfaces import CPACSInOut

cpacs_inout = CPACSInOut()

# ----- Input -----

# cpacs_inout.add_input(
#         descr='Wing area of the main (largest) wing',
#         cpacs_path='/cpacs/toolspecific/CEASIOMpy/geometry/analysis/wingArea',
#         default_value=None,
#         unit='m^2',
#         var_name='wing_area'
#         )

# cpacs_inout.add_input(
#         descr='Wing span of the main (largest) wing',
#         cpacs_path='/cpacs/toolspecific/CEASIOMpy/geometry/analysis/wingSpan',
#         default_value=None,
#         unit='m',
#         var_name='wing_span'
#         )

cpacs_inout.add_input(
        descr='Wetted area of the aircraft (calculated by SU2)',
        cpacs_path='/cpacs/toolspecific/CEASIOMpy/geometry/analysis/wettedArea',
        default_value=None,
        unit='m^2',
        var_name='wetted_area'
        )

cpacs_inout.add_input(
        descr='Aircraft cruise speed',
        cpacs_path='/cpacs/toolspecific/CEASIOMpy/ranges/cruiseSpeed',
        default_value=272,
        unit='m/s',
        var_name='cruise_speed'
        )

cpacs_inout.add_input(
        descr='Aircraft cruise altitude',
        cpacs_path='/cpacs/toolspecific/CEASIOMpy/ranges/cruiseAltitude',
        default_value=12000,
        unit='m',
        var_name='cruise_alt'
        )

# ----- Output -----

cpacs_inout.add_output(
        descr='Skin friction drag coefficient',
        cpacs_path='/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2/cd0',
        default_value=None,
        unit='1',
        var_name='cd0'
        )
