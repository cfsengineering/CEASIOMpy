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

from asyncio import futures
import gmsh
import os
from ceasiompy.utils.ceasiomlogger import get_logger
import numpy as np

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


def classify_wing(wing_part, aircraft_parts):
    """
    Function to classify the points and line of a wing
    ...

    Args:
    ----------
    wing_part : AircraftPart
        aircraft part to classify
    ...
    aircraft_parts : list(AircraftPart)
        parts of the aircraft
    ...
    """
    # find the profiles that composed the wing and its sections

    profiles = []
    """
    A profile is composed of two Spline (one upper and one lower) that are connected
    with the same two points (the leading and trailing edge points)
    this definition is only valid for non truncated profile
    for a truncated profile further operation need to be done do determine the two
    trailing edge points
    """
    lines_composition = []

    for line in wing_part.lines:

        # Seek for the adjacent points of each line in the wing part

        _, adj_points = gmsh.model.getAdjacencies(*line)

        # store the line composition : line dimTag and the two adjacent points dimTag

        lines_composition.append({"line_dimtag": line[1], "points_tags": list(adj_points)})

    # try to find simple profile (untruncated) first

    for line_comp in lines_composition:

        pair_points = sorted(line_comp["points_tags"])

        for line_comp_other in lines_composition:

            # seek for another line that share the exact same two points

            if line_comp_other["line_dimtag"] != line_comp["line_dimtag"]:
                if pair_points == sorted(line_comp_other["points_tags"]):

                    # a profile is found
                    # find leading and trailing edge points

                    p1 = gmsh.model.occ.getBoundingBox(0, pair_points[0])
                    p2 = gmsh.model.occ.getBoundingBox(0, pair_points[1])

                    # assuming the wing is oriented along the x axis
                    # pair_points = [le,te]

                    if p1[0] > p2[0]:
                        pair_points.reverse()

                    # determine upper and lower spline
                    c1 = gmsh.model.occ.getCenterOfMass(1, line_comp["line_dimtag"])
                    c2 = gmsh.model.occ.getCenterOfMass(1, line_comp_other["line_dimtag"])

                    splines_dim_tag = [
                        line_comp["line_dimtag"],
                        line_comp_other["line_dimtag"],
                    ]
                    if c2[2] > c1[2]:
                        splines_dim_tag.reverse()

                    le2te_vector = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]]

                    chord = np.linalg.norm(le2te_vector)

                    profiles.append(
                        {
                            "truncated": False,
                            "lines_dimtag": splines_dim_tag,
                            "points_tag": pair_points,
                            "chord_length": chord,
                        }
                    )
                    # remove the profile from the list to avoid double counting
                    lines_composition.remove(line_comp_other)
                    truncated_profile = False

    # if none of the line share the same two points, the wing is truncated
    if profiles == []:

        truncated_profile = True
        log.info("No simple profile found : try to find a truncated profile")

        profile_lines = []
        profile_points = []

        # Compare two line of the wing searching for this time only one point in common
        for line_comp in lines_composition:
            pair_points = line_comp["points_tags"]

            for line_comp_other in lines_composition:
                pair_points_other = line_comp_other["points_tags"]

                if line_comp_other["line_dimtag"] != line_comp["line_dimtag"]:

                    # Search if at least one point is shared by the two lines

                    if pair_points[0] in pair_points_other or pair_points[1] in pair_points_other:

                        # determine the common point in the two pair of points

                        if pair_points[0] in pair_points_other:

                            common_point = pair_points[0]
                            points = set([*pair_points, *pair_points_other])

                        else:
                            common_point = pair_points[1]
                            points = set([*pair_points, *pair_points_other])

                        # if those 3 point form a truncated profile with a third line,
                        # those 3 points and lines should form a looping line

                        # find the looping line by seeking the line adj to the points
                        # all the adj line will be added to the pool of lines
                        # if one line is already in the pool, then it is shared by two points
                        # and one line of the looping line is found
                        pool_line = []
                        loop_line = []

                        for pt in points:
                            adj_lines, _ = gmsh.model.getAdjacencies(0, pt)

                            for line in adj_lines:

                                if line in pool_line:
                                    loop_line.append(line)

                                pool_line.append(line)

                        # if 3 line sharing common points are found, then the profile is found
                        if len(loop_line) == 3:

                            # a profile is found
                            loop_line = sorted(loop_line)

                            # store all the profile found but first check that it was not already founded
                            if loop_line not in profile_lines:

                                profile_lines.append(loop_line)
                                profile_points.append(list(points))

        # With all the truncated profiles found, we can do further operation and classification
        for profile_line, profile_point in zip(profile_lines, profile_points):

            # TODO: code a function to find the correct orientation of the profile

            # find leading and trailing edge points

            p1x, p1y, p1z, _, _, _ = gmsh.model.occ.getBoundingBox(0, profile_point[0])
            p2x, p2y, p2z, _, _, _ = gmsh.model.occ.getBoundingBox(0, profile_point[1])
            p3x, p3y, p3z, _, _, _ = gmsh.model.occ.getBoundingBox(0, profile_point[2])

            # assuming that the distance between the two trailing edge points is smaller
            # than the chord length

            d12 = [
                np.linalg.norm([p2x - p1x, p2y - p1y, p2z - p1z]),
                profile_point[0],
                profile_point[1],
            ]
            d23 = [
                np.linalg.norm([p3x - p2x, p3y - p2y, p3z - p2z]),
                profile_point[1],
                profile_point[2],
            ]
            d31 = [
                np.linalg.norm([p1x - p3x, p1y - p3y, p1z - p3z]),
                profile_point[2],
                profile_point[0],
            ]

            pts = [d12[1:], d23[1:], d31[1:]]
            distances = [d12[0], d23[0], d31[0]]

            # the two trailing edge points are the closest togheter
            te_points = pts[distances.index(min(distances))]

            # remove te points from the list to find le point
            profile_point.remove(te_points[0]), profile_point.remove(te_points[1])

            # classify the profile
            profiles.append(
                {
                    "truncated": True,
                    "lines_dimtag": profile_line,
                    "points_tag": [*profile_point, *te_points],
                    "chord_length": max(distances),
                }
            )

    # Now that profiles in the wing are classify, we can seek the pair of profiles that
    # forms a wing section

    wing_sections = []
    """
    A wing section is composed of two profiles and the lines that connect their
    leading and trailing edge points
    """

    if not truncated_profile:

        for profile in profiles:

            profile_pts = profile["points_tag"]

            # find the leading and trailing edge lines who leaves the profile

            adj_le_lines, _ = gmsh.model.getAdjacencies(0, profile_pts[0])
            adj_le_lines = list(adj_le_lines)

            adj_te_lines, _ = gmsh.model.getAdjacencies(0, profile_pts[1])
            adj_te_lines = list(adj_te_lines)

            # remove from all the adjacent line the ones that are the profile spline

            [adj_le_lines.remove(spline) for spline in profile["lines_dimtag"]]
            [adj_te_lines.remove(spline) for spline in profile["lines_dimtag"]]

            # the remaining lines are the leading and trailing edge lines

            profile["adj_le_lines"] = adj_le_lines
            profile["adj_te_lines"] = adj_te_lines

        # then search if there is another profile who shares the same le/te lines
        for profile in profiles:
            for other_profile in profiles:

                if other_profile != profile:

                    # find the shared leading edge line
                    for line_le in profile["adj_le_lines"]:
                        if line_le in other_profile["adj_le_lines"]:

                            # find the shared trailing edge line
                            for line_te in profile["adj_te_lines"]:
                                if line_te in other_profile["adj_te_lines"]:

                                    # TODO: classify the surfaces between the profile

                                    # # determine the surfaces of the wing section
                                    # surfaces = []

                                    # adj_surfs_le, _ = gmsh.model.getAdjacencies(1, line_le)
                                    # adj_surfs_te, _ = gmsh.model.getAdjacencies(1, line_te)

                                    # if sorted(list(adj_surfs_le)) == sorted(list(adj_surfs_le)):
                                    #     for surf_tag in adj_surfs_te:
                                    #         surfaces.append((2, surf_tag))

                                    # classify the wing section:

                                    wing_sections.append(
                                        {
                                            "truncated": truncated_profile,
                                            "profiles": [
                                                profile["lines_dimtag"],
                                                other_profile["lines_dimtag"],
                                            ],
                                            "le_line": [line_le],
                                            "te_line": [line_te],
                                            "le_points": [
                                                (0, profile["points_tag"][0]),
                                                (0, other_profile["points_tag"][0]),
                                            ],
                                            "te_points": [
                                                (0, profile["points_tag"][1]),
                                                (0, other_profile["points_tag"][1]),
                                            ],
                                            "mean_chord": 0.5
                                            * (
                                                profile["chord_length"]
                                                + other_profile["chord_length"]
                                            ),
                                        }
                                    )

                                    # remove from the list to avoid double counting
                                    profiles.remove(other_profile)

    else:

        # truncated profiles need to be handeled differently for the te
        for profile in profiles:

            # similar opertation on the leading edge
            le_point = profile["points_tag"][0]

            adj_le_lines, _ = gmsh.model.getAdjacencies(0, le_point)
            adj_le_lines = set(adj_le_lines)

            # multiple trailing edge lines
            adj_te_lines = []

            for point in profile["points_tag"][1:]:

                adj_lines, _ = gmsh.model.getAdjacencies(0, point)
                adj_te_lines += list(adj_lines)

            adj_te_lines = set(adj_te_lines)

            # then search if there is another profile who shares the same le/te lines
            for other_profile in profiles:

                # leading edge

                oth_le_point = other_profile["points_tag"][0]
                oth_adj_le_lines, _ = gmsh.model.getAdjacencies(0, oth_le_point)
                oth_adj_le_lines = set(oth_adj_le_lines)

                # trailing edge

                oth_adj_te_lines = []
                for point in other_profile["points_tag"][1:]:
                    oth_adj_lines, _ = gmsh.model.getAdjacencies(0, point)
                    oth_adj_te_lines += list(oth_adj_lines)
                oth_adj_te_lines = set(oth_adj_te_lines)

                # seek for the shared leading edge and trailing line

                line_le = oth_adj_le_lines.intersection(adj_le_lines)
                lines_te = oth_adj_te_lines.intersection(adj_te_lines)

                # there must be 1 le line and 2 te lines
                if len(line_le) == 1 and len(lines_te) == 2:

                    # TODO: classify the surfaces between the profile
                    # classify the wing section
                    wing_sections.append(
                        {
                            "truncated": truncated_profile,
                            "profiles": [
                                profile["lines_dimtag"],
                                other_profile["lines_dimtag"],
                            ],
                            "le_line": list(line_le),
                            "te_line": list(lines_te),
                            "le_points": [
                                (0, profile["points_tag"][0]),
                                (0, other_profile["points_tag"][0]),
                            ],
                            "te_points": [
                                (0, profile["points_tag"][1]),
                                (0, profile["points_tag"][2]),
                                (0, other_profile["points_tag"][1]),
                                (0, other_profile["points_tag"][2]),
                            ],
                            "mean_chord": 0.5
                            * (profile["chord_length"] + other_profile["chord_length"]),
                        }
                    )
                    # remove from the list to avoid double counting
                    profiles.remove(other_profile)

    # add the wing sections founded to the wing Aircraftpart
    wing_part.wing_sections = wing_sections

    # Dealing with the special wing section that is attached to the fuselage :
    # this wing section is special because multiple lines form the profile that is
    # attached to the fuselage

    fuselage = False

    # First seek if the aircraft contain a fuselage
    for part in aircraft_parts:
        if "fuselage" in part.name:
            fuselage = True

    if fuselage:

        # find all the lines and points in the wing that we already classified

        already_classifed_lines = []
        le_points = []
        te_points = []

        for wing_section in wing_sections:
            profiles = wing_section["profiles"]
            for profile in profiles:
                for line in profile:
                    already_classifed_lines.append(line)
            for line in wing_section["le_line"]:
                already_classifed_lines.append(line)
            for line in wing_section["te_line"]:
                already_classifed_lines.append(line)
            for point in wing_section["le_points"]:
                le_points.append(point[1])
            for point in wing_section["te_points"]:
                te_points.append(point[1])

        # transform in set
        already_classifed_lines = set(already_classifed_lines)
        le_points = set(le_points)
        te_points = set(te_points)

        # seek for unclassified lines comming from classified leading edge points
        # since all the wing except the part that is link to the fuselage is classifed
        # the remaining unclassified comming from classified le / te points must be the
        # the le/te lines linked to the fuselage
        adj_lines = []

        for point in list(le_points):

            adj_local_lines, _ = gmsh.model.getAdjacencies(0, point)

            for line in adj_local_lines:
                adj_lines.append(line)

        adj_lines = set(adj_lines)
        le_line_fus_wing = list(adj_lines.difference(already_classifed_lines))

        # seek for unclassified lines comming from classified trailing edge points
        adj_lines = []

        for point in list(te_points):

            adj_local_lines, _ = gmsh.model.getAdjacencies(0, point)

            for line in adj_local_lines:
                adj_lines.append(line)

        adj_lines = set(adj_lines)
        te_line_fus_wing = list(adj_lines.difference(already_classifed_lines))

        # find the points of the wing leading edge and trailing edge

        _, le_points = gmsh.model.getAdjacencies(1, le_line_fus_wing[0])

        te_points = []

        for line in te_line_fus_wing:
            _, points = gmsh.model.getAdjacencies(1, line)

            for point in points:
                te_points.append(point)

        # TODO: classify the surfaces and profiles

        # classify the wing section
        wing_sections.append(
            {
                "truncated": truncated_profile,
                "profiles": [],
                "le_line": [le_line_fus_wing[0]],
                "te_line": [te_line_fus_wing],
                "le_points": [le_points],
                "te_points": [te_points],
            }
        )

        return log.info(f"{wing_part.name} classified")


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
    domain_lenght = farfield_factor * max(aircraft.sizes)

    center_aircraft = gmsh.model.occ.get_center_of_mass(*aircraft.dim_tag)
    ext_domain = gmsh.model.occ.addSphere(*center_aircraft, domain_lenght)
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
    for part in aircraft_parts[0:1]:
        if "wing" in part.name:
            classify_wing(part, aircraft_parts)

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
        "test_files/simple",
        "",
        open_gmsh=True,
        farfield_factor=5,
        symmetry=False,
        mesh_size_farfield=12,
        mesh_size_fuselage=0.2,
        mesh_size_wings=0.2,
    )
    print("Nothing to execute!")
