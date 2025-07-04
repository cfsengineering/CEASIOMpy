"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains different functions to classify and manipulate wing elements

| Author: Tony Govoni
| Creation: 2022-04-05

TODO:
    - The wing classification of untruncated profile may sometimes detect the wrong le/te
    This is due to other parts (like pylon) cutting the wing geometry, this lead to over-
    refinement of some part of the wings. It may be possible to add more constraint to the
    function detect_normal_profile() in order to prevent this.
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import gmsh
import numpy as np

from typing import List, Dict, Tuple

from ceasiompy import log


# =================================================================================================
#   CLASSES
# =================================================================================================


class ModelPart:
    """
    A class to represent part of the aircraft or other part of the gmsh model
    in order to classify its entities and dimension tags
    ...

    Attributes
    ----------
    uid : str
        name of the part which correspond to its .brep file name for aircraft parts
        or a simple name describing the part function in the model

    """

    def __init__(self, uid):
        self.uid = uid
        self.part_type = ""

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
        self.children_dimtag = set()
        # Physical groups
        self.physical_groups = []

        self.mesh_size = None

        self.wing_sections = []

        # Bounding box (used in RANS)
        self.bounding_box = []

    def associate_child_to_parent(self, child_dimtag):
        """
        Function to associate a child to a parent.
        all the entities belonging to a child (volume generated by the fragment operation)
        are associated to their parent part (volume before the fragment operation)

        Args:
        ----------
        child_dimtag : tuple (dim,tag)
            dimtag of the child volume
        """

        # Detect 2D or 3D child
        if child_dimtag[0] == 3:
            # Associate a 3D the child to the parent
            child_volume = [child_dimtag]

            child_surfaces, child_lines, child_points = get_entities_from_volume(child_volume)

            # Get the dimtags (3D only)
            child_volume_tag = [dimtag[1] for dimtag in child_volume]
            # Store in parent parts for latter use (3D only)
            self.volume.extend(child_volume)
            self.volume_tag.extend(child_volume_tag)

        # 2D child and parent
        elif child_dimtag[0] == 2:
            child_surfaces = [child_dimtag]
            child_lines = sorted(
                gmsh.model.getBoundary(
                    child_surfaces, combined=True, oriented=False, recursive=False
                )
            )

            child_points = list(
                gmsh.model.getBoundary(
                    child_surfaces, combined=True, oriented=False, recursive=True
                )
            )
            child_points.sort()

        elif child_dimtag[0] != 2 and child_dimtag[0] != 3:
            raise ValueError("Dimension of the child is not 2 or 3")

        # Get the dimtags
        child_surfaces_tags = [dimtag[1] for dimtag in child_surfaces]
        child_lines_tags = [dimtag[1] for dimtag in child_lines]
        child_points_tags = [dimtag[1] for dimtag in child_points]

        # Store in parent parts for latter use
        self.points.extend(child_points)
        self.lines.extend(child_lines)
        self.surfaces.extend(child_surfaces)
        self.points_tags.extend(child_points_tags)
        self.lines_tags.extend(child_lines_tags)
        self.surfaces_tags.extend(child_surfaces_tags)

    def clean_inside_entities(self, final_domain):
        """
        Function to clean inside entities of the part.
        Inside entities are entities that are not part of the final domain.

        Args:
        ----------
        final_domain : ModelPart
            final_domain part
        """
        if self.part_type == "rotor":
            # Detect all the entities in the domain with gmsh functions
            self.surfaces = sorted(
                list(set(self.surfaces).intersection(set(gmsh.model.getEntities(dim=2))))
            )
            self.lines = sorted(
                list(set(self.lines).intersection(set(gmsh.model.getEntities(dim=1))))
            )
            self.points = sorted(
                list(set(self.points).intersection(set(gmsh.model.getEntities(dim=0))))
            )

            # Update the dimtags
            self.surfaces_tags = [dimtag[1] for dimtag in self.surfaces]
            self.lines_tags = [dimtag[1] for dimtag in self.lines]
            self.points_tags = [dimtag[1] for dimtag in self.points]
            return

        # if not rotor part
        # Detect only shared entities with the final domain
        self.surfaces = sorted(list(set(self.surfaces).intersection(set(final_domain.surfaces))))
        self.lines = sorted(list(set(self.lines).intersection(set(final_domain.lines))))
        self.points = sorted(list(set(self.points).intersection(set(final_domain.points))))

        # Update the dimtags
        self.surfaces_tags = sorted([dimtag[1] for dimtag in self.surfaces])
        self.lines_tags = sorted([dimtag[1] for dimtag in self.lines])
        self.points_tags = sorted([dimtag[1] for dimtag in self.points])


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def detect_normal_profile(le_te_pair: List, line_comp1, line_comp2):
    """
    Function to detect leading and trailing edge lines for normal profile (not truncated)
    le/te lines are linked by the two same surfaces
    ...

    Args:
    ----------
    le_te_pair : list
        list of all the previously found pair of le/te lines
    line_comp1 : dict
        dictionary containing a line and its surfaces
    line_comp2 : dict
        dictionary containing a line and its surfaces
    ...

    Returns:
    ----------
    le_te_pair : list (tag)
    True/False : if le/te pair found
    """

    lines = sorted(list(set([line_comp1["line_tag"], line_comp2["line_tag"]])))

    # Check if lines are not already in the found list
    if lines in le_te_pair:
        return le_te_pair, False

    # Check if the surfaces are the same
    surfaces = list(line_comp1["surf_tags"].intersection(line_comp2["surf_tags"]))
    if len(surfaces) != 2:
        return le_te_pair, False

    # Check if the le and te line are not connected i.e. 4 distinct points
    points = []
    for line in lines:
        _, adj_points = gmsh.model.getAdjacencies(1, line)
        points.extend(list(adj_points))
    if len(set(points)) != 4:
        return le_te_pair, False

    le_te_pair.append(lines)

    return le_te_pair, True


