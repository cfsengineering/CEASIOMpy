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

from ceasiompy.utils.moduleinterfaces import CPACSInOut

from ceasiompy.utils.commonxpaths import SU2MESH_XPATH, GEOMETRY_MODE_XPATH, SELECTED_AEROMAP_XPATH
from ceasiompy.CPACS2GMSH import (
    INCLUDE_GUI,
    HAS_PENTAGROW,
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
    GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH,
    GMSH_AUTO_REFINE_XPATH,
    GMSH_NUMBER_LAYER_XPATH,
    GMSH_H_FIRST_LAYER_XPATH,
    GMSH_MAX_THICKNESS_LAYER_XPATH,
    GMSH_GROWTH_RATIO_XPATH,
    GMSH_GROWTH_FACTOR_XPATH,
    GMSH_FEATURE_ANGLE_XPATH,
    GMSH_EXPORT_PROP_XPATH,
    GMSH_INTAKE_PERCENT_XPATH,
    GMSH_EXHAUST_PERCENT_XPATH,
    GMSH_SAVE_CGNS_XPATH,
    GMSH_MESH_CHECKER_XPATH,
    GMSH_2D_AIRFOIL_MESH_SIZE_XPATH,
    GMSH_2D_EXT_MESH_SIZE_XPATH,
    GMSH_2D_FARFIELD_RADIUS_XPATH,
    GMSH_2D_STRUCTURED_MESH_XPATH,
    GMSH_2D_FARFIELD_TYPE_XPATH,
    GMSH_2D_FIRST_LAYER_HEIGHT_XPATH,
    GMSH_2D_HEIGHT_LENGTH_XPATH,
    GMSH_2D_WAKE_LENGTH_XPATH,
    GMSH_2D_NO_BL_XPATH,
    GMSH_2D_RATIO_XPATH,
    GMSH_2D_NB_LAYERS_XPATH,
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
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
)

cpacs_inout.add_input(
    var_name="type_mesh",
    var_type=list,
    default_value=["Euler", "RANS"],
    unit=None,
    descr="Choose between Euler and RANS mesh",
    xpath=GMSH_MESH_TYPE_XPATH,
    gui_name="Choose the mesh type",
    gui_group="Mesh type",
    gui=HAS_PENTAGROW,
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_group="Mesh options",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_group="Mesh options",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_group="Mesh options",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_group="Mesh options",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_group="Mesh options",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
)

cpacs_inout.add_input(
    var_name="n_power_factor",
    var_type=float,
    default_value=2,
    unit=None,
    descr="Power of the power law of the refinement on LE and TE. ",
    xpath=GMSH_N_POWER_FACTOR_XPATH,
    gui=INCLUDE_GUI,
    gui_name="n power factor",
    gui_group="Advanced mesh parameters",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_group="Advanced mesh parameters",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_group="Advanced mesh parameters",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_group="Advanced mesh parameters",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_group="Advanced mesh parameters",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
)

cpacs_inout.add_input(
    var_name="refine_factor_angled_lines",
    var_type=float,
    default_value=1.5,
    unit="1",
    descr="Refinement factor of edges at intersections that are not flat enough",
    xpath=GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH,
    gui=True,
    gui_name="Refinement factor of lines in between angled surfaces (only in RANS)",
    gui_group="Advanced mesh parameters",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",

)

cpacs_inout.add_input(
    var_name="h_first_layer",
    var_type=float,
    default_value=3,
    unit="[\u03bcm]",
    descr="is the height of the first prismatic cell, touching the wall, in mesh length units.",
    xpath=GMSH_H_FIRST_LAYER_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Height of first layer",
    gui_group="RANS options",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
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
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
)

cpacs_inout.add_input(
    var_name="geom_output_format",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Save also the geometry in the .cgns format",
    xpath=GMSH_SAVE_CGNS_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Save CGNS",
    gui_group="Saving options",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
)

cpacs_inout.add_input(
    var_name="mesh_checker",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Check mesh quality with pyvista",
    xpath=GMSH_MESH_CHECKER_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Mesh Checker",
    gui_group="Mesh Checker",
    gui_cond=f"{GEOMETRY_MODE_XPATH}!=2D",
)

# ==============================================================================
#   AEROMAP INPUT (for both 2D and 3D)
# ==============================================================================

cpacs_inout.add_input(
    var_name="aeromap_uid",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Aeromap UID to use for CFD conditions (AoA, Mach, altitude, etc.)",
    xpath=SELECTED_AEROMAP_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Aeromap Selection",
    gui_group="Aeromap Options",
)

# ==============================================================================
#   2D AIRFOIL MESH PARAMETERS
# ==============================================================================

