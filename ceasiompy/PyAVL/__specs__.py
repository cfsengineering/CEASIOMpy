from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import CEASIOMPY_XPATH, AVL_PLOT_XPATH, AVL_VORTEX_DISTR_XPATH
from pathlib import Path

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True  # Because it is just an example not a real module

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

include_gui = True

RESULTS_DIR = Path("Results", "PyAVL")

# ----- Input -----

# * In the following example we add three (!) new entries to 'cpacs_inout'
# * Try to use (readable) loops instead of copy-pasting three almost same entries :)
cpacs_inout.add_input(
    var_name="aeromap_uid",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to calculate",
    xpath="/cpacs/toolspecific/CEASIOMpy/aerodynamics/avl/aeroMapUID",
    gui=True,
    gui_name="__AEROMAP_SELECTION",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="other_var",
    var_type=float,
    default_value=1.0,
    unit=None,
    descr="Must be in the range [-3.0 ; +3.0]",
    xpath=AVL_VORTEX_DISTR_XPATH + "/Distribution",
    gui=True,
    gui_name="Choice of distribution",
    gui_group="Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="other_var",
    var_type=int,
    default_value=20,
    unit=None,
    descr="Select the number of chordwise vortices",
    xpath=AVL_VORTEX_DISTR_XPATH + "/Nchordwise",
    gui=True,
    gui_name="Number of chordwise vortices",
    gui_group="Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="other_var",
    var_type=int,
    default_value=50,
    unit=None,
    descr="Select the number of spanwise vortices",
    xpath=AVL_VORTEX_DISTR_XPATH + "/Nspanwise",
    gui=True,
    gui_name="Number of spanwise vortices",
    gui_group="Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="other_var",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Select to save geometry and results plots",
    xpath=AVL_PLOT_XPATH,
    gui=True,
    gui_name="Save plots",
    gui_group="Plots",
)

# ----- Output -----

cpacs_inout.add_output(
    var_name="output",
    default_value=None,
    unit="1",
    descr="Description of the output",
    xpath=CEASIOMPY_XPATH + "/test/myOutput",
)
