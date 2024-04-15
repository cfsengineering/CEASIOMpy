from pathlib import Path

from ceasiompy.utils.commonxpath import (
    AEROPERFORMANCE_XPATH,
    GEOM_XPATH,
    RANGE_XPATH,
    REF_XPATH,
    EDGE_AEROMAP_UID_XPATH,
    EDGE_CFL_NB_XPATH,
    EDGE_FIXED_CL_XPATH,
    EDGE_MAX_ITER_XPATH,
    EDGE_MG_LEVEL_XPATH,
    EDGE_NB_CPU_XPATH,
    EDGE_MESH_XPATH,
    EDGE_SOLVER_XPATH,
    EDGE_ABOC_XPATH,
)
from ceasiompy.utils.moduleinterfaces import CPACSInOut

# ===== Module Status =====
# True if the module is active
# False if the module is disabled (not working or not ready)
module_status = True

# ===== Results directory path =====

RESULTS_DIR = Path("Results", "EdgeRun")

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

cpacs_inout.add_input(
    var_name="aeromap_uid",
    var_type=list,
    default_value=None,
    unit=None,
    descr="Name of the aero map to calculate",
    xpath=EDGE_AEROMAP_UID_XPATH,
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
    var_name="fixed_cl",
    var_type=str,
    default_value="NO",
    unit="-",
    descr="FIXED_CL_MODE parameter for SU2",
    xpath=EDGE_FIXED_CL_XPATH,
    gui=False,
    gui_name=None,
    gui_group=None,
)

cpacs_inout.add_input(
    var_name="nb_proc",
    var_type=int,
    default_value=64,
    unit="1",
    descr="Number of proc to use to run EDGE",
    xpath=EDGE_NB_CPU_XPATH,
    gui=True,
    gui_name="Nb of processor",
    gui_group="CPU",
)

cpacs_inout.add_input(
    var_name="max_iter",
    var_type=int,
    default_value=200,
    unit="1",
    descr="Maximum number of iterations performed by EDGE",
    xpath=EDGE_MAX_ITER_XPATH,
    gui=True,
    gui_name="Maximum iterations",
    gui_group="EDGE Parameters",
)

cpacs_inout.add_input(
    var_name="cfl_nb",
    var_type=float,
    default_value=1.0,
    unit="1",
    descr="CFL Number, Courant–Friedrichs–Lewy condition",
    xpath=EDGE_CFL_NB_XPATH,
    gui=False,
    gui_name="CFL Number",
    gui_group="EDGE Parameters",
)

cpacs_inout.add_input(
    var_name="mg_level",
    var_type=int,
    default_value=1,
    unit="1",
    descr="Multi-grid level (0 = no multigrid)",
    xpath=EDGE_MG_LEVEL_XPATH,
    gui=True,
    gui_name="Multigrid Level",
    gui_group="EDGE Parameters",
)

cpacs_inout.add_input(
    var_name="calculation_type",
    var_type=list,
    default_value=["Euler", "RANS"],
    unit="1",
    descr="Chose if perform a RANS or an Euler calculation",
    xpath=EDGE_SOLVER_XPATH,
    gui=True,
    gui_name="Solver for calculation",
    gui_group="EDGE parameters",
)

cpacs_inout.add_input(
    var_name="EDGE_mesh_path",
    var_type="pathtype",
    default_value="-",
    unit="1",
    descr="Absolute path of the EDGE mesh",
    xpath=EDGE_MESH_XPATH,
    gui=True,
    gui_name="EDGE Mesh",
    gui_group="Inputs",
)

cpacs_inout.add_input(
    var_name="EDGE_ABOC_path",
    var_type="pathtype",
    default_value="-",
    unit="1",
    descr="Absolute path of the EDGE Boundary Condition file",
    xpath=EDGE_ABOC_XPATH,
    gui=True,
    gui_name="EDGE ABOC",
    gui_group="Inputs",
)

# ----- Output -----

cpacs_inout.add_output(
    var_name="wetted_area",
    var_type=float,
    default_value=None,
    unit="m^2",
    descr="Aircraft wetted area calculated by EDGE",
    xpath=GEOM_XPATH + "/analyses/wettedArea",
)

cpacs_inout.add_output(
    var_name="aeromap_EDGE",  # name to change...
    # var_type=CPACS_aeroMap, # no type pour output, would it be useful?
    default_value=None,
    unit="-",
    descr="aeroMap with aero coefficients calculated by EDGE",
    xpath=AEROPERFORMANCE_XPATH + "/aeroMap/aeroPerformanceMap",
)
