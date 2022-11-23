from pathlib import Path

from ceasiompy.utils.ceasiompyutils import get_reasonable_nb_cpu
from ceasiompy.utils.commonxpath import (
    AEROPERFORMANCE_XPATH,
    GEOM_XPATH,
    RANGE_XPATH,
    REF_XPATH,
    SU2_AEROMAP_UID_XPATH,
    SU2_BC_FARFIELD_XPATH,
    SU2_BC_WALL_XPATH,
    SU2_CFL_NB_XPATH,
    SU2_CONTROL_SURF_XPATH,
    SU2_DAMPING_DER_XPATH,
    SU2_EXTRACT_LOAD_XPATH,
    SU2_FIXED_CL_XPATH,
    SU2_MAX_ITER_XPATH,
    SU2_MG_LEVEL_XPATH,
    SU2_NB_CPU_XPATH,
    SU2_ROTATION_RATE_XPATH,
    SU2_TARGET_CL_XPATH,
    SU2_UPDATE_WETTED_AREA_XPATH,
    SU2_XPATH,
    SU2MESH_XPATH,
)
from ceasiompy.utils.moduleinterfaces import CPACSInOut

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "SU2")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

cpacs_inout.add_input(
    var_name="aeromap_uid",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to calculate",
    xpath=SU2_AEROMAP_UID_XPATH,
    gui=True,
    gui_name="__AEROMAP_SELECTION",
    gui_group="Aeromap settings",
)

cpacs_inout.add_input(
    var_name="ref_len",
    var_type=float,
    default_value=None,
    unit="m",
    descr="Reference length of the aircraft",
    xpath=REF_XPATH + "/length",
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name="ref_area",
    var_type=float,
    default_value=None,
    unit="m^2",
    descr="Reference area of the aircraft",
    xpath=REF_XPATH + "/area",
    gui=False,
    gui_name=None,
    gui_group=None,
)


for direction in ["x", "y", "z"]:
    cpacs_inout.add_input(
        var_name=f"ref_ori_moment_{direction}",
        var_type=float,
        default_value=0.0,
        unit="m",
        descr=f"Fuselage scaling on {direction} axis",
        xpath=REF_XPATH + f"/point/{direction}",
        gui=False,
        gui_name=None,
        gui_group=None,
    )


cpacs_inout.add_input(
    var_name="cruise_mach",
    var_type=float,
    default_value=0.78,
    unit="1",
    descr="Aircraft cruise Mach number",
    xpath=RANGE_XPATH + "/cruiseMach",
    gui=False,
    gui_name="Cruise Mach",
    gui_group="If fixed CL",
)

cpacs_inout.add_input(
    var_name="cruise_alt",
    var_type=float,
    default_value=120000.0,
    unit="m",
    descr="Aircraft cruise altitude",
    xpath=RANGE_XPATH + "/cruiseAltitude",
    gui=False,
    gui_name="Cruise Altitude",
    gui_group="If fixed CL",
)

cpacs_inout.add_input(
    var_name="target_cl",
    var_type=float,
    default_value=1.0,
    unit="1",
    descr="Value of CL to achieve to have a level flight with the given conditions",
    xpath=SU2_TARGET_CL_XPATH,
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name="fixed_cl",
    var_type=str,
    default_value="NO",
    unit="-",
    descr="FIXED_CL_MODE parameter for SU2",
    xpath=SU2_FIXED_CL_XPATH,
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name="damping_der",
    var_type=bool,
    default_value=False,
    unit="1",
    descr="To check if damping derivatives should be calculated or not",
    xpath=SU2_DAMPING_DER_XPATH,
    gui=True,
    gui_name="Damping Derivatives",
    gui_group="Aeromap Options",
)

cpacs_inout.add_input(
    var_name="rotation_rate",
    var_type=float,
    default_value=1.0,
    unit="rad/s",
    descr="Rotation rate use to calculate damping derivatives",
    xpath=SU2_ROTATION_RATE_XPATH,
    gui=True,
    gui_name="Rotation Rate",
    gui_group="Aeromap Options",
)

