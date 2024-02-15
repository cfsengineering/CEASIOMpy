from pathlib import Path

from ceasiompy.utils.commonxpath import (
    GMSH_AUTO_REFINE_XPATH,
    GMSH_EXHAUST_PERCENT_XPATH,
    GMSH_EXPORT_PROP_XPATH,
    GMSH_FARFIELD_FACTOR_XPATH,
    GMSH_N_POWER_FACTOR_XPATH,
    GMSH_N_POWER_FIELD_XPATH,
    GMSH_INTAKE_PERCENT_XPATH,
    GMSH_MESH_SIZE_FARFIELD_XPATH,
    GMSH_MESH_SIZE_FUSELAGE_XPATH,
    GMSH_MESH_SIZE_WINGS_XPATH,
    GMSH_MESH_SIZE_ENGINES_XPATH,
    GMSH_MESH_SIZE_PROPELLERS_XPATH,
    GMSH_OPEN_GUI_XPATH,
    GMSH_REFINE_TRUNCATED_XPATH,
    GMSH_REFINE_FACTOR_XPATH,
    GMSH_SYMMETRY_XPATH,
    SU2MESH_XPATH,
    GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH,
    GMSH_MESH_SIZE_FACTOR_WINGS_XPATH,
    GMSH_MESH_TYPE_XPATH,
    GMSH_MESH_FORMAT_XPATH,
    GMSH_NUMBER_LAYER_XPATH,
    GMSH_H_FIRST_LAYER_XPATH,
    GMSH_MAX_THICKNESS_LAYER_XPATH,
    GMSH_GROWTH_FACTOR_XPATH,
    GMSH_MIN_MAX_MESH_SIZE_XPATH,
    GMSH_FEATURE_ANGLE_XPATH,
)
from ceasiompy.utils.moduleinterfaces import CPACSInOut

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "GMSH")


# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

cpacs_inout.add_input(
    var_name="open_gmsh",
    var_type=bool,
    default_value=False,
    unit="1",
    descr="Open GMSH GUI when the mesh is created",
    xpath=GMSH_OPEN_GUI_XPATH,
    gui=True,
    gui_name="Open GMSH GUI",
    gui_group="General options",
)

cpacs_inout.add_input(
    var_name="type_mesh",
    var_type=list,
    default_value=["Euler", "RANS"],
    unit="1",
    descr="Chose between Euler and RANS mesh",
    xpath=GMSH_MESH_TYPE_XPATH,
    gui=True,
    gui_name="Chose the mesh type",
    gui_group="Mesh type",
)

cpacs_inout.add_input(
    var_name="symmetry",
    var_type=bool,
    default_value=False,
    unit="1",
    descr="Create a symmetry condition",
    xpath=GMSH_SYMMETRY_XPATH,
    gui=True,
    gui_name="Use Symmetry",
    gui_group="Domain",
)

cpacs_inout.add_input(
    var_name="farfield_factor",
    var_type=float,
    default_value=6,
    unit="[-]",
    descr="Farfield size factor compare to the aircraft largest dimension",
    xpath=GMSH_FARFIELD_FACTOR_XPATH,
    gui=True,
    gui_name="Farfield size factor",
    gui_group="Domain",
)

cpacs_inout.add_input(
    var_name="farfield_mesh_size_factor",
    var_type=float,
    default_value=10,
    unit="[-]",
    descr="""Factor proportional to the biggest cell on the plane
            to obtain cell size on the farfield(just for Euler)""",
    xpath=GMSH_MESH_SIZE_FARFIELD_XPATH,
    gui=True,
    gui_name="Farfield mesh size factor",
    gui_group="Euler options",
)

cpacs_inout.add_input(
    var_name="fuselage_mesh_size_factor",
    var_type=float,
    default_value=1,
    unit="[-]",
    descr="Factor proportional to fuselage radius of curvature to obtain cell size on it",
    xpath=GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH,
    gui=True,
    gui_name="Fuselage mesh size factor",
    gui_group="Euler options",
)

cpacs_inout.add_input(
    var_name="wing_mesh_size_factor",
    var_type=float,
    default_value=1.5,
    unit="[-]",
    descr="Factor proportional to wing radius of curvature to obtain cell size on it",
    xpath=GMSH_MESH_SIZE_FACTOR_WINGS_XPATH,
    gui=True,
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
    gui=True,
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
    gui=True,
    gui_name="Propellers",
    gui_group="Euler options",
)

