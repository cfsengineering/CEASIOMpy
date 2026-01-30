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

from ceasiompy.utils.moduleinterfaces import get_specs_for_module
from cpacspy.cpacsfunctions import (
    create_branch,
    get_float_vector,
    get_value_or_default,
)

from pathlib import Path
from cpacspy.cpacspy import CPACS

from ceasiompy import log
from ceasiompy.utils.commonxpaths import (
    GEOM_XPATH,
    SU2MESH_XPATH,
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

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def _get_defaults_from_specs():
    """
    Get default values from __specs__.py file.

    Returns:
        dict: Dictionary mapping xpath to default value
    """
    specs = get_specs_for_module("CPACS2GMSH")
    defaults = {}
    for entry in specs.cpacs_inout.inputs:
        defaults[entry.xpath] = entry.default_value
        # For list types (dropdowns), use first item as default
        if isinstance(defaults[entry.xpath], list) and len(defaults[entry.xpath]) > 0:
            defaults[entry.xpath] = defaults[entry.xpath][0]
    return defaults


def _read_mesh_parameters(tixi, defaults):
    """
    Read mesh parameters from CPACS with defaults.

    Args:
        tixi: TIXI handle
        defaults: Dictionary of default values from specs

    Returns:
        dict: Dictionary of mesh parameters
    """
    params = {
        "airfoil_mesh_size": get_value_or_default(
            tixi, GMSH_2D_AIRFOIL_MESH_SIZE_XPATH, defaults.get(GMSH_2D_AIRFOIL_MESH_SIZE_XPATH)
        ),
        "ext_mesh_size": get_value_or_default(
            tixi, GMSH_2D_EXT_MESH_SIZE_XPATH, defaults.get(GMSH_2D_EXT_MESH_SIZE_XPATH)
        ),
        "structured_mesh": get_value_or_default(
            tixi, GMSH_2D_STRUCTURED_MESH_XPATH, defaults.get(GMSH_2D_STRUCTURED_MESH_XPATH)
        ),
        "first_layer_height": get_value_or_default(
            tixi, GMSH_2D_FIRST_LAYER_HEIGHT_XPATH, defaults.get(GMSH_2D_FIRST_LAYER_HEIGHT_XPATH)
        ),
        "farfield_type": get_value_or_default(
            tixi, GMSH_2D_FARFIELD_TYPE_XPATH, defaults.get(GMSH_2D_FARFIELD_TYPE_XPATH)
        ),
        "farfield_radius": get_value_or_default(
            tixi, GMSH_2D_FARFIELD_RADIUS_XPATH, defaults.get(GMSH_2D_FARFIELD_RADIUS_XPATH)
        ),
        "wake_length": get_value_or_default(
            tixi, GMSH_2D_WAKE_LENGTH_XPATH, defaults.get(GMSH_2D_WAKE_LENGTH_XPATH)
        ),
        "height_length": get_value_or_default(
            tixi, GMSH_2D_HEIGHT_LENGTH_XPATH, defaults.get(GMSH_2D_HEIGHT_LENGTH_XPATH)
        ),
        "length": get_value_or_default(
            tixi, GMSH_2D_LENGTH_XPATH, defaults.get(GMSH_2D_LENGTH_XPATH)
        ),
        "no_boundary_layer": get_value_or_default(
            tixi, GMSH_2D_NO_BL_XPATH, defaults.get(GMSH_2D_NO_BL_XPATH)
        ),
        "growth_ratio": get_value_or_default(
            tixi, GMSH_2D_RATIO_XPATH, defaults.get(GMSH_2D_RATIO_XPATH)
        ),
        "number_of_layers": int(
            get_value_or_default(
                tixi, GMSH_2D_NB_LAYERS_XPATH, defaults.get(GMSH_2D_NB_LAYERS_XPATH)
            )
        ),
        "mesh_format": get_value_or_default(
            tixi, GMSH_2D_MESH_FORMAT_XPATH, defaults.get(GMSH_2D_MESH_FORMAT_XPATH)
        ),
    }

    # Force CType for structured mesh
    if params["structured_mesh"]:
        params["farfield_type"] = "CType"
        log.info("Structured mesh enabled: forcing farfield type to CType")

    return params


def _get_airfoil_info(tixi):
    """
    Extract airfoil type and name from CPACS.

    Args:
        tixi: TIXI handle

    Returns:
        tuple: (airfoil_type, airfoil_name, airfoil_file)
    """
    airfoil_type = tixi.getTextElement(GEOM_XPATH + "/airfoilType")
    airfoil_name = None
    airfoil_file = None

    if airfoil_type == "NACA":
        airfoil_name = tixi.getTextElement(GEOM_XPATH + "/airfoilCode")
        log.info(f"Using NACA airfoil from CPACS: {airfoil_name}")

    elif airfoil_type == "Custom":
        try:
            airfoil_name = tixi.getTextElement(GEOM_XPATH + "/airfoilName")
            log.info(f"Using custom airfoil from CPACS: {airfoil_name}")
        except Exception:
            log.error("Custom airfoil type but no name found in CPACS")

    return airfoil_type, airfoil_name, airfoil_file


def _write_airfoil_from_pointlist(
    tixi, airfoil_xpath: str, wkdir: Path, airfoil_name: str | None
):
    pointlist_xpath = airfoil_xpath + "/pointList"
    if not tixi.checkElement(pointlist_xpath + "/x"):
        return None

    x_vals = get_float_vector(tixi, pointlist_xpath + "/x")
    if tixi.checkElement(pointlist_xpath + "/z"):
        z_vals = get_float_vector(tixi, pointlist_xpath + "/z")
    elif tixi.checkElement(pointlist_xpath + "/y"):
        z_vals = get_float_vector(tixi, pointlist_xpath + "/y")
    else:
        return None

    if len(x_vals) != len(z_vals) or not x_vals:
        return None

    safe_name = (airfoil_name or "custom").replace(" ", "_")
    airfoil_file = wkdir / f"airfoil_{safe_name}.dat"

    with open(airfoil_file, "w") as f:
        f.write(f"{safe_name}\n")
        for x, z in zip(x_vals, z_vals):
            f.write(f"{x:.8f} {z:.8f}\n")

    return airfoil_file


def _find_airfoil_file(tixi, airfoil_type, wkdir: Path):
    """
    Find airfoil profile file in CPACS wingAirfoils (only for Custom type).

    Args:
        tixi: TIXI handle
        airfoil_type: Type of airfoil (NACA or Custom)

    Returns:
        tuple: (airfoil_name, airfoil_file Path or None, inline_generated bool)
    """
    if airfoil_type != "Custom":
        return None, None, False

    try:
        airfoils_xpath = "/cpacs/vehicles/profiles/wingAirfoils"
        n_airfoils = tixi.getNamedChildrenCount(airfoils_xpath, "wingAirfoil")

        # Iterate backwards to get the most recent airfoil
        for i in range(n_airfoils, 0, -1):
            airfoil_xpath = f"{airfoils_xpath}/wingAirfoil[{i}]"

            # Try to get the airfoil file path
            if tixi.checkElement(airfoil_xpath + "/pointList/file"):
                file_path = tixi.getTextElement(airfoil_xpath + "/pointList/file")
                if file_path and Path(file_path).exists():
                    airfoil_file = Path(file_path)
                    # Get airfoil name from CPACS
                    try:
                        airfoil_name = tixi.getTextElement(airfoil_xpath + "/name")
                    except Exception:
                        airfoil_name = Path(file_path).stem.replace("airfoil_", "")

                    log.info(f"Found airfoil profile in CPACS: {airfoil_file}")
                    return airfoil_name, airfoil_file, False

            # Fall back to inline pointList if present
            try:
                airfoil_name = tixi.getTextElement(airfoil_xpath + "/name")
            except Exception:
                airfoil_name = None

            inline_file = _write_airfoil_from_pointlist(
                tixi, airfoil_xpath, wkdir, airfoil_name
            )
            if inline_file:
                log.info(f"Built airfoil profile from pointList: {inline_file}")
                return airfoil_name, inline_file, True

    except Exception as e:
        log.debug(f"Could not search for airfoil profiles in CPACS: {e}")

    return None, None, False


def _run_gmshairfoil2d(params, wkdir, airfoil_type, airfoil_name, airfoil_file):
    """
    Build the gmshairfoil2d command line.

    Args:
        params: Dictionary of mesh parameters
        wkdir: Working directory Path
        airfoil_type: Type of airfoil (NACA or Custom)
        airfoil_name: Name/code of the airfoil
        airfoil_file: Path to airfoil file (if Custom)

    Returns:
        tuple: (command list, expected_mesh_file Path, needs_rename bool)
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
        cmd.extend(
            [
                "--first_layer",
                str(params["first_layer_height"]),
                "--ratio",
                str(params["growth_ratio"]),
                "--nb_layers",
                str(params["number_of_layers"]),
            ]
        )
    else:
        cmd.append("--no_bl")
        log.info("Boundary layer disabled, using unstructured mesh with triangles only")

    # Add farfield parameters
    if params["farfield_type"] == "Circular":
        cmd.extend(["--farfield", str(params["farfield_radius"])])
    elif params["farfield_type"] == "CType":
        cmd.append("--farfield_ctype")
        if params["structured_mesh"]:
            cmd.extend(["--arg_struc", f"{params['wake_length']}x{params['height_length']}"])
    elif params["farfield_type"] == "Rectangular":
        cmd.extend(["--box", f"{params['length']}x{params['height_length']}"])

    # Add structured mesh option
    if params["structured_mesh"]:
        cmd.append("--structured")

    # Determine airfoil input and expected output file
    needs_rename = False

    if airfoil_file and airfoil_file.exists():
        # Copy airfoil file to working directory if needed
        if airfoil_file.parent != wkdir:
            local_airfoil_file = wkdir / airfoil_file.name
            shutil.copy(airfoil_file, local_airfoil_file)
            airfoil_file = local_airfoil_file

        cmd.extend(["--airfoil_path", str(airfoil_file)])
        log.info(f"Generating mesh using airfoil file: {airfoil_file}")

        # Handle double 'airfoil_' prefix
        file_stem = airfoil_file.stem
        if file_stem.startswith("airfoil_"):
            file_stem = file_stem[8:]
            needs_rename = True

        expected_mesh_file = wkdir / f"mesh_airfoil_{file_stem}.{params['mesh_format']}"

    elif airfoil_type == "NACA":
        cmd.extend(["--naca", airfoil_name])
        log.info(f"Generating mesh for NACA {airfoil_name} airfoil")
        expected_mesh_file = wkdir / f"mesh_airfoil_{airfoil_name}.{params['mesh_format']}"

    elif airfoil_type == "Custom":
        if not airfoil_name:
            raise ValueError("Custom airfoil requires airfoilName in CPACS")
        cmd.extend(["--airfoil", airfoil_name])
        log.info(f"Generating mesh for airfoil: {airfoil_name}")
        expected_mesh_file = wkdir / f"mesh_airfoil_{airfoil_name}.{params['mesh_format']}"

    else:
        raise ValueError(f"Unknown airfoil type: {airfoil_type}")

    return cmd, expected_mesh_file, needs_rename


def process_2d_airfoil(cpacs: CPACS, wkdir: Path) -> None:
    """
    Process 2D airfoil geometry and generate 2D mesh.

    This function handles the 2D airfoil case, reading the airfoil configuration
    from the CPACS file and generating a 2D mesh using gmshairfoil2d.

    Args:
        cpacs (CPACS): CPACS object containing the airfoil geometry
        wkdir (Path): Working directory path

    """
    log.info("Processing 2D airfoil geometry...")

    tixi = cpacs.tixi

    # Get default values and read mesh parameters
    defaults = _get_defaults_from_specs()
    params = _read_mesh_parameters(tixi, defaults)

    # Get airfoil information from CPACS
    airfoil_type, airfoil_name, airfoil_file = _get_airfoil_info(tixi)
    inline_generated = False

    # Try to find airfoil file if Custom type
    if airfoil_type == "Custom":
        found_name, found_file, inline_generated = _find_airfoil_file(
            tixi, airfoil_type, wkdir
        )
        if found_file:
            airfoil_file = found_file
            if found_name:
                airfoil_name = found_name

    # Build gmshairfoil2d command
    cmd, expected_mesh_file, needs_rename = _run_gmshairfoil2d(
        params, wkdir, airfoil_type, airfoil_name, airfoil_file
    )

    # Execute gmshairfoil2d
    log.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=wkdir)

    if result.returncode != 0:
        error_msg = f"Mesh generation failed with return code {result.returncode}"
        if result.stderr:
            log.error(f"gmshairfoil2d stderr:\n{result.stderr}")
            error_msg += f"\nError: {result.stderr}"
        if result.stdout:
            log.error(f"gmshairfoil2d stdout:\n{result.stdout}")
            error_msg += f"\nOutput: {result.stdout}"
        raise RuntimeError(error_msg)

    # Rename file if needed to remove double 'airfoil_' prefix
    if needs_rename:
        gmsh_output_file = wkdir / f"mesh_airfoil_airfoil_{airfoil_name}.{params['mesh_format']}"
        if gmsh_output_file.exists():
            import shutil
            shutil.move(gmsh_output_file, expected_mesh_file)
            log.info(f"Renamed {gmsh_output_file.name} to {expected_mesh_file.name}")

    # Verify mesh file was created
    if not expected_mesh_file.exists():
        error_msg = f"Mesh file not found after generation: {expected_mesh_file}"
        if result.stdout:
            log.info(f"gmshairfoil2d output:\n{result.stdout}")
            error_msg += f"\n\nGmshairfoil2d output:\n{result.stdout}"
        if result.stderr:
            log.warning(f"gmshairfoil2d stderr:\n{result.stderr}")
            error_msg += f"\n\nGmshairfoil2d stderr:\n{result.stderr}"
        raise RuntimeError(error_msg)

    log.info(f"2D mesh generated successfully: {expected_mesh_file}")

    # Save mesh path to CPACS
    create_branch(tixi, SU2MESH_XPATH)
    tixi.updateTextElement(SU2MESH_XPATH, str(expected_mesh_file))
    cpacs.save_cpacs(cpacs.cpacs_file, overwrite=True)

    # Clean up temporary airfoil file generated from inline pointList
    if airfoil_type == "Custom" and airfoil_file and inline_generated:
        airfoil_file.unlink(missing_ok=True)

    log.info("2D airfoil processing completed.")
