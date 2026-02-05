"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of ThermoData.
"""

# Imports

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.su2run import (
    SU2_FIXED_CL_XPATH,
    SU2_TARGET_CL_XPATH,
)
from ceasiompy.utils.commonxpaths import (
    RANGE_XPATH,
    ENGINE_TYPE_XPATH,
)

# Variable

cpacs_inout = CPACSInOut()

cpacs_inout.add_input(
    var_name="net_force",
    var_type=float,
    default_value=2000,
    unit="N",
    descr="Engine net force",
    xpath=RANGE_XPATH + "/NetForce",
    gui=True,
    gui_name="NetForce",
    gui_group="Cruise",
)

cpacs_inout.add_input(
    var_name="engine type",
    var_type=list,
    default_value=[0, 1],
    unit=None,
    descr="0: TBJ, 1: TBF ",
    xpath=ENGINE_TYPE_XPATH,
    gui=True,
    gui_name="0 for Turbojet 1 for Turbofan",
    gui_group="User inputs",
)
