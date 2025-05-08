"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

GUI Interface of CPACS2GMSH.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

from pathlib import Path

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy import log
from ceasiompy.utils.commonxpaths import SU2MESH_XPATH
from ceasiompy.CPACS2GMSH import (
    INCLUDE_GUI,
    GMSH_OPEN_GUI_XPATH,
    GMSH_MESH_TYPE_XPATH,
    GMSH_CTRLSURF_ANGLE_XPATH,
    GMSH_SYMMETRY_XPATH,
    GMSH_FARFIELD_FACTOR_XPATH,
    GMSH_MESH_SIZE_FARFIELD_XPATH,
    GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH,
    GMSH_MESH_SIZE_FACTOR_WINGS_XPATH,
    GMSH_MESH_SIZE_ENGINES_XPATH,
    GMSH_MESH_SIZE_PROPELLERS_XPATH,
    GMSH_N_POWER_FACTOR_XPATH,
    GMSH_N_POWER_FIELD_XPATH,
    GMSH_REFINE_FACTOR_XPATH,
    GMSH_REFINE_TRUNCATED_XPATH,
    GMSH_REFINE_FACTOR_SHARP_EDGES_XPATH,
    GMSH_AUTO_REFINE_XPATH,
    GMSH_NUMBER_LAYER_XPATH,
    GMSH_H_FIRST_LAYER_XPATH,
    GMSH_MAX_THICKNESS_LAYER_XPATH,
    GMSH_GROWTH_RATIO_XPATH,
    GMSH_GROWTH_FACTOR_XPATH,
    GMSH_FEATURE_ANGLE_XPATH,
    GMSH_SURFACE_MESH_SIZE_XPATH,
    GMSH_EXPORT_PROP_XPATH,
    GMSH_INTAKE_PERCENT_XPATH,
    GMSH_EXHAUST_PERCENT_XPATH,
)

# ==============================================================================
#   VARIABLE
# ==============================================================================

cpacs_inout = CPACSInOut()

# ==============================================================================
#   GUI INPUTS
# ==============================================================================

cpacs_inout.add_input(
    var_name="open_gmsh",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Open GMSH GUI when the mesh is created",
    xpath=GMSH_OPEN_GUI_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Open GMSH GUI",
    gui_group="General options",
)

cpacs_inout.add_input(
    var_name="type_mesh",
    var_type=list,
    default_value=["Euler", "RANS"],
    unit=None,
    descr="Choose between Euler and RANS mesh",
    xpath=GMSH_MESH_TYPE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Choose the mesh type",
    gui_group="Mesh type",
)

cpacs_inout.add_input(
    var_name="aileron",
    var_type="multiselect",
    default_value=[0.0],
    unit="[deg]",
    descr="List of Aileron, Elevator, Rudder angles",
    xpath=GMSH_CTRLSURF_ANGLE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Aileron/Elevator/Rudder Angles",
    gui_group="Control surface settings",
)

cpacs_inout.add_input(
    var_name="symmetry",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Create a symmetry condition",
    xpath=GMSH_SYMMETRY_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Use Symmetry",
    gui_group="Domain",
)

cpacs_inout.add_input(
    var_name="farfield_factor",
    var_type=float,
    default_value=10,
    unit=None,
    descr="Farfield size factor compare to the aircraft largest dimension",
    xpath=GMSH_FARFIELD_FACTOR_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Farfield size factor",
    gui_group="Domain",
)

cpacs_inout.add_input(
    var_name="farfield_mesh_size_factor",
    var_type=float,
    default_value=10,
    unit=None,
    descr="""Factor proportional to the biggest cell on the plane
            to obtain cell size on the farfield(just for Euler)""",
    xpath=GMSH_MESH_SIZE_FARFIELD_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Farfield mesh size factor",
    gui_group="Euler options",
)

cpacs_inout.add_input(
    var_name="fuselage_mesh_size_factor",
    var_type=float,
    default_value=1.0,
    unit=None,
    descr="Factor proportional to fuselage radius of curvature to obtain cell size on it",
    xpath=GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Fuselage mesh size factor",
    gui_group="Euler options",
)

cpacs_inout.add_input(
    var_name="wing_mesh_size_factor",
    var_type=float,
    default_value=1.0,
    unit=None,
    descr="Factor proportional to wing radius of curvature to obtain cell size on it",
    xpath=GMSH_MESH_SIZE_FACTOR_WINGS_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Wings mesh size factor",
    gui_group="Euler options",
)

cpacs_inout.add_input(
    var_name="engine_mesh_size",
    var_type=float,
    default_value=0.23,
    unit="[m]",
    descr="Value assigned for the engine surfaces mesh size",
    xpath=GMSH_MESH_SIZE_ENGINES_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Engines",
    gui_group="Euler options",
)

cpacs_inout.add_input(
    var_name="propeller_mesh_size",
    var_type=float,
    default_value=0.23,
    unit="[m]",
    descr="Value assigned for the propeller surfaces mesh size",
    xpath=GMSH_MESH_SIZE_PROPELLERS_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Propellers",
    gui_group="Euler options",
)

