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

# =================================================================================================
#   IMPORTS
# =================================================================================================

import re
import gmsh

import numpy as np

from ceasiompy.CPACS2GMSH.func.wingclassification import classify_wing
from ceasiompy.utils.ceasiompyutils import bool_, get_part_type
from cpacspy.cpacsfunctions import create_branch

from ceasiompy.CPACS2GMSH.func.mesh_sizing import fuselage_size, wings_size
from ceasiompy.CPACS2GMSH.func.utils import initialize_gmsh, write_gmsh, cfg_rotors
from ceasiompy.CPACS2GMSH.func.advancemeshing import (
    refine_wing_section,
    set_domain_mesh,
    refine_small_surfaces,
    min_fields,
)

from pathlib import Path
from ceasiompy.CPACS2GMSH.func.wingclassification import ModelPart
from ceasiompy.utils.configfiles import ConfigFile
from tixi3.tixi3wrapper import Tixi3
from typing import List, Dict, Tuple

from ceasiompy import log
from ceasiompy.CPACS2GMSH.func.utils import MESH_COLORS

from ceasiompy.CPACS2GMSH import (
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

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


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


def generate_gmsh(
    tixi: Tixi3,
    brep_dir: Path,
    results_dir: Path,
    open_gmsh: bool = False,
    farfield_factor: float = 6.0,
    symmetry: bool = False,
    farfield_size_factor=10,
    n_power_factor=2,
    n_power_field=0.9,
    fuselage_mesh_size_factor=1,
    wing_mesh_size_factor=0.5,
    mesh_size_engines: float = 0.23,
    mesh_size_propellers: float = 0.23,
    refine_factor: float = 2.0,
    refine_truncated: bool = False,
    auto_refine: bool = True,
    testing_gmsh: bool = False,
    surf: str = None,
    angle: str = None,
) -> Path:
    """
    Generates a mesh from brep files forming an airplane.

    1. Airplane is fused with the different brep files: fuselage, wings etc.
    2. Farfield is generated.
    3. Airplane is subtracted to farfield to generate the final fluid domain.

    A marker for each airplane part and farfield surfaces is reported in the mesh file.

    Args:
        cpacs (CPACS): CPACS file.
        brep_dir (Path): Path to the directory containing the brep files.
        results_dir (Path): Path to the directory containing the result mesh files.
        open_gmsh (bool = False): Opens gmsh's GUI after the mesh generation if set to true.
        farfield_factor (float = 6): Factor to enlarge the farfield.
        symmetry (bool = False): Mesh will be generated with symmetry wrt to the x,z plane.

        #mesh_size_farfield (float): Size of the farfield mesh.
        #mesh_size_fuselage (float): Size of the fuselage mesh.
        #mesh_size_wings (float): Size of the wing mesh.

        mesh_size_engines (float = 0.23): Size of the engine mesh.
        mesh_size_propellers (float = 0.23): Size of the propeller mesh.

        #advance_mesh (bool):
        # If set to true,
        # the mesh will be generated with advanced meshing options.

        refine_factor (float = 2.0): Refine factor for the mesh's LE and TE.
        refine_truncated (bool = False): Refinement can change to match the truncated te thickness.
        auto_refine (bool = False): Mesh will be checked for quality.
        testing_gmsh (bool = False): Gmsh sessions will not be clear and killed at the end of
            the function, this allow to test the gmsh feature after the call of generate_gmsh()

    Returns:
        (Path, List[ModelPart]):
            - Path to the mesh file generated by gmsh.
            - List of the aircraft parts in the model.

    """
    # Determine if rotors are present in the aircraft model
    rotor_model = cfg_rotors(brep_dir)

    # Retrieve all breps
    brep_files = sorted(brep_dir.glob("*.brep"))

    # Initialize gmsh
    initialize_gmsh()
    gmsh.logger.start()
    # gmsh.option.setNumber("Geometry.Tolerance", 1e-3)  # Adjust as needed

    # Import each aircraft original parts / parent parts
    aircraft_parts: List[ModelPart] = []
    parts_parent_dimtag = []

    log.info(f"Importing files from {brep_dir}.")

    # Fuse correctly
    for brep_file in brep_files:
        # Import the part and create the aircraft part object
        part_entities = gmsh.model.occ.importShapes(str(brep_file), highestDimOnly=False)

        # Create the aircraft part object
        part_obj = ModelPart(uid=brep_file.stem)
        part_obj.part_type = get_part_type(tixi, part_obj.uid)

        # Add to the list of aircraft parts
        aircraft_parts.append(part_obj)
        parts_parent_dimtag.append(part_entities[0])

        log.info(f"Part: {part_obj.uid} imported.")
        gmsh.model.occ.synchronize()

    ###########################################
    # Create external domain for the farfield #
    ###########################################

    model_bb = gmsh.model.getBoundingBox(-1, -1)  # Get bounding box of whole model
    model_dimensions = [
        abs(model_bb[0] - model_bb[3]),
        abs(model_bb[1] - model_bb[4]),
        abs(model_bb[2] - model_bb[5]),
    ]
    model_center = [
        model_bb[0] + model_dimensions[0] / 2,
        0,  # the y coordinate is set to zero because sometimes (when act disk
        # actuator is present) the coordinate of the model is not exact
        model_bb[2] + model_dimensions[2] / 2,
    ]

    domain_length = farfield_factor * max(model_dimensions)

    farfield = gmsh.model.occ.addSphere(*model_center, domain_length)

    gmsh.model.occ.synchronize()
    ext_domain = [(3, farfield)]

    ##################################################
    # Ensure domain is symmetric if symmetry == True #
    ##################################################

    if symmetry:
        log.info("Preparing: symmetry operation.")
        sym_plane = gmsh.model.occ.addDisk(*model_center, domain_length, domain_length)
        sym_vector = [0, 1, 0]
        plane_vector = [0, 0, 1]
        if sym_vector != plane_vector:
            rotation_axis = np.cross(sym_vector, plane_vector)
            gmsh.model.occ.rotate(
                [(2, sym_plane)],
                *model_center,
                *rotation_axis,
                np.pi / 2,
            )
            sym_box = gmsh.model.occ.extrude(
                [(2, sym_plane)], *(np.multiply(sym_vector, -domain_length * 1.1))
            )
        parts_parent_dimtag.append(sym_box[1])

    ###########################################
    # Fragment operation aircraft to farfield #
    ###########################################

    # gmsh.model.occ.fragmentfragment produces fragments_dimtag and children_dimtag

    # 1. fragments_dimtag:
    # fragments_dimtag is a list of tuples (dimtag, tag) of all the volumes in the model.
    # The first fragment is the entire domain, each fragments are sub-volumes of the domain.
    # Since it is associated to the entire domain we don't need it.

    # 2. children_dimtag:
    # children_dimtag is a list list of tuples (dimtag, tag).
    # The rest of children_dimtag are list of tuples (dimtag, tag)
    # that represent volumes in the model.
    # children_dimtag is "sorted" according to the order of importation of the parent parts.
    # Ror example: if the first part imported was "fuselage1" then the first children_dimtag
    # is a list of all the "child" volumes in the model that are from the "parent" "fuselage1"
    # we can then associate each entities in the model to their parent origin.

    # When two parents part ex. a fuselage and a wing intersect each other
    # two children are generated for both parts, thus if a child is shared by
    # two parent parts (or more), then this child is a volume given
    # by the intersection of the two parent parts, we don't need them and some
    # of its surfaces, lines and point in the final models.

    # Thus we need to find those unwanted child and their entities that don't belong
    # to the final model, and remove them.

    # afterward the entities of each child will be associated with their parent part names
    # then we can delete all the child in the model, and only keep the final domain
    # Removing a child will not delete its entities shared by the final domain, this means that
    # at the end we will only have one volume with all the surfaces,lines,points assigned
    # to the original parent parts imported at the begging of the function

    # If symmetry is applied the last children_dimtag is all the volume in the symmetry cylinder
    # thus the we can easily remove them and only keep the volumes of half domain.

    log.info("Start fragment operation between the aircraft and the farfield.")

    _, children_dimtag = gmsh.model.occ.fragment(ext_domain, parts_parent_dimtag)

    gmsh.model.occ.synchronize()
    log.info("Fragment operation finished.")

    unwanted_children = []
    if symmetry:
        # Take the unwanted children from symmetry
        unwanted_children = children_dimtag[-1]
        # Careful: this only take into account volumes elements in the symmetry
        # Disk actuator that are 2D element are not taken into account
        # and will be removed latter

        # remove them from the model
        gmsh.model.occ.remove(unwanted_children, recursive=True)
        # gmsh.model.mesh.removeDuplicateNodes()
        gmsh.model.occ.synchronize()

    # Get the children of the aircraft parts
    aircraft_parts_children_dimtag = children_dimtag[1:]

    log.info("Before/after fragment operation relations:")
    for parent, children in zip(aircraft_parts, aircraft_parts_children_dimtag):
        # don't assign unwanted children if symmetry was used
        children = [child for child in children if child not in unwanted_children]
        log.info(f"{parent.uid} has generated {children} children")
        parent.children_dimtag = set(children)

    # Some parent may have no children (due to symmetry), we need to remove them
    unwanted_parents = []
    for parent in aircraft_parts:
        if parent.part_type == "rotor":
            # Control possible 2D children not removed by the fragment symmetry unwanted_children
            for dimtag in list(parent.children_dimtag):
                try:  # check if the child exists in the model
                    gmsh.model.getType(*dimtag)

                except Exception:
                    # if not remove it from the parent
                    parent.children_dimtag.remove(dimtag)

        if not parent.children_dimtag:
            log.info(f"{parent.uid} has no more children due to symmetry, it will be deleted.")
            unwanted_parents.append(parent)

    # Remove unwanted parents
    # Redefine aircraft_parts
    if unwanted_parents:
        aircraft_parts = [part for part in aircraft_parts if part not in unwanted_parents]

    # Process and add children that are shared by two parent parts in the shared children list
    # and put them in a new unwanted children list

    unwanted_children = set()

    if len(aircraft_parts) > 1:
        for p, part in enumerate(aircraft_parts):
            for other_part in aircraft_parts[(p + 1) :]:
                shared_children = part.children_dimtag.intersection(other_part.children_dimtag)

                if shared_children:
                    part.children_dimtag = part.children_dimtag - shared_children
                    other_part.children_dimtag = other_part.children_dimtag - shared_children

                unwanted_children = unwanted_children.union(shared_children)

    # Convert set to list
    unwanted_children = list(unwanted_children)

    # Remove unwanted children from the model
    gmsh.model.occ.remove(unwanted_children, recursive=True)

    gmsh.model.occ.synchronize()
    log.info(f"Unwanted children {unwanted_children} removed from model.")

    # Associate good child with their parent
    good_children = []

    for parent in aircraft_parts:
        for child_dimtag in parent.children_dimtag:
            if child_dimtag not in unwanted_children:
                good_children.append(child_dimtag)
                log.info(f"Associating child {child_dimtag} to parent {parent.uid}")
                parent.associate_child_to_parent(child_dimtag)

    # Now that its clear which child entities in the model are from which parent part,
    # we can delete the child volumes and only keep the final domain.
    gmsh.model.occ.remove(good_children, recursive=True)

    gmsh.model.occ.synchronize()
    # Now only the final domain is left, in the model, we can find its entities
    # we will use the ModelPart class to store the entities of the final domain
    final_domain = ModelPart("fluid")
    left_volume = gmsh.model.getEntities(dim=3)

    len_left_volume = len(left_volume)
    if len_left_volume != 1:
        ValueError("Issue with intersection of two volumes.")

    log.info(f"Left volume {left_volume}.")
    final_domain.associate_child_to_parent(*left_volume)

    ###############
    # Clean model #
    ###############

    # As already discussed, it is often that two parts intersect each other,
    # it can also happened that some parts create holes inside other parts
    # for example a fuselage and 2 wings defined in the center of the fuselage
    # will create a holed fragment of the fuselage.
    # This is not a problem since this hole is not in the final domain volume
    # but there might be some lines and surfaces from the hole in the fuselage
    # that were not eliminated since they were shared by the unwanted children
    # and those lines and surfaces were assigned to the fuselage part.

    # thus we need to clean a bit the associated entities by the function
    # associate_child_to_parent() by comparing them with the entities of the
    # final domain

    # Create an aircraft part containing all the parts of the aircraft
    aircraft = ModelPart("aircraft")

    for part in aircraft_parts:
        part.clean_inside_entities(final_domain)

        aircraft.points.extend(part.points)
        aircraft.lines.extend(part.lines)
        aircraft.surfaces.extend(part.surfaces)
        aircraft.volume.extend(part.volume)
        aircraft.points_tags.extend(part.points_tags)
        aircraft.lines_tags.extend(part.lines_tags)
        aircraft.surfaces_tags.extend(part.surfaces_tags)
        aircraft.volume_tag.extend(part.volume_tag)

        # Set surface BC for each part of the aircraft
        if part.part_type == "engine":
            define_engine_bc(part, brep_dir)
        else:
            surfaces_group = gmsh.model.addPhysicalGroup(2, part.surfaces_tags)
            if part.part_type == "rotor":
                gmsh.model.setPhysicalName(
                    2, surfaces_group, f"{part.uid}{ACTUATOR_DISK_INLET_SUFFIX}"
                )
            else:
                gmsh.model.setPhysicalName(2, surfaces_group, f"{part.uid}")
            part.physical_groups.append(surfaces_group)

    log.info("Model has been cleaned.")

    # Farfield
    # farfield entities are simply the entities left in the final domain that
    # don't belong to the aircraft.

    farfield_surfaces = list(set(final_domain.surfaces) - set(aircraft.surfaces))
    farfield_points = list(set(final_domain.points) - set(aircraft.points))
    farfield_surfaces_tags = list(set(final_domain.surfaces_tags) - set(aircraft.surfaces_tags))

    if symmetry:
        symmetry_surfaces = []
        symmetry_surfaces_tags = []

        # If symmetry was used, it means that in the farfield entities we have
        # a surface that is the plane of symmetry, we need to find it
        # and remove it from the farfield entities

        # In general it is easy because the symmetry plane should be the only surface
        # in the farfield who touch the aircraft

        for farfield_surface in farfield_surfaces:
            _, adj_lines_tags = gmsh.model.getAdjacencies(*farfield_surface)

            if set(adj_lines_tags).intersection(set(aircraft.lines_tags)):
                farfield_surfaces.remove(farfield_surface)
                farfield_surfaces_tags.remove(farfield_surface[1])

                symmetry_surfaces.append(farfield_surface)
                symmetry_surfaces_tags.append(farfield_surface[1])

        symmetry_group = gmsh.model.addPhysicalGroup(2, symmetry_surfaces_tags)
        gmsh.model.setPhysicalName(2, symmetry_group, "symmetry")

    farfield = gmsh.model.addPhysicalGroup(2, farfield_surfaces_tags)
    gmsh.model.setPhysicalName(2, farfield, "Farfield")

    # Fluid domain
    ps = gmsh.model.addPhysicalGroup(3, final_domain.volume_tag)
    gmsh.model.setPhysicalName(3, ps, final_domain.uid)

    gmsh.model.occ.synchronize()
    log.info("Markers for SU2 generated")
    # Mesh Generation

    # Set mesh size of the aircraft parts

    # not that points common between parts will have the size of the last part
    # to set its mesh size.
    # Thus be sure to define mesh size in a certain order to control
    # the size of the points on boundaries.

    fuselage_maxlen, fuselage_minlen = fuselage_size(tixi)
    mesh_size_fuselage = ((fuselage_maxlen + fuselage_minlen) / 2) / fuselage_mesh_size_factor
    log.info(f"Mesh size fuselage={mesh_size_fuselage:.3f} m")

    create_branch(tixi, GMSH_MESH_SIZE_FUSELAGE_XPATH)
    tixi.updateDoubleElement(GMSH_MESH_SIZE_FUSELAGE_XPATH, mesh_size_fuselage, "%.3f")

    wing_maxlen, wing_minlen = wings_size(tixi)
    mesh_size_wing = ((wing_maxlen * 0.8 + wing_minlen) / 2) / wing_mesh_size_factor

    log.info(f"Mesh size wing={mesh_size_wing:.3f} m")

    create_branch(tixi, GMSH_MESH_SIZE_WINGS_XPATH)
    create_branch(tixi, GMSH_MESH_SIZE_CTRLSURFS_XPATH)

    tixi.updateDoubleElement(GMSH_MESH_SIZE_WINGS_XPATH, mesh_size_wing, "%.3f")

    AIRCRAFT_DICT = {
        "fuselage": mesh_size_fuselage,
        "wing": mesh_size_wing,
        "pylon": mesh_size_wing,
        "engine": mesh_size_engines,
        "rotor": mesh_size_propellers,
    }

    for part in aircraft_parts:
        if part.part_type in AIRCRAFT_DICT:
            part.mesh_size = AIRCRAFT_DICT[part.part_type]
            gmsh.model.mesh.setSize(part.points, AIRCRAFT_DICT[part.part_type])
            gmsh.model.setColor(part.surfaces, *MESH_COLORS[part.part_type], recursive=False)
        else:
            log.warning(f"Incorrect part.part_type {part.part_type} in generategmesh.py.")

    # Set mesh size and color of the farfield
    h_max_model = max(wing_maxlen, fuselage_maxlen)
    mesh_size_farfield = h_max_model * farfield_size_factor

    log.info(f"Farfield mesh size={mesh_size_farfield:.3f} m")

    gmsh.model.mesh.setSize(farfield_points, mesh_size_farfield)
    gmsh.model.setColor(farfield_surfaces, *MESH_COLORS["farfield"], recursive=False)

    if symmetry:
        gmsh.model.setColor(symmetry_surfaces, *MESH_COLORS["symmetry"], recursive=False)

    # Wing leading edge and trailing edge detection
    for part in aircraft_parts:
        if part.part_type in ["wing", "ctrlsurf"]:
            classify_wing(part, aircraft_parts)
            log.info(
                f"Classification of {part.uid} done"
                f" {len(part.wing_sections)} section(s) found "
            )

    # Generate advance meshing features
    mesh_fields = {"nbfields": 0, "restrict_fields": []}
    if refine_factor != 1:
        log.info(f"Refining wings with factor {refine_factor}")

        # Refine wings
        for part in aircraft_parts:
            if part.part_type == "wing":
                refine_wing_section(
                    mesh_fields,
                    final_domain.volume_tag,
                    aircraft,
                    part,
                    mesh_size_wing,
                    refine=refine_factor,
                    refine_truncated=refine_truncated,
                )

        # Domain mesh
        set_domain_mesh(
            mesh_fields,
            aircraft_parts,
            mesh_size_farfield,
            max(model_dimensions),
            final_domain.volume_tag,
            n_power_factor,
            n_power_field,
        )

        # Generate the minimal background mesh field
        mesh_fields = min_fields(mesh_fields)

    # Mesh generation
    log.info("Start of gmsh 2D surface meshing process")

    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.LcIntegrationPrecision", 1e-6)
    gmsh.model.occ.synchronize()

    gmsh.model.mesh.generate(1)
    gmsh.model.mesh.generate(2)

    gmsh.model.occ.synchronize()

    # Control of the mesh quality
    if refine_factor != 1 and auto_refine:
        bad_surfaces = []

        for part in aircraft_parts:
            refined_surfaces, mesh_fields = refine_small_surfaces(
                mesh_fields,
                part,
                mesh_size_farfield,
                max(model_dimensions),
                final_domain.volume_tag,
            )
            bad_surfaces.extend(refined_surfaces)

        log.info("Refining small surfaces.")

        if bad_surfaces:
            log.info(f"{len(bad_surfaces)} surface(s) needs to be refined")

            # Reset the background mesh
            mesh_fields = min_fields(mesh_fields)

            if bool_(open_gmsh):
                log.info("Insufficient mesh size surfaces are displayed in red")
                log.info("GMSH GUI is open, close it to continue...")
                gmsh.fltk.run()

            log.info("Start of gmsh 2D surface remeshing process")

            gmsh.model.mesh.generate(1)
            gmsh.model.mesh.generate(2)

            for surface in bad_surfaces:
                gmsh.model.setColor([(2, surface)], *MESH_COLORS["good_surface"], recursive=False)
            gmsh.model.occ.synchronize()

            log.info("Remeshing process finished")
            if bool_(open_gmsh):
                log.info("Corrected mesh surfaces are displayed in green")

    gmsh.model.occ.removeAllDuplicates()
    gmsh.model.occ.synchronize()

    # Fuse surfaces
    fusings: Dict[str, List] = {}
    tags_dict: Dict[str, List] = {}
    tags = []
    # Get all physical groups
    # TODO: Remap getPhysicalGroups
    surfaces: List[Tuple[int, int]] = gmsh.model.getPhysicalGroups(dim=2)

    fusing = True
    if fusing:
        for dim, tag in surfaces:
            name = gmsh.model.getPhysicalName(dim, tag)
            log.info(f"Dimension: {dim}, Tag: {tag}, Name: {name}")
            # Remove '_Seg{i}'
            root_name = re.sub(r"_Seg\d+", "", name)
            if root_name not in fusings:
                fusings[root_name] = []
                tags_dict[root_name] = []

            fusings[root_name].append(gmsh.model.getEntitiesForPhysicalGroup(dim, tag))
            tags_dict[root_name].append(tag)
            tags.append(tag)

        for fusing in fusings:
            fused_len = len(fusings[fusing])
            if fused_len > 1:
                fused_entities = list(set(
                    [entity for group in fusings[fusing] for entity in group]
                ))
                fused_tags = list(set(
                    [tag for tag in tags_dict[fusing]]
                ))
                log.info(f"Fusing {fused_len} wings named {fusing}")
                new_tag = max(tags) + 1
                tags.append(new_tag)
                gmsh.model.addPhysicalGroup(2, fused_entities, new_tag)
                gmsh.model.setPhysicalName(dim, new_tag, fusing)
                gmsh.model.removePhysicalGroups([(2, tag) for tag in fused_tags])
                gmsh.model.occ.synchronize()

    # Necessary for after fusing back wings
    gmsh.model.occ.removeAllDuplicates()
    gmsh.model.occ.synchronize()

    # Apply smoothing
    log.info("2D mesh smoothing process started")
    gmsh.model.mesh.optimize("Laplace2D", niter=10)
    log.info("Smoothing process finished")

    # gmsh.model.occ.removeAllDuplicates()

    # Synchronize again to update the model after removing duplicates
    gmsh.model.occ.synchronize()

    surfaces: List[Tuple[int, int]] = gmsh.model.getPhysicalGroups(dim=2)

    for dim, tag in surfaces:
        name = gmsh.model.getPhysicalName(dim, tag)
        log.info(f"New Dimension: {dim}, Tag: {tag}, Name: {name}")

    if surf is None:
        surface_mesh_path = Path(results_dir, "surface_mesh.msh")
        gmsh.write(str(surface_mesh_path))
        # cgnsmesh_path = Path(results_dir, "mesh.cgns")
        # gmsh.write(str(cgnsmesh_path))
    else:
        surface_mesh_path = Path(results_dir, f"surface_mesh_{surf}_{angle}.msh")
        gmsh.write(str(surface_mesh_path))

    if bool_(open_gmsh):
        log.info("Result of 2D surface mesh")
        log.info("GMSH GUI is open, close it to continue...")
        gmsh.fltk.run()

    log.info("Start of gmsh 3D volume meshing process")
    gmsh.model.mesh.generate(3)
    gmsh.model.occ.synchronize()

    if rotor_model:
        log.info("Duplicating disk actuator mesh surfaces")
        for part in aircraft_parts:
            if part.part_type == "rotor":
                duplicate_disk_actuator_surfaces(part)

        # option to use when duplicating disk actuator surfaces
        gmsh.option.setNumber("Mesh.SaveAll", 1)

        # Control surface orientation
        control_disk_actuator_normal()

    if surf is None:
        su2mesh_path = write_gmsh(results_dir, "mesh.su2")
    else:
        mesh_name = f"mesh_{surf}_{angle}"
        su2mesh_path = write_gmsh(results_dir, f"{mesh_name}.su2")

    process_gmsh_log(gmsh.logger.get())

    gmsh.model.occ.synchronize()

    log.info("Mesh generation finished")
    # Create duplicated mesh surface for disk actuator

    if not testing_gmsh:
        gmsh.clear()
        gmsh.finalize()

    return su2mesh_path

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")
