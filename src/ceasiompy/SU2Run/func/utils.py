"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to manipulate SU2 configuration and results.

| Author : Aidan Jungo
| Creation: 2019-09-30
| Modified: Leon Deligny
| Date: 24-Feb-2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


from cpacspy.cpacsfunctions import get_value

from pathlib import Path
from tixi3.tixi3wrapper import Tixi3
from ceasiompy.utils.configfiles import ConfigFile
from ceasiompy.Database.func.storing import CeasiompyDb
from typing import (
    Dict,
    List,
    Tuple,
)

from ceasiompy import log
from ceasiompy.utils.commonxpaths import (
    USED_SU2_MESH_XPATH,
    SELECTED_AEROMAP_XPATH,
)
from ceasiompy.SU2Run.func import (
    SU2_FORCES_MOM,
    AERO_COEFFICIENTS,
)
from ceasiompy.SU2Run import (
    MODULE_DIR,
    TEMPLATE_TYPE,
    CONTROL_SURFACE_LIST,
    SU2_CONTROL_SURF_BOOL_XPATH,
    SU2_CONTROL_SURF_ANGLE_XPATH,
)
from ceasiompy.utils.commonnames import (
    CONFIG_CFD_NAME,
    ENGINE_INTAKE_SUFFIX,
    ENGINE_EXHAUST_SUFFIX,
    ACTUATOR_DISK_INLET_SUFFIX,
    ACTUATOR_DISK_OUTLET_SUFFIX,
    SU2_FORCES_BREAKDOWN_NAME,
)

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def check_one_entry(dict_dir: List[Dict], mach: float, alt: float, angle: str) -> Path:
    """
    Check that there exists exactly one entry with "angle" == "none" in dict_dir
    """

    one_entry = [
        d for d in dict_dir if d["mach"] == mach and d["alt"] == alt and d["angle"] == angle
    ]
    if len(one_entry) != 1:
        raise ValueError(
            f"Expected exactly one angle={angle}"
            f"for mach={mach}, alt={alt}, "
            f"but found {len(one_entry)}."
        )
    else:
        return one_entry[0]["dir"]


def process_config_dir(config_dir: Path, dict_dir: List[Dict]) -> None:
    config_name = config_dir.name
    log.info(f"dir.name {config_name}")
    if config_name.endswith("aoa0.0_aos0.0"):
        angle = "none"
    elif config_name.endswith("dynstab"):
        angle = config_name.split("_")[3].split("angle")[1]
    else:
        log.warning(f"Skipping results of directory {config_dir}.")
        return None

    dict_dir.append({
        "mach": float(config_name.split("_")[2].split("mach")[1]),
        "alt": float(config_name.split("_")[1].split("alt")[1]),
        "dir": config_dir,
        "angle": angle,
    })


def check_force_file_exists(config_dir: Path) -> Path:
    force_file_path = Path(config_dir, "no_deformation", SU2_FORCES_BREAKDOWN_NAME)
    if not force_file_path.exists():
        raise OSError("No result force file have been found!")
    return force_file_path


def get_aeromap_uid(tixi: Tixi3, fixed_cl: str) -> str:
    if fixed_cl == "YES":
        return "aeroMap_fixedCL_SU2"
    else:
        return str(get_value(tixi, SELECTED_AEROMAP_XPATH))


def su2_format(string: str) -> str:
    """
    Converts a string to SU2 tuple string format.
    """
    return "( " + string + " )"


def save_cfg_dir(
    cfg: ConfigFile,
    wkdir: Path,
    case_dir_name: str,
    rate_type: str,
    cfg_dict: Dict,
    cfg_param: str,
) -> None:
    """Specific use for add_damping_derivatives."""
    cfg[cfg_param] = cfg_dict[rate_type][0]
    drate = cfg_dict[rate_type][1]
    case_dir = Path(wkdir, f"{case_dir_name}_{drate}")
    case_dir.mkdir()
    cfg.write_file(Path(case_dir, CONFIG_CFD_NAME), overwrite=True)


