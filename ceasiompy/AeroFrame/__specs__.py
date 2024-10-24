from pathlib import Path

from ceasiompy.utils.commonxpath import (
    AEROFRAME_SETTINGS,
    AEROPERFORMANCE_XPATH,
    AVL_AEROMAP_UID_XPATH,
    AVL_PLOT_XPATH,
    AVL_VORTEX_DISTR_XPATH,
    CEASIOMPY_XPATH,
    FRAMAT_MATERIAL_XPATH,
    FRAMAT_MESH_XPATH,
    FRAMAT_SECTION_XPATH,
)
from ceasiompy.utils.moduleinterfaces import CPACSInOut

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

RESULTS_DIR = Path("Results", "AeroFrame")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

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
    var_name="panel_distribution",
    var_type=list,
    default_value=["equal", "cosine", "sine"],
    unit=None,
    descr=("Select the type of distribution"),
    xpath=AVL_VORTEX_DISTR_XPATH + "/Distribution",
    gui=True,
    gui_name="Choice of distribution",
    gui_group="AVL: Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="chordwise_vort",
    var_type=int,
    default_value=8,
    unit=None,
    descr="Select the number of chordwise vortices",
    xpath=AVL_VORTEX_DISTR_XPATH + "/Nchordwise",
    gui=True,
    gui_name="Number of chordwise vortices",
    gui_group="AVL: Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="spanwise_vort",
    var_type=int,
    default_value=30,
    unit=None,
    descr="Select the number of spanwise vortices",
    xpath=AVL_VORTEX_DISTR_XPATH + "/Nspanwise",
    gui=True,
    gui_name="Number of spanwise vortices",
    gui_group="AVL: Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="save_plots",
    var_type=bool,
    default_value=True,
    unit=None,
    descr="Select to save geometry and results plots",
    xpath=AVL_PLOT_XPATH,
    gui=True,
    gui_name="Save AVL plots",
    gui_group="Plots",
)

cpacs_inout.add_input(
    var_name="N_beam",
    var_type=int,
    default_value=15,
    unit=None,
    descr="Enter number of nodes for the beam mesh.",
    xpath=FRAMAT_MESH_XPATH + "/NumberNodes",
    gui=True,
    gui_name="Number of beam nodes",
    gui_group="FramAT: Mesh properties",
)

cpacs_inout.add_input(
    var_name="young_modulus",
    var_type=float,
    default_value=70,
    unit=None,
    descr="Enter the Young modulus of the wing material in GPa.",
    xpath=FRAMAT_MATERIAL_XPATH + "/YoungModulus",
    gui=True,
    gui_name="Young modulus [GPa]",
    gui_group="FramAT: Material properties",
)

cpacs_inout.add_input(
    var_name="shear_modulus",
    var_type=float,
    default_value=26,
    unit=None,
    descr="Enter the shear modulus of the wing material in GPa.",
    xpath=FRAMAT_MATERIAL_XPATH + "/ShearModulus",
    gui=True,
    gui_name="Shear modulus [GPa]",
    gui_group="FramAT: Material properties",
)

cpacs_inout.add_input(
    var_name="material_density",
    var_type=float,
    default_value=1960,
    unit=None,
    descr="Enter the density of the wing material in kg/m³.",
    xpath=FRAMAT_MATERIAL_XPATH + "/Density",
    gui=True,
    gui_name="Material density [kg/m³]",
    gui_group="FramAT: Material properties",
)

cpacs_inout.add_input(
    var_name="cross_section_area",
    var_type=float,
    default_value=-1,
    unit=None,
    descr="Enter the area of the cross-section in m².",
    xpath=FRAMAT_SECTION_XPATH + "/Area",
    gui=True,
    gui_name="Cross-section area [m²]",
    gui_group="FramAT: Cross-section properties",
)

cpacs_inout.add_input(
    var_name="cross_section_Ix",
    var_type=float,
    default_value=-1,
    unit=None,
    descr="Enter the second moment of area of the cross-section \
            about the horizontal axis, in m⁴.",
    xpath=FRAMAT_SECTION_XPATH + "/Ix",
    gui=True,
    gui_name="Second moment of area Ix [m⁴]",
    gui_group="FramAT: Cross-section properties",
)

cpacs_inout.add_input(
    var_name="cross_section_Iy",
    var_type=float,
    default_value=-1,
    unit=None,
    descr="Enter the second moment of area of the cross-section \
            about the vertical axis, in m⁴",
    xpath=FRAMAT_SECTION_XPATH + "/Iy",
    gui=True,
    gui_name="Second moment of area Iy [m⁴]",
    gui_group="FramAT: Cross-section properties",
)

cpacs_inout.add_input(
    var_name="n_iter_max",
    var_type=int,
    default_value=8,
    unit=None,
    descr="Enter the maximum number of iterations of the aeroelastic-loop.",
    xpath=AEROFRAME_SETTINGS + "/MaxNumberIterations",
    gui=True,
    gui_name="Maximum number of iterations",
    gui_group="AeroFrame: Convergence settings",
)

cpacs_inout.add_input(
    var_name="tolerance",
    var_type=float,
    default_value=1e-3,
    unit=None,
    descr="Enter the tolerance for convergence of the wing deformation.",
    xpath=AEROFRAME_SETTINGS + "/Tolerance",
    gui=True,
    gui_name="Tolerance",
    gui_group="AeroFrame: Convergence settings",
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
