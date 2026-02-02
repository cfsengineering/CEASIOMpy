"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

2D airfoil mesh generation functions for CPACS2GMSH module.
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import shutil
import subprocess

from shlex import join as shlex_join
from ceasiompy.utils.ceasiompyutils import get_results_directory
from cpacspy.cpacsfunctions import (
    get_value,
    create_branch,
    get_float_vector,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3

from ceasiompy import log
from ceasiompy.CPACS2GMSH import MODULE_NAME
from ceasiompy.utils.commonxpaths import (
    SU2MESH_XPATH,
    AIRFOILS_XPATH,
)
from ceasiompy.CPACS2GMSH import (
    GMSH_2D_AIRFOIL_MESH_SIZE_XPATH,
    GMSH_2D_EXT_MESH_SIZE_XPATH,
    GMSH_2D_FARFIELD_RADIUS_XPATH,
    GMSH_2D_STRUCTURED_MESH_XPATH,
    GMSH_2D_FARFIELD_TYPE_XPATH,
    GMSH_2D_FIRST_LAYER_HEIGHT_XPATH,
    GMSH_2D_WAKE_LENGTH_XPATH,
    GMSH_2D_HEIGHT_LENGTH_XPATH,
    GMSH_2D_LENGTH_XPATH,
    GMSH_2D_NO_BL_XPATH,
    GMSH_2D_RATIO_XPATH,
    GMSH_2D_NB_LAYERS_XPATH,
    GMSH_2D_MESH_FORMAT_XPATH,
)


# Methods
def _safe_get_value(tixi: Tixi3, xpath: str):
    if tixi.checkElement(xpath):
        return get_value(tixi, xpath)
    return None


def _read_mesh_parameters(tixi: Tixi3):
    """
    Read mesh parameters from CPACS with defaults.

    Args:
        tixi: TIXI handle
        defaults: Dictionary of default values from specs

    Returns:
        dict: Dictionary of mesh parameters
    """
    params = {
        "airfoil_mesh_size": _safe_get_value(tixi, GMSH_2D_AIRFOIL_MESH_SIZE_XPATH),
        "ext_mesh_size": _safe_get_value(tixi, GMSH_2D_EXT_MESH_SIZE_XPATH),
        "structured_mesh": _safe_get_value(tixi, GMSH_2D_STRUCTURED_MESH_XPATH),
        "first_layer_height": _safe_get_value(tixi, GMSH_2D_FIRST_LAYER_HEIGHT_XPATH),
        "farfield_type": _safe_get_value(tixi, GMSH_2D_FARFIELD_TYPE_XPATH),
        "farfield_radius": _safe_get_value(tixi, GMSH_2D_FARFIELD_RADIUS_XPATH),
        "wake_length": _safe_get_value(tixi, GMSH_2D_WAKE_LENGTH_XPATH),
        "height_length": _safe_get_value(tixi, GMSH_2D_HEIGHT_LENGTH_XPATH),
        "length": _safe_get_value(tixi, GMSH_2D_LENGTH_XPATH),
        "no_boundary_layer": _safe_get_value(tixi, GMSH_2D_NO_BL_XPATH),
        "growth_ratio": _safe_get_value(tixi, GMSH_2D_RATIO_XPATH),
        "number_of_layers": _safe_get_value(tixi, GMSH_2D_NB_LAYERS_XPATH),
        "mesh_format": _safe_get_value(tixi, GMSH_2D_MESH_FORMAT_XPATH),
    }

    # Force CType for structured mesh
    if params["structured_mesh"]:
        params["farfield_type"] = "CType"
        log.info("Structured mesh enabled: forcing farfield type to CType")

    return params


def _run_gmshairfoil2d(params, wkdir, airfoil_file):
    """
    Build the gmshairfoil2d command line.

    Args:
        params: Dictionary of mesh parameters
        wkdir: Working directory Path
        airfoil_file: Path to airfoil file.

    Returns:
        tuple: (command list, expected_mesh_file Path, fallback_mesh_file Path | None)
    """
    aoa = 0.0
    deflection = 0.0
    log.info("Using deflection angle: 0.0 deg (fixed for now)")

    cmd = [
        "gmshairfoil2d",
        "--aoa",
        str(aoa),
        "--deflection",
        str(deflection),
        "--airfoil_mesh_size",
        str(params["airfoil_mesh_size"]),
        "--ext_mesh_size",
        str(params["ext_mesh_size"]),
        "--format",
        params["mesh_format"],
        "--output",
        str(wkdir),
    ]

    # Add boundary layer parameters
    if not params["no_boundary_layer"]:
        nb_of_layers = params["number_of_layers"]
        if nb_of_layers is None:
            raise ValueError(f"Number of layers not specified in Settings {nb_of_layers=}")

        cmd.extend([
            "--first_layer",
            str(params["first_layer_height"]),
            "--ratio",
            str(params["growth_ratio"]),
            "--nb_layers",
            str(int(nb_of_layers)),
        ])
    else:
        cmd.append("--no_bl")
        log.info("Boundary layer disabled, using unstructured mesh with triangles only")

    # Add farfield parameters
    if params["farfield_type"] == "Circular":
        if params["farfield_radius"] is None:
            raise ValueError("Farfield radius is required for Circular farfield type.")
        cmd.extend(["--farfield", str(params["farfield_radius"])])
    elif params["farfield_type"] == "CType":
        cmd.append("--farfield_ctype")
        if params["structured_mesh"]:
            if params["wake_length"] is None or params["height_length"] is None:
                raise ValueError(
                    "Wake and height lengths are required for structured CType farfield."
                )
            cmd.extend(["--arg_struc", f"{params['wake_length']}x{params['height_length']}"])
    elif params["farfield_type"] == "Rectangular":
        if params["length"] is None or params["height_length"] is None:
            raise ValueError("Length and height are required for Rectangular farfield type.")
        cmd.extend(["--box", f"{params['length']}x{params['height_length']}"])

    # Add structured mesh option
    if params["structured_mesh"]:
        cmd.append("--structured")

    # Determine airfoil input and expected output file
    if airfoil_file and airfoil_file.exists():
        # Copy airfoil file to working directory if needed
        if airfoil_file.parent != wkdir:
            local_airfoil_file = wkdir / airfoil_file.name
            shutil.copy(airfoil_file, local_airfoil_file)
            airfoil_file = local_airfoil_file

        cmd.extend(["--airfoil_path", str(airfoil_file)])
        log.info(f"Generating mesh using airfoil file: {airfoil_file}")

        file_stem = airfoil_file.stem
        expected_mesh_file = wkdir / f"mesh_airfoil_{file_stem}.{params['mesh_format']}"
        fallback_mesh_file = None
        if file_stem.startswith("airfoil_"):
            fallback_mesh_file = wkdir / f"mesh_airfoil_{file_stem[8:]}.{params['mesh_format']}"

    return cmd, expected_mesh_file, fallback_mesh_file


def _log_process_streams(
    result,
    *,
    stdout_level="info",
    stderr_level="error",
    prefix="gmshairfoil2d",
):
    if result.stdout:
        getattr(log, stdout_level)(f"{prefix} stdout:\n{result.stdout}")
    if result.stderr:
        getattr(log, stderr_level)(f"{prefix} stderr:\n{result.stderr}")


def _collect_process_details(result, *, stdout_label="Output", stderr_label="Error"):
    details = []
    if result.stderr:
        details.append(f"{stderr_label}: {result.stderr}")
    if result.stdout:
        details.append(f"{stdout_label}: {result.stdout}")
    return "\n".join(details)


def _generating_dat_file(cpacs: CPACS) -> Path:
    wingairfoil_xpath = AIRFOILS_XPATH + "/wingAirfoil[1]"
    wkdir = get_results_directory(MODULE_NAME)
    tixi = cpacs.tixi

    if not tixi.checkElement(wingairfoil_xpath):
        raise ValueError(f"Missing wing airfoil definition at {wingairfoil_xpath}")

    def _safe_airfoil_name(value: str) -> str:
        safe = "".join(
            char
            if (char.isalnum() or char in ("-", "_"))
            else "_" for char in value.strip()
        )
        return safe or "airfoil"

    airfoil_id = "airfoil"
    if tixi.checkAttribute(wingairfoil_xpath, "uID"):
        airfoil_id = tixi.getTextAttribute(wingairfoil_xpath, "uID")
    elif tixi.checkElement(wingairfoil_xpath + "/name"):
        airfoil_id = tixi.getTextElement(wingairfoil_xpath + "/name")

    airfoil_id = _safe_airfoil_name(airfoil_id)
    dat_file = wkdir / f"airfoil_{airfoil_id}.dat"

    file_xpath = wingairfoil_xpath + "/pointList/file"
    if tixi.checkElement(file_xpath):
        file_path = Path(tixi.getTextElement(file_xpath))
        if file_path.exists():
            if file_path.resolve() != dat_file.resolve():
                shutil.copy(file_path, dat_file)
            log.info(f"Using airfoil point file from CPACS: {dat_file}")
            return dat_file

    pointlist_xpath = wingairfoil_xpath + "/pointList"
    if not tixi.checkElement(pointlist_xpath + "/x"):
        raise ValueError(f"Missing airfoil x-coordinates at {pointlist_xpath}/x")

    x_vals = get_float_vector(tixi, pointlist_xpath + "/x")
    if tixi.checkElement(pointlist_xpath + "/z"):
        z_vals = get_float_vector(tixi, pointlist_xpath + "/z")
    elif tixi.checkElement(pointlist_xpath + "/y"):
        z_vals = get_float_vector(tixi, pointlist_xpath + "/y")
    else:
        raise ValueError(f"Missing airfoil z/y-coordinates at {pointlist_xpath}")

    if len(x_vals) != len(z_vals) or not x_vals:
        raise ValueError("Airfoil coordinate lists are empty or length-mismatched")

    with open(dat_file, "w") as dat_handle:
        dat_handle.write(f"{airfoil_id}\n")
        for coord_x, coord_z in zip(x_vals, z_vals):
            dat_handle.write(f"{coord_x:.8f}\t{coord_z:.8f}\n")

    log.info(f"Wrote airfoil coordinates to {dat_file}")
    return dat_file


# Functions
def process_2d_airfoil(cpacs: CPACS, wkdir: Path) -> None:
    """
    Process 2D airfoil geometry and generate 2D mesh.

    This function handles the 2D airfoil case, reading the airfoil configuration
    from the CPACS file and generating a 2D mesh using gmshairfoil2d.
    """
    log.info("Processing 2D airfoil geometry...")

    tixi = cpacs.tixi

    # Get default values and read mesh parameters
    log.info("Reading mesh parameters.")
    params = _read_mesh_parameters(tixi)

    log.info("Generating .dat file for gmshairfoil2d from CPACS file.")
    airfoil_file = _generating_dat_file(cpacs)

    # Build gmshairfoil2d command
    log.info("Building gmshairfoil2d command.")
    cmd, expected_mesh_file, fallback_mesh_file = _run_gmshairfoil2d(
        wkdir=wkdir,
        params=params,
        airfoil_file=airfoil_file,
    )

    # Execute gmshairfoil2d
    log.info(f"Running: {shlex_join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=wkdir)

    if result.returncode != 0:
        error_msg = f"Mesh generation failed with return code {result.returncode}"
        _log_process_streams(result, stdout_level="error", stderr_level="error")
        details = _collect_process_details(result)
        if details:
            error_msg = f"{error_msg}\n{details}"
        raise RuntimeError(error_msg)

    # Verify mesh file was created
    if not expected_mesh_file.exists() and fallback_mesh_file and fallback_mesh_file.exists():
        expected_mesh_file = fallback_mesh_file

    if not expected_mesh_file.exists():
        error_msg = f"Mesh file not found after generation: {expected_mesh_file}"
        candidates = sorted(wkdir.glob(f"mesh_airfoil_*.{params['mesh_format']}"))
        if candidates:
            error_msg = (
                f"{error_msg}\nAvailable mesh files: "
                + ", ".join(str(path) for path in candidates)
            )
        _log_process_streams(result, stdout_level="info", stderr_level="warning")
        details = _collect_process_details(
            result,
            stdout_label="Gmshairfoil2d output",
            stderr_label="Gmshairfoil2d stderr",
        )
        if details:
            error_msg = f"{error_msg}\n\n{details}"
        raise RuntimeError(error_msg)

    log.info(f"2D mesh generated successfully: {expected_mesh_file}")

    # Save mesh path to CPACS
    create_branch(tixi, SU2MESH_XPATH)
    tixi.updateTextElement(SU2MESH_XPATH, str(expected_mesh_file))

    log.info("2D airfoil processing completed.")
