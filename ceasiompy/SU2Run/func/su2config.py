"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function generate or modify SU2 configuration files

Python version: >=3.8

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
from ceasiompy.SU2Run.func.su2actuatordiskfile import (
    get_advanced_ratio,
    get_radial_stations,
    save_plots,
    thrust_calculator,
    write_actuator_disk_data,
    write_header,
)
from ceasiompy.SU2Run.func.su2utils import get_mesh_markers, get_su2_config_template
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonnames import (
    ACTUATOR_DISK_FILE_NAME,
    ACTUATOR_DISK_INLET_SUFFIX,
    ACTUATOR_DISK_OUTLET_SUFFIX,
    CONFIG_CFD_NAME,
    SU2_FORCES_BREAKDOWN_NAME,
)
from ceasiompy.utils.commonxpath import (
    GMSH_SYMMETRY_XPATH,
    PROP_XPATH,
    RANGE_XPATH,
    SU2_ACTUATOR_DISK_XPATH,
    SU2_AEROMAP_UID_XPATH,
    SU2_BC_FARFIELD_XPATH,
    SU2_BC_WALL_XPATH,
    SU2_CFL_NB_XPATH,
    SU2_CFL_ADAPT_XPATH,
    SU2_CFL_ADAPT_PARAM_DOWN_XPATH,
    SU2_CFL_ADAPT_PARAM_UP_XPATH,
    SU2_CFL_MAX_XPATH,
    SU2_CFL_MIN_XPATH,
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


def add_damping_derivatives(cfg, wkdir, case_dir_name, rotation_rate):
    """Add damping derivatives parameter to the config file and save them to their respective
    directory.

    Args:
        cfg (ConfigFile): ConfigFile object.
        wkdir (Path): Path to the working directory
        case_dir_name (str): Name of the case directory
        rotation_rate (float): Rotation rate that will be impose to calculate damping derivatives
    """

    cfg["GRID_MOVEMENT"] = "ROTATING_FRAME"

    cfg["ROTATION_RATE"] = f"{rotation_rate} 0.0 0.0"
    case_dir = Path(wkdir, f"{case_dir_name}_dp")
    case_dir.mkdir()
    cfg.write_file(Path(case_dir, CONFIG_CFD_NAME), overwrite=True)

    cfg["ROTATION_RATE"] = f"0.0 {rotation_rate} 0.0"
    case_dir = Path(wkdir, f"{case_dir_name}_dq")
    case_dir.mkdir()
    cfg.write_file(Path(case_dir, CONFIG_CFD_NAME), overwrite=True)

    cfg["ROTATION_RATE"] = f"0.0 0.0 {rotation_rate}"
    case_dir = Path(wkdir, f"{case_dir_name}_dr")
    case_dir.mkdir()
    cfg.write_file(Path(case_dir, CONFIG_CFD_NAME), overwrite=True)

    log.info("Damping derivatives cases directories has been created.")


def add_actuator_disk(cfg, cpacs, case_dir_path, actuator_disk_file, mesh_markers, alt, mach):
    """Add actuator disk parameter to the config file.

    Args:
        cfg (ConfigFile): ConfigFile object.
        cpacs (CPACS): CPACS object from cpacspy library
        case_dir_path (Path): Path object to the current case directory
        actuator_disk_file (Path): Path to the actuator disk file
        mesh_markers (dict): Dictionary containing all the mesh markers

    Returns:
        cfg (ConfigFile): ConfigFile object.
    """

    ad_inlet_marker = sorted(mesh_markers["actuator_disk_inlet"])
    ad_outlet_marker = sorted(mesh_markers["actuator_disk_outlet"])

    if "None" in ad_inlet_marker or "None" in ad_outlet_marker:
        return

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
        hub_radius = 0.0  # TODO: get correctly from CPACS

        rotor_xpath = cpacs.tixi.uIDGetXPath(rotor_uid)

        number_of_blades_xpath = (
            rotor_xpath + "/rotorHub/rotorBladeAttachments/rotorBladeAttachment/numberOfBlades"
        )
        number_of_blades = get_value_or_default(cpacs.tixi, number_of_blades_xpath, 3)

        # TODO: this is the nominal speed, how to get a speed which correspond to each flight cond.
        rotational_velocity_xpath = rotor_xpath + "/nominalRotationsPerMinute"
        rotational_velocity = (
            get_value_or_default(cpacs.tixi, rotational_velocity_xpath, 3000) / 60.0
        )

        rotor_uid_pos[rotor_uid] = (
            pos_x,
            pos_y,
            pos_z,
            radius,
            hub_radius,
            number_of_blades,
            rotational_velocity,
        )

    cfg["ACTDISK_DOUBLE_SURFACE"] = "YES"
    cfg["ACTDISK_TYPE"] = "VARIABLE_LOAD"
    cfg["ACTDISK_FILENAME"] = ACTUATOR_DISK_FILE_NAME
    cfg["MGLEVEL"] = 0  # Calculation diverges if multigrid is used with a disk actuator

    actdisk_markers = []

    f = open(actuator_disk_file, "w")
    f = write_header(f)

    for maker_inlet, marker_outlet in zip(ad_inlet_marker, ad_outlet_marker):
        inlet_uid = maker_inlet.split(ACTUATOR_DISK_INLET_SUFFIX)[0]
        outlet_uid = marker_outlet.split(ACTUATOR_DISK_OUTLET_SUFFIX)[0]

        if inlet_uid != outlet_uid:
            raise ValueError("The inlet and outlet markers of the actuator disk must be the same.")

        if "_mirrored" in maker_inlet:
            uid = inlet_uid.split("_mirrored")[0]
            sym = -1
        else:
            uid = inlet_uid
            sym = 1

        center = []
        center.append(round(rotor_uid_pos[uid][0], 5))
        center.append(round(sym * rotor_uid_pos[uid][1], 5))
        center.append(round(rotor_uid_pos[uid][2], 5))

        axis = (1.0, 0.0, 0.0)  # TODO: get the axis by applying the rotation matrix
        radius = round(rotor_uid_pos[uid][3], 5)
        hub_radius = round(rotor_uid_pos[uid][4], 5)
        number_of_blades = round(rotor_uid_pos[uid][5], 5)
        rotational_velocity = round(rotor_uid_pos[uid][6], 5)

        actdisk_markers.append(maker_inlet)
        actdisk_markers.append(marker_outlet)
        actdisk_markers.append(str(center[0]))
        actdisk_markers.append(str(center[1]))
        actdisk_markers.append(str(center[2]))
        actdisk_markers.append(str(center[0]))
        actdisk_markers.append(str(center[1]))
        actdisk_markers.append(str(center[2]))

        Atm = Atmosphere(alt)
        free_stream_velocity = mach * Atm.speed_of_sound[0]

        radial_stations = get_radial_stations(radius, hub_radius)
        advanced_ratio = get_advanced_ratio(free_stream_velocity, rotational_velocity, radius)

        prandtl_correction_xpath = PROP_XPATH + "/propeller/blade/loss"
        prandtl_correction = get_value_or_default(cpacs.tixi, prandtl_correction_xpath, True)

        thrust_xpath = PROP_XPATH + "/propeller/thrust"
        thrust = get_value_or_default(cpacs.tixi, thrust_xpath, 3000)
        total_thrust_coefficient = float(
            thrust / (Atm.density * rotational_velocity**2 * (radius * 2) ** 4)
        )

        (
            radial_thrust_coefs,
            radial_power_coefs,
            non_dimensional_radius,
            optimal_axial_interference_factor,
            optimal_rotational_interference_factor,
            prandtl_correction_values,
        ) = thrust_calculator(
            radial_stations,
            total_thrust_coefficient,
            radius,
            free_stream_velocity,
            prandtl_correction,
            number_of_blades,
            rotational_velocity,
        )

        save_plots(
            radial_stations,
            radial_thrust_coefs,
            radial_power_coefs,
            non_dimensional_radius,
            optimal_axial_interference_factor,
            optimal_rotational_interference_factor,
            prandtl_correction_values,
            case_dir_path,
            inlet_uid,
        )

        f = write_actuator_disk_data(
            file=f,
            inlet_marker=maker_inlet,
            outlet_marker=marker_outlet,
            center=center,
            axis=axis,
            radius=radius,
            advanced_ratio=advanced_ratio,
            radial_stations=radial_stations,
            radial_thrust_coefs=radial_thrust_coefs,
            radial_power_coefs=radial_power_coefs,
        )

    cfg["MARKER_ACTDISK"] = " (" + ", ".join(actdisk_markers) + " )"

    f.close()


def generate_su2_cfd_config(cpacs_path, cpacs_out_path, wkdir):
    """Function to create SU2 config file.

    Function 'generate_su2_cfd_config' reads data in the CPACS file and generate configuration
    files for one or multiple flight conditions (alt,mach,aoa,aos)

    Source:
        * SU2 config template: https://github.com/su2code/SU2/blob/master/config_template.cfg

    Args:
        cpacs_path (Path): Path to CPACS file
        cpacs_out_path (Path):Path to CPACS output file
        wkdir (Path): Path to the working directory

    """

    cpacs = CPACS(cpacs_path)

    su2_mesh = Path(get_value(cpacs.tixi, SU2MESH_XPATH))
    if not su2_mesh.is_file():
        raise FileNotFoundError(f"SU2 mesh file {su2_mesh} not found")

    mesh_markers = get_mesh_markers(su2_mesh)

    create_branch(cpacs.tixi, SU2_BC_WALL_XPATH)
    bc_wall_str = ";".join(mesh_markers["wall"])
    cpacs.tixi.updateTextElement(SU2_BC_WALL_XPATH, bc_wall_str)

    create_branch(cpacs.tixi, SU2_BC_FARFIELD_XPATH)
    bc_farfiled_str = ";".join(mesh_markers["engine_intake"] + mesh_markers["engine_exhaust"])
    cpacs.tixi.updateTextElement(SU2_BC_FARFIELD_XPATH, bc_farfiled_str)

    create_branch(cpacs.tixi, SU2_ACTUATOR_DISK_XPATH)
    bc_actuator_disk_str = ";".join(
        mesh_markers["actuator_disk_inlet"] + mesh_markers["actuator_disk_outlet"]
    )
    cpacs.tixi.updateTextElement(SU2_ACTUATOR_DISK_XPATH, bc_actuator_disk_str)

    fixed_cl = get_value_or_default(cpacs.tixi, SU2_FIXED_CL_XPATH, "NO")
    target_cl = get_value_or_default(cpacs.tixi, SU2_TARGET_CL_XPATH, 1.0)

    if fixed_cl == "NO":
        # Get the first aeroMap as default one or create automatically one
        aeromap_list = cpacs.get_aeromap_uid_list()

        if aeromap_list:
            aeromap_default = aeromap_list[0]
            log.info(f'The aeromap is {aeromap_default}')

            aeromap_uid = get_value_or_default(cpacs.tixi, SU2_AEROMAP_UID_XPATH, aeromap_default)

            activate_aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)
            alt_list = activate_aeromap.get("altitude").tolist()
            mach_list = activate_aeromap.get("machNumber").tolist()
            aoa_list = activate_aeromap.get("angleOfAttack").tolist()
            aos_list = activate_aeromap.get("angleOfSideslip").tolist()

        else:
            default_aeromap = cpacs.create_aeromap("DefaultAeromap")
            default_aeromap.description = "AeroMap created automatically"

            mach = get_value_or_default(cpacs.tixi, RANGE_XPATH + "/cruiseMach", 0.3)
            alt = get_value_or_default(cpacs.tixi, RANGE_XPATH + "/cruiseAltitude", 10000)

            default_aeromap.add_row(alt=alt, mach=mach, aos=0.0, aoa=0.0)
            default_aeromap.save()

            alt_list = [alt]
            mach_list = [mach]
            aoa_list = [0.0]
            aos_list = [0.0]

            aeromap_uid = get_value_or_default(cpacs.tixi, SU2_AEROMAP_UID_XPATH, "DefaultAeromap")
            log.info(f"{aeromap_uid} has been created")

    else:  # if fixed_cl == 'YES':
        log.info("Configuration file for fixed CL calculation will be created.")

        fixed_cl_aeromap = cpacs.create_aeromap("aeroMap_fixedCL_SU2")
        fixed_cl_aeromap.description = f"AeroMap created for SU2 fixed CL value of {target_cl}"

        mach = get_value_or_default(cpacs.tixi, RANGE_XPATH + "/cruiseMach", 0.78)
        alt = get_value_or_default(cpacs.tixi, RANGE_XPATH + "/cruiseAltitude", 12000)

        fixed_cl_aeromap.add_row(alt=alt, mach=mach, aos=0.0, aoa=0.0)
        fixed_cl_aeromap.save()

        alt_list = [alt]
        mach_list = [mach]
        aoa_list = [0.0]
        aos_list = [0.0]

    cfg = ConfigFile(get_su2_config_template())

    # Check if symmetry plane is defined (Default: False)
    sym_factor = 1.0
    if get_value_or_default(cpacs.tixi, GMSH_SYMMETRY_XPATH, False):
        log.info("Symmetry plane is defined. The reference area will be divided by 2.")
        sym_factor = 2.0

    # General parameters
    cfg["RESTART_SOL"] = "NO"
    cfg["REF_LENGTH"] = cpacs.aircraft.ref_length
    cfg["REF_AREA"] = cpacs.aircraft.ref_area / sym_factor
    cfg["REF_ORIGIN_MOMENT_X"] = cpacs.aircraft.ref_point_x
    cfg["REF_ORIGIN_MOMENT_Y"] = cpacs.aircraft.ref_point_y
    cfg["REF_ORIGIN_MOMENT_Z"] = cpacs.aircraft.ref_point_z

    # Settings

    cfl_down = get_value_or_default(cpacs.tixi, SU2_CFL_ADAPT_PARAM_DOWN_XPATH, 0.5)
    cfl_up = get_value_or_default(cpacs.tixi, SU2_CFL_ADAPT_PARAM_UP_XPATH, 1.5)
    cfl_min = get_value_or_default(cpacs.tixi, SU2_CFL_MIN_XPATH, 0.5)
    cfl_max = get_value_or_default(cpacs.tixi, SU2_CFL_MAX_XPATH, 100)

    if get_value_or_default(cpacs.tixi, SU2_CFL_ADAPT_XPATH, True):
        cfg["CFL_ADAPT"] = "YES"

    else:
        cfg["CFL_ADAPT"] = "NO"

    cfg["INNER_ITER"] = int(get_value_or_default(cpacs.tixi, SU2_MAX_ITER_XPATH, 200))
    cfg["CFL_NUMBER"] = get_value_or_default(cpacs.tixi, SU2_CFL_NB_XPATH, 1.0)
    cfg["CFL_ADAPT_PARAM"] = f"( {cfl_down}, {cfl_up}, {cfl_min}, {cfl_max} )"
    cfg["MGLEVEL"] = int(get_value_or_default(cpacs.tixi, SU2_MG_LEVEL_XPATH, 3))

    # Fixed CL mode (AOA will not be taken into account)
    cfg["FIXED_CL_MODE"] = fixed_cl
    cfg["TARGET_CL"] = target_cl
    cfg["DCL_DALPHA"] = "0.1"
    cfg["UPDATE_AOA_ITER_LIMIT"] = "50"
    cfg["ITER_DCL_DALPHA"] = "80"

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

    # Output
    cfg["WRT_FORCES_BREAKDOWN"] = "YES"
    cfg["BREAKDOWN_FILENAME"] = SU2_FORCES_BREAKDOWN_NAME
    cfg["OUTPUT_FILES"] = "(RESTART, PARAVIEW, SURFACE_PARAVIEW)"
    cfg["HISTORY_OUTPUT"] = "(INNER_ITER, RMS_RES, AERO_COEFF)"

    # Parameters which will vary for the different cases (alt,mach,aoa,aos)
    for case_nb in range(len(alt_list)):
        cfg["MESH_FILENAME"] = str(su2_mesh)

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

        if get_value_or_default(cpacs.tixi, SU2_ACTUATOR_DISK_XPATH, False):
            actuator_disk_file = Path(wkdir, ACTUATOR_DISK_FILE_NAME)
            add_actuator_disk(
                cfg, cpacs, case_dir_path, actuator_disk_file, mesh_markers, alt, mach
            )

            if actuator_disk_file.exists():
                case_actuator_disk_file = Path(case_dir_path, ACTUATOR_DISK_FILE_NAME)
                copyfile(actuator_disk_file, case_actuator_disk_file)

                bc_wall_str = (
                    "("
                    + ",".join(
                        mesh_markers["wall"]
                        + mesh_markers["actuator_disk_inlet"]
                        + mesh_markers["actuator_disk_outlet"]
                    )
                    + ")"
                )

                cfg["MARKER_PLOTTING"] = bc_wall_str
                cfg["MARKER_MONITORING"] = bc_wall_str

        config_output_path = Path(case_dir_path, CONFIG_CFD_NAME)
        cfg.write_file(config_output_path, overwrite=True)

        if get_value_or_default(cpacs.tixi, SU2_DAMPING_DER_XPATH, False):
            rotation_rate = get_value_or_default(cpacs.tixi, SU2_ROTATION_RATE_XPATH, 1.0)
            add_damping_derivatives(cfg, wkdir, case_dir_name, rotation_rate)

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

                cfg.write_file(Path(config_dir_path, CONFIG_CFD_NAME), overwrite=True)

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
