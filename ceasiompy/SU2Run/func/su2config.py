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
from shutil import copyfile

from ambiance import Atmosphere
from ceasiompy.SU2Run.func.su2actuatordiskfile import write_actuator_disk_data, write_header
from ceasiompy.SU2Run.func.su2utils import get_mesh_markers, get_su2_config_template
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonnames import (
    ACTUATOR_DISK_FILE_NAME,
    CONFIG_CFD_NAME,
    SU2_FORCES_BREAKDOWN_NAME,
)
from ceasiompy.utils.commonxpath import (
    GMSH_SYMMETRY_XPATH,
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

    cpacs = CPACS(cpacs_path)

    # Get the SU2 Mesh
    su2_mesh_path = Path(get_value(cpacs.tixi, SU2MESH_XPATH))
    if not su2_mesh_path.is_file():
        raise FileNotFoundError(f"SU2 mesh file {su2_mesh_path} not found")

    # Get Mesh Marker and save them in the CPACS file
    mesh_markers = get_mesh_markers(su2_mesh_path)

    create_branch(cpacs.tixi, SU2_BC_WALL_XPATH)
    bc_wall_str = ";".join(mesh_markers["wall"])
    cpacs.tixi.updateTextElement(SU2_BC_WALL_XPATH, bc_wall_str)

    create_branch(cpacs.tixi, SU2_BC_FARFIELD_XPATH)
    bc_farfiled_str = ";".join(mesh_markers["engine_intake"] + mesh_markers["engine_exhaust"])
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

    # Check if symmetry plane is defined (Default: False)
    sym_factor = 1.0
    if get_value_or_default(cpacs.tixi, GMSH_SYMMETRY_XPATH, False):
        log.info("Symmetry plane is defined. The reference area will be divided by 2.")
        sym_factor = 2.0

    # General parmeters
    cfg["RESTART_SOL"] = "NO"
    cfg["REF_LENGTH"] = cpacs.aircraft.ref_length
    cfg["REF_AREA"] = cpacs.aircraft.ref_area / sym_factor
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
    bc_wall_str = f"( {','.join(mesh_markers['wall'])} )"
    cfg["MARKER_EULER"] = bc_wall_str
    farfield_bc = (
        mesh_markers["farfield"] + mesh_markers["engine_intake"] + mesh_markers["engine_exhaust"]
    )
    cfg["MARKER_FAR"] = f"( {','.join(farfield_bc)} )"
    cfg["MARKER_SYM"] = f"( {','.join(mesh_markers['symmetry'])} )"
    cfg["MARKER_PLOTTING"] = bc_wall_str
    cfg["MARKER_MONITORING"] = bc_wall_str
    cfg["MARKER_MOVING"] = "( NONE )"  # TODO: when do we need to define MARKER_MOVING?
    cfg["DV_MARKER"] = bc_wall_str

    # Actuator disk (TODO: create a subfunction)
    ad_inlet_marker = sorted(mesh_markers["actuator_disk_inlet"])
    ad_outlet_marker = sorted(mesh_markers["actuator_disk_outlet"])
    actuator_disk_file = Path(wkdir, ACTUATOR_DISK_FILE_NAME)

    if "None" not in ad_inlet_marker and "None" not in ad_outlet_marker:

        if len(ad_inlet_marker) != len(ad_outlet_marker):
            raise ValueError(
                "The number of inlet and outlet markers of the actuator disk must be the same."
            )

        # Get rotorcraft configuration (propeller)
        try:
            rotorcraft_config = cpacs.rotorcraft.configuration
        except AttributeError:
            raise ValueError(
                "The actuator disk is defined but no rotorcraft configuration is defined in "
                "the CPACS file."
            )

        rotor_uid_pos = {}
        for i in range(1, rotorcraft_config.get_rotor_count() + 1):

            rotor = rotorcraft_config.get_rotor(i)

            rotor_uid = rotor.get_uid()
            pos_x = rotor.get_translation().x
            pos_y = rotor.get_translation().y
            pos_z = rotor.get_translation().z
            radius = rotor.get_radius()

            rotor_uid_pos[rotor_uid] = (pos_x, pos_y, pos_z, radius)

        cfg["ACTDISK_DOUBLE_SURFACE"] = "YES"
        cfg["ACTDISK_TYPE"] = "VARIABLE_LOAD"
        cfg["ACTDISK_FILENAME"] = ACTUATOR_DISK_FILE_NAME

        # Multi grid diverges when there is a disk actuator
        cfg["MGLEVEL"] = 0

        actdisk_markers = []

        f = open(actuator_disk_file, "w")
        f = write_header(f)

        for maker_inlet, marker_outlet in zip(ad_inlet_marker, ad_outlet_marker):
            inlet_uid = maker_inlet.split("_AD_Inlet")[0]
            outlet_uid = marker_outlet.split("_AD_Outlet")[0]

            if inlet_uid != outlet_uid:
                raise ValueError(
                    "The inlet and outlet markers of the actuator disk must be the same."
                )

            if "_mirrored" in maker_inlet:
                uid = inlet_uid.split("_mirrored")[0]
                sym = -1
            else:
                uid = inlet_uid
                sym = 1

            center = [] * 3
            center.append(round(rotor_uid_pos[uid][0], 5))
            center.append(round(sym * rotor_uid_pos[uid][1], 5))
            center.append(round(rotor_uid_pos[uid][2], 5))

            # TODO: get the axis by applying the rotation matrix
            axis = (1.0, 0.0, 0.0)
            radius = round(rotor_uid_pos[uid][3], 5)

            actdisk_markers.append(maker_inlet)
            actdisk_markers.append(marker_outlet)
            actdisk_markers.append(str(center[0]))
            actdisk_markers.append(str(center[1]))
            actdisk_markers.append(str(center[2]))
            actdisk_markers.append(str(center[0]))
            actdisk_markers.append(str(center[1]))
            actdisk_markers.append(str(center[2]))

            f = write_actuator_disk_data(f, maker_inlet, marker_outlet, center, axis, radius)

        cfg["MARKER_ACTDISK"] = " (" + ", ".join(actdisk_markers) + " )"

        f.close()

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

        case_dir_name = (
            f"Case{str(case_nb).zfill(2)}_alt{alt}_mach{round(mach, 2)}"
            f"_aoa{round(aoa, 1)}_aos{round(aos, 1)}"
        )

        case_dir_path = Path(wkdir, case_dir_name)
        if not case_dir_path.exists():
            case_dir_path.mkdir()

        config_output_path = Path(case_dir_path, CONFIG_CFD_NAME)
        cfg.write_file(config_output_path, overwrite=True)

        if actuator_disk_file.exists():
            case_actuator_disk_file = Path(case_dir_path, ACTUATOR_DISK_FILE_NAME)
            copyfile(actuator_disk_file, case_actuator_disk_file)

        # Damping derivatives  (TODO: create a subfunctions)
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

        # Control surfaces deflections (TODO: create a subfunctions)
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

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    log.info("Nothing to execute!")
