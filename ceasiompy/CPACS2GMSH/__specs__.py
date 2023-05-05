from pathlib import Path

from ceasiompy.utils.commonxpath import (
    GMSH_AUTO_REFINE_XPATH,
    GMSH_EXHAUST_PERCENT_XPATH,
    GMSH_EXPORT_PROP_XPATH,
    GMSH_FARFIELD_FACTOR_XPATH,
    GMSH_N_POWER_FACTOR_XPATH,
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
    var_name="farfield_mesh_size",
    var_type=float,
    default_value=25,
    unit="[m]",
    descr="Value assigned for the farfield surface mesh size",
    xpath=GMSH_MESH_SIZE_FARFIELD_XPATH,
    gui=True,
    gui_name="Farfield",
    gui_group="Mesh size",
)

cpacs_inout.add_input(
    var_name="fuselage_mesh_size",
    var_type=float,
    default_value=0.4,
    unit="[m]",
    descr="Value assigned for the fuselage surfaces mesh size",
    xpath=GMSH_MESH_SIZE_FUSELAGE_XPATH,
    gui=True,
    gui_name="Fuselage",
    gui_group="Mesh size",
)

cpacs_inout.add_input(
    var_name="wing_mesh_size",
    var_type=float,
    default_value=0.23,
    unit="[m]",
    descr="Value assigned for the wings surfaces mesh size",
    xpath=GMSH_MESH_SIZE_WINGS_XPATH,
    gui=True,
    gui_name="Wings",
    gui_group="Mesh size",
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
    gui_group="Mesh size",
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
    gui_group="Mesh size",
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
    var_name="refine_factor",
    var_type=float,
    default_value=7.0,
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
    default_value=True,
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
