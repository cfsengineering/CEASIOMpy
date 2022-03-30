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

log = get_logger(__file__.split(".")[0])


# ==============================================================================
#   CLASSES
# ==============================================================================
class AircraftPart:
    """
    A class to represent part of the aircraft in order to keep track of each gmsh
    part entities and their location in space

    For each AircraftPart, its surfaces,lines and points locations are stored
    in order to remap them correctly when gmsh boolean operations are performed
    ...

    Attributes
    ----------
    dim_tag : tuple
        tuple (dim,tag) of the gmsh volume of the aircraft part
    name : str
        name of the part which correspond to its .brep file name

    """

    def __init__(self, dim_tag, name):
        self.dim_tag = dim_tag
        self.name = name
        self.bb, self.sizes = get_visual_bounding_box(self.dim_tag, 1e-3)
        self.points = []
        self.lines = []
        self.surfaces = []
        self.surfaces_tags = []
        self.score = give_score(self)

    def get_entities(self):
        """
        Function to grab the points,lines and surfaces entites of the part
        ...
        """

        self.points = sorted(
            set(gmsh.model.occ.getEntitiesInBoundingBox(*self.bb, dim=0)),
            key=lambda tup: tup[1],
        )
        self.lines = sorted(
            set(gmsh.model.occ.getEntitiesInBoundingBox(*self.bb, dim=1)),
            key=lambda tup: tup[1],
        )
        self.surfaces = sorted(
            set(gmsh.model.occ.getEntitiesInBoundingBox(*self.bb, dim=2)),
            key=lambda tup: tup[1],
        )

    def clear_entities(self):
        """
        Function to reset the entities of the part
        ...
        """

        self.points = list()

        self.lines = list()

        self.surfaces = list()

    def get_entities_bb_visual(self, enhance=0):
        """
        Function to get the visual bouding box of each entity in the part
        ...

        Args:
        ----------
        enhance : float
            enhance factor for the bounding box size, sometimes OCC doesnt detect
            entities on the boundary of the original bb, an small enhance help to
            resolve this issue
        ...
        """

        self.points_bb_visual = [get_visual_bounding_box(point, enhance) for point in self.points]
        self.lines_bb_visual = [get_visual_bounding_box(line, enhance) for line in self.lines]
        self.surfaces_bb_visual = [
            get_visual_bounding_box(surface, enhance) for surface in self.surfaces
        ]

    def get_entities_bb(self):
        """
        Function to get the strict bouding box of each entity in the part
        ...
        """
        self.points_bb = [gmsh.model.occ.getBoundingBox(*point) for point in self.points]
        self.lines_bb = [gmsh.model.occ.getBoundingBox(*line) for line in self.lines]
        self.surfaces_bb = [gmsh.model.occ.getBoundingBox(*surface) for surface in self.surfaces]

    def remap_entites(self):
        """
        Function to remap the entities of the part using the bb of the part entites
        ...
        """
        for bb in self.points_bb:

            points_found = gmsh.model.occ.getEntitiesInBoundingBox(*bb, dim=0)
            [self.points.append(point) for point in points_found]

        self.points = set(self.points)

        for bb in self.lines_bb:

            lines_found = gmsh.model.occ.getEntitiesInBoundingBox(*bb, dim=1)
            [self.lines.append(line) for line in lines_found]

        self.lines = set(self.lines)

        for bb in self.surfaces_bb:

            surfaces_found = gmsh.model.occ.getEntitiesInBoundingBox(*bb, dim=2)
            [self.surfaces.append(surface) for surface in surfaces_found]

        self.surfaces = set(self.surfaces)


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def get_visual_bounding_box(dim_tag, enhance=0):
    """
    Function to find the bounding box (bb) of a gmsh object
    The bounding box is extend by a fraction of its size in order to prevent
    non detection of entites on the boundary of the original bb
    ...

    Args:
    ----------
    dim_tag : tuple
        tuple (dim,tag) is the dim and tag of the gmsh volume of the airplane part
    enhance : float
        scaling factor to enhance the size of the bounding box
    ...

    Return :
    ----------
    bb : tuple
        tuple containing the bottom right and top left location of the bb
    size : tuple
        tuple  containing the size of the bb in each dimention
    """

    bb = list(gmsh.model.occ.getBoundingBox(*dim_tag))
    sizes = [abs(bb[0] - bb[3]), abs(bb[1] - bb[4]), abs(bb[2] - bb[5])]

    # Extend a bit the bounding_box if enhance is non zero
    bb[0] = bb[0] - sizes[0] * enhance
    bb[1] = bb[1] - sizes[1] * enhance
    bb[2] = bb[2] - sizes[2] * enhance
    bb[3] = bb[3] + sizes[0] * enhance
    bb[4] = bb[4] + sizes[1] * enhance
    bb[5] = bb[5] + sizes[2] * enhance

    # Update size due to the extend
    sizes = (abs(bb[0] - bb[3]), abs(bb[1] - bb[4]), abs(bb[2] - bb[5]))

    return (bb[0], bb[1], bb[2], bb[3], bb[4], bb[5]), sizes