cpacs_inout.add_input(
    var_name="n_layer",
    var_type=int,
    default_value=20,
    unit="[-]",
    descr="Number of prismatic element layers.",
    xpath=GMSH_NUMBER_LAYER_XPATH,
    gui=True,
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
    gui=True,
    gui_name="Height of first layer",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="max_layer_thickness",
    var_type=float,
    default_value=10,
    unit="[cm]",
    descr="The maximum allowed absolute thickness of the prismatic layer.",
    xpath=GMSH_MAX_THICKNESS_LAYER_XPATH,
    gui=True,
    gui_name="Max layer thickness",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="growth_factor",
    var_type=float,
    default_value=1.2,
    unit="[-]",
    descr="Desired growth factor between edge lengths of coincident tetrahedra",
    xpath=GMSH_GROWTH_FACTOR_XPATH,
    gui=True,
    gui_name="Growth factor",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="feature_angle",
    var_type=float,
    default_value=80,
    unit="[grad]",
    descr="Whenever the dihedral angle of two triangle is smaller than this limit, the resulting edge is understood to represent an actual geometrical feature. Larger angles are treated as resulting from approximation of curved surfaces by linear triangles",
    xpath=GMSH_FEATURE_ANGLE_XPATH,
    gui=True,
    gui_name="Feature Angle",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="min_max_mesh_factor",
    var_type=float,
    default_value=5,
    unit="[10^-3]",
    descr="Minimum and maximum mesh size factor compare to the aircraft largest dimension",
    xpath=GMSH_MIN_MAX_MESH_SIZE_XPATH,
    gui=True,
    gui_name="Max and min mesh size",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="type_output_penta",
    var_type=list,
    default_value=["su2", "cgns", "sml"],
    unit="1",
    descr="Choice between the file type generated by pentagrow",
    xpath=GMSH_MESH_FORMAT_XPATH,
    gui=True,
    gui_name="Choice the output file type",
    gui_group="RANS options",
)

cpacs_inout.add_input(
    var_name="export_propellers",
    var_type=bool,
    default_value=False,
    unit="1",
    descr="Export propeller(s) to be use as disk actuator",
    xpath=GMSH_EXPORT_PROP_XPATH,
    gui=True,
    gui_name="Export propeller(s)",
    gui_group="General options",
)

cpacs_inout.add_input(
    var_name="n_power_factor",
    var_type=float,
    default_value=2,
    unit="1",
    descr="Value that changes the number of cells near the aircraft parts",
    xpath=GMSH_N_POWER_FACTOR_XPATH,
    gui=True,
    gui_name="n power factor",
    gui_group="Advanced mesh parameters",
)

cpacs_inout.add_input(
    var_name="n_power_field",
    var_type=float,
    default_value=0.9,
    unit="1",
    descr="Value that changes the measure of fist cells near aircraft parts",
    xpath=GMSH_N_POWER_FIELD_XPATH,
    gui=True,
    gui_name="n power field",
    gui_group="Advanced mesh parameters",
)

cpacs_inout.add_input(
    var_name="refine_factor",
    var_type=float,
    default_value=2.0,
    unit="1",
    descr="Refinement factor of wing leading/trailing edge mesh",
    xpath=GMSH_REFINE_FACTOR_XPATH,
    gui=True,
    gui_name="LE/TE refinement factor",
    gui_group="Advanced mesh parameters",
)
cpacs_inout.add_input(
    var_name="refine_truncated",
    var_type=bool,
    default_value=False,
    unit="1",
    descr="Enable the refinement of truncated trailing edge",
    xpath=GMSH_REFINE_TRUNCATED_XPATH,
    gui=True,
    gui_name="Refine truncated TE",
    gui_group="Advanced mesh parameters",
)

cpacs_inout.add_input(
    var_name="auto_refine",
    var_type=bool,
    default_value=False,
    unit="1",
    descr="Automatically refine the mesh on surfaces that are small compare to the chosen mesh"
    "size, this option increase the mesh generation time",
    xpath=GMSH_AUTO_REFINE_XPATH,
    gui=True,
    gui_name="Auto refine",
    gui_group="Advanced mesh parameters",
)

cpacs_inout.add_input(
    var_name="intake_percent",
    var_type=float,
    default_value=20,
    unit="[%]",
    descr="Position of the intake surface boundary condition in percentage of"
    " the engine length from the beginning of the engine",
    xpath=GMSH_INTAKE_PERCENT_XPATH,
    gui=True,
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
    gui=True,
    gui_name="Engine exhaust position",
    gui_group="Engines",
)


# ----- Output -----

cpacs_inout.add_output(
    var_name="su2_mesh_path",
    var_type="pathtype",
    default_value=None,
    unit="1",
    descr="Absolute path of the SU2 mesh",
    xpath=SU2MESH_XPATH,
)