cpacs_inout.add_input(
    var_name="control_surf",
    var_type=bool,
    default_value=False,
    unit="1",
    descr="To check if control surfaces deflections should be calculated or not",
    xpath=SU2_CONTROL_SURF_XPATH,
    gui=True,
    gui_name="Control Surfaces",
    gui_group="Aeromap Options",
)

cpacs_inout.add_input(
    var_name="nb_proc",
    var_type=int,
    default_value=get_reasonable_nb_cpu(),
    unit="1",
    descr="Number of proc to use to run SU2",
    xpath=SU2_NB_CPU_XPATH,
    gui=True,
    gui_name="Nb of processor",
    gui_group="CPU",
)

cpacs_inout.add_input(
    var_name="max_iter",
    var_type=int,
    default_value=800,
    unit="1",
    descr="Maximum number of iterations performed by SU2",
    xpath=SU2_MAX_ITER_XPATH,
    gui=True,
    gui_name="Maximum iterations",
    gui_group="SU2 Parameters",
)

cpacs_inout.add_input(
    var_name="cfl_nb",
    var_type=float,
    default_value=8.0,
    unit="1",
    descr="CFL Number, Courant–Friedrichs–Lewy condition",
    xpath=SU2_CFL_NB_XPATH,
    gui=True,
    gui_name="CFL Number",
    gui_group="SU2 Parameters",
)

cpacs_inout.add_input(
    var_name="mg_level",
    var_type=int,
    default_value=3,
    unit="3",
    descr="Multi-grid level (0 = no multigrid)",
    xpath=SU2_MG_LEVEL_XPATH,
    gui=True,
    gui_name="Multigrid Level",
    gui_group="SU2 Parameters",
)

cpacs_inout.add_input(
    var_name="su2_mesh_path",
    var_type="pathtype",
    default_value="-",
    unit="1",
    descr="Absolute path of the SU2 mesh",
    xpath=SU2MESH_XPATH,
    gui=True,
    gui_name="SU2 Mesh",
    gui_group="Inputs",
)

cpacs_inout.add_input(
    var_name="update_wetted_area",
    var_type=bool,
    default_value=False,
    unit="1",
    descr="Option to update the wetted area from the latest SU2 result.",
    xpath=SU2_UPDATE_WETTED_AREA_XPATH,
    gui=True,
    gui_name="Update Wetted Area",
    gui_group="Results",
)

cpacs_inout.add_input(
    var_name="check_extract_loads",
    var_type=bool,
    default_value=False,
    unit="1",
    descr="Option to extract loads (forces in each point) from results",
    xpath=SU2_EXTRACT_LOAD_XPATH,
    gui=True,
    gui_name="Extract loads",
    gui_group="Results",
)


# ----- Output -----

cpacs_inout.add_output(
    var_name="start_time",
    var_type=str,
    default_value=None,
    unit="1",
    descr="Start time of the last SU2 calculation",
    xpath=SU2_XPATH + "/startTime",
)

cpacs_inout.add_output(
    var_name="end_time",
    var_type=str,
    default_value=None,
    unit="1",
    descr="Start time of the last SU2 calculation",
    xpath=SU2_XPATH + "/endTime",
)

cpacs_inout.add_output(
    var_name="wetted_area",
    var_type=float,
    default_value=None,
    unit="m^2",
    descr="Aircraft wetted area calculated by SU2",
    xpath=GEOM_XPATH + "/analyses/wettedArea",
)

cpacs_inout.add_output(
    var_name="bc_wall_list",
    var_type=list,
    default_value=None,
    unit="1",
    descr="Wall boundary conditions found in the SU2 mesh",
    xpath=SU2_BC_WALL_XPATH,
)

cpacs_inout.add_output(
    var_name="bc_farfield_list",
    var_type=list,
    default_value=None,
    unit="1",
    descr="Farfield boundary conditions found in the SU2 mesh (for off engines)",
    xpath=SU2_BC_FARFIELD_XPATH,
)

cpacs_inout.add_output(
    var_name="aeromap_SU2",  # name to change...
    # var_type=CPACS_aeroMap, # no type pour output, would it be useful?
    default_value=None,
    unit="-",
    descr="aeroMap with aero coefficients calculated by SU2",
    xpath=AEROPERFORMANCE_XPATH + "/aeroMap/aeroPerformanceMap",
)