def add_damping_derivatives(
    cfg: ConfigFile, wkdir: Path, case_dir_name: str, rotation_rate: float
) -> None:
    """
    Add damping derivatives parameter to the config file cfg and
    save them to their respective directory.

    Args:
        cfg (ConfigFile): ConfigFile object.
        wkdir (Path): Path to the working directory.
        case_dir_name (str): Name of the case directory.
        rotation_rate (float): Rotation rate that will be impose to calculate damping derivatives.

    """

    cfg["GRID_MOVEMENT"] = "ROTATING_FRAME"

    RATE_DICT = {
        "roll": [f"{rotation_rate} 0.0 0.0", f"p_{rotation_rate}"],
        "pitch": [f"0.0 {rotation_rate} 0.0", f"q_{rotation_rate}"],
        "yaw": [f"0.0 0.0 {rotation_rate}", f"r_{rotation_rate}"],
    }

    RATE = "ROTATION_RATE"
    save_cfg_dir(cfg, wkdir, case_dir_name, "roll", RATE_DICT, RATE)
    save_cfg_dir(cfg, wkdir, case_dir_name, "pitch", RATE_DICT, RATE)
    save_cfg_dir(cfg, wkdir, case_dir_name, "yaw", RATE_DICT, RATE)

    log.info("Damping derivatives cases directories have been created.")


def access_coef(line: str) -> float:
    """
    Extracts and returns the coefficient from a given line of text.
    """
    return float(line.split(":")[1].split("|")[0])


def validate_file(_file: Path, file_name: str) -> None:
    """
    Check if the _file is indeed a file.
    """
    if not _file.is_file():
        raise FileNotFoundError(f"The {file_name} file at '{_file}' has not been found!")


def get_mesh_markers(su2_mesh_path: Path) -> Dict:
    """
    Get the name of all the SU2 mesh marker found in the SU2 mesh file
    sorted as farfield, symmetry, engine_intake, engine_exhaust and wall.

    Args:
        su2_mesh_path (Path): Path to the SU2 mesh.

    Returns:
        Dict: Dictionary of the mesh markers found in the SU2 mesh file.

    """

    validate_file(su2_mesh_path, "SU2 mesh")

    # Check if it is a su2 file
    if not su2_mesh_path.suffix == ".su2":
        raise ValueError("The input must be SU2 mesh (*.su2)!")

    mesh_markers = {
        "farfield": [],
        "symmetry": [],
        "engine_intake": [],
        "engine_exhaust": [],
        "actuator_disk_inlet": [],
        "actuator_disk_outlet": [],
        "wall": [],
    }

    with open(su2_mesh_path) as f:

        for line in f.readlines():
            if "MARKER_TAG" not in line:
                continue

            marker = line.split("=")[1].strip()

            if "farfield" in marker.lower():
                mesh_markers["farfield"].append(marker)
                log.info(f"'{marker}' marker has been marked as farfield.")
            elif "symmetry" in marker.lower():
                mesh_markers["symmetry"].append(marker)
                log.info(f"'{marker}' marker has been marked as symmetry.")
            elif marker.endswith(ENGINE_INTAKE_SUFFIX):
                mesh_markers["engine_intake"].append(marker)
                log.info(f"'{marker}' marker has been marked as engine_intake.")
            elif marker.endswith(ENGINE_EXHAUST_SUFFIX):
                mesh_markers["engine_exhaust"].append(marker)
                log.info(f"'{marker}' marker has been marked as engine_exhaust.")
            elif marker.endswith(ACTUATOR_DISK_INLET_SUFFIX):
                mesh_markers["actuator_disk_inlet"].append(marker)
                log.info(f"'{marker}' marker has been marked as actuator_disk_inlet.")
            elif marker.endswith(ACTUATOR_DISK_OUTLET_SUFFIX):
                mesh_markers["actuator_disk_outlet"].append(marker)
                log.info(f"'{marker}' marker has been marked as actuator_disk_outlet.")
            else:
                # In SU2 wings and fuselages are marked as wall.
                mesh_markers["wall"].append(marker)
                log.info(f"'{marker}' marker has been marked as wall.")

    # Check if markers were found
    if not any(mesh_markers.values()):
        raise ValueError("No mesh markers found!")

    # Add none to False values in mesh_markers
    for key, value in mesh_markers.items():
        if not value:
            mesh_markers[key] = ["None"]

    return mesh_markers


