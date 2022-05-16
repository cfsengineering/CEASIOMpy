"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function generate or modify SU2 configuration files

Python version: >=3.7

| Author: Aidan Jungo
| Creation: 2020-02-24

TODO:

    * add and test control surface functions

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

from ambiance import Atmosphere
from ceasiompy.SU2Run.func.su2utils import get_mesh_marker, get_su2_config_template
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonnames import CONFIG_CFD_NAME, SU2_FORCES_BREAKDOWN_NAME
from ceasiompy.utils.commonxpath import (
    RANGE_XPATH,
    SU2_AEROMAP_UID_XPATH,
    SU2_BC_FARFIELD_XPATH,
    SU2_BC_WALL_XPATH,
    SU2_CFL_NB_XPATH,
    SU2_CONTROL_SURF_XPATH,
    SU2_DAMPING_DER_XPATH,
    SU2_DEF_MESH_XPATH,
    SU2_FIXED_CL_XPATH,
    SU2_MAX_ITER_XPATH,
    SU2_MG_LEVEL_XPATH,
    SU2_ROTATION_RATE_XPATH,
    SU2_TARGET_CL_XPATH,
    SU2MESH_XPATH,
)
from ceasiompy.utils.configfiles import ConfigFile
from cpacspy.cpacsfunctions import (
    create_branch,
    get_string_vector,
    get_value,
    get_value_or_default,
)
from cpacspy.cpacspy import CPACS

log = get_logger()

