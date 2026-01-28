"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

2D airfoil mesh generation functions for CPACS2GMSH module.

| Author: Giacomo Benedetti, Leon Deligny
| Creation: 2025-01-28

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import subprocess
from pathlib import Path

from cpacspy.cpacspy import CPACS
from cpacspy.cpacsfunctions import get_value_or_default, create_branch

from ceasiompy import log
from ceasiompy.utils.commonxpaths import SU2MESH_XPATH, GEOM_XPATH
from ceasiompy.utils.moduleinterfaces import get_specs_for_module
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

    # Get default values from specs
    specs = get_specs_for_module("CPACS2GMSH")
    defaults = {}
    for entry in specs.cpacs_inout.inputs:
        defaults[entry.xpath] = entry.default_value
        # For list types (dropdowns), use first item as default
        if isinstance(defaults[entry.xpath], list) and len(defaults[entry.xpath]) > 0:
            defaults[entry.xpath] = defaults[entry.xpath][0]

    # Retrieve mesh parameters from CPACS (with defaults from specs)
    airfoil_mesh_size = get_value_or_default(
        tixi, GMSH_2D_AIRFOIL_MESH_SIZE_XPATH, defaults.get(GMSH_2D_AIRFOIL_MESH_SIZE_XPATH)
    )
    ext_mesh_size = get_value_or_default(
        tixi, GMSH_2D_EXT_MESH_SIZE_XPATH, defaults.get(GMSH_2D_EXT_MESH_SIZE_XPATH)
    )
    structured_mesh = get_value_or_default(
        tixi, GMSH_2D_STRUCTURED_MESH_XPATH, defaults.get(GMSH_2D_STRUCTURED_MESH_XPATH)
    )
    first_layer_height = get_value_or_default(
        tixi, GMSH_2D_FIRST_LAYER_HEIGHT_XPATH, defaults.get(GMSH_2D_FIRST_LAYER_HEIGHT_XPATH)
    )
    farfield_type = get_value_or_default(
        tixi, GMSH_2D_FARFIELD_TYPE_XPATH, defaults.get(GMSH_2D_FARFIELD_TYPE_XPATH)
    )

    # Force CType for structured mesh
    if structured_mesh:
        farfield_type = "CType"
        log.info("Structured mesh enabled: forcing farfield type to CType")

    farfield_radius = get_value_or_default(
        tixi, GMSH_2D_FARFIELD_RADIUS_XPATH, defaults.get(GMSH_2D_FARFIELD_RADIUS_XPATH)
    )

    wake_length = get_value_or_default(
        tixi, GMSH_2D_WAKE_LENGTH_XPATH, defaults.get(GMSH_2D_WAKE_LENGTH_XPATH)
    )
    height_length = get_value_or_default(
        tixi, GMSH_2D_HEIGHT_LENGTH_XPATH, defaults.get(GMSH_2D_HEIGHT_LENGTH_XPATH)
    )
    length = get_value_or_default(
        tixi, GMSH_2D_LENGTH_XPATH, defaults.get(GMSH_2D_LENGTH_XPATH)
    )
    no_boundary_layer = get_value_or_default(
        tixi, GMSH_2D_NO_BL_XPATH, defaults.get(GMSH_2D_NO_BL_XPATH)
    )
    growth_ratio = get_value_or_default(
        tixi, GMSH_2D_RATIO_XPATH, defaults.get(GMSH_2D_RATIO_XPATH)
    )
    number_of_layers = int(
        get_value_or_default(tixi, GMSH_2D_NB_LAYERS_XPATH, defaults.get(GMSH_2D_NB_LAYERS_XPATH))
    )
    mesh_format = get_value_or_default(
        tixi, GMSH_2D_MESH_FORMAT_XPATH, defaults.get(GMSH_2D_MESH_FORMAT_XPATH)
    )

    # AoA is always 0 for 2D airfoil mesh
    aoa = 0.0
    # log.info("Using AoA: 0.0 deg (fixed for 2D airfoil)")

    # Deflection angle is always 0 (flap feature not implemented yet)
    deflection = 0.0
    log.info("Using deflection angle: 0.0 deg (fixed for now)")

    # Determine airfoil type and look for airfoil profile in CPACS
    airfoil_type = None
    airfoil_name = None
    airfoil_file = None

    airfoil_type = tixi.getTextElement(GEOM_XPATH + "/airfoilType")

    # Get airfoil code/name from CPACS based on type
    if airfoil_type == "NACA":
        airfoil_name = tixi.getTextElement(GEOM_XPATH + "/airfoilCode")
        log.info(f"Using NACA airfoil from CPACS: {airfoil_name}")

    elif airfoil_type == "Custom":
        try:
            airfoil_name = tixi.getTextElement(GEOM_XPATH + "/airfoilName")
            log.info(f"Using custom airfoil from CPACS: {airfoil_name}")
        except Exception:
            log.error("Custom airfoil type but no name found in CPACS")

    # Try to find airfoil profile file in CPACS wingAirfoils ONLY if airfoil_type is Custom
    # For NACA airfoils, we use the code directly instead of a file
    if airfoil_type == "Custom":
        try:
            airfoils_xpath = "/cpacs/vehicles/profiles/wingAirfoils"
            n_airfoils = tixi.getNamedChildrenCount(airfoils_xpath, "wingAirfoil")

            # Iterate backwards to get the most recent airfoil
            for i in range(n_airfoils, 0, -1):
                airfoil_xpath = f"{airfoils_xpath}/wingAirfoil[{i}]"
                try:
                    # Try to get the airfoil file path
                    file_path = tixi.getTextElement(airfoil_xpath + "/pointList/file")
                    if file_path and Path(file_path).exists():
                        airfoil_file = Path(file_path)
                        # Get airfoil name from CPACS
                        try:
                            airfoil_name = tixi.getTextElement(airfoil_xpath + "/name")
                        except Exception:
                            airfoil_name = Path(file_path).stem.replace("airfoil_", "")
                        log.info(f"Found airfoil profile in CPACS: {airfoil_file}")
                        break
                except Exception:
                    continue
        except Exception as e:
            log.debug(f"Could not search for airfoil profiles in CPACS: {e}")

    # Build gmshairfoil2d command
    # Note: gmshairfoil2d generates the output filename automatically as mesh_<name>.<format>

    cmd = [
        "gmshairfoil2d",
        "--aoa",
        str(aoa),
        "--deflection",
        str(deflection),
        "--airfoil_mesh_size",
        str(airfoil_mesh_size),
        "--ext_mesh_size",
        str(ext_mesh_size),
        "--format",
        mesh_format,
        "--output",
        str(wkdir),
    ]

    # Add boundary layer parameters only if boundary layer is enabled
    if not no_boundary_layer:
        cmd.extend(
            [
                "--first_layer",
                str(first_layer_height),
                "--ratio",
                str(growth_ratio),
                "--nb_layers",
                str(number_of_layers),
            ]
        )
    else:
        cmd.append("--no_bl")
        log.info("Boundary layer disabled, using unstructured mesh with triangles only")

    # Add farfield parameters based on type
    if farfield_type == "Circular":
        cmd.extend(["--farfield", str(farfield_radius)])
    elif farfield_type == "CType":
        cmd.append("--farfield_ctype")
        # For CType, use arg_struc parameter if structured mesh
        if structured_mesh:
            cmd.extend(["--arg_struc", f"{wake_length}x{height_length}"])
    elif farfield_type == "Rectangular":
        cmd.extend(["--box", f"{length}x{height_length}"])

    # Add structured mesh option if enabled
    if structured_mesh:
        cmd.append("--structured")

    # Use airfoil file if found in CPACS, otherwise use NACA code or name
    if airfoil_file and airfoil_file.exists():
        # Copy airfoil file to working directory if not already there
        if airfoil_file.parent != wkdir:
            import shutil

            local_airfoil_file = wkdir / airfoil_file.name
            shutil.copy(airfoil_file, local_airfoil_file)
            airfoil_file = local_airfoil_file

        cmd.extend(["--airfoil_path", str(airfoil_file)])
        log.info(f"Generating mesh using airfoil file: {airfoil_file}")
        # gmshairfoil2d generates mesh_airfoil_<filename_without_extension>.<format>
        gmsh_output_file = wkdir / f"mesh_airfoil_{airfoil_file.stem}.{mesh_format}"
        # Final expected mesh file - remove double 'airfoil_' prefix if present
        file_stem = airfoil_file.stem
        if file_stem.startswith("airfoil_"):
            file_stem = file_stem[8:]  # Remove 'airfoil_' prefix for consistency
            expected_mesh_file = wkdir / f"mesh_airfoil_{file_stem}.{mesh_format}"
            needs_rename = True
        else:
            expected_mesh_file = gmsh_output_file
            needs_rename = False

    elif airfoil_type == "NACA":
        if airfoil_name is None:
            airfoil_name = tixi.getTextElement(GEOM_XPATH + "/airfoilCode")

        cmd.extend(["--naca", airfoil_name])
        log.info(f"Generating mesh for NACA {airfoil_name} airfoil")
        expected_mesh_file = wkdir / f"mesh_airfoil_{airfoil_name}.{mesh_format}"
        needs_rename = False

    elif airfoil_type == "Custom":
        try:
            airfoil_name = tixi.getTextElement(GEOM_XPATH + "/airfoilName")
            cmd.extend(["--airfoil", airfoil_name])
            log.info(f"Generating mesh for airfoil: {airfoil_name}")
            expected_mesh_file = wkdir / f"mesh_airfoil_{airfoil_name}.{mesh_format}"
            needs_rename = False
        except Exception:
            log.error("Custom airfoil selected but no airfoil name provided")
            raise ValueError("Custom airfoil requires airfoilName in CPACS")

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
    if needs_rename and gmsh_output_file.exists():
        import shutil
        shutil.move(gmsh_output_file, expected_mesh_file)
        log.info(f"Renamed {gmsh_output_file.name} to {expected_mesh_file.name} for consistency")

    # Verify that the mesh file was actually created
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

    log.info("2D airfoil processing completed.")
