<<<<<<< HEAD
"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CLCalculator.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.CLCalculator import include_gui

=======
from pathlib import Path
from ceasiompy.utils.moduleinterfaces import CPACSInOut
>>>>>>> origin/main
from ceasiompy.utils.commonxpath import (
    REF_XPATH,
    CLCALC_XPATH,
    SU2_FIXED_CL_XPATH,
    SU2_TARGET_CL_XPATH,
)

<<<<<<< HEAD
# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================
=======
# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "CLCalculator")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ===== Input =====
>>>>>>> origin/main

cpacs_inout.add_input(
    var_name="mass_type",
    var_type=list,
<<<<<<< HEAD
    default_value=["mTOM", "mZFM", "Custom", "%% fuel mass"],
    unit=None,
    descr="Type of mass to use for CL calculation",
    xpath=CLCALC_XPATH + "/massType",
    gui=include_gui,
=======
    default_value=["mTOM", "mZFM", "Custom", "% fuel mass"],
    unit=None,
    descr="Type of mass to use for CL calculation",
    xpath=CLCALC_XPATH + "/massType",
    gui=True,
>>>>>>> origin/main
    gui_name="Type",
    gui_group="Mass",
)

cpacs_inout.add_input(
    var_name="custom_mass",
    var_type=float,
    default_value=0.0,
    unit="kg",
    descr="Mass value if Custom is selected",
    xpath=CLCALC_XPATH + "/customMass",
<<<<<<< HEAD
    gui=include_gui,
=======
    gui=True,
>>>>>>> origin/main
    gui_name="Custom mass",
    gui_group="Mass",
)

cpacs_inout.add_input(
    var_name="percent_fuel_mass",
    var_type=float,
    default_value=100,
<<<<<<< HEAD
    unit=None,
    descr="Percentage of fuel mass between mTOM and mZFM, if % fuel mass is selected",
    xpath=CLCALC_XPATH + "/percentFuelMass",
    gui=include_gui,
=======
    unit="-",
    descr="Percentage of fuel mass between mTOM and mZFM, if % fuel mass is selected",
    xpath=CLCALC_XPATH + "/percentFuelMass",
    gui=True,
>>>>>>> origin/main
    gui_name="Percent fuel mass",
    gui_group="Mass",
)

cpacs_inout.add_input(
    var_name="cruise_mach",
    var_type=float,
    default_value=0.78,
<<<<<<< HEAD
    unit=None,
    descr="Aircraft cruise Mach number",
    xpath=CLCALC_XPATH + "/cruiseMach",
    gui=include_gui,
=======
    unit="1",
    descr="Aircraft cruise Mach number",
    xpath=CLCALC_XPATH + "/cruiseMach",
    gui=True,
>>>>>>> origin/main
    gui_name="Mach",
    gui_group="Cruise",
)

cpacs_inout.add_input(
    var_name="cruise_alt",
    var_type=float,
    default_value=12000.0,
<<<<<<< HEAD
    unit="[m]",
    descr="Aircraft cruise altitude",
    xpath=CLCALC_XPATH + "/cruiseAltitude",
    gui=include_gui,
=======
    unit="m",
    descr="Aircraft cruise altitude",
    xpath=CLCALC_XPATH + "/cruiseAltitude",
    gui=True,
>>>>>>> origin/main
    gui_name="Altitude",
    gui_group="Cruise",
)

cpacs_inout.add_input(
    var_name="load_fact",
    var_type=float,
    default_value=1.05,
<<<<<<< HEAD
    unit=None,
    descr="Aircraft cruise altitude",
    xpath=CLCALC_XPATH + "/loadFactor",
    gui=include_gui,
=======
    unit="1",
    descr="Aircraft cruise altitude",
    xpath=CLCALC_XPATH + "/loadFactor",
    gui=True,
>>>>>>> origin/main
    gui_name="Load Factor",
    gui_group="Cruise",
)

cpacs_inout.add_input(
    var_name="ref_area",
    var_type=float,
    default_value=None,
<<<<<<< HEAD
    unit="[m^2]",
=======
    unit="m^2",
>>>>>>> origin/main
    descr="Aircraft reference area",
    xpath=REF_XPATH + "/area",
    gui=False,
    gui_name=None,
    gui_group=None,
)

<<<<<<< HEAD
# ==============================================================================
#   GUI OUTPUTS
# ==============================================================================
=======

# ===== Output =====
>>>>>>> origin/main

cpacs_inout.add_output(
    var_name="target_cl",
    default_value=None,
<<<<<<< HEAD
    unit=None,
=======
    unit="1",
>>>>>>> origin/main
    descr="Value of CL to achieve to have a level flight with the given conditions",
    xpath=SU2_TARGET_CL_XPATH,
)

cpacs_inout.add_output(
    var_name="fixed_cl",
    default_value=None,
<<<<<<< HEAD
    unit=None,
    descr="FIXED_CL_MODE parameter for SU2",
    xpath=SU2_FIXED_CL_XPATH,
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
=======
    unit="-",
    descr="FIXED_CL_MODE parameter for SU2",
    xpath=SU2_FIXED_CL_XPATH,
)
>>>>>>> origin/main
