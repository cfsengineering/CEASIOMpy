"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains different functions to classify and manipulate wing elements.

TODO:
    - The wing classification of untruncated profile may sometimes detect the wrong le/te
    This is due to other parts (like pylon) cutting the wing geometry, this lead to over-
    refinement of some part of the wings. It may be possible to add more constraint to the
    function detect_normal_profile() in order to prevent this.
"""

# Imports

import gmsh
import numpy as np

from ceasiompy import log


# Functions

def detect_normal_profile(le_te_pair: list, line_comp1, line_comp2):
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
    le_te_pair: list,
    line_comp1: dict,
    line_comp2: dict,
    line_comp3: dict,
) -> tuple[list, bool]:
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


def find_chord_length(le_te_pair: list):
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
        f"Using truncated profile with computed chord length {chord_length} "
        f"and le_te_pair of {le_te_pair}."
    )

    return chord_length


def exclude_lines(wing_part: ModelPart, aircraft_parts: list) -> list:
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


def classify_wing(wing_part: ModelPart, aircraft_parts: list) -> None:
    """
    Function to classify the leading and trailing edge of the wing.

    Args:
        wing_part (ModelPart): Wing part to classify/order.
        aircraft_parts (list(ModelPart)): Parts of the aircraft

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
