"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function generate or modify SU2 configuration files

Python version: >=3.8

| Author: Aidan Jungo
| Creation: 2020-02-24
| Modified: Leon Deligny
| Date: 24-Feb-2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import numpy as np

from shutil import copyfile
from ceasiompy.SU2Run.func.plot import save_plots
from ceasiompy.CPACS2GMSH.func.mesh_sizing import wings_size
from ceasiompy.utils.geometryfunctions import get_leading_edge
from ceasiompy.SU2Run.func.dotderivatives import load_parameters

from ceasiompy.utils.ceasiompyutils import (
    bool_,
    get_aeromap_conditions,
)

from cpacspy.cpacsfunctions import (
    get_value,
    open_tigl,
    create_branch,
    get_value_or_default,
)
from ceasiompy.SU2Run.func.actuatordiskfile import (
    write_header,
    thrust_calculator,
    get_advanced_ratio,
    get_radial_stations,
    write_actuator_disk_data,
)
from ceasiompy.SU2Run.func.utils import (
    su2_format,
    validate_file,
    get_su2_cfg_tpl,
    get_mesh_markers,
    su2_mesh_list_from_db,
    check_control_surface,
    add_damping_derivatives,
    get_surface_pitching_omega,
)

from pathlib import Path
from ambiance import Atmosphere
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3
from cpacspy.rotorcraft import Rotorcraft
from ceasiompy.utils.configfiles import ConfigFile

from typing import (
    Dict,
    List,
    Tuple,
)

from ceasiompy import log
from ceasiompy.SU2Run import CONTROL_SURFACE_LIST

