"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains diffrent functions to classify and manipulate wing elements

Python version: >=3.7

| Author: Tony Govoni
| Creation: 2022-04-05

TODO:

    -For the special wing section add the profile in profile list
    one profile is easy, the other one is more complicated but it
    seams to be formed of the remaining lines of the wing that are not
    classified

    - Add for a a wing the surfaces of the fuselage that are touching the wing
    thus a refinement of the fuselage near the wing can be done
    by making extra fields restricted to those surfaces with the maxmeshsize of
    the fuselage

    - Try to handle special case when symmetry is applied and it cuts the vertical
    wing such that there is no profile to be found :
    ex. optimal.xml with sym : wing3 no sections found

    - Try to handle the problem of the pylon that completely destroy the wing classifier
    by adding multiple curve inside the wing section
    a similar problem will happen when the wing is cut by flaps
"""


# ==============================================================================
#   IMPORTS
# ==============================================================================
import gmsh
import numpy as np

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def classify_profile(profile_list, line_comp1, line_comp2):
    """
    Function to detect and classify lines and points that form a profile in a wing part
    A profile is composed of two Spline (one upper and one lower) that are connected
    with the same two points (the leading and trailing edge points)

    two lines (line_comp1 and line_comp2) are given as input
    classify_profile() try to detect if those two lines form a profile
    ...

    Args:
    ----------
    profile_list : list
        list of all the previously found profile
    line_comp1 : dict
        dictionary containing a line and its two points
    line_comp2 : dict
        dictionary containing a line and its two points
    ...

    Returns:
    ----------
    True : if the two lines form a profile
    False : otherwise
    """
    pair_points = sorted(line_comp1["points_tags"])

    if pair_points == sorted(line_comp2["points_tags"]) and (
        line_comp2["line_dimtag"] != line_comp1["line_dimtag"]
    ):
        # find leading and trailing edge points
        p1 = gmsh.model.occ.getBoundingBox(0, pair_points[0])
        p2 = gmsh.model.occ.getBoundingBox(0, pair_points[1])

        # assuming the wing is oriented along the x axis
        # pair_points = [le,te]

        if p1[0] > p2[0]:
            pair_points.reverse()

        # determine upper and lower spline
        c1 = gmsh.model.occ.getCenterOfMass(1, line_comp1["line_dimtag"])
        c2 = gmsh.model.occ.getCenterOfMass(1, line_comp2["line_dimtag"])

        splines_dim_tag = [
            line_comp1["line_dimtag"],
            line_comp2["line_dimtag"],
        ]
        if c2[2] > c1[2]:
            splines_dim_tag.reverse()

        le2te_vector = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]]

        chord = np.linalg.norm(le2te_vector)

        # find the leading and trailing edge lines who leaves the profile
        adj_le_lines, _ = gmsh.model.getAdjacencies(0, pair_points[0])
        adj_le_lines = set(adj_le_lines)

        adj_te_lines, _ = gmsh.model.getAdjacencies(0, pair_points[1])
        adj_te_lines = set(adj_te_lines)

        # remove from all the adjacent line the ones that are the profile spline
        adj_le_lines.difference(set(splines_dim_tag))
        adj_te_lines.difference(set(splines_dim_tag))

        # the remaining lines are the leading and trailing edge lines

        profile_list.append(
            {
                "truncated": False,
                "lines_dimtag": splines_dim_tag,
                "points_tag": pair_points,
                "adj_le_lines": list(adj_le_lines),
                "adj_te_lines": list(adj_te_lines),
                "chord_length": chord,
            }
        )
        return True
    else:
        return False


def classify_trunc_profile(profile_list, profile_lines, line_comp1, line_comp2):
    """
    Function to detect and classify lines and points that form a truncated profile in a wing part
    A profile is composed of two Spline (one upper and one lower) that are connected
    with the same leading edge points, but with two different trailing edge points

    two lines (line_comp1 and line_comp2) are given as input
    classify_profile() try to detect if those two lines form a profile
    ...

    Args:
    ----------
    profile_list : list
        list of all the previously found profile
    profile_lines : list
        list of all the previously found profile lines
    line_comp1 : dict
        dictionary containing a line and its two points
    line_comp2 : dict
        dictionary containing a line and its two points
    ...
    Returns:
    ----------
    True : if the two lines form a profile
    False : otherwise
    """
    pair_points = line_comp1["points_tags"]
    pair_points_other = line_comp2["points_tags"]

    # If it is the same lines it cannot form a profile,
    # or if the two lines are not connected with the same two points. it cannot form a profile
    if (line_comp2["line_dimtag"] == line_comp1["line_dimtag"]) or (
        (pair_points[0] not in pair_points_other) and (pair_points[1] not in pair_points_other)
    ):
        return False
    else:
        # determine the common point in the two pair of points

        if pair_points[0] in pair_points_other:
            points = set([*pair_points, *pair_points_other])

        else:
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
        points = list(points)
        # if 3 line sharing common points are found, then the profile is found
        if len(loop_line) != 3:
            return False
        # check that each line share only one point with the two other line
        for k in range(0, len(loop_line)):

            _, adj_points = gmsh.model.getAdjacencies(1, loop_line[k])

            for line in loop_line[:k] + loop_line[k + 1 :]:
                _, adj_points_other = gmsh.model.getAdjacencies(1, line)

                if len(set(adj_points).intersection(set(adj_points_other))) != 1:
                    return False

        # a profile is found
        loop_line = sorted(loop_line)

        # store all the profile found but first check that it was not already founded
        if loop_line in profile_lines:
            return False

        profile_lines.append(loop_line)

        # TODO: code a function to find the correct orientation of the profile

        # find leading and trailing edge points

        p1x, p1y, p1z, _, _, _ = gmsh.model.occ.getBoundingBox(0, points[0])
        p2x, p2y, p2z, _, _, _ = gmsh.model.occ.getBoundingBox(0, points[1])
        p3x, p3y, p3z, _, _, _ = gmsh.model.occ.getBoundingBox(0, points[2])

        # assuming that the distance between the two trailing edge points is smaller
        # than the chord length

        d12 = [
            np.linalg.norm([p2x - p1x, p2y - p1y, p2z - p1z]),
            points[0],
            points[1],
        ]
        d23 = [
            np.linalg.norm([p3x - p2x, p3y - p2y, p3z - p2z]),
            points[1],
            points[2],
        ]
        d31 = [
            np.linalg.norm([p1x - p3x, p1y - p3y, p1z - p3z]),
            points[2],
            points[0],
        ]

        pts = [d12[1:], d23[1:], d31[1:]]
        distances = [d12[0], d23[0], d31[0]]

        # the two trailing edge points are the closest together

        te_points = pts[distances.index(min(distances))]

        # remove te points from the list to find le point

        points.remove(te_points[0]), points.remove(te_points[1])

        # find the leading and trailing edge lines who leaves the profile

        le_point = points[0]
        adj_le_lines, _ = gmsh.model.getAdjacencies(0, le_point)
        adj_le_lines = set(adj_le_lines)

        # multiple trailing edge lines

        adj_te_lines = []

        for point in te_points:

            adj_lines, _ = gmsh.model.getAdjacencies(0, point)
            adj_te_lines += list(adj_lines)

        adj_te_lines = set(adj_te_lines)

        # remove from all the adjacent line the ones that are the profile spline
        adj_le_lines = adj_le_lines.difference(set(loop_line))
        adj_te_lines = adj_te_lines.difference(set(loop_line))

        # classify the profile
        profile_list.append(
            {
                "truncated": True,
                "lines_dimtag": loop_line,
                "points_tag": [*points, *te_points],
                "adj_le_lines": list(adj_le_lines),
                "adj_te_lines": list(adj_te_lines),
                "chord_length": max(distances),
            }
        )
        return True


def classify_wing_section(wing_sections, profile, other_profile):
    """
    Function to detect and classify wing section in a wing part
    A wing section is composed of two profiles and the lines that connect their
    leading and trailing edge points
    ...

    Args:
    ----------
    wing_sections : list
        list of all the previously found wing_section
    profile : dict
        dictionary containing a profile
    other_profile : dict
        dictionary containing a profile
    ...
    Returns:
    ----------
    True : if the two profiles form a wing section
    False : otherwise
    """
    if profile == other_profile:
        return False

    truncated_profile = profile["truncated"]

    if not truncated_profile:

        if other_profile == profile:
            return False

        # find the shared leading edge line
        le_line = (set(profile["adj_le_lines"])).intersection(set(other_profile["adj_le_lines"]))
        te_line = (set(profile["adj_te_lines"])).intersection(set(other_profile["adj_te_lines"]))

        if len(le_line) != 1 and len(te_line) != 1:
            return False

        # verify that this wing section was not already found
        # the leading edge line is a unique feature of the wing section
        le_line = list(le_line)
        te_line = list(te_line)

        previous_le_lines = [wing_section["le_line"][0] for wing_section in wing_sections]

        if le_line[0] in previous_le_lines:  # if leading edge line already found
            return False

        # classify the wing section:

        section_surfaces = []

        adj_le_surfaces, _ = gmsh.model.getAdjacencies(1, le_line[0])
        adj_te_surfaces, _ = gmsh.model.getAdjacencies(1, te_line[0])

        [section_surfaces.append(adj_le_surface) for adj_le_surface in adj_le_surfaces]
        [section_surfaces.append(adj_te_surface) for adj_te_surface in adj_te_surfaces]

        section_surfaces = list(set(section_surfaces))

        wing_sections.append(
            {
                "truncated": truncated_profile,
                "profiles": [
                    profile["lines_dimtag"],
                    other_profile["lines_dimtag"],
                ],
                "le_line": le_line,
                "te_line": te_line,
                "le_points": [
                    (0, profile["points_tag"][0]),
                    (0, other_profile["points_tag"][0]),
                ],
                "te_points": [
                    (0, profile["points_tag"][1]),
                    (0, other_profile["points_tag"][1]),
                ],
                "mean_chord": 0.5 * (profile["chord_length"] + other_profile["chord_length"]),
                "surfaces": section_surfaces,
            }
        )
        return True

    else:
        # seek for the shared leading edge and trailing line
        le_line = (set(profile["adj_le_lines"])).intersection(set(other_profile["adj_le_lines"]))
        te_line = (set(profile["adj_te_lines"])).intersection(set(other_profile["adj_te_lines"]))

        # there must be 1 le line and 2 te lines
        if len(le_line) == 1 and len(te_line) == 2:

            # verify that this wing section was not already found
            # the leading edge line is a unique feature of the wing section
            le_line = list(le_line)
            te_line = list(te_line)
            previous_le_lines = [wing_section["le_line"][0] for wing_section in wing_sections]

            if le_line[0] in previous_le_lines:
                return False

            # classify the surfaces between the profile
            # TODO: classify the wing tip surfaces

            section_surfaces = []

            adj_le_surfaces, _ = gmsh.model.getAdjacencies(1, le_line[0])
            adj_te_surfaces, _ = gmsh.model.getAdjacencies(1, te_line[0])

            [section_surfaces.append(adj_le_surface) for adj_le_surface in adj_le_surfaces]
            [section_surfaces.append(adj_te_surface) for adj_te_surface in adj_te_surfaces]

            section_surfaces = list(set(section_surfaces))
            # classify the wing section
            wing_sections.append(
                {
                    "truncated": truncated_profile,
                    "profiles": [
                        profile["lines_dimtag"],
                        other_profile["lines_dimtag"],
                    ],
                    "le_line": le_line,
                    "te_line": te_line,
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
                    "mean_chord": 0.5 * (profile["chord_length"] + other_profile["chord_length"]),
                    "surfaces": section_surfaces,
                }
            )
            return True


def classify_special_section(wing_part, wing_sections, profiles):
    """
    Function to detect and classify a special wing section in a wing part,
    this wing section is connected to the fuselage of the plane

    The junction between the fuselage and the wing can be a simple profile or
    a complex arrangement of lines, thus detecting and classifying this wing section
    is not exactly the same method than standart wing sections
    ...

    Args:
    ----------
    wing_part : ModelPart
        aircraft part to classify
    wing_sections : list
        list of all the previously found wing_section
    profile : dict
        dictionary containing a profile
    other_profile : dict
        dictionary containing a profile
    ...
    Returns:
    ----------
    True : if the special wing section is classified
    False : if already classified
    """

    # seek if there is at least a profile in this wing
    if len(profiles) == 0:
        # part of the aircraft may be deleted due to symmetry application
        return False
    # Search if this is the only wing section of the wing
    if len(wing_sections) != 0:
        # find all the lines and points in the wing that we already classified
        already_classified_lines = []
        le_points_wing = []
        te_points_wing = []

        for wing_section in wing_sections:

            profiles = wing_section["profiles"]

            for profile in profiles:
                for line in profile:
                    already_classified_lines.append(line)

            for line in wing_section["le_line"]:
                already_classified_lines.append(line)

            for line in wing_section["te_line"]:
                already_classified_lines.append(line)

            for point in wing_section["le_points"]:
                le_points_wing.append(point[1])

            for point in wing_section["te_points"]:
                te_points_wing.append(point[1])

        # transform in set
        already_classified_lines = set(already_classified_lines)
        le_points_wing = set(le_points_wing)
        te_points_wing = set(te_points_wing)
        """
        seek for unclassified lines comming from classified leading edge points
        Normally all the wing except the part that is link to the fuselage is classifed
        the remaining unclassified comming from classified le / te points must be the
        the le/te lines linked to the fuselage

        But sometimes if no fuselage line interesect the wing profile embedded in the wing
        the profile projection on the fuselage is a simple profile so it must has been
        normally classified and thus the already_classified_lines and points are exactly all
        the lines and points of the wing
        """
        # seek if the profile projection on the fuselage is a simple profile

        if (already_classified_lines == set(wing_part.lines_tags)) and (
            (le_points_wing.union(te_points_wing)) == set(wing_part.points_tags)
        ):
            return False
        adj_lines = []

        for point in list(le_points_wing):

            adj_local_lines, _ = gmsh.model.getAdjacencies(0, point)

            for line in adj_local_lines:
                adj_lines.append(line)

        adj_lines = set(adj_lines)
        le_line_fus_wing = list(adj_lines.difference(already_classified_lines))

        # seek for unclassified lines comming from classified trailing edge points
        adj_lines = []

        for point in list(te_points_wing):

            adj_local_lines, _ = gmsh.model.getAdjacencies(0, point)

            for line in adj_local_lines:
                adj_lines.append(line)

        adj_lines = set(adj_lines)
        te_line_fus_wing = list(adj_lines.difference(already_classified_lines))

        # find the points of the wing leading edge and trailing edge
        _, le_points = gmsh.model.getAdjacencies(1, le_line_fus_wing[0])

        te_points = []

        for line in te_line_fus_wing:
            _, points = gmsh.model.getAdjacencies(1, line)

            for point in points:
                te_points.append(point)

        # mean chord determination
        # mean chord determination
        middle_le_line = [gmsh.model.occ.getCenterOfMass(1, line) for line in le_line_fus_wing]
        middle_te_line = [gmsh.model.occ.getCenterOfMass(1, line) for line in te_line_fus_wing]
        center_le_line = np.mean(middle_le_line, axis=0)
        center_te_line = np.mean(middle_te_line, axis=0)

        mean_chord = np.linalg.norm(center_le_line - center_te_line)
        le_points = list(le_points)
        te_points = list(te_points)

        # TODO: classify the surfaces tip of the wing
        section_surfaces = []

        adj_le_surfaces, _ = gmsh.model.getAdjacencies(1, le_line_fus_wing[0])
        adj_te_surfaces, _ = gmsh.model.getAdjacencies(1, te_line_fus_wing[0])

        [section_surfaces.append(adj_le_surface) for adj_le_surface in adj_le_surfaces]
        [section_surfaces.append(adj_te_surface) for adj_te_surface in adj_te_surfaces]

        section_surfaces = list(set(section_surfaces))

        # classify the wing section
        wing_sections.append(
            {
                "truncated": wing_section["truncated"],
                "profiles": [],
                "le_line": le_line_fus_wing,
                "te_line": te_line_fus_wing,
                "le_points": le_points,
                "te_points": te_points,
                "mean_chord": mean_chord,
                "surfaces": section_surfaces,
            }
        )

        return True
    else:
        # the special wing section is the only wing section of the wing

        tip_wing_profile = profiles[0]

        # thus it is simple to find the leading edge and trailing edge lines

        le_line_fus_wing = list(
            (set(tip_wing_profile["adj_le_lines"])).difference(
                set(tip_wing_profile["lines_dimtag"])
            )
        )
        te_line_fus_wing = list(
            (set(tip_wing_profile["adj_te_lines"])).difference(
                set(tip_wing_profile["lines_dimtag"])
            )
        )

        # find the points of the wing leading edge and trailing edge

        _, le_points = gmsh.model.getAdjacencies(1, le_line_fus_wing[0])

        te_points = []

        for line in te_line_fus_wing:
            _, points = gmsh.model.getAdjacencies(1, line)

            for point in points:
                te_points.append(point)

        le_points = list(le_points)
        te_points = list(te_points)

        # mean chord determination
        middle_le_line = [gmsh.model.occ.getCenterOfMass(1, line) for line in le_line_fus_wing]
        middle_te_line = [gmsh.model.occ.getCenterOfMass(1, line) for line in te_line_fus_wing]
        center_le_line = np.mean(middle_le_line, axis=0)
        center_te_line = np.mean(middle_te_line, axis=0)

        mean_chord = np.linalg.norm(center_le_line - center_te_line)

        section_surfaces = []

        adj_le_surfaces, _ = gmsh.model.getAdjacencies(1, le_line_fus_wing[0])
        adj_te_surfaces, _ = gmsh.model.getAdjacencies(1, te_line_fus_wing[0])

        [section_surfaces.append(adj_le_surface) for adj_le_surface in adj_le_surfaces]
        [section_surfaces.append(adj_te_surface) for adj_te_surface in adj_te_surfaces]

        section_surfaces = list(set(section_surfaces))
        # classify the wing section
        wing_sections.append(
            {
                "truncated": tip_wing_profile["truncated"],
                "profiles": [],
                "le_line": le_line_fus_wing,
                "te_line": te_line_fus_wing,
                "le_points": le_points,
                "te_points": te_points,
                "mean_chord": mean_chord,
                "surfaces": section_surfaces,
            }
        )
        return True


def classify_wing(wing_part):
    """
    Function to classify the points and line of a wing part
    points and lines are classified in the wing section to identify the trailing and leading edge
    and the profiles who forms each wing section
    ...

    Args:
    ----------
    wing_part : ModelPart
        aircraft part to classify
    ...
    aircraft_parts : list(ModelPart)
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

    for line_comp1 in lines_composition:

        for line_comp2 in lines_composition:

            profile_found = classify_profile(profiles, line_comp1, line_comp2)

            if profile_found:
                lines_composition.remove(line_comp2)

    # if none of the line share the same two points, the wing is truncated
    if profiles == []:

        profile_lines = []

        # Compare two line of the wing searching for this time only one point in common
        for line_comp1 in lines_composition:
            for line_comp2 in lines_composition:

                profile_found = classify_trunc_profile(
                    profiles, profile_lines, line_comp1, line_comp2
                )
                if profile_found:
                    lines_composition.remove(line_comp2)

    # Now that profiles in the wing are classify, we can seek the pair of profiles that
    # forms a wing section

    wing_sections = []
    """
    A wing section is composed of two profiles and the lines that connect their
    leading and trailing edge points
    """

    # then search if there is another profile who shares the same le/te lines

    for profile in profiles:
        for other_profile in profiles:

            classify_wing_section(wing_sections, profile, other_profile)

    # add the wing sections founded to the wing ModelPart

    wing_part.wing_sections = wing_sections

    # Dealing with the special wing section that is attached to the fuselage :
    # this wing section is special because multiple lines form the profile that is
    # attached to the fuselage

    classify_special_section(wing_part, wing_sections, profiles)

    # update wing sections in the part

    wing_part.wing_sections = wing_sections


# ==============================================================================
#    MAIN
# ==============================================================================
if __name__ == "__main__":
    print("Nothing to execute!")