def detect_truncated_profile(
    le_te_pair: List,
    line_comp1: Dict,
    line_comp2: Dict,
    line_comp3: Dict,
) -> Tuple[List, bool]:
    """
    Function to detect leading and trailing edge lines for truncated profile
    le/te lines are linked by shared surfaces
    """
    lines = sorted(
        list(
            set(
                [
                    line_comp1["line_tag"],
                    line_comp2["line_tag"],
                    line_comp3["line_tag"],
                ]
            )
        )
    )

    # Check if the 3 lines are distinct
    if len(lines) != 3:
        return le_te_pair, False

    # Check if lines are already in le_te_pair
    if lines in le_te_pair:
        return le_te_pair, False

    # Check surface sharing between each lines
    if len(line_comp1["surf_tags"].intersection(line_comp2["surf_tags"])) != 1:
        return le_te_pair, False
    if len(line_comp2["surf_tags"].intersection(line_comp3["surf_tags"])) != 1:
        return le_te_pair, False
    if len(line_comp1["surf_tags"].intersection(line_comp3["surf_tags"])) != 1:
        return le_te_pair, False

    surfaces = sorted(
        list(line_comp1["surf_tags"].union(line_comp2["surf_tags"], line_comp3["surf_tags"]))
    )
    # Check nb of surface:
    if len(surfaces) != 3:
        return le_te_pair, False

    # Check if the le and te line are not connected i.e. 6 distinct points
    points = []
    for line in lines:
        _, adj_points = gmsh.model.getAdjacencies(1, line)
        points.extend(list(adj_points))
    if len(set(points)) != 6:
        return le_te_pair, False

    # add the le/te pair to the list
    le_te_pair.append(lines)
    return le_te_pair, True


def find_chord_length(le_te_pair: List):
    """
    Function to find the chord length of the wing section based on the le/te pair
    """

    if len(le_te_pair) == 2:
        # sharpe profile
        x1, y1, z1 = gmsh.model.occ.getCenterOfMass(1, le_te_pair[0])
        x2, y2, z2 = gmsh.model.occ.getCenterOfMass(1, le_te_pair[1])
        chord_length = np.linalg.norm([x2 - x1, y2 - y1, z2 - z1])
        log.info(f"Using sharp-e profile with computed {chord_length}.")
        return chord_length

    # truncated profile
    x1, y1, z1 = gmsh.model.occ.getCenterOfMass(1, le_te_pair[0])
    x2, y2, z2 = gmsh.model.occ.getCenterOfMass(1, le_te_pair[1])
    x3, y3, z3 = gmsh.model.occ.getCenterOfMass(1, le_te_pair[2])

    # Assuming the distance between the 2 trailing edge points is smaller than the chord length
    d12 = np.linalg.norm([x2 - x1, y2 - y1, z2 - z1])
    d13 = np.linalg.norm([x3 - x1, y3 - y1, z3 - z1])
    d23 = np.linalg.norm([x3 - x2, y3 - y2, z3 - z2])

    # The two trailing edge lines are the closest together
    chord_length = max([d12, d23, d13])
    log.info(
        f"Using truncated profile with computed {chord_length} "
        f"with length le_te_pair of {le_te_pair}."
    )

    return chord_length


