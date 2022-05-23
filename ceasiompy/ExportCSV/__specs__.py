from pathlib import Path
from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import EXPORT_XPATH


# ===== Results directory path =====

RESULTS_DIR = Path("Results", "Aeromaps")


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
    # gui_group='Multipe aeromap'
)

# ----- Output -----
