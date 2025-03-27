"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions and constants for CPACS2GMSH module.

Python version: >=3.8

| Author : Leon Deligny
| Creation: 2025-Feb-25

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import gmsh

import numpy as np

from cpacspy.cpacsfunctions import get_value
from ceasiompy import log

from tixi3.tixi3wrapper import Tixi3
from typing import Dict
from pathlib import Path
from ceasiompy.utils.configfiles import ConfigFile

from ceasiompy.utils.commonxpath import (
    GMSH_AUTO_REFINE_XPATH,
    GMSH_EXHAUST_PERCENT_XPATH,
    GMSH_FARFIELD_FACTOR_XPATH,
    GMSH_N_POWER_FACTOR_XPATH,
    GMSH_N_POWER_FIELD_XPATH,
    GMSH_INTAKE_PERCENT_XPATH,
    GMSH_MESH_SIZE_FARFIELD_XPATH,
    GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH,
    GMSH_MESH_SIZE_FACTOR_WINGS_XPATH,
    GMSH_MESH_SIZE_ENGINES_XPATH,
    GMSH_MESH_SIZE_PROPELLERS_XPATH,
    GMSH_OPEN_GUI_XPATH,
    GMSH_REFINE_FACTOR_XPATH,
    GMSH_REFINE_TRUNCATED_XPATH,
    GMSH_SYMMETRY_XPATH,
    GMSH_MESH_TYPE_XPATH,
    GMSH_NUMBER_LAYER_XPATH,
    GMSH_H_FIRST_LAYER_XPATH,
    GMSH_MAX_THICKNESS_LAYER_XPATH,
    GMSH_GROWTH_FACTOR_XPATH,
    GMSH_GROWTH_RATIO_XPATH,
    GMSH_SURFACE_MESH_SIZE_XPATH,
    GMSH_FEATURE_ANGLE_XPATH,
)


# =================================================================================================
#   CONSTANTS
# =================================================================================================

# Define mesh color for GMSH, only use in GUI (red, green, blue, brightness)
MESH_COLORS = {
    "farfield": (255, 200, 0, 100),
    "symmetry": (153, 255, 255, 100),
    "wing": (0, 200, 200, 100),
    "fuselage": (255, 215, 0, 100),
    "pylon": (255, 15, 255, 100),
    "engine": (127, 0, 255, 100),
    "rotor": (0, 0, 0, 100),
    "bad_surface": (255, 0, 0, 255),
    "good_surface": (0, 255, 0, 100),
}

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def cfg_rotors(brep_dir: Path) -> bool:
    rotor_model = False
    if Path(brep_dir, "config_rotors.cfg").exists():
        rotor_model = True

        log.info("Adding disk actuator")
        config_file = ConfigFile(Path(brep_dir, "config_rotors.cfg"))

        add_disk_actuator(brep_dir, config_file)

    return rotor_model


def add_disk_actuator(brep_dir: Path, config_file: ConfigFile):
    """
    Creates a 2D disk in a given location to represent a rotor as a disk actuator.

    Args:
        brep_dir (Path): Path to the brep files of the aircraft that also contains the rotor config file.
        config_file (Configfile): Config file of the propellers configuration on the aircraft.

    """

    nb_rotor = int(config_file["NB_ROTOR"])

    for k in range(1, nb_rotor + 1):
        # get the rotor configuration from cfg file
        rotor_uid = config_file[f"UID_{k}"]
        radius = float(config_file[f"{rotor_uid}_ROTOR_RADIUS"])
        sym = int(config_file[f"{rotor_uid}_SYMMETRIC"])
        trans_vector = (
            float(config_file[f"{rotor_uid}_TRANS_X"]),
            float(config_file[f"{rotor_uid}_TRANS_Y"]),
            float(config_file[f"{rotor_uid}_TRANS_Z"]),
        )
        rot_vector = (
            float(config_file[f"{rotor_uid}_ROT_X"]),
            float(config_file[f"{rotor_uid}_ROT_Y"]),
            float(config_file[f"{rotor_uid}_ROT_Z"]),
        )

        # Adding rotating disk
        gmsh.initialize()
        # generate the inlet_disk (gmsh always create a disk in the xy plane)
        disk_tag = gmsh.model.occ.addDisk(*trans_vector, radius, radius)
        disk_dimtag = (2, disk_tag)

        # y axis 180deg flip to make the inlet of the disk face forward
        gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 0, 1, 0, np.radians(180))
        gmsh.model.occ.synchronize()

        # rotation given in the cpacs file
        # x axis
        gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 1, 0, 0, np.radians(rot_vector[0]))
        # y axis
        gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 0, 1, 0, np.radians(rot_vector[1]))
        # z axis
        gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 0, 0, 1, np.radians(rot_vector[2]))

        gmsh.model.occ.synchronize()

        path_disk = Path(brep_dir, f"{rotor_uid}.brep")
        gmsh.write(str(path_disk))

        gmsh.clear()
        gmsh.finalize()

        if sym == 2:
            # Adding the symmetric
            gmsh.initialize()
            # generate the inlet_disk (gmsh always create a disk in the xy plane)
            disk_tag = gmsh.model.occ.addDisk(*trans_vector, radius, radius)
            disk_dimtag = (2, disk_tag)

            # y axis 180deg flip to make the inlet of the disk face forward is not necessary for
            # the mirrored part, and for now the symmetry is not implemented correctly since
            # the symmetry does not take into account the orientation of the rotor and the plane
            # of symmetry is assume to be the xz plane
            # When the face of the disk actuator are not oriented well the simulation shows
            # increasing cd and will probably diverge

            # rotation given in the cpacs file
            # x axis
            gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 1, 0, 0, np.radians(rot_vector[0]))
            # y axis
            gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 0, 1, 0, np.radians(rot_vector[1]))
            # z axis
            gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 0, 0, 1, np.radians(rot_vector[2]))

            gmsh.model.occ.synchronize()

            gmsh.model.occ.mirror([disk_dimtag], 0, 1, 0, 0)
            gmsh.model.occ.synchronize()
            path_disk = Path(brep_dir, f"{rotor_uid}_mirrored.brep")
            gmsh.write(str(path_disk))

            gmsh.clear()
            gmsh.finalize()