def exclude_lines(wing_part: ModelPart, aircraft_parts: List) -> List:
    """
    Function to exclude lines from the wing part that are common with the other aircraft_parts.

    Args:
    ----------
    wing_part : ModelPart
        wing part
    aircraft_parts : list(ModelPart)
        list of aircraft parts
    ...
    Returns:
    ----------
    return a list(dim,tag) of uncommon lines
    """

    other_parts = aircraft_parts.copy()
    other_parts.remove(wing_part)

    other_lines = []
    for other_part in other_parts:
        other_lines.extend(other_part.lines)

    return list(set(wing_part.lines) - set(other_lines))


def get_entities_from_volume(volume_dimtag):
    """
    Function to get the entities belonging to a volume.
    Surfaces and lines are found with the gmsh.model.getBoundary() function.
    Points are found with the gmsh.model.getEntities() function using recursive set to True.
    This choice seems the most efficient and robust at the state of development of Gmsh

    Args:
    ----------
    volume_dimtag : list
        a list containing the dimtag of the volume [(dim,tag)]
        which is a standard input format for other gmsh function
    ...

    Returns:
    ----------
    surfaces_dimtags : list(tuple)
        a list of tuples containing the dimtag of the surfaces
    lines_dimtags : list(tuple)
        a list of tuples containing the dimtag of the lines
    points_dimtags : list(tuple)
        a list of tuples containing the dimtag of the points
    """

    surfaces_dimtags = gmsh.model.getBoundary(
        volume_dimtag, combined=True, oriented=False, recursive=False
    )

    lines_dimtags = sorted(
        set().union(
            *[
                gmsh.model.getBoundary([surface], combined=True, oriented=False, recursive=False)
                for surface in surfaces_dimtags
            ]
        )
    )

    points_dimtags = list(
        set().union(
            *[
                gmsh.model.getBoundary([surface], combined=True, oriented=False, recursive=True)
                for surface in surfaces_dimtags
            ]
        )
    )
    points_dimtags.sort()

    return surfaces_dimtags, lines_dimtags, points_dimtags


def classify_wing(wing_part: ModelPart, aircraft_parts: List) -> None:
    """
    Function to classify the leading and trailing edge of the wing.

    Args:
        wing_part (ModelPart): Wing part to classify/order.
        aircraft_parts (List(ModelPart)): Parts of the aircraft

    """

    # Get the lines of the wing part not touching the other parts
    # and store the line dimtag with its adjacent surfaces
    lines_composition = []
    for line in exclude_lines(wing_part, aircraft_parts):
        adj_surfs, _ = gmsh.model.getAdjacencies(*line)
        lines_composition.append({"line_tag": line[1], "surf_tags": set(adj_surfs)})

    # Find the pair of le/te lines with all the lines of the wing part
    le_te_pair = []

    for i, line_comp1 in enumerate(lines_composition):
        for line_comp2 in lines_composition[(i + 1) :]:
            # try to detect if two line form a normal profile
            le_te_pair, found_normal = detect_normal_profile(le_te_pair, line_comp1, line_comp2)
            if not found_normal:
                for line_comp3 in lines_composition:
                    # try to detect if three line form a truncated profile
                    le_te_pair, _ = detect_truncated_profile(
                        le_te_pair, line_comp1, line_comp2, line_comp3
                    )

    # Classify pair of le/te lines in the wing part
    wing_part.wing_sections = []
    for le_te in le_te_pair:
        wing_part.wing_sections.append(
            {"lines_tags": le_te, "mean_chord": find_chord_length(le_te)}
        )
