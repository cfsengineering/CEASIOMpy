from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import (
    CEASIOMPY_XPATH,
    AVL_PLOT_XPATH,
    AVL_VORTEX_DISTR_XPATH,
    AVL_FUSELAGE_XPATH,
    AVL_AEROMAP_UID_XPATH,
    AEROPERFORMANCE_XPATH,
)
from pathlib import Path

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True  # Because it is just an example not a real module

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "PyAVL")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

# * In the following example we add three (!) new entries to 'cpacs_inout'
# * Try to use (readable) loops instead of copy-pasting three almost same entries :)
cpacs_inout.add_input(
    var_name="aeromap_uid",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to calculate",
    xpath=AVL_AEROMAP_UID_XPATH,
    gui=True,
    gui_name="__AEROMAP_SELECTION",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="integrate_fuselage",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Select to integrate the fuselage in the AVL model",
    xpath=AVL_FUSELAGE_XPATH,
    gui=True,
    gui_name="Integrate fuselage",
    gui_group="Fuselage",
)

cpacs_inout.add_input(
    var_name="panel_distribution",
    var_type=list,
    default_value=["cosine", "sine", "equal"],
    unit=None,
    descr=("Select the type of distribution"),
    xpath=AVL_VORTEX_DISTR_XPATH + "/Distribution",
    gui=True,
    gui_name="Choice of distribution",
    gui_group="Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="chordwise_vort",
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
    var_name="spanwise_vort",
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
    var_name="save_plots",
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

cpacs_inout.add_output(
    var_name="aeromap_avl",  # name to change...
    # var_type=CPACS_aeroMap, # no type pour output, would it be useful?
    default_value=None,
    unit="-",
    descr="aeroMap with aero coefficients calculated by AVL",
    xpath=AEROPERFORMANCE_XPATH + "/aeroMap/aeroPerformanceMap",
)
