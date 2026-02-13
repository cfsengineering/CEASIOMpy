"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Use .brep files parts of an airplane to generate a fused airplane in GMSH with
the OCC kernel. Then Spherical farfield is created around the airplane and the
resulting domain is meshed using gmsh

| Author: Tony Govoni
| Creation: 2022-03-22

TODO:

    - It may be good to move all the function and some of the code in generategmsh()
    that are related to disk actuator to another python script and import it here

    - It may be better to propose more options for the mesh size of the different
    part (pylon,engine,rotor)

    - Add a boolean to deactivate the refinement factor according to the thickness of the
    truncated te of the wings. This options often create very small meshes and is not
    always required.

"""

# Imports

import re
import gmsh

import numpy as np

from ceasiompy.cpacs2gmsh.func.wingclassification import classify_wing
from ceasiompy.utils.ceasiompyutils import get_part_type
from cpacspy.cpacsfunctions import create_branch

from ceasiompy.cpacs2gmsh.func.mesh_sizing import wings_size
from ceasiompy.cpacs2gmsh.func.utils import initialize_gmsh, write_gmsh, cfg_rotors
from ceasiompy.cpacs2gmsh.func.advancemeshing import (
    refine_wing_section,
    set_domain_mesh,
    refine_small_surfaces,
    min_fields,
)

from pathlib import Path
from ceasiompy.cpacs2gmsh.func.wingclassification import ModelPart
from ceasiompy.utils.configfiles import ConfigFile
from tixi3.tixi3wrapper import Tixi3
from typing import List, Dict, Tuple, Callable, Optional

from ceasiompy import log
from ceasiompy.cpacs2gmsh.func.utils import MESH_COLORS

from ceasiompy.cpacs2gmsh import (
    GMSH_MESH_SIZE_FUSELAGE_XPATH,
    GMSH_MESH_SIZE_WINGS_XPATH,
    GMSH_MESH_SIZE_CTRLSURFS_XPATH,
)
from ceasiompy.utils.commonnames import (
    ACTUATOR_DISK_INLET_SUFFIX,
    ACTUATOR_DISK_OUTLET_SUFFIX,
    ENGINE_EXHAUST_SUFFIX,
    ENGINE_INTAKE_SUFFIX,
    GMSH_ENGINE_CONFIG_NAME,
)


# Functions

def define_engine_bc(engine_part, brep_dir):
    """
    Function to define the boundary conditions for the engine part.
    The engine is defined as a volume and the boundary conditions intake exhaust
    are set to be fixed.

    Args:
    ----------
    engine_part : ModelPart
        engine part of the aircraft to set the bc on
    brep_dir : Path
        path to the brep files of the aircraft that also contains the engine config file

    """

    # Check if the engine is double or simple flux and
    # the engine normal and distance between the intake and exhaust

    config_file_path = Path(brep_dir, GMSH_ENGINE_CONFIG_NAME)
    config_file = ConfigFile(config_file_path)

    doubleflux = bool(int(config_file[f"{engine_part.uid}_DOUBLE_FLUX"]))
    engine_normal = [0, 0, 0]
    engine_normal[0] = float(config_file[f"{engine_part.uid}_NORMAL_X"])
    engine_normal[1] = float(config_file[f"{engine_part.uid}_NORMAL_Y"])
    engine_normal[2] = float(config_file[f"{engine_part.uid}_NORMAL_Z"])
    scaling_x = float(config_file[f"{engine_part.uid}_SCALING_X"])

    # Determine which surfaces are possible engine intake and exhaust by their normal orientation
    possible_intake = []
    possible_exhaust = []
    # and which surface tag will be excluded from the engine surfaces
    int_exh_surf_tag = []

    # Loop all the engine surfaces to seek for potential right placed surfaces
    for dimtag in engine_part.surfaces:
        surface_center = gmsh.model.occ.getCenterOfMass(*dimtag)
        parametric_coord = gmsh.model.getParametrization(*dimtag, list(surface_center))

        # GMSH normal is defined exiting the volume
        # note here that the volume is the fluid, so the inside of the engine is the outside
        # of the volume, so intake normal is opposite to engine normal
        normal = gmsh.model.getNormal(dimtag[1], parametric_coord)
        absolute_same = np.isclose(
            np.absolute(engine_normal), np.absolute(normal), atol=1e-04, equal_nan=False
        )
        same = np.isclose(engine_normal, normal, atol=1e-04, equal_nan=False)

        if absolute_same.all():
            if same.all():
                possible_exhaust.append(dimtag)
            else:
                possible_intake.append(dimtag)

    intake_x = float(config_file[f"{engine_part.uid}_fanCowl_INTAKE_X"])
    exhaust_x = float(config_file[f"{engine_part.uid}_fanCowl_EXHAUST_X"])
    engine_distance = (exhaust_x - intake_x) * scaling_x

    # Determine which surfaces are possible engine intake and exhaust by their
    # respective distance is the same as the one when the engine was converted
    for intake in possible_intake:
        for exhaust in possible_exhaust:
            pos_intake = gmsh.model.occ.getCenterOfMass(*intake)
            pos_exhaust = gmsh.model.occ.getCenterOfMass(*exhaust)
            distance = np.linalg.norm(np.subtract(pos_intake, pos_exhaust))

            if np.isclose(distance, engine_distance, atol=1e-04, equal_nan=False):
                engine_part.intake_tag = [intake[1]]
                engine_part.exhaust_fan_tag = [exhaust[1]]
                int_exh_surf_tag.extend(engine_part.intake_tag)
                int_exh_surf_tag.extend(engine_part.exhaust_fan_tag)
                break

    if doubleflux:
        intake_x = float(config_file[f"{engine_part.uid}_fanCowl_INTAKE_X"])
        exhaust_core_x = float(config_file[f"{engine_part.uid}_coreCowl_EXHAUST_X"])
        core_distance = (exhaust_core_x - intake_x) * scaling_x

        # Determine which exhaust goes with the intake by their respective distance
        for intake in possible_intake:
            for exhaust in possible_exhaust:
                pos_intake = gmsh.model.occ.getCenterOfMass(*intake)
                pos_exhaust = gmsh.model.occ.getCenterOfMass(*exhaust)
                distance = np.linalg.norm(np.subtract(pos_intake, pos_exhaust))
                if np.isclose(distance, core_distance, atol=1e-04, equal_nan=False):
                    engine_part.exhaust_core_tag = [exhaust[1]]
                    int_exh_surf_tag.extend(engine_part.exhaust_core_tag)
                    break

    # Set the boundary conditions
    # Engine_normal_surface
    engine_part.other_surfaces_tags = list(
        set(engine_part.surfaces_tags).difference(set(int_exh_surf_tag))
    )
    surfaces_group = gmsh.model.addPhysicalGroup(2, engine_part.other_surfaces_tags)
    gmsh.model.setPhysicalName(2, surfaces_group, f"{engine_part.uid}")

    # Intake
    intake_fan_group = gmsh.model.addPhysicalGroup(2, engine_part.intake_tag)
    gmsh.model.setPhysicalName(2, intake_fan_group, f"{engine_part.uid}_fan{ENGINE_INTAKE_SUFFIX}")

    # Exhaust
    exhaust_fan_group = gmsh.model.addPhysicalGroup(2, engine_part.exhaust_fan_tag)
    gmsh.model.setPhysicalName(
        2, exhaust_fan_group, f"{engine_part.uid}_fan{ENGINE_EXHAUST_SUFFIX}"
    )
    if doubleflux:
        exhaust_core_group = gmsh.model.addPhysicalGroup(2, engine_part.exhaust_core_tag)
        gmsh.model.setPhysicalName(
            2, exhaust_core_group, f"{engine_part.uid}_core{ENGINE_EXHAUST_SUFFIX}"
        )


def process_gmsh_log(gmsh_log):
    """
    Function to process the gmsh log file.
    It is used to retrieve the mesh quality
    and the time needed to mesh the model
    ...

    Args:
    ----------
    gmsh_log : list(str)
        list of gmsh log events
    """

    # Find last logs about mesh quality
    quality_log = [log for log in gmsh_log if "< quality <" in log]
    final_quality_log = quality_log[-10:]

    log.info("Final mesh quality :")
    for log_line in final_quality_log:
        log.info(log_line)

    total_time = 0
    time_log = [log for log in gmsh_log if "CPU" in log]
    for message in time_log:
        total_time += float(message.split("CPU")[1].split("s")[0])

    log.info(f"Total meshing time : {round(total_time, 2)}s")


def duplicate_disk_actuator_surfaces(part: ModelPart):
    """
    Duplicate the surfaces of a disk actuator.

    Args:
        part (ModelPart): Part object of the rotor modeled as a disk actuator.

    """

    # "crack" the mesh by duplicating the elements and nodes on the disk surface
    if len(part.physical_groups) > 1:
        raise ValueError("Disk actuator can only have one surface.")

    gmsh.plugin.setNumber("Crack", "Dimension", 2)
    gmsh.plugin.setNumber("Crack", "PhysicalGroup", part.physical_groups[0])
    # find the last physical group tag
    new_tag = 1 + len(gmsh.model.getPhysicalGroups(dim=-1))
    gmsh.plugin.setNumber("Crack", "NewPhysicalGroup", new_tag)

    # Set the new physical group for the back surface
    gmsh.model.setPhysicalName(2, new_tag, f"{part.uid}{ACTUATOR_DISK_OUTLET_SUFFIX}")
    gmsh.plugin.run("Crack")
    log.info("Created outlet disk actuator surface")


def control_disk_actuator_normal():
    """
    Function to control the surface orientation of disk actuator in the model
    sometimes the 'crack' plugin change the surface orientation of the inlet and outlet
    of disk actuator, thus we need to control if the inlet and outlet surface are
    well oriented, if not we switch the physical groups names of the inlet and outlet.

    """

    # Get the physical groups list
    physical_groups = gmsh.model.getPhysicalGroups(dim=2)
    physical_groups_name = [gmsh.model.getPhysicalName(*group) for group in physical_groups]

    inlet_groups = [
        group
        for group in physical_groups
        if ACTUATOR_DISK_INLET_SUFFIX in gmsh.model.getPhysicalName(*group)
    ]

    # Check the disk actuator  inlet normal, should point forward (x>0))
    for inlet_group in inlet_groups:
        # Get the normal
        surface_tag = gmsh.model.getEntitiesForPhysicalGroup(*inlet_group)
        surface_dimtag = (2, *surface_tag)
        surface_center = gmsh.model.occ.getCenterOfMass(*surface_dimtag)
        parametric_coord = gmsh.model.getParametrization(*surface_dimtag, list(surface_center))
        normal_x = gmsh.model.getNormal(surface_dimtag[1], parametric_coord)[0]

        if normal_x >= 0.0:
            continue

        # Switch the physical group name
        inlet_name = gmsh.model.getPhysicalName(*inlet_group)
        outlet_name = inlet_name.replace(ACTUATOR_DISK_INLET_SUFFIX, ACTUATOR_DISK_OUTLET_SUFFIX)

        outlet_group = physical_groups[physical_groups_name.index(outlet_name)]

        # Delete the physical group name
        gmsh.model.removePhysicalName(inlet_name)
        gmsh.model.removePhysicalName(outlet_name)

        # Rename by swapping inlet outlet
        gmsh.model.setPhysicalName(*inlet_group, outlet_name)
        gmsh.model.setPhysicalName(*outlet_group, inlet_name)
