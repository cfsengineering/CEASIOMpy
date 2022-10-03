from pathlib import Path
from ceasiompy.utils.moduleinterfaces import CPACSInOut

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working of not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "CPACSCreator")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

# No inputs value for this modules

# ----- Output -----

# No outputs value for this modules