cpacs_inout.add_input(
    var_name="no_boundary_layer",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Disable boundary layer (unstructured mesh with triangles only)",
    xpath=GMSH_2D_NO_BL_XPATH,
    gui=INCLUDE_GUI,
    gui_name="No Boundary Layer",
    gui_group="2D Airfoil Mesh",
    gui_cond=f"{GEOMETRY_MODE_XPATH}==2D",
)

cpacs_inout.add_input(
    var_name="airfoil_mesh_size",
    var_type=float,
    default_value=0.01,
    unit="[mm]",
    descr="Mesh size on the airfoil contour for 2D mesh generation",
    xpath=GMSH_2D_AIRFOIL_MESH_SIZE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Airfoil Mesh Size",
    gui_group="2D Airfoil Mesh",
    gui_cond=f"{GEOMETRY_MODE_XPATH}==2D",
)

cpacs_inout.add_input(
    var_name="external_mesh_size",
    var_type=float,
    default_value=0.2,
    unit="[mm]",
    descr="Mesh size in the external domain for 2D mesh generation",
    xpath=GMSH_2D_EXT_MESH_SIZE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="External Mesh Size",
    gui_group="2D Airfoil Mesh",
    gui_cond=f"{GEOMETRY_MODE_XPATH}==2D",
)

cpacs_inout.add_input(
    var_name="structured_mesh",
    var_type=bool,
    default_value=False,
    unit=None,
    descr="Chose if you want a structured mesh or a hybrid one",
    xpath=GMSH_2D_STRUCTURED_MESH_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Structured Mesh",
    gui_group="2D Airfoil Mesh",
    gui_cond=f"{GEOMETRY_MODE_XPATH}==2D",
)

cpacs_inout.add_input(
    var_name="first_layer_height",
    var_type=float,
    default_value=0.001,
    unit="[mm]",
    descr="First layer height for 2D mesh generation",
    xpath=GMSH_2D_FIRST_LAYER_HEIGHT_XPATH,
    gui=INCLUDE_GUI,
    gui_name="First Layer Height",
    gui_group="2D Airfoil Mesh",
    gui_cond=f"{GMSH_2D_NO_BL_XPATH}!=True",
)

cpacs_inout.add_input(
    var_name="farfield_type",
    var_type=list,
    default_value=["Rectangular", "Circular", "CType"],
    unit=None,
    descr="Choose farfield shape (automatically set to CType for structured mesh)",
    xpath=GMSH_2D_FARFIELD_TYPE_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Farfield Type",
    gui_group="2D Airfoil Mesh",
    gui_cond=f"{GMSH_2D_STRUCTURED_MESH_XPATH}!=True",
)

cpacs_inout.add_input(
    var_name="farfield_radius",
    var_type=float,
    default_value=10.0,
    unit="[m]",
    descr="Farfield radius for circular farfield in 2D mesh generation",
    xpath=GMSH_2D_FARFIELD_RADIUS_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Farfield Radius",
    gui_group="2D Airfoil Mesh",
    gui_cond=f"{GMSH_2D_FARFIELD_TYPE_XPATH}==Circular",
)

cpacs_inout.add_input(
    var_name="wake_length",
    var_type=float,
    default_value=6,
    unit="[m]",
    descr="Wake length downstream of the airfoil for rectangular/C-type farfield",
    xpath=GMSH_2D_WAKE_LENGTH_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Wake Length",
    gui_group="2D Airfoil Mesh",
    gui_cond=f"{GMSH_2D_FARFIELD_TYPE_XPATH}!=Circular",
)

cpacs_inout.add_input(
    var_name="height_length",
    var_type=float,
    default_value=5,
    unit="[m]",
    descr="Height of domain for rectangular/C-type farfield",
    xpath=GMSH_2D_HEIGHT_LENGTH_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Height Length",
    gui_group="2D Airfoil Mesh",
    gui_cond=f"{GMSH_2D_FARFIELD_TYPE_XPATH}!=Circular",
)

cpacs_inout.add_input(
    var_name="growth_ratio",
    var_type=float,
    default_value=1.2,
    unit=None,
    descr="Growth ratio of boundary layer cells",
    xpath=GMSH_2D_RATIO_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Growth Ratio",
    gui_group="2D Airfoil Mesh",
    gui_cond=f"{GMSH_2D_NO_BL_XPATH}!=True",
)

cpacs_inout.add_input(
    var_name="number_of_layers",
    var_type=int,
    default_value=35,
    unit=None,
    descr="Total number of layers in the boundary layer",
    xpath=GMSH_2D_NB_LAYERS_XPATH,
    gui=INCLUDE_GUI,
    gui_name="Number of Layers",
    gui_group="2D Airfoil Mesh",
    gui_cond=f"{GMSH_2D_NO_BL_XPATH}!=True",
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
