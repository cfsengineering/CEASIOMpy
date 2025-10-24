from ceasiompy.utils.guixpaths import (
    SU2MESH_XPATH,
    SUMO_REFINE_LEVEL_XPATH,
    SPECIFIED_SUMOFILE_XPATH,
)
from ceasiompy.utils.moduleinterfaces import CPACSInOut


# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

cpacs_inout.add_input(
    var_name="sumo_file_path",
    var_type="pathtype",
    default_value="-",
    unit="1",
    descr="Absolute path to the SUMO file",
    xpath=SPECIFIED_SUMOFILE_XPATH,
    gui=True,
    gui_name="SUMO File path",
    gui_group="Inputs",
)

cpacs_inout.add_input(
    var_name="refine_level",
    var_type=float,
    default_value=1.0,
    unit="1",
    descr="0 is baseline, +1 env. equal double mesh points",
    xpath=SUMO_REFINE_LEVEL_XPATH,
    gui=True,
    gui_name="Refinement Level",
    gui_group="SUMO options",
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