def check_control_surface(input_string: str) -> str:
    if "aileron" in input_string:
        return "aileron"
    elif "rudder" in input_string:
        return "rudder"
    elif "elevator" in input_string:
        return "elevator"
    else:
        return "no_deformation"


def retrieve_su2_mesh(
    su2_mesh_list: List[Tuple[bytes, str, str, float]],
    aircraft_name: str,
    angle: float,
    deformation_list: List[str],
) -> List[Tuple[bytes, str, str, float]]:
    """
    Connect to ceasiompy.db and retrieve the first .su2 mesh for:
        - Specific aircraft name
        - Specific deformation from the deformation_list
        - Specific angle of deformation

    Append the result to the su2_mesh_list.
    """
    db = CeasiompyDb()

    for deformation in deformation_list:
        # Query to retrieve the last su2_data value
        query = """
                    SELECT su2_file_data
                    FROM gmsh_data
                    WHERE aircraft = ? AND deformation = ? AND angle = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
        db.cursor.execute(query, (aircraft_name, deformation, angle))

        su2_mesh: bytes = db.cursor.fetchone()
        log.info(
            f"Loading .su2 file for aircraft {aircraft_name}, "
            f"deformation {deformation} of angle {angle} [deg]."
        )
        su2_mesh_list.append((su2_mesh[0], aircraft_name, deformation, angle))

    db.close()


def get_surface_pitching_omega(oscillation_type: str, omega: float) -> str:
    """
    Returns how the deforming surface will move around origin point,
    in terms on what oscillation we choose.

    Args:
        oscillation_type (str): Either 'alpha' or 'beta'.
        omega (float): Angular frequency.

    Raises:
        ValueError: Checks correct format for oscillation_type.

    Returns:
        str: Either '0.0 omega 0.0 ' or '0.0 0.0 omega '.

    """
    if oscillation_type == "alpha":
        return f"0.0 {omega} 0.0 "
    elif oscillation_type == "beta":
        return f"0.0 0.0 {omega} "
    else:
        raise ValueError("Invalid oscillation_type in get_surface_pitching_omega.")


def su2_mesh_list_from_db(tixi: Tixi3) -> List[Tuple[bytes, str, str, float]]:

    aircraft_name = get_value(tixi, USED_SU2_MESH_XPATH + "list")
    su2_mesh_list = []

    # No control surfaces
    if not get_value(tixi, SU2_CONTROL_SURF_BOOL_XPATH):
        retrieve_su2_mesh(su2_mesh_list, aircraft_name, 0.0, ["no_deformation"])

    else:
        angles = str(get_value(tixi, SU2_CONTROL_SURF_ANGLE_XPATH))
        angles_list = list(set([float(angle) for angle in angles.split(";")]))

        for angle in angles_list:
            if angle != 0.0:
                retrieve_su2_mesh(su2_mesh_list, aircraft_name, angle, CONTROL_SURFACE_LIST)
            else:
                retrieve_su2_mesh(su2_mesh_list, aircraft_name, 0.0, ["no_deformation"])

    return su2_mesh_list


def get_su2_cfg_tpl(tpl_type: str) -> Path:
    """
    Get path of the SU2 config template of template_type
    corresponding to the correct SU2 version.

    Args:
        template_type (str): Either "euler" or "rans".

    Returns:
        su2_cfg_tpe_euler_path (str): Path of the SU2 config template.

    """

    if tpl_type not in TEMPLATE_TYPE:
        log.warning(
            "template_type (str) should be either " "'EULER' or 'RANS' in get_su2_config_template."
        )

    tpl_type = tpl_type.lower()

    return Path(MODULE_DIR, "files", f"cfg_tpl_{tpl_type}.cfg")


def get_su2_aerocoefs(
    force_file: Path,
) -> Tuple[float, float, float, float, float, float, float]:
    """
    Get aerodynamic coefficients and velocity from the force_file.

    Note:
        force_file should be: forces_breakdown.dat

    Args:
        force_file (Path): Path to the SU2 forces file.

    Returns:
        cl, cd, cs, cmd, cms, cml, velocity: Aerodynamic coefficients and velocity.

    """

    validate_file(force_file, "SU2 force")

    # In case they are not found in force_file
    results = {key: None for key in AERO_COEFFICIENTS.values()}

    # Call access_coef for the correct coefficient
    def parse_line(line: str) -> None:
        for key, var_name in AERO_COEFFICIENTS.items():
            if key in line:
                if (key == "Free-stream velocity") and ("m/s" in line):
                    results[var_name] = float(line.split(" ")[7])
                elif not key == "Free-stream velocity":
                    results[var_name] = access_coef(line)

    # Parse each line in the file
    with open(force_file) as f:
        for line in f.readlines():
            parse_line(line)

    return (
        results["cl"],
        results["cd"],
        results["cs"],
        results["cmd"],
        results["cms"],
        results["cml"],
        results["velocity"],
    )


def get_su2_forces_moments(
    force_file: Path,
) -> Tuple[float, float, float, float, float, float, float]:
    """
    Get aerodynamic forces and moments from the force_file.

    Note:
        force_file should be: forces_breakdown.dat

    Args:
        force_file (Path): Path to the SU2 forces file.

    Returns:
        cl, cd, cs, cmd, cms, cml: Aerodynamic coefficients and velocity.

    """

    validate_file(force_file, "SU2 force")

    # In case they are not found in force_file
    results = {key: None for key in SU2_FORCES_MOM.values()}

    # Call access_coef for the correct coefficient
    def parse_line(line: str):
        for key, var_name in SU2_FORCES_MOM.items():
            if key in line:
                results[var_name] = access_coef(line)

    # Parse each line in the file
    with open(force_file) as f:
        for line in f.readlines():
            parse_line(line)

    return (
        results["cfx"],
        results["cfy"],
        results["cfz"],
        results["cmx"],
        results["cmy"],
        results["cmz"],
    )


def get_efficiency_and_aoa(force_file: Path) -> Tuple[float, float]:
    """
    Get efficiency (CL/CD) and Angle of Attack (AoA) in the force_file.
    """

    validate_file(force_file, "SU2 force")
    cl_cd, aoa = None, None

    with open(force_file) as f:
        for line in f.readlines():
            if "CL/CD" in line:
                cl_cd = access_coef(line)
                continue

            if "Angle of attack (AoA):" in line:
                aoa = float(line.split("Angle of attack (AoA):")[1].split("deg,")[0].strip())
                continue

            if cl_cd and aoa:
                log.info(f"CL/CD ratio has been found and is equal to: {cl_cd}.")
                log.info(f"AoA has been found and is equal to: {aoa}.")
                return cl_cd, aoa

    if cl_cd is None:
        raise ValueError(f"No value has been found for the CL/CD ratio in {force_file}.")
    else:
        raise ValueError(f"No value has been found for the AoA in {force_file}")


def get_wetted_area(su2_logfile: Path) -> float:
    """
    Get SU2 logfile and returns the wetted area value
    previously calculated by SU2.
    """

    validate_file(su2_logfile, "SU2 log")

    with open(su2_logfile) as f:
        for line in f.readlines():
            if "Wetted area =" not in line:
                continue

            wetted_area = float(line.split(" ")[3])
            log.info(f"Wetted area value has been found : {wetted_area} [m^2].")
            return wetted_area

    log.warning("No value has been found for the wetted area, returning 0 [m^2].")

    return 0
