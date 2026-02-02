"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of Aeroframe.
"""

# Imports

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.PyAVL import (
    AVL_DISTR_XPATH,
    AVL_NSPANWISE_XPATH,
    AVL_NCHORDWISE_XPATH,
)
from ceasiompy.AeroFrame import (
    FRAMAT_IX_XPATH,
    FRAMAT_IY_XPATH,
    FRAMAT_AREA_XPATH,
    FRAMAT_DENSITY_XPATH,
    FRAMAT_NB_NODES_XPATH,
    FRAMAT_SHEARMODULUS_XPATH,
    FRAMAT_YOUNGMODULUS_XPATH,
    AEROFRAME_TOLERANCE_XPATH,
    AEROFRAME_MAXNB_ITERATIONS_XPATH,
)

# Variable

cpacs_inout = CPACSInOut()

# ==============================================================================
#   CALL
# ==============================================================================

cpacs_inout.add_input(
    var_name="panel_distribution",
    var_type=list,
    default_value=["equal", "cosine", "sine"],
    unit=None,
    descr=("Select the type of distribution"),
    xpath=AVL_DISTR_XPATH,
    gui=True,
    gui_name="Choice of distribution",
    gui_group="AVL: Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="chordwise_vort",
    var_type=int,
    default_value=20,
    unit=None,
    descr="Select the number of chordwise vortices",
    xpath=AVL_NCHORDWISE_XPATH,
    gui=True,
    gui_name="Number of chordwise vortices",
    gui_group="AVL: Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="spanwise_vort",
    var_type=int,
    default_value=50,
    unit=None,
    descr="Select the number of spanwise vortices",
    xpath=AVL_NSPANWISE_XPATH,
    gui=True,
    gui_name="Number of spanwise vortices",
    gui_group="AVL: Vortex Lattice Spacing Distributions",
)

cpacs_inout.add_input(
    var_name="N_beam",
    var_type=int,
    default_value=15,
    unit=None,
    descr="Enter number of nodes for the beam mesh.",
    xpath=FRAMAT_NB_NODES_XPATH,
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
    xpath=FRAMAT_YOUNGMODULUS_XPATH,
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
    xpath=FRAMAT_SHEARMODULUS_XPATH,
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
    xpath=FRAMAT_DENSITY_XPATH,
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
    xpath=FRAMAT_AREA_XPATH,
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
    xpath=FRAMAT_IX_XPATH,
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
    xpath=FRAMAT_IY_XPATH,
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
    xpath=AEROFRAME_MAXNB_ITERATIONS_XPATH,
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
    xpath=AEROFRAME_TOLERANCE_XPATH,
    gui=True,
    gui_name="Tolerance",
    gui_group="AeroFrame: Convergence settings",
)