from ceasiompy.utils.commonnames import (
    CONFIG_CFD_NAME,
    ACTUATOR_DISK_FILE_NAME,
    SU2_FORCES_BREAKDOWN_NAME,
    ACTUATOR_DISK_INLET_SUFFIX,
    ACTUATOR_DISK_OUTLET_SUFFIX,

)
from ceasiompy.utils.commonxpath import (
    SU2MESH_XPATH,
    SU2_CFL_NB_XPATH,
    ENGINE_TYPE_XPATH,
    SU2_BC_WALL_XPATH,
    SU2_CFL_MAX_XPATH,
    SU2_CFL_MIN_XPATH,
    SU2_FIXED_CL_XPATH,
    SU2_MAX_ITER_XPATH,
    SU2_MG_LEVEL_XPATH,
    SU2_CFL_ADAPT_XPATH,
    SU2_TARGET_CL_XPATH,
    SU2_DAMPING_DER_XPATH,
    SU2_AEROMAP_UID_XPATH,
    SU2_BC_FARFIELD_XPATH,
    PROPELLER_THRUST_XPATH,
    SU2_ACTUATOR_DISK_XPATH,
    SU2_ROTATION_RATE_XPATH,
    SU2_CEASIOMPYDATA_XPATH,
    PROPELLER_BLADE_LOSS_XPATH,
    SU2_CFL_ADAPT_PARAM_UP_XPATH,
    SU2_CFL_ADAPT_PARAM_DOWN_XPATH,
    ENGINE_BC_PRESSUREOUTLET_XPATH,
    ENGINE_BC_TEMPERATUREOUTLET_XPATH,
    SU2_DYNAMICDERIVATIVES_INNERITER_XPATH,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def add_actuator_disk(
    cfg: ConfigFile,
    tixi: Tixi3,
    case_dir_path: Path,
    actuator_disk_file: Path,
    mesh_markers: Dict,
    alt: float,
    mach: float
) -> None:
    """
    Add actuator disk parameter to the config file.

    Args:
        cfg (ConfigFile): ConfigFile object.
        cpacs (CPACS): CPACS object from cpacspy library.
        case_dir_path (Path): Path object to the current case directory.
        actuator_disk_file (Path): Path to the actuator disk file.
        mesh_markers (dict): Dictionary containing all the mesh markers.
        alt (float): Altitude in meters.
        mach (float): Mach number.

    """

    # Access markers
    ad_inlet_marker = sorted(mesh_markers["actuator_disk_inlet"])
    ad_outlet_marker = sorted(mesh_markers["actuator_disk_outlet"])

    if "None" in ad_inlet_marker or "None" in ad_outlet_marker:
        # No markers to add so return cfg
        return cfg

    if len(ad_inlet_marker) != len(ad_outlet_marker):
        raise ValueError(
            "The number of inlet and outlet markers of the actuator disk must be the same."
        )

    # Get rotorcraft configuration (propeller)
    try:
        tigl_rotor = open_tigl(tixi, rotorcraft=True)
        rotorcraft = Rotorcraft(tixi, tigl_rotor)
        rotorcraft_config = rotorcraft.configuration
    except AttributeError:
        raise ValueError(
            "The actuator disk is defined but no rotorcraft "
            "configuration is defined in the CPACS file."
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

        rotor_xpath = tixi.uIDGetXPath(rotor_uid)

        number_of_blades_xpath = (
            rotor_xpath + "/rotorHub/rotorBladeAttachments/rotorBladeAttachment/numberOfBlades"
        )
        number_of_blades = get_value_or_default(tixi, number_of_blades_xpath, 3)

        # TODO: this is the nominal speed, how to get a speed which correspond to
        # each flight condition
        rotational_velocity_xpath = rotor_xpath + "/nominalRotationsPerMinute"
        rotational_velocity = (
            get_value_or_default(tixi, rotational_velocity_xpath, 3000) / 60.0
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

        actdisk_markers.extend([
            maker_inlet, marker_outlet,
            str(center[0]), str(center[1]), str(center[2]),
            str(center[0]), str(center[1]), str(center[2]),
        ])

        Atm = Atmosphere(alt)
        free_stream_velocity = mach * Atm.speed_of_sound[0]

        radial_stations = get_radial_stations(radius, hub_radius)
        advanced_ratio = get_advanced_ratio(free_stream_velocity, rotational_velocity, radius)

        prandtl_correction = bool_(get_value(tixi, PROPELLER_BLADE_LOSS_XPATH))

        thrust = get_value(tixi, PROPELLER_THRUST_XPATH)
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
            radial_stations=radial_stations,
            radial_thrust_coefs=radial_thrust_coefs,
            radial_power_coefs=radial_power_coefs,
            non_dimensional_radius=non_dimensional_radius,
            optimal_axial_interference_factor=optimal_axial_interference_factor,
            optimal_rotational_interference_factor=optimal_rotational_interference_factor,
            prandtl_correction_values=prandtl_correction_values,
            case_dir_path=case_dir_path,
            propeller_uid=inlet_uid,
        )

        write_actuator_disk_data(
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

    cfg["MARKER_ACTDISK"] = su2_format(", ".join(actdisk_markers))
    f.close()


def add_thermodata(
    cfg: ConfigFile,
    tixi: Tixi3,
    alt: float,
    case_nb: int,
    alt_list: List,
) -> None:
    if tixi.checkElement(ENGINE_TYPE_XPATH):
        log.info("Adding engine BC to the SU2 config file.")
        engine_type = get_value(tixi, ENGINE_TYPE_XPATH)
        log.info(f"Engine type {engine_type}.")

        alt = alt_list[case_nb]
        Atm = Atmosphere(alt)
        tot_temp_in = Atm.temperature[0]
        tot_pressure_in = Atm.pressure[0]

        if len(alt_list) > 1:
            tot_temp_out = get_value(tixi, ENGINE_BC_TEMPERATUREOUTLET_XPATH).split(";")
            tot_pressure_out = get_value(tixi, ENGINE_BC_PRESSUREOUTLET_XPATH).split(";")
            tot_temp_out = tot_temp_out[case_nb]
            tot_pressure_out = tot_pressure_out[case_nb]
        else:
            tot_temp_out = get_value(tixi, ENGINE_BC_TEMPERATUREOUTLET_XPATH)
            tot_pressure_out = get_value(tixi, ENGINE_BC_PRESSUREOUTLET_XPATH)
        cfg["INLET_TYPE"] = "TOTAL_CONDITIONS"
        cfg["MARKER_INLET"] = su2_format(
            f"INLET_ENGINE, {tot_temp_in}, {tot_pressure_in}, {1},{0},{0}, "
            f"OUTLET_ENGINE, {tot_temp_out}, {tot_pressure_out}, {1},{0},{0}"
        )
    else:
        log.warning(f"No engines found at xPath {ENGINE_TYPE_XPATH}.")


def add_reynolds_number(alt: float, mach: float, cfg: ConfigFile, cpacs_path: Path) -> None:
    """
    In case of RANS simulation, compute and add Reynolds number to configuration file cfg.

    Args:
        alt (float): Altitude.
        mach (float): Mach number.
        cfg (ConfigFile): Configuration file.
        cpacs_path (Path): CPACS path.

    """

    Atm = Atmosphere(alt)

    # Get speed from Mach Number
    speed = mach * Atm.speed_of_sound[0]

    ref_chord = wings_size(cpacs_path)[0] / 0.15
    log.info(f"Reference chord is {ref_chord}.")

    # Reynolds number based on the mean chord
    reynolds = int(ref_chord * speed / Atm.kinematic_viscosity[0])
    cfg["REYNOLDS_NUMBER"] = reynolds
    log.info(f"Reynolds number is {reynolds}.")


def add_case_data(
    tixi: Tixi3,
    wkdir: Path,
    cfg: ConfigFile,
    cpacs_path: Path,
    rans: bool,
    mesh_markers: Dict,
    case_dir_name: str,
    mach: float,
    alt: float,
    case_nb: int,
    alt_list: List,
    ctrlsurf: str,
) -> None:
    """
    Adds case-specific data to the SU2 configuration file and sets up the case directory.

    Args:
        cpacs (CPACS): CPACS object containing the CPACS data.
        wkdir (Path): Working directory path.
        cfg (ConfigFile): SU2 configuration file object.
        cpacs_path (Path): Path to the CPACS file.
        rans (bool): Flag indicating if RANS (Reynolds-Averaged Navier-Stokes) is used.
        mesh_markers (Dict): Dictionary containing mesh markers.
        case_dir_name (str): Name of the case directory.
        mach (float): Mach number for the case.
        alt (float): Altitude for the case.
        case_nb (int): Case number.
        alt_list (List): List of altitudes.

    """

    add_thermodata(cfg, tixi, alt, case_nb, alt_list)

    if rans:
        add_reynolds_number(alt, mach, cfg, cpacs_path)

    case_dir_path = Path(wkdir, case_dir_name)
    if not case_dir_path.exists():
        case_dir_path.mkdir()

    if bool_(get_value(tixi, SU2_ACTUATOR_DISK_XPATH)):
        actuator_disk_file = Path(wkdir, ACTUATOR_DISK_FILE_NAME)
        add_actuator_disk(
            cfg=cfg,
            tixi=tixi,
            case_dir_path=case_dir_path,
            actuator_disk_file=actuator_disk_file,
            mesh_markers=mesh_markers,
            alt=alt,
            mach=mach,
        )

        if actuator_disk_file.exists():
            case_actuator_disk_file = Path(case_dir_path, ACTUATOR_DISK_FILE_NAME)
            copyfile(actuator_disk_file, case_actuator_disk_file)

            bc_wall_str = su2_format(
                ",".join(mesh_markers["wall"] + mesh_markers["actuator_disk_inlet"]
                         + mesh_markers["actuator_disk_outlet"])
            )

            cfg["MARKER_PLOTTING"] = bc_wall_str
            cfg["MARKER_MONITORING"] = bc_wall_str

    if bool_(get_value(tixi, SU2_DAMPING_DER_XPATH)):
        rotation_rate = get_value(tixi, SU2_ROTATION_RATE_XPATH)
        add_damping_derivatives(cfg, wkdir, case_dir_name, rotation_rate)

    ctrlsurf_case_dir_path = Path(case_dir_path, ctrlsurf)
    if not ctrlsurf_case_dir_path.exists():
        ctrlsurf_case_dir_path.mkdir()

    config_output_path = Path(ctrlsurf_case_dir_path, CONFIG_CFD_NAME)
    cfg.write_file(config_output_path, overwrite=True)


def configure_cfd_environment(
    cpacs: CPACS,
    wkdir: Path,
    cfg: ConfigFile,
    su2_mesh_path: Path,
    rans: bool,
    dyn_stab: bool,
    mesh_markers: Dict,
    ctrlsurf: str,
) -> None:
    """
    Configure cfd environment for SU2 simulation.

    Args:
        cpacs (CPACS): CPACS file.
        wkdir (Path): Working directory (SU2).
        cfg (ConfigFile): Configuration file to modify.
        su2_mesh (Path): Path to the SU2 mesh file.
        rans (bool): True if RANS simulation.
        mesh_markers (Dict): Dictionary of the mesh markers found in the SU2 mesh file.

    """
    tixi = cpacs.tixi
    cpacs_path = cpacs.cpacs_file

    alt_list, mach_list, aoa_list, aos_list = get_aeromap_conditions(cpacs, SU2_AEROMAP_UID_XPATH)

    cfg["MARKER_MOVING"] = su2_format("NONE")
    cfg["MESH_FILENAME"] = str(su2_mesh_path)

    mach_len = len(mach_list)

    # Parameters which will vary for the different cases (alt, mach, aoa, aos)
    for case_nb in range(mach_len):

        alt = alt_list[case_nb]
        mach = mach_list[case_nb]

        if dyn_stab:
            aoa = 0.0
            aos = 0.0
        else:
            aoa = aoa_list[case_nb]
            aos = aos_list[case_nb]

        Atm = Atmosphere(alt)

        cfg["MACH_NUMBER"] = mach
        cfg["AOA"] = aoa
        cfg["SIDESLIP_ANGLE"] = aos
        cfg["FREESTREAM_PRESSURE"] = Atm.pressure[0]
        cfg["FREESTREAM_TEMPERATURE"] = Atm.temperature[0]

        if dyn_stab:
            markers_len = len(mesh_markers["wall"])

            for oscillation_type in ["alpha", "beta"]:
                # Center of gravity
                x1, _, z1, c = get_leading_edge(tixi)
                x_cg = x1 + (c / 4)

                # Load parameters
                a, omega, n, _ = load_parameters(tixi)

                time_step = (2 / (n - 1)) * np.pi / omega

                #######################
                # UNSTEADY SIMULATION #
                #######################

                cfg["TIME_DOMAIN"] = "YES"
                cfg["TIME_MARCHING"] = "DUAL_TIME_STEPPING-2ND_ORDER"

                cfg["TIME_STEP"] = str(time_step)

                cfg["MAX_TIME"] = str(2 * np.pi / omega)

                inner_iter = get_value(tixi, SU2_DYNAMICDERIVATIVES_INNERITER_XPATH)

                # Maximum number of inner iterations
                cfg["INNER_ITER"] = str(inner_iter)

                # Starting direct solver iteration for the unsteady adjoint
                cfg["UNST_ADJOINT_ITER"] = "0"

                # Frequencies corresponding to the list in OUTPUT_FILES
                cfg["OUTPUT_WRT_FREQ"] = "1"

                ##########################
                # CONVERGENCE PARAMETERS #
                ##########################

                # Maximum number of time iterations
                cfg["TIME_ITER"] = str(2 * np.pi / omega)

                cfg["CONV_RESIDUAL_MINVAL"] = "-8"
                cfg["CONV_STARTITER"] = "0"
                cfg["CONV_CAUCHY_ELEMS"] = "2"  # "100"
                cfg["CONV_CAUCHY_EPS"] = "1E-10"

                ###########################
                # DYNAMIC MESH DEFINITION #
                ###########################

                surf_omega = get_surface_pitching_omega(oscillation_type, omega)

                cfg["SURFACE_MOVEMENT"] = su2_format(("DEFORMING " * markers_len))
                cfg["MARKER_MOVING"] = su2_format(",".join(mesh_markers["wall"]))
                cfg["SURFACE_MOTION_ORIGIN"] = su2_format((f"{x_cg} 0.0 {z1} " * markers_len))
                cfg["SURFACE_PITCHING_OMEGA"] = su2_format((surf_omega * markers_len))
                cfg["SURFACE_PITCHING_AMPL"] = su2_format((f"{a} {a} {a} " * markers_len))

                case_dir_name = (
                    f"Case{str(case_nb + mach_len).zfill(2)}"
                    f"_alt{round(alt, 2)}"
                    f"_mach{round(mach, 2)}"
                    f"_angle{oscillation_type}_dynstab"
                )

                add_case_data(
                    tixi=tixi,
                    wkdir=wkdir,
                    cfg=cfg,
                    cpacs_path=cpacs_path,
                    rans=rans,
                    mesh_markers=mesh_markers,
                    case_dir_name=case_dir_name,
                    mach=mach,
                    alt=alt,
                    case_nb=case_nb,
                    alt_list=alt_list,
                    ctrlsurf=ctrlsurf,
                )

        else:
            case_dir_name = (
                f"Case{str(case_nb).zfill(2)}_alt{alt}_mach{round(mach, 2)}"
                f"_aoa{round(aoa, 1)}_aos{round(aos, 1)}"
            )

            add_case_data(
                tixi=tixi,
                wkdir=wkdir,
                cfg=cfg,
                cpacs_path=cpacs_path,
                rans=rans,
                mesh_markers=mesh_markers,
                case_dir_name=case_dir_name,
                mach=mach,
                alt=alt,
                case_nb=case_nb,
                alt_list=alt_list,
                ctrlsurf=ctrlsurf,
            )


def define_markers(tixi: Tixi3, su2_mesh_path: Path) -> Dict:
    """
    Define markers in CPACS file.
    We assume that among all imported meshes,
    there will be the same markers.

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.
        su2_mesh_path (Path): Path to a mesh.

    """
    mesh_markers = get_mesh_markers(su2_mesh_path)
    for key, value in mesh_markers.items():
        mesh_markers[key] = [str(item).replace(" ", "") for item in value]

    # Generate wall
    create_branch(tixi, SU2_BC_WALL_XPATH)
    bc_wall_str = ";".join(mesh_markers["wall"])
    tixi.updateTextElement(SU2_BC_WALL_XPATH, bc_wall_str)

    # Generate Farfield
    create_branch(tixi, SU2_BC_FARFIELD_XPATH)
    bc_farfiled_str = ";".join(
        mesh_markers["engine_intake"]
        + mesh_markers["engine_exhaust"]
    )
    tixi.updateTextElement(SU2_BC_FARFIELD_XPATH, bc_farfiled_str)

    # Generate Actuator disk
    create_branch(tixi, SU2_ACTUATOR_DISK_XPATH)
    bc_actuator_disk_str = ";".join(
        mesh_markers["actuator_disk_inlet"]
        + mesh_markers["actuator_disk_outlet"]
    )
    tixi.updateTextElement(SU2_ACTUATOR_DISK_XPATH, bc_actuator_disk_str)

    return mesh_markers


def load_su2_mesh_paths(tixi: Tixi3, results_dir: Path) -> Tuple[List[Path], List[Path]]:
    """
    Retrieve su2 mesh file data and paths.
    TODO: Add Args and Returns

    """

    # Not using ceasiompy.db data
    if not bool_(get_value(tixi, SU2_CEASIOMPYDATA_XPATH)):

        if tixi.checkElement(SU2MESH_XPATH):
            tixi_su2_mesh_paths = get_value(tixi, SU2MESH_XPATH)
            su2_mesh_paths = [Path(x) for x in str(tixi_su2_mesh_paths).split(';')]

    # Using ceasiompy.db data
    else:
        su2_mesh_list = su2_mesh_list_from_db(tixi)

        # Upload files to the working directory and update paths
        su2_mesh_paths = []
        for (su2_mesh, aircraft_name, deformation, angle) in su2_mesh_list:
            su2_path = results_dir / f"{aircraft_name}_{deformation}_{angle}.su2"

            with open(su2_path, 'w') as su2_file:
                su2_file.write(su2_mesh[0].decode('utf-8'))

            su2_mesh_paths.append(Path(su2_path))

        if not tixi.checkElement(SU2MESH_XPATH):
            tixi.createElement(SU2MESH_XPATH)

        # Update tixi element at SU2MESH_XPATH with new paths
        tixi_su2_mesh_paths = ';'.join(str(su2_mesh_paths))
        tixi.updateTextElement(SU2MESH_XPATH, tixi_su2_mesh_paths)

    dynstab_su2_mesh_paths = [
        mesh for mesh in su2_mesh_paths
        if not any(exclude in str(mesh) for exclude in CONTROL_SURFACE_LIST)
    ]

    return su2_mesh_paths, dynstab_su2_mesh_paths


def generate_su2_cfd_config(
    cpacs: CPACS,
    wkdir: Path,
    su2_mesh_paths: List[Path],
    mesh_markers: Dict,
    dyn_stab: bool,
    rans: bool
) -> None:
    """
    Reads data in the CPACS file and generate configuration files
    for one or multiple flight conditions (alt, mach, aoa, aos).

    Source:
        * SU2 config template: https://github.com/su2code/SU2/blob/master/config_template.cfg

    Args:
        cpacs_path (Path): Path to CPACS file.
        cpacs_out_path (Path): Path to CPACS output file.
        wkdir (Path): Path to the working directory.
        dyn_stab (bool): True if dynamic stability computation.
        rans (bool): True if RANS simulation.

    """
    tixi = cpacs.tixi

    for su2_mesh_path in su2_mesh_paths:
        ctrlsurf = check_control_surface(str(su2_mesh_path))
        log.info(f"Using SU2 mesh at path: {su2_mesh_path}.")

        validate_file(su2_mesh_path, "SU2 mesh")

        fixed_cl = get_value(tixi, SU2_FIXED_CL_XPATH)
        target_cl = get_value(tixi, SU2_TARGET_CL_XPATH)

        tpl_type = "RANS" if rans else "EULER"
        cfg = ConfigFile(get_su2_cfg_tpl(tpl_type))

        if dyn_stab and 'ITER' in cfg.data:
            cfg.data.pop('ITER', None)

        # General parameters
        aircraft = cpacs.aircraft
        cfg["RESTART_SOL"] = "NO"
        cfg["REF_LENGTH"] = aircraft.ref_length
        cfg["REF_AREA"] = aircraft.ref_area

        # TODO: Careful as not center gravity.
        cfg["REF_ORIGIN_MOMENT_X"] = aircraft.ref_point_x
        cfg["REF_ORIGIN_MOMENT_Y"] = aircraft.ref_point_y
        cfg["REF_ORIGIN_MOMENT_Z"] = aircraft.ref_point_z

        # SU2 version 8.1.0.
        cfg["MUSCL_FLOW"] = "NO"
        cfg["MUSCL_ADJFLOW"] = "NO"
        cfg["MGLEVEL"] = int(get_value(tixi, SU2_MG_LEVEL_XPATH))

        # Settings
        cfl_down = get_value(tixi, SU2_CFL_ADAPT_PARAM_DOWN_XPATH)
        cfl_up = get_value(tixi, SU2_CFL_ADAPT_PARAM_UP_XPATH)
        cfl_min = get_value(tixi, SU2_CFL_MIN_XPATH)
        cfl_max = get_value(tixi, SU2_CFL_MAX_XPATH)

        if not dyn_stab:
            cfg["CFL_ADAPT"] = str(get_value(tixi, SU2_CFL_ADAPT_XPATH))
            cfg["INNER_ITER"] = int(get_value(tixi, SU2_MAX_ITER_XPATH))
            cfg["CFL_NUMBER"] = str(get_value(tixi, SU2_CFL_NB_XPATH))
            cfg["CFL_ADAPT_PARAM"] = su2_format(f"{cfl_down}, {cfl_up}, {cfl_min}, {cfl_max}")

            # Fixed CL mode (AOA will not be taken into account)
            cfg["FIXED_CL_MODE"] = fixed_cl
            cfg["TARGET_CL"] = target_cl
            cfg["DCL_DALPHA"] = "0.1"
            cfg["UPDATE_AOA_ITER_LIMIT"] = "50"
            cfg["ITER_DCL_DALPHA"] = "80"

        # Mesh Marker
        bc_wall_str = su2_format(f"{','.join(mesh_markers['wall'])}")

        cfg["MARKER_EULER"] = bc_wall_str
        farfield_bc = (
            mesh_markers["farfield"]
            + mesh_markers["engine_intake"]
            + mesh_markers["engine_exhaust"]
        )
        cfg["MARKER_FAR"] = su2_format(f"{','.join(farfield_bc)}")
        cfg["MARKER_SYM"] = su2_format(f"{','.join(mesh_markers['symmetry'])}")
        cfg["MARKER_PLOTTING"] = bc_wall_str
        cfg["MARKER_MONITORING"] = bc_wall_str
        cfg["DV_MARKER"] = bc_wall_str

        # Output
        cfg["WRT_FORCES_BREAKDOWN"] = "YES"
        cfg["BREAKDOWN_FILENAME"] = SU2_FORCES_BREAKDOWN_NAME
        cfg["OUTPUT_FILES"] = su2_format("RESTART, PARAVIEW, SURFACE_PARAVIEW")
        cfg["HISTORY_OUTPUT"] = su2_format("INNER_ITER, RMS_RES, AERO_COEFF")

        configure_cfd_environment(
            cpacs=cpacs,
            wkdir=wkdir,
            cfg=cfg,
            su2_mesh_path=su2_mesh_path,
            rans=rans,
            dyn_stab=dyn_stab,
            mesh_markers=mesh_markers,
            ctrlsurf=ctrlsurf,
        )


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