MODULE_DIR = Path(__file__).parent


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def generate_su2_cfd_config(cpacs_path, cpacs_out_path, wkdir):
    """Function to create SU2 config file.

    Function 'generate_su2_cfd_config' reads data in the CPACS file and generate
    configuration files for one or multiple flight conditions (alt,mach,aoa,aos)

    Source:
        * SU2 config template: https://github.com/su2code/SU2/blob/master/config_template.cfg

    Args:
        cpacs_path (Path): Path to CPACS file
        cpacs_out_path (Path):Path to CPACS output file
        wkdir (Path): Path to the working directory

    """

    cpacs = CPACS(str(cpacs_path))

    # Get the SU2 Mesh
    su2_mesh_path = Path(get_value(cpacs.tixi, SU2MESH_XPATH))
    if not su2_mesh_path.is_file():
        raise FileNotFoundError(f"SU2 mesh file {su2_mesh_path} not found")

    # Get Mesh Marker and save them in the CPACS file
    bc_wall_list, engine_bc_list = get_mesh_marker(su2_mesh_path)

    create_branch(cpacs.tixi, SU2_BC_WALL_XPATH)
    bc_wall_str = ";".join(bc_wall_list)
    cpacs.tixi.updateTextElement(SU2_BC_WALL_XPATH, bc_wall_str)

    create_branch(cpacs.tixi, SU2_BC_FARFIELD_XPATH)
    bc_farfiled_str = ";".join(engine_bc_list)
    cpacs.tixi.updateTextElement(SU2_BC_FARFIELD_XPATH, bc_farfiled_str)

    # Fixed CL parameters
    fixed_cl = get_value_or_default(cpacs.tixi, SU2_FIXED_CL_XPATH, "NO")
    target_cl = get_value_or_default(cpacs.tixi, SU2_TARGET_CL_XPATH, 1.0)

    if fixed_cl == "NO":

        # Get the first aeroMap as default one
        aeromap_default = cpacs.get_aeromap_uid_list()[0]
        aeromap_uid = get_value_or_default(cpacs.tixi, SU2_AEROMAP_UID_XPATH, aeromap_default)
        log.info(f'Configuration file for "{aeromap_uid}" calculation will be created.')

        active_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

        # Get parameters of the aeroMap (altitude, machNumber, angleOfAttack, angleOfSideslip)
        alt_list = active_aeromap.get("altitude").tolist()
        mach_list = active_aeromap.get("machNumber").tolist()
        aoa_list = active_aeromap.get("angleOfAttack").tolist()
        aos_list = active_aeromap.get("angleOfSideslip").tolist()

        param_count = len(alt_list)

    else:  # if fixed_cl == 'YES':
        log.info("Configuration file for fixed CL calculation will be created.")

        # Parameters fixed CL calculation
        param_count = 1

        # Create a new aeroMap
        fix_cl_aeromap = cpacs.create_aeromap("aeroMap_fixedCL_SU2")
        fix_cl_aeromap.description = "AeroMap created for SU2 fixed CL value of: " + str(target_cl)

        # Get cruise mach and altitude
        cruise_mach_xpath = RANGE_XPATH + "/cruiseMach"
        mach = get_value_or_default(cpacs.tixi, cruise_mach_xpath, 0.78)
        cruise_alt_xpath = RANGE_XPATH + "/cruiseAltitude"
        alt = get_value_or_default(cpacs.tixi, cruise_alt_xpath, 12000)

        # Add new parameters to the aeroMap and save it
        fix_cl_aeromap.add_row(alt=alt, mach=mach, aos=0.0, aoa=0.0)
        fix_cl_aeromap.save()

        # Parameter lists
        alt_list = [alt]
        mach_list = [mach]
        aoa_list = [0.0]
        aos_list = [0.0]

    # Get and modify the default configuration file
    su2_congig_template_path = get_su2_config_template()
    cfg = ConfigFile(su2_congig_template_path)

    # General parmeters
    cfg["RESTART_SOL"] = "NO"
    cfg["REF_LENGTH"] = cpacs.aircraft.ref_lenght
    cfg["REF_AREA"] = cpacs.aircraft.ref_area
    cfg["REF_ORIGIN_MOMENT_X"] = cpacs.aircraft.ref_point_x
    cfg["REF_ORIGIN_MOMENT_Y"] = cpacs.aircraft.ref_point_y
    cfg["REF_ORIGIN_MOMENT_Z"] = cpacs.aircraft.ref_point_z

    # Settings
    cfg["INNER_ITER"] = int(get_value_or_default(cpacs.tixi, SU2_MAX_ITER_XPATH, 200))
    cfg["CFL_NUMBER"] = get_value_or_default(cpacs.tixi, SU2_CFL_NB_XPATH, 1.0)
    cfg["MGLEVEL"] = int(get_value_or_default(cpacs.tixi, SU2_MG_LEVEL_XPATH, 3))

    # Fixed CL mode (AOA will not be taken into account)
    cfg["FIXED_CL_MODE"] = fixed_cl
    cfg["TARGET_CL"] = target_cl
    cfg["DCL_DALPHA"] = "0.1"
    cfg["UPDATE_AOA_ITER_LIMIT"] = "50"
    cfg["ITER_DCL_DALPHA"] = "80"
    # TODO: correct value for the 3 previous parameters ??

    # Mesh Marker
    bc_wall_str = "(" + ",".join(bc_wall_list) + ")"
    cfg["MARKER_EULER"] = bc_wall_str
    cfg["MARKER_FAR"] = " (Farfield, " + ",".join(engine_bc_list) + ")"
    cfg["MARKER_SYM"] = " (0)"  # TODO: maybe make that a variable?
    cfg["MARKER_PLOTTING"] = bc_wall_str
    cfg["MARKER_MONITORING"] = bc_wall_str
    cfg["MARKER_MOVING"] = "( NONE )"  # TODO: when do we need to define MARKER_MOVING?
    cfg["DV_MARKER"] = bc_wall_str

    # Output
    cfg["WRT_FORCES_BREAKDOWN"] = "YES"
    cfg["BREAKDOWN_FILENAME"] = SU2_FORCES_BREAKDOWN_NAME
    cfg["OUTPUT_FILES"] = "(RESTART, PARAVIEW, SURFACE_PARAVIEW)"

    # Parameters which will vary for the different cases (alt,mach,aoa,aos)
    for case_nb in range(param_count):

        cfg["MESH_FILENAME"] = str(su2_mesh_path)

        alt = alt_list[case_nb]
        mach = mach_list[case_nb]
        aoa = aoa_list[case_nb]
        aos = aos_list[case_nb]

        Atm = Atmosphere(alt)

        cfg["MACH_NUMBER"] = mach
        cfg["AOA"] = aoa
        cfg["SIDESLIP_ANGLE"] = aos
        cfg["FREESTREAM_PRESSURE"] = Atm.pressure[0]
        cfg["FREESTREAM_TEMPERATURE"] = Atm.temperature[0]
        cfg["ROTATION_RATE"] = "0.0 0.0 0.0"

        case_dir_name = "".join(
            [
                "Case",
                str(case_nb).zfill(2),
                "_alt",
                str(alt),
                "_mach",
                str(round(mach, 2)),
                "_aoa",
                str(round(aoa, 1)),
                "_aos",
                str(round(aos, 1)),
            ]
        )

        case_dir_path = Path(wkdir, case_dir_name)
        if not case_dir_path.exists():
            case_dir_path.mkdir()

        config_output_path = Path(case_dir_path, CONFIG_CFD_NAME)
        cfg.write_file(config_output_path, overwrite=True)

        # Damping derivatives
        if get_value_or_default(cpacs.tixi, SU2_DAMPING_DER_XPATH, False):

            rotation_rate = str(get_value_or_default(cpacs.tixi, SU2_ROTATION_RATE_XPATH, 1.0))

            cfg["GRID_MOVEMENT"] = "ROTATING_FRAME"

            cfg["ROTATION_RATE"] = f"{rotation_rate} 0.0 0.0"
            case_dir = Path(wkdir, f"{case_dir_name}_dp")
            case_dir.mkdir()
            config_output_path = Path(case_dir, CONFIG_CFD_NAME)
            cfg.write_file(config_output_path, overwrite=True)

            cfg["ROTATION_RATE"] = f"0.0 {rotation_rate} 0.0"
            case_dir = Path(wkdir, f"{case_dir_name}_dq")
            case_dir.mkdir()
            config_output_path = Path(case_dir, CONFIG_CFD_NAME)
            cfg.write_file(config_output_path, overwrite=True)

            cfg["ROTATION_RATE"] = f"0.0 0.0 {rotation_rate}"
            case_dir = Path(wkdir, f"{case_dir_name}_dr")
            case_dir.mkdir()
            config_output_path = Path(case_dir, CONFIG_CFD_NAME)
            cfg.write_file(config_output_path, overwrite=True)

            log.info("Damping derivatives cases directory has been created.")

        # Control surfaces deflections
        if get_value_or_default(cpacs.tixi, SU2_CONTROL_SURF_XPATH, False):

            # Get deformed mesh list
            if cpacs.tixi.checkElement(SU2_DEF_MESH_XPATH):
                su2_def_mesh_list = get_string_vector(cpacs.tixi, SU2_DEF_MESH_XPATH)
            else:
                log.warning("No SU2 deformed mesh has been found!")
                su2_def_mesh_list = []

            for su2_def_mesh in su2_def_mesh_list:

                mesh_path = Path(wkdir, "MESH", su2_def_mesh)
                config_dir_path = Path(wkdir, case_dir_name + "_" + su2_def_mesh.split(".")[0])
                config_dir_path.mkdir()
                cfg["MESH_FILENAME"] = mesh_path

                config_output_path = Path(wkdir, config_dir_path, CONFIG_CFD_NAME)
                cfg.write_file(config_output_path, overwrite=True)

    cpacs.save_cpacs(str(cpacs_out_path), overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
