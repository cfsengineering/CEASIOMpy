from pathlib import Path

from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import (
    REF_XPATH,
    WINGS_XPATH,
    PYTORNADO_XPATH,
    AEROPERFORMANCE_XPATH,
)

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "PyTornado")


# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ===== Input =====

cpacs_inout.add_input(
    var_name="",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to evaluate",
    xpath=PYTORNADO_XPATH + "/aeroMapUID",
    gui=True,
    gui_name="__AEROMAP_SELECTION",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="delete_old_wkdirs",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Delete old PyTornado working directories (if existent)",
    xpath=PYTORNADO_XPATH + "/deleteOldWKDIRs",
    gui=False,
    gui_name="Delete",
    gui_group="Delete old working directories",
)


# ----- Discretisation -----
# TO BE IMPROVED IN NEW PYTORNADO VERSION
cpacs_inout.add_input(
    var_name="",
    var_type=int,
    default_value=20,
    unit=None,
    descr="The number of chordwise VLM panels",
    xpath=PYTORNADO_XPATH + "/vlm_autopanels_c",
    gui=True,
    gui_name="Number of chordwise panels",
    gui_group="Dicretisation",
)

cpacs_inout.add_input(
    var_name="",
    var_type=int,
    default_value=5,
    unit=None,
    descr="The number of spanwise VLM panels",
    xpath=PYTORNADO_XPATH + "/vlm_autopanels_s",
    gui=True,
    gui_name="Number of spanwise panels",
    gui_group="Dicretisation",
)

cpacs_inout.add_input(
    var_name="",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Save plot of the aircraft geometry",
    xpath=PYTORNADO_XPATH + "/plot/geometry/save",
    gui=True,
    gui_name="Save geometry plot",
    gui_group="Plots",
)

cpacs_inout.add_input(
    var_name="",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Save plot of the results (pressure coefficient)",
    xpath=PYTORNADO_XPATH + "/plot/results/save",
    gui=True,
    gui_name="Save results plot",
    gui_group="Plots",
)

cpacs_inout.add_input(
    var_name="",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Save plot of the lattices",
    xpath=PYTORNADO_XPATH + "/plot/lattice/save",
    gui=True,
    gui_name="Save lattices plot",
    gui_group="Plots",
)

cpacs_inout.add_input(
    var_name="",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Save the downwash matrix plot",
    xpath=PYTORNADO_XPATH + "/plot/matrix_downwash/save",
    gui=True,
    gui_name="Save matrix_downwash plot",
    gui_group="Plots",
)

cpacs_inout.add_input(
    var_name="",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Save PyTornado global results as a json file",
    xpath=PYTORNADO_XPATH + "/save_results/global",
    gui=True,
    gui_name="Save global results",
    gui_group="Save CPACS external results",
)

cpacs_inout.add_input(
    var_name="",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Save PyTornado panelwise results as a dat file",
    xpath=PYTORNADO_XPATH + "/save_results/panelwise",
    gui=True,
    gui_name="Save panelwise results",
    gui_group="Save CPACS external results",
)

cpacs_inout.add_input(
    var_name="check_extract_loads",
    var_type=bool,
    default_value=False,
    unit="1",
    descr="Option to extract loads from results (only last calculated case)",
    xpath=PYTORNADO_XPATH + "/save_results/extractLoads",
    gui=True,
    gui_name="Extract loads",
    gui_group="Save CPACS external results",
)

cpacs_inout.add_input(
    var_name="x_CG",
    default_value=None,
    unit="m",
    descr="Centre of gravity (x-coordinate)",
    xpath=REF_XPATH + "/point/x",
)

cpacs_inout.add_input(
    var_name="y_CG",
    default_value=None,
    unit="m",
    descr="Centre of gravity (y-coordinate)",
    xpath=REF_XPATH + "/point/y",
)

cpacs_inout.add_input(
    var_name="z_CG",
    default_value=None,
    unit="m",
    descr="Centre of gravity (z-coordinate)",
    xpath=REF_XPATH + "/point/z",
)

cpacs_inout.add_input(
    var_name="area",
    default_value=None,
    unit="m^2",
    descr="Reference area for force and moment coefficients",
    xpath=REF_XPATH + "/area",
)

cpacs_inout.add_input(
    var_name="length",
    default_value=None,
    unit="m",
    descr="Reference length for force and moment coefficients",
    xpath=REF_XPATH + "/length",
)

cpacs_inout.add_input(
    var_name="wing",
    default_value=None,
    unit="-",
    descr="Aircraft lifting surface",
    xpath=WINGS_XPATH,
)


# ----- Output -----

cpacs_inout.add_output(
    var_name="aeromap_PyTornado",  # name to change...
    # var_type=CPACS_aeroMap, # no type for output, would it be useful?
    default_value=None,
    unit="-",
    descr="aeroMap with aero coefficients calculated by PyTornado",
    xpath=AEROPERFORMANCE_XPATH + "/aeroMap/aeroPerformanceMap",
)
