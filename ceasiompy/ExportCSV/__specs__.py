from pathlib import Path
from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import EXPORT_XPATH

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working of not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "AeroCoefficients")


# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = False

# ----- Input -----

cpacs_inout.add_input(
    var_name="",
    var_type=list,
    default_value=None,
    descr="List of aeroMap to plot",
    xpath=EXPORT_XPATH + "/aeroMapToExport",
    gui=True,
    gui_name="__AEROMAP_CHECHBOX",
    gui_group="Aeromap settings",
)

# ----- Output -----