cpacs_inout.add_input(
    var_name="n_power_factor",
    var_type=float,
    default_value=2,
    unit=None,
    descr="Value that changes the number of cells near the aircraft parts",
    xpath=GMSH_N_POWER_FACTOR_XPATH,
    gui=INCLUDE_GUI,
    gui_name="n power factor",
    gui_group="Advanced Euler mesh parameters",
)

cpacs_inout.add_input(
    var_name="n_power_field",
    var_type=float,
    default_value=0.9,
    unit=None,
    descr="Value that changes the measure of fist cells near aircraft parts",
    xpath=GMSH_N_POWER_FIELD_XPATH,
    gui=INCLUDE_GUI,
    gui_name="n power field",
    gui_group="Advanced Euler mesh parameters",
)

cpacs_inout.add_input(
    var_name="refine_factor",
    var_type=float,
    default_value=2.0,
    unit=None,
    descr="Refinement factor of wing leading/trailing edge mesh",
    xpath=GMSH_REFINE_FACTOR_XPATH,
    gui=INCLUDE_GUI,
    gui_name="LE/TE refinement factor",
    gui_group="Advanced Euler mesh parameters",
)

cpacs_inout.add_input(
    var_name="refine_truncated",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Enable the refinement of truncated trailing edge",
    xpath=GMSH_REFINE_TRUNCATED_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Refine truncated TE",
    gui_group="Advanced Euler mesh parameters",
)

cpacs_inout.add_input(
    var_name="auto_refine",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Automatically refine the mesh on surfaces that are small compare to the chosen mesh"
    "size, this option increase the mesh generation time",
    xpath=GMSH_AUTO_REFINE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Auto refine",
    gui_group="Advanced Euler mesh parameters",
)

cpacs_inout.add_input(
    var_name="refine_factor_sharp_edges",
    var_type=float,
    default_value=1.0,
    unit="1",
    descr="Refinement factor of other sharp edges mesh",
    xpath=GMSH_REFINE_FACTOR_SHARP_EDGES_XPATH,
    gui=True,
    gui_name="other sharp edges refinement factor",
    gui_group="Advanced Euler mesh parameters",
)

cpacs_inout.add_input(
    var_name="n_layer",
    var_type=int,
    default_value=20,
    unit=None,
    descr="Number of prismatic element layers.",
    xpath=GMSH_NUMBER_LAYER_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Number of layer",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="h_first_layer",
    var_type=float,
    default_value=3,
    unit="[\u03BCm]",
    descr="is the height of the first prismatic cell, touching the wall, in mesh length units.",
    xpath=GMSH_H_FIRST_LAYER_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Height of first layer",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="max_layer_thickness",
    var_type=float,
    default_value=100,
    unit="[mm]",
    descr="The maximum allowed absolute thickness of the prismatic layer.",
    xpath=GMSH_MAX_THICKNESS_LAYER_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Max layer thickness",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="growth_ratio",
    var_type=float,
    default_value=1.2,
    unit=None,
    descr="the largest allowed ratio between the wall-normal edge lengths of consecutive cells",
    xpath=GMSH_GROWTH_RATIO_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Growth ratio",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="growth_factor",
    var_type=float,
    default_value=1.4,
    unit=None,
    descr="Desired growth factor between edge lengths of coincident tetrahedra",
    xpath=GMSH_GROWTH_FACTOR_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Growth factor",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="feature_angle",
    var_type=float,
    default_value=40,
    unit="[grad]",
    descr="Larger angles are treated as resulting from approximation of curved surfaces",
    xpath=GMSH_FEATURE_ANGLE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Feature Angle",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="surface_mesh_factor",
    var_type=float,
    default_value=5,
    unit="[10^-3]",
    descr="Surface mesh size factor compared to aircraft largest dimension (omogeneus everywhere)",
    xpath=GMSH_SURFACE_MESH_SIZE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Surface mesh size",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="export_propellers",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Export propeller(s) to be use as disk actuator",
    xpath=GMSH_EXPORT_PROP_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Export propeller(s)",
    gui_group="General options",
)

cpacs_inout.add_input(
    var_name="intake_percent",
    var_type=float,
    default_value=20,
    unit="[%]",
    descr="Position of the intake surface boundary condition in percentage of"
    " the engine length from the beginning of the engine",
    xpath=GMSH_INTAKE_PERCENT_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Engine intake position",
    gui_group="Engines",
)
cpacs_inout.add_input(
    var_name="exhaust_percent",
    var_type=float,
    default_value=20,
    unit="[%]",
    descr="Position of the exhaust surface boundary condition in percentage of"
    " the engine length from the end of the engine",
    xpath=GMSH_EXHAUST_PERCENT_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Engine exhaust position",
    gui_group="Engines",
)

# ==============================================================================
#   GUI OUTPUTS
# ==============================================================================

cpacs_inout.add_output(
    var_name="su2_mesh_path",
    var_type="pathtype",
    default_value=None,
    unit=None,
    descr="Absolute path of the SU2 mesh",
    xpath=SU2MESH_XPATH,
)

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to be executed.")