def give_score(part):
    """
    Function to give a score to a part, a part with a higher score will be given
    priority to the surface assignation
    ...

    Args:
    ----------
    part : AircraftPart
        aircraft part to assign a score
    ...
    """
    if "engine" in part.name:
        return 3
    if "fuselage" in part.name:
        return 2
    if "wing" in part.name:
        return 1


def hierarchy_surface(part1, part2, surfaces, operation):
    """
    Function to select which of two part sharing an common surface should be the final
    parent of the surface
    ...

    Args:
    ----------
    part1 : AircraftPart
        aircraft part sharing a surface with part2
    part2 : AircraftPart
        aircraft part sharing a surface with part1
    operation : int
        operation to perform on the the surface : 0 := remove, 1 := add
    ...
    """

    # Get score of each part
    part1_score = part1.score
    part2_score = part2.score

    if part1_score >= part2_score:
        if operation == 0:

            [part2.surfaces.remove(surface) for surface in surfaces]
            return log.info(f"{surfaces} were removed from {part2.name}")

        else:

            part1.surfaces.add(surfaces)
            return log.info(f"{surfaces} was added to {part1.name}")

    else:
        if operation == 0:

            [part1.surfaces.remove(surface) for surface in surfaces]
            return log.info(f"{surfaces} were removed from {part1.name}")

        else:

            part2.surfaces.add(surfaces)
            return log.info(f"{surfaces} was added to {part2.name}")


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
    """Function to generate a mesh from brep files forming an airplane
    Function 'generate_gmsh' is a subfunction of CPACS2GMSH which return a
    mesh file.
    The airplane is fused with the different brep files : fuselage, wings and
    other parts are identified anf fused together, then a farfield is generated
    and the airplane is substracted to him to generate the final fluid domain
    marker of each airplane part and farfield surfaces is reported in the mesh
    file.
    Args:
        brep_dir_path (path):  Path to the directory containing the brep files
    """
    gmsh.initialize()

    # import each aircraft original part and find the entities bounding box (bb)
    # when bbs are found, remove the part from the model the part

    aircraft_parts = []

    # if symmetry:

    #     # Delete the symmetric part of the aicraft
    #     log.info("Symmetry detected, deleting unused symmetric part of the aircraft")

    #     for file in os.listdir(brep_dir_path):
    #         if "_m" in file:
    #             os.remove(os.path.join(brep_dir_path, file))

    for file in os.listdir(brep_dir_path):

        if ".brep" in file:

            log.info(f"Finding boundary boxes :{file[:-5]}")

            # Import the part and create the aircraft part object

            part = gmsh.model.occ.importShapes(
                os.path.join(brep_dir_path, file), highestDimOnly=True
            )

            gmsh.model.occ.synchronize()
            part_obj = AircraftPart(*part, file[:-5])

            gmsh.model.occ.synchronize()
            aircraft_parts.append(part_obj)

            # since the part is alone in the model we can grab its entities

            part_obj.points = sorted(
                set(gmsh.model.occ.getEntities(dim=0)), key=lambda tup: tup[1]
            )
            part_obj.lines = sorted(set(gmsh.model.occ.getEntities(dim=1)), key=lambda tup: tup[1])
            part_obj.surfaces = sorted(
                set(gmsh.model.occ.getEntities(dim=2)), key=lambda tup: tup[1]
            )

            # Find the bounding box of the part (strict and enhance)

            part_obj.get_entities_bb()
            part_obj.get_entities_bb_visual(1e-3)

            # bb found, so we can clear the entites and remove the part

            part_obj.clear_entities()
            gmsh.model.occ.remove([part_obj.dim_tag], recursive=True)
            gmsh.model.occ.synchronize()

    nb_parts = len(aircraft_parts)

    # Fuse operation of the aircraft

    for file in os.listdir(brep_dir_path):
        if ".brep" in file:

            log.info(f"Preparing:{file[:-5]}")

            # reimport

            part = gmsh.model.occ.importShapes(
                os.path.join(brep_dir_path, file), highestDimOnly=True
            )

            # remap the correct volume tag
            for original_part in aircraft_parts:
                if original_part.name == str(file[:-5]):

                    original_part.dim_tag = tuple(*part)

    gmsh.model.occ.synchronize()

    part_to_fuse = [part.dim_tag for part in aircraft_parts]

    log.info(f"Start Fusing process, {len(part_to_fuse)} parts to fuse")
    if len(part_to_fuse) > 1:

        fused_shape, side = gmsh.model.occ.fuse(
            [part_to_fuse[0]], part_to_fuse[1:], removeObject=True, removeTool=True
        )
        gmsh.model.occ.synchronize()

        # An aircraft part representing the whole aircraft is created
        aircraft = AircraftPart(*fused_shape, "aircraft")

    else:

        fused_shape = part_to_fuse[0]
        aircraft = aircraft_parts[0]

    # create external domain for the farfield

    center_aircraft = gmsh.model.occ.get_center_of_mass(*aircraft.dim_tag)
    ext_domain = gmsh.model.occ.addSphere(*center_aircraft, farfield_factor * max(aircraft.sizes))
    gmsh.model.occ.synchronize()

    # cut the fluid with the airplane

    final_domain, side = gmsh.model.occ.cut(
        [(3, ext_domain)],
        [aircraft.dim_tag],
        removeObject=True,
        removeTool=True,
    )
    gmsh.model.occ.synchronize()

    # Cut the domain for symmetry

    if symmetry:

        domain_lenght = farfield_factor * max(aircraft.sizes)
        box_symm = gmsh.model.occ.addBox(
            (center_aircraft[0] - domain_lenght) * 1.05,
            center_aircraft[1] - 2 * domain_lenght,
            (center_aircraft[2] - domain_lenght) * 1.05,
            2 * domain_lenght * 1.05,
            2 * domain_lenght,
            2 * domain_lenght * 1.05,
        )

        gmsh.model.occ.synchronize()

        # cut the domain in half

        final_domain, side = gmsh.model.occ.cut(
            [(3, final_domain[0][1])],
            [(3, box_symm)],
            removeObject=True,
            removeTool=True,
        )
        gmsh.model.occ.synchronize()

    # Find the aircraft entities after all the boolean operations
    aircraft.get_entities()

    """
    After the fuse and the boolean operation all the entites are unknown,
    we need to find from which original part
    of the aircraft they belong to
    """

    # for each aircraft original part, find the entities inside their entity bounding box

    for part in aircraft_parts:

        log.info(f"Remapping :{part.name}")
        part.remap_entites()

    # Check if remaping has been done correctly

    Flag_duplicated_surface = False
    Flag_missing_surface = False

    aircraft_total_surfaces = len(aircraft.surfaces)

    # 1) search for duplicated surface that may be shared by more than one part"
    for i in range(nb_parts):
        for j in range(nb_parts):

            if i != j:
                twin_surfaces = aircraft_parts[i].surfaces.intersection(aircraft_parts[j].surfaces)

                if twin_surfaces:  # check if not empty
                    # One of the two part need to transfert the duplicated surface to the other
                    Flag_duplicated_surface = True
                    hierarchy_surface(aircraft_parts[i], aircraft_parts[j], twin_surfaces, 0)

    # count if the number of surface remaped is equal to the fused aircraft surfaces
    check_surface = sum([len(part.surfaces) for part in aircraft_parts])

    if Flag_duplicated_surface:

        log.info("Duplicated surfaces were found, second remapping triggered")
        if check_surface == aircraft_total_surfaces:

            log.info("Duplicate surface remapping successful")

        else:

            Flag_missing_surface = True
            log.info("Duplicate surface remapping done , but there is still :")
            log.info(f"{aircraft_total_surfaces - check_surface} missing surfaces")

    if check_surface != aircraft_total_surfaces:

        Flag_missing_surface = True
        log.info(f"{aircraft_total_surfaces - check_surface}missing surfaces")

    # 2) search for missing surfaces

    if Flag_missing_surface:

        log.info("Missing surfaces remapping triggered")

        # find which surface is missing

        surfaces_found = set.union(*[part.surfaces for part in aircraft_parts])
        surfaces_missing = set(aircraft.surfaces).difference(surfaces_found)

        # remap the missing surfaces

        for surface in surfaces_missing:
            potential_parts = []

            for part in aircraft_parts:
                surfaces_in_part = set(gmsh.model.occ.getEntitiesInBoundingBox(*part.bb, dim=2))

                if surface in surfaces_in_part:
                    potential_parts.append(part)

            if len(potential_parts) == 1:

                part.surfaces.add(surface)
                log.info(f"{surface} was added to {part.name}")

            if len(potential_parts) == 2:

                hierarchy_surface(*potential_parts, surface, 1)

            if len(potential_parts) > 2:
                raise ValueError(f"Too many parts found for surface{surface}")

        check_surface = sum([len(part.surfaces) for part in aircraft_parts])

        if check_surface != aircraft_total_surfaces:
            log.info("There is still missing surfaces, check that your cpacs geometry is healthy")

        else:
            log.info("Missing surfaces remapping successful ")

    # Remap the entities of the farfield:

    final_domain_points = gmsh.model.getEntities(dim=0)
    final_domain_lines = gmsh.model.getEntities(dim=1)
    final_domain_surfaces = gmsh.model.getEntities(dim=2)

    # Find the entites belonging to the farfield

    farfield_points = set([point for point in final_domain_points if point not in aircraft.points])
    farfield_lines = set([line for line in final_domain_lines if line not in aircraft.lines])
    farfield_surfaces = set(
        [surface for surface in final_domain_surfaces if surface not in aircraft.surfaces]
    )

    # check sum on the entire domain:

    check_points = len(aircraft.points) + len(farfield_points)
    check_lines = len(aircraft.lines) + len(farfield_lines)
    check_surfaces = aircraft_total_surfaces + len(farfield_surfaces)

    if (
        (len(final_domain_points) != check_points)
        or (len(final_domain_lines) != check_lines)
        or (len(final_domain_surfaces) != check_surfaces)
    ):
        raise ValueError("Unmatching number of entities in the current model")

    else:
        log.info("Remapping of the external domain as been successfull")

    # Form physical groups

    # Aircraft

    for part in aircraft_parts:
        for surface in part.surfaces:

            part.surfaces_tags.append(surface[1])

        bc_part = gmsh.model.addPhysicalGroup(2, part.surfaces_tags)
        gmsh.model.setPhysicalName(2, bc_part, part.name)

    # Farfield
    if symmetry:
        symm_plane_bb = (
            (center_aircraft[0] - domain_lenght) * 1.05,
            -0.1,
            (center_aircraft[2] - domain_lenght) * 1.05,
            (center_aircraft[0] + domain_lenght) * 1.05,
            0.1,
            (center_aircraft[0] + domain_lenght) * 1.05,
        )
        # Find the entity of the symmetry plane
        symm_surface = gmsh.model.occ.getEntitiesInBoundingBox(*symm_plane_bb, dim=2)
        farfield_surfaces = list(farfield_surfaces.difference(set(symm_surface)))

        farfield = gmsh.model.addPhysicalGroup(2, [farfield_surfaces[0][1]])
        gmsh.model.setPhysicalName(2, farfield, "farfield")

        symmetry = gmsh.model.addPhysicalGroup(2, [symm_surface[0][1]])
        gmsh.model.setPhysicalName(2, symmetry, "symmetry_plane")

    else:
        # Farfield without symmetry
        farfield_surfaces_tags = []

        for surface in farfield_surfaces:
            farfield_surfaces_tags.append(surface[1])

        farfield = gmsh.model.addPhysicalGroup(2, farfield_surfaces_tags)
        gmsh.model.setPhysicalName(2, farfield, "farfield")

    # Fluid domain

    ps = gmsh.model.addPhysicalGroup(3, [final_domain[0][1]])
    gmsh.model.setPhysicalName(3, ps, "fluid")

    gmsh.model.occ.synchronize()

    # Mesh Tags

    wing_surfaces_tags = []
    fuselage_surfaces_tags = []

    for part in aircraft_parts:

        if "wing" in part.name:
            wing_surfaces_tags += part.surfaces_tags

        if "fuselage" in part.name:
            fuselage_surfaces_tags += part.surfaces_tags

    # Set mesh size

    for part in aircraft_parts:

        if "wing" in part.name:
            gmsh.model.mesh.setSize(list(part.points), mesh_size_wings)

        if "fuselage" in part.name:
            gmsh.model.mesh.setSize(list(part.points), mesh_size_fuselage)

    # Find missing points or points that are between two part of different mesh size

    points_found = set.union(*[part.points for part in aircraft_parts])
    points_missing = set(aircraft.points).difference(points_found)

    if points_missing:
        log.info("Points remapping")

        for point in points_missing:

            adj_lines, _ = gmsh.model.getAdjacencies(*point)
            adj_surfaces_tags = []

            for line_tag in adj_lines:

                adj_surfaces_2_line, _ = gmsh.model.getAdjacencies(1, line_tag)

                for surface_tag in adj_surfaces_2_line:
                    adj_surfaces_tags.append(surface_tag)

            # The point size will be a function of the nearby parts

            point_mesh_size = []

            for adj_surface_tag in adj_surfaces_tags:

                if adj_surface_tag in wing_surfaces_tags:
                    point_mesh_size.append(mesh_size_wings)

                if adj_surface_tag in fuselage_surfaces_tags:
                    point_mesh_size.append(mesh_size_fuselage)

            point_mesh_size = set(point_mesh_size)
            gmsh.model.mesh.setSize([point], sum(point_mesh_size) / len(point_mesh_size))

    # Farfiled size

    gmsh.model.mesh.setSize(list(farfield_points), mesh_size_farfield)

    # Color the mesh according to the surfaces found on the airplane parts
    # Color code

    mesh_color_wing = (0, 255, 0)
    mesh_color_fus = (0, 0, 255)
    mesh_color_farfield = (255, 255, 0)

    # Color assignation for each part

    for part in aircraft_parts:

        if "wing" in part.name:
            color = mesh_color_wing

        if "fuselage" in part.name:
            color = mesh_color_fus
        gmsh.model.setColor(list(part.surfaces), *color, a=150, recursive=True)

    gmsh.model.setColor(list(farfield_surfaces), *mesh_color_farfield, a=150, recursive=True)

    # Generate mesh

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

    print("Nothing to execute!")