def write_gmsh(results_dir: str, file: str) -> Path:
    su2mesh_path = Path(results_dir, file)
    gmsh.write(str(su2mesh_path))
    return Path(su2mesh_path)


def initialize_gmsh():
    # Initialize gmsh
    gmsh.initialize()
    # Stop gmsh output log in the terminal
    gmsh.option.setNumber("General.Terminal", 0)
    # Log complexity
    gmsh.option.setNumber("General.Verbosity", 5)


def check_path(file: str):
    if os.path.exists(file):
        log.info(f"{file} exists")
    else:
        log.warning(f"{file} does not exist")


def load_rans_cgf_params(
    fuselage_maxlen: float,
    farfield_factor: float,
    n_layer: float,
    h_first_layer: float,
    max_layer_thickness: float,
    growth_factor: float,
    growth_ratio: float,
    feature_angle: float,
) -> Dict:

    InitialHeight = h_first_layer * (10**-5)
    MaxLayerThickness = max_layer_thickness / 10
    FarfieldRadius = fuselage_maxlen * farfield_factor * 100
    HeightIterations = 8
    NormalIterations = 8
    MaxCritIterations = 128
    LaplaceIterations = 8

    return {
        "InputFormat": "stl",
        "NLayers": n_layer,
        "FeatureAngle": feature_angle,
        "InitialHeight": InitialHeight,
        "MaxGrowthRatio": growth_ratio,
        "MaxLayerThickness": MaxLayerThickness,
        "FarfieldRadius": FarfieldRadius,
        "OutputFormat": "su2",  # fixed
        "HolePosition": "0.0 0.0 0.0",
        "FarfieldCenter": "0.0 0.0 0.0",
        "TetgenOptions": "-pq1.3VY",
        "TetGrowthFactor": growth_factor,
        "HeightIterations": HeightIterations,
        "NormalIterations": NormalIterations,
        "MaxCritIterations": MaxCritIterations,
        "LaplaceIterations": LaplaceIterations,
    }


def retrieve_gui_values(tixi: Tixi3):
    """
    Return input values from CEASIOMpy's GUI interface.

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.

    Returns:
        GUI values

    """
    # Retrieve value from the GUI Setting
    open_gmsh = get_value(tixi, GMSH_OPEN_GUI_XPATH)
    type_mesh = get_value(tixi, GMSH_MESH_TYPE_XPATH)
    symmetry = get_value(tixi, GMSH_SYMMETRY_XPATH)

    farfield_factor = get_value(tixi, GMSH_FARFIELD_FACTOR_XPATH)
    farfield_size_factor = get_value(tixi, GMSH_MESH_SIZE_FARFIELD_XPATH)

    n_power_factor = get_value(tixi, GMSH_N_POWER_FACTOR_XPATH)
    n_power_field = get_value(tixi, GMSH_N_POWER_FIELD_XPATH)

    fuselage_mesh_size_factor = get_value(tixi, GMSH_MESH_SIZE_FACTOR_FUSELAGE_XPATH)
    wing_mesh_size_factor = get_value(tixi, GMSH_MESH_SIZE_FACTOR_WINGS_XPATH)

    mesh_size_engines = get_value(tixi, GMSH_MESH_SIZE_ENGINES_XPATH)
    mesh_size_propellers = get_value(tixi, GMSH_MESH_SIZE_PROPELLERS_XPATH)

    refine_factor = get_value(tixi, GMSH_REFINE_FACTOR_XPATH)
    refine_truncated = get_value(tixi, GMSH_REFINE_TRUNCATED_XPATH)
    auto_refine = get_value(tixi, GMSH_AUTO_REFINE_XPATH)

    intake_percent = get_value(tixi, GMSH_INTAKE_PERCENT_XPATH)
    exhaust_percent = get_value(tixi, GMSH_EXHAUST_PERCENT_XPATH)

    n_layer = get_value(tixi, GMSH_NUMBER_LAYER_XPATH)
    h_first_layer = get_value(tixi, GMSH_H_FIRST_LAYER_XPATH)
    max_layer_thickness = get_value(tixi, GMSH_MAX_THICKNESS_LAYER_XPATH)

    growth_factor = get_value(tixi, GMSH_GROWTH_FACTOR_XPATH)
    growth_ratio = get_value(tixi, GMSH_GROWTH_RATIO_XPATH)

    min_max_mesh_factor = get_value(tixi, GMSH_SURFACE_MESH_SIZE_XPATH)

    feature_angle = get_value(tixi, GMSH_FEATURE_ANGLE_XPATH)
    
    return (
        open_gmsh, type_mesh, symmetry,
        farfield_factor, farfield_size_factor,
        n_power_factor, n_power_field,
        fuselage_mesh_size_factor, wing_mesh_size_factor,
        mesh_size_engines, mesh_size_propellers,
        refine_factor, refine_truncated, auto_refine,
        intake_percent, exhaust_percent,
        n_layer, h_first_layer, max_layer_thickness,
        growth_factor, growth_ratio,
        min_max_mesh_factor, feature_angle, 

    )

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
