"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of DynamicStability.


| Author: Leon Deligny
| Creation: 25 March 2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.DynamicStability import include_gui
from ceasiompy.PyAVL import SOFTWARE_NAME as AVL_SOFTWARE
from ceasiompy.SU2Run import SOFTWARE_NAME as SU2_SOFTWARE
from ceasiompy.DynamicStability import SOFTWARE_NAME as SDSA_SOFTWARE

from ceasiompy.utils.commonxpath import (
    DYNAMICSTABILITY_NCHORDWISE_XPATH,
    DYNAMICSTABILITY_NSPANWISE_XPATH,
    DYNAMICSTABILITY_VISUALIZATION_XPATH,
    DYNAMICSTABILITY_CGRID_XPATH,
    DYNAMICSTABILITY_SOFTWARE_XPATH,
    DYNAMICSTABILITY_MACHLIST_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="dynamic_stability_software_data",
    var_type=list,
    default_value=[f"{AVL_SOFTWARE}", f"{SU2_SOFTWARE}"],
    unit=None,
    descr="Which data from ceasiompy.db to use.",
    xpath=DYNAMICSTABILITY_SOFTWARE_XPATH,
    gui=include_gui,
    gui_name="Use data from which software",
    gui_group="Software Settings",
)

cpacs_inout.add_input(
    var_name="mach_list",
    var_type="multiselect",
    default_value=[0.1],  # [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
    unit="mach",
    descr=f"List of mach numbers used in {SDSA_SOFTWARE}",
    xpath=DYNAMICSTABILITY_MACHLIST_XPATH,
    gui=include_gui,
    gui_name="Mach List",
    gui_group="Mach Settings",
)

cpacs_inout.add_input(
    var_name="chordwise_vort",
    var_type=int,
    default_value=12,
    unit=None,
    descr="Select the number of chordwise vortices",
    xpath=DYNAMICSTABILITY_NCHORDWISE_XPATH,
    gui=include_gui,
    gui_name="Number of chordwise vortices",
    gui_group="Chordwise Settings",
)

cpacs_inout.add_input(
    var_name="spanwise_vort",
    var_type=int,
    default_value=20,
    unit=None,
    descr="Select the number of spanwise vortices",
    xpath=DYNAMICSTABILITY_NSPANWISE_XPATH,
    gui=include_gui,
    gui_name="Number of spanwise vortices",
    gui_group="Spanwise Settings",
)

cpacs_inout.add_input(
    var_name="dlm_aerogrid_visualization",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Visualization of the aerogrid the DLM is going to use",
    xpath=DYNAMICSTABILITY_VISUALIZATION_XPATH,
    gui=include_gui,
    gui_name="aerogrid visualization",
    gui_group="Visualization",
)

cpacs_inout.add_input(
    var_name="c_grid",
    var_type=str,
    default_value="C:/Program Files/SDSA/Grid/test.inp",
    unit=None,
    descr="Select the cGrid path",
    xpath=DYNAMICSTABILITY_CGRID_XPATH,
    gui=include_gui,
    gui_name="cGrid path",
    gui_group="cGrid Setting",
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
