"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Use .brep files parts of an airplane to generate a fused airplane in GMSH with
the OCC kernel. Then Spherical farfield is created arround the airplane and the
resulting domain is meshed using gmsh

Python version: >=3.7

| Author: Tony Govoni
| Creation: 2022-03-22

TODO:

    -

"""


# ==============================================================================
#   IMPORTS
# ==============================================================================
import gmsh
import os
from ceasiompy.utils.ceasiomlogger import get_logger
import numpy as np
from ceasiompy.CPACS2GMSH.func.wingclassification import classify_wing
from ceasiompy.CPACS2GMSH.func.advancemeshing import (
    refine_wing_section,
    set_fuselage_mesh,
    set_farfiled_mesh,
)

log = get_logger(__file__.split(".")[0])


# ==============================================================================
#   CLASSES
# ==============================================================================
class AircraftPart:
    """
    A class to represent part of the aircraft in order to classify its entities
    ...

    Attributes
    ----------
    name : str
        name of the part which correspond to its .brep file name

    """

    def __init__(self, name):

        self.name = name

        # dimtag
        self.points = []
        self.lines = []
        self.surfaces = []
        self.volume = []
        # tag only
        self.points_tags = []
        self.lines_tags = []
        self.surfaces_tags = []
        self.volume_tag = []
        # children
        self.childs_dimtag = set()


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def get_entities_from_volume(volume_dimtag):
    surfaces_dimtags = gmsh.model.getBoundary(
        volume_dimtag, combined=True, oriented=False, recursive=False
    )

    lines_dimtag = list(
        set().union(
            *[
                gmsh.model.getBoundary([surface], combined=True, oriented=False, recursive=False)
                for surface in surfaces_dimtags
            ]
        )
    )
    lines_dimtag.sort()
    points_dimtag = list(
        set().union(
            *[
                gmsh.model.getBoundary([surface], combined=True, oriented=False, recursive=True)
                for surface in surfaces_dimtags
            ]
        )
    )
    points_dimtag.sort()

    return surfaces_dimtags, lines_dimtag, points_dimtag


def associate_child_to_parent(child_dimtag, parent):
    """
    Associate childs to parent
    """

    child_volume = [child_dimtag]

    child_surfaces, child_lines, child_points = get_entities_from_volume(child_volume)

    # first get the dimtags
    child_volume_tag = [dimtag[1] for dimtag in child_volume]
    child_surfaces_tags = [dimtag[1] for dimtag in child_surfaces]
    child_lines_tags = [dimtag[1] for dimtag in child_lines]
    child_points_tags = [dimtag[1] for dimtag in child_points]

    # store in parent parts for latter use
    parent.points.extend(child_points)
    parent.lines.extend(child_lines)
    parent.surfaces.extend(child_surfaces)
    parent.volume.extend(child_volume)

    parent.points_tags.extend(child_points_tags)
    parent.lines_tags.extend(child_lines_tags)
    parent.surfaces_tags.extend(child_surfaces_tags)
    parent.volume_tag.extend(child_volume_tag)


def generate_gmsh(
    brep_dir_path,
    results_dir,
    open_gmsh=False,
    farfield_factor=5,
    symmetry=False,
    mesh_size_farfield=12,
    mesh_size_fuselage=0.2,
    mesh_size_wings=0.2,
):
    """
    Function to generate a mesh from brep files forming an airplane
    Function 'generate_gmsh' is a subfunction of CPACS2GMSH which return a
    mesh file.
    The airplane is fused with the different brep files : fuselage, wings and
    other parts are identified anf fused together, then a farfield is generated
    and the airplane is substracted to him to generate the final fluid domain
    marker of each airplane part and farfield surfaces is reported in the mesh
    file.
    Args:
    ----------
    brep_dir_path : (path)
        Path to the directory containing the brep files
    results_dir : (path)
        Path to the directory containing the result (mesh) files
    open_gmsh : bool
        Open gmsh GUI after the mesh generation if set to true
    farfield_factor = float
        Factor to enlarge the farfield : factor times the largest dimension(x,y,z)
        of the aircraft
    symmetry : bool
        If set to true, the mesh will be generated with symmetry wrt the x,z plane
    mesh_size_farfield : float
        Size of the farfield mesh
    mesh_size_fuselage : float
        Size of the fuselage mesh
    mesh_size_wings : float
        Size of the wing mesh

    """
    gmsh.initialize()

    # import each aircraft original parts / parent parts
    aircraft_parts = []
    parts_parent_dimtag = []

    for file in os.listdir(brep_dir_path):

        if ".brep" in file:

            log.info(f"Importing :{file[:-5]}")

            # Import the part and create the aircraft part object

            part_entities = gmsh.model.occ.importShapes(
                os.path.join(brep_dir_path, file), highestDimOnly=False
            )
            gmsh.model.occ.synchronize()

            part_obj = AircraftPart(f"{file[:-5]}")
            aircraft_parts.append(part_obj)
            parts_parent_dimtag.append(part_entities[0])

    # create external domain for the farfield
    bb = gmsh.model.getBoundingBox(-1, -1)
    model_dimensions = [abs(bb[0] - bb[3]), abs(bb[1] - bb[4]), abs(bb[2] - bb[5])]
    model_center = [
        bb[0] + model_dimensions[0] / 2,
        bb[1] + model_dimensions[1] / 2,
        bb[2] + model_dimensions[2] / 2,
    ]

    domain_length = farfield_factor * max(model_dimensions)
    farfield = gmsh.model.occ.addSphere(*model_center, domain_length)
    gmsh.model.occ.synchronize()

    ext_domain = [(3, farfield)]

    if symmetry:
        log.info("Preparing: symmetry operation")
        sym_plane = gmsh.model.occ.addDisk(*model_center, domain_length, domain_length)
        sym_vector = [0, 1, 0]
        plane_vector = [0, 0, 1]
        if sym_vector != plane_vector:
            rotation_axis = np.cross(sym_vector, plane_vector)
            gmsh.model.occ.rotate([(2, sym_plane)], *model_center, *rotation_axis, np.pi / 2)
            sym_box = gmsh.model.occ.extrude(
                [(2, sym_plane)], *(np.multiply(sym_vector, -domain_length * 1.1))
            )
        parts_parent_dimtag.append(sym_box[1])

    # Generate fragment beteen the aircraft and the farfield

    log.info("Start fragment operation")

    fragments_dimtag, childs_dimtag = gmsh.model.occ.fragment(ext_domain, parts_parent_dimtag)
    gmsh.model.occ.synchronize()

    log.info("Fragment operation finished")

    """
    fragment produce fragments_dimtag and childs_dimtag

    fragments_dimtag is a list of tuples (dimtag, tag) of all the volumes in the model
    the firts fragment is the enitre domain, each other fragment are subvolume of the domain

    childs_dimtag is a list list of tuples (dimtag, tag)
    the first list is associated to the entire domain as for fragments_dimtag, we dont need it
    so for the following we work with childs_dimtag[1:]

    The rest of childs_dimtag are list of tuples (dimtag, tag) that represent the volumes in the
    model childs_dimtag is "sorted" according to the order of importation of the parent parts.
    for example if the first part imported was "fuselage1" then the first childs_dimtag is
    all the "child" volumes in the model that are from the "parent" "fuselage1"
    we can then associate each entities in the model to their parent origin

    When two parents part ex. a fuselage and a wing intersect each other
    two childs are generated for both parts, thus if a child is shared by
    two parent parts (or more), then this child is a volume given
    by the intersection of the two parent parts, we don't need them and some
    of its surfaces, lines and point in the final models

    Thus we need to find those unwanted child and their entites that don't belong
    to the final model, and remove them

    afterward the entities of each child will be associated with their parent part names
    then we can delete all the child in the model, and only keep the final domain
    Removing a child will not delete its entities shared by the final domain, this means that
    at the end we will only have one volume with all the surfaces,lines,points assigned
    to the original parent parts imported at the begging of the function

    If symmetry is applied the last childs_dimtag is all the volume in the symmerty cylinder
    thus the we can easily remove them and only keep the volumes of half domain
    """
    unwanted_childs = []
    if symmetry:
        # take the unwanted childs from symmetry
        unwanted_childs = childs_dimtag[-1]

        # remove them from the model
        gmsh.model.occ.remove(unwanted_childs, recursive=True)
        gmsh.model.occ.synchronize()

    print("update child removed from symmertry")
    gmsh.model.occ.synchronize()
    gmsh.fltk.run()

    # Get the final domain (farfield fluid domain with the aircraft volume removed)

    final_domain = fragments_dimtag[0]

    # Get the childs of the aicraft parts

    aircraft_parts_childs_dimtag = childs_dimtag[1:]

    log.info("Before/after fragment operation relations:")
    for parent, childs in zip(aircraft_parts, aircraft_parts_childs_dimtag):

        # don't assign unwanted childs if symmetry was used

        childs = [child for child in childs if child not in unwanted_childs]

        log.info(f"{parent.name} has generated {childs} childs")
        parent.childs_dimtag = set(childs)

    # Some parent may have no childs (due to symmetry), we need to remove them
    for parent in aircraft_parts:
        if not parent.childs_dimtag:
            log.info(f"{parent.name} has no more childs due to symmetry, it will be deleted")

    # Process and add childs that are shared by two parent parts in the shared childs list
    # and put them in a new unwanted childs list

    unwanted_childs = []

    for part in aircraft_parts:
        for other_part in aircraft_parts:

            if part != other_part:
                shared_childs = part.childs_dimtag.intersection(other_part.childs_dimtag)

                if part.childs_dimtag.intersection(other_part.childs_dimtag):
                    part.childs_dimtag = part.childs_dimtag - shared_childs
                    other_part.childs_dimtag = other_part.childs_dimtag - shared_childs

                unwanted_childs.extend(list(shared_childs))

    # remove duplicated from the unwanted child list

    unwanted_childs = list(set(unwanted_childs))

    # and remove them from the model

    gmsh.model.occ.remove(unwanted_childs, recursive=True)
    gmsh.model.occ.synchronize()
    log.info(f"Unwanted childs {unwanted_childs} removed from model")

    print("inside volumes should be removed from the model")
    gmsh.model.occ.synchronize()
    gmsh.fltk.run()

    # Associate good child with their parent
    good_childs = []
    for parent in aircraft_parts:
        for child_dimtag in parent.childs_dimtag:
            if child_dimtag not in unwanted_childs:
                good_childs.append(child_dimtag)
                log.info(f"Associating child {child_dimtag} to parent {parent.name}")
                associate_child_to_parent(child_dimtag, parent)

    # Now that its clear which child entites in the model are from which parent part,
    # we can delete the child volumes and only keep the final domain

    gmsh.model.occ.remove(good_childs, recursive=True)
    gmsh.model.occ.synchronize()
    print("all other volumes should be removed from the model")
    gmsh.model.occ.synchronize()
    gmsh.fltk.run()

    # Now only the final domain is left, in the model
    # Find the final domain entites
    final_domain_volume = [final_domain]
    (
        final_domain_surfaces,
        final_domain_lines,
        final_domain_points,
    ) = get_entities_from_volume(final_domain_volume)

    final_domain_surfaces_tags = [dimtag[1] for dimtag in final_domain_surfaces]
    final_domain_lines_tags = [dimtag[1] for dimtag in final_domain_lines]
    final_domain_points_tags = [dimtag[1] for dimtag in final_domain_points]

    """
    As already discussed, it is often that two parts intersect each other,
    it can also happend that some parts create holes inside other parts
    for example a fuselage and 2 wings defined in the center of the fuselage
    will create a holed fragment of the fuselage
    This is not a problem since this hole is not in the final domain volume
    but they may be some lines and surfaces from the hole in the fuselage
    that were not eliminated since they were shared by the unwanted childs
    and those lines and surfaces were assigned to the fuselage part

    thus we need to clean a bit the associated entities by the function
    associate_child_to_parent() by comparing them with the entities of the
    final domain

    """
    for parent in aircraft_parts:
        # detect only shared entities with the final domain

        parent.surfaces = list(set(parent.surfaces).intersection(set(final_domain_surfaces)))
        parent.lines = list(set(parent.lines).intersection(set(final_domain_lines)))
        parent.points = list(set(parent.points).intersection(set(final_domain_points)))

        parent.surfaces_tags = list(
            set(parent.surfaces_tags).intersection(set(final_domain_surfaces_tags))
        )
        parent.lines_tags = list(set(parent.lines_tags).intersection(set(final_domain_lines_tags)))
        parent.points_tags = list(
            set(parent.points_tags).intersection(set(final_domain_points_tags))
        )
        # # generate physical groups
        # surfaces_group = gmsh.model.addPhysicalGroup(2, parent.surfaces_tags)
        # gmsh.model.setPhysicalName(2, surfaces_group, f"{parent.name}_surfaces")
        # lines_group = gmsh.model.addPhysicalGroup(1, parent.lines_tags)
        # gmsh.model.setPhysicalName(1, lines_group, f"{parent.name}_lines")
        # points_group = gmsh.model.addPhysicalGroup(0, parent.points_tags)
        # gmsh.model.setPhysicalName(0, points_group, f"{parent.name}_points")

    log.info("Model cleaned")

    # Create an aircraft part containing all the parts of the aircraft

    aircraft = AircraftPart("aircraft")

    for part in aircraft_parts:

        aircraft.points.extend(part.points)
        aircraft.lines.extend(part.lines)
        aircraft.surfaces.extend(part.surfaces)
        aircraft.volume.extend(part.volume)
        aircraft.points_tags.extend(part.points_tags)
        aircraft.lines_tags.extend(part.lines_tags)
        aircraft.surfaces_tags.extend(part.surfaces_tags)
        aircraft.volume_tag.extend(part.volume_tag)

    # Form physical groups for SU2

    bc_aircraft = gmsh.model.addPhysicalGroup(2, aircraft.surfaces_tags)
    gmsh.model.setPhysicalName(2, bc_aircraft, "aircraft")

    # Farfield
    # farfield entities are simply the entites left in the final domain
    # that don't belong to the aircraft
    farfield_surfaces = list(set(final_domain_surfaces) - set(aircraft.surfaces))
    farfield_lines = list(set(final_domain_lines) - set(aircraft.lines))
    farfield_points = list(set(final_domain_points) - set(aircraft.points))

    farfield_surfaces_tags = list(set(final_domain_surfaces_tags) - set(aircraft.surfaces_tags))
    farfield_lines_tags = list(set(final_domain_lines_tags) - set(aircraft.lines_tags))
    farfield_points_tags = list(set(final_domain_points_tags) - set(aircraft.points_tags))

    if symmetry:

        symmetry_surfaces = []
        symmetry_surfaces_tags = []
        """
        If symmetry was used, it means that in the farfield entites we have
        a surface that is the plane of symmetry, we need to find it
        and remove it from the farfield entities

        In general it is easy because the symmetry plane should be the only surface
        in the farfield who touch the aircraft
        """

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
    gmsh.model.setPhysicalName(2, farfield, "farfield")

    # Fluid domain
    final_domain_volume_tag = [final_domain_volume[0][1]]
    ps = gmsh.model.addPhysicalGroup(3, final_domain_volume_tag)
    gmsh.model.setPhysicalName(3, ps, "fluid")

    gmsh.model.occ.synchronize()
    log.info("Markers for SU2 generated")

    # Mesh Generation

    # Set mesh size of the aircraft parts
    for part in aircraft_parts:
        if "fuselage" in part.name:
            gmsh.model.mesh.setSize(part.points, mesh_size_fuselage)
        if "wing" in part.name:
            gmsh.model.mesh.setSize(part.points, mesh_size_wings)

    # Set mesh size of the farfield
    gmsh.model.mesh.setSize(farfield_points, mesh_size_farfield)

    # Color the mesh according to the aircraft parts

    # Color code
    mesh_color_wing = (0, 255, 0)
    mesh_color_fus = (0, 0, 255)
    mesh_color_farfield = (255, 255, 0)
    mesh_color_symmetry = (255, 0, 255)

    # Color assignation for each part

    for part in aircraft_parts:

        if "wing" in part.name:
            color = mesh_color_wing

        if "fuselage" in part.name:
            color = mesh_color_fus
        gmsh.model.setColor(part.surfaces, *color, a=150, recursive=False)

    gmsh.model.setColor(farfield_surfaces, *mesh_color_farfield, a=150, recursive=False)
    if symmetry:
        gmsh.model.setColor(symmetry_surfaces, *mesh_color_symmetry, a=150, recursive=False)

    # Generate advance meshing features
    # mesh_fields = {"nbfields": 0, "restrict_fields": []}
    # for part in aircraft_parts:
    #     if "wing" in part.name:
    #         classify_wing(part, aircraft_parts)
    #         nb_sect = len(part.wing_sections)
    #         log.info(f"Classification of {part.name} done, {nb_sect} section(s) found ")
    #         refine_wing_section(
    #             mesh_fields,
    #             part,
    #             mesh_size_wings,
    #             refine=2,
    #             chord_percent=0.2,
    #         )
    #     if "fuselage" in part.name:
    #         set_fuselage_mesh(mesh_fields, part, mesh_size_fuselage)
    # set_farfiled_mesh(mesh_fields, farfield_surfaces, mesh_size_farfield)
    # mesh_fields["nbfields"] += 1
    # gmsh.model.mesh.field.add("Min", mesh_fields["nbfields"])
    # gmsh.model.mesh.field.setNumbers(
    #     mesh_fields["nbfields"], "FieldsList", mesh_fields["restrict_fields"]
    # )
    # gmsh.model.mesh.field.setAsBackgroundMesh(mesh_fields["nbfields"])
    # gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    # gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    # gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

    # Mesh generation
    gmsh.model.occ.synchronize()

    gmsh.model.mesh.generate(1)
    gmsh.model.mesh.generate(2)

    # Apply smoothing

    gmsh.model.mesh.optimize("Laplace2D", niter=1)

    if open_gmsh:
        log.info("Result of 2D surface mesh")
        gmsh.fltk.run()

    gmsh.model.mesh.generate(3)
    gmsh.model.occ.synchronize()

    su2mesh_path = os.path.join(results_dir, "mesh.su2")
    gmsh.write(su2mesh_path)

    if open_gmsh:
        log.info("Result of the 3D mesh")
        gmsh.fltk.run()

    gmsh.finalize()
    return su2mesh_path


# ==============================================================================
#    MAIN
# ==============================================================================
if __name__ == "__main__":
    generate_gmsh(
        "test_files/concorde",
        "",
        open_gmsh=True,
        farfield_factor=4,
        symmetry=True,
        mesh_size_farfield=12,
        mesh_size_fuselage=0.1,
        mesh_size_wings=0.1,
    )
    print("Nothing to execute!")
