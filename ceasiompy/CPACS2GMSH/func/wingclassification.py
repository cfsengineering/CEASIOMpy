"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains diffrent functions to classify and manipulate wing elements

Python version: >=3.7

| Author: Tony Govoni
| Creation: 2022-04-05

TODO:

    -

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
        adj_le_lines = list(adj_le_lines)

        adj_te_lines, _ = gmsh.model.getAdjacencies(0, pair_points[1])
        adj_te_lines = list(adj_te_lines)

        # remove from all the adjacent line the ones that are the profile spline

        [adj_le_lines.remove(spline) for spline in splines_dim_tag]
        [adj_te_lines.remove(spline) for spline in splines_dim_tag]

        # the remaining lines are the leading and trailing edge lines

        profile_list.append(
            {
                "truncated": False,
                "lines_dimtag": splines_dim_tag,
                "points_tag": pair_points,
                "adj_le_lines": adj_le_lines,
                "adj_te_lines": adj_te_lines,
                "chord_length": chord,
            }
        )
        return True
    else:
        return False


def classify_trunc_profile(profiles, profile_lines, line_comp, line_comp_other):
    pair_points = line_comp["points_tags"]
    pair_points_other = line_comp_other["points_tags"]

    if (line_comp_other["line_dimtag"] == line_comp["line_dimtag"]) or (
        (pair_points[0] not in pair_points_other) and (pair_points[1] not in pair_points_other)
    ):
        return False
    else:
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
        points = list(points)
        # if 3 line sharing common points are found, then the profile is found
        if len(loop_line) != 3:
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

        # the two trailing edge points are the closest togheter
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

        # classify the profile
        profiles.append(
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
    truncated_profile = profile["truncated"]

    if not truncated_profile:

        if other_profile == profile:
            return False

        # find the shared leading edge line
        le_line = (set(profile["adj_le_lines"])).intersection(set(other_profile["adj_le_lines"]))
        te_line = (set(profile["adj_te_lines"])).intersection(set(other_profile["adj_te_lines"]))

        if len(le_line) == 1 and len(te_line) == 1:
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
                    "le_line": list(le_line),
                    "te_line": list(te_line),
                    "le_points": [
                        (0, profile["points_tag"][0]),
                        (0, other_profile["points_tag"][0]),
                    ],
                    "te_points": [
                        (0, profile["points_tag"][1]),
                        (0, other_profile["points_tag"][1]),
                    ],
                    "mean_chord": 0.5 * (profile["chord_length"] + other_profile["chord_length"]),
                }
            )
            return True

    else:

        # seek for the shared leading edge and trailing line
        le_line = (set(profile["adj_le_lines"])).intersection(set(other_profile["adj_le_lines"]))
        te_line = (set(profile["adj_te_lines"])).intersection(set(other_profile["adj_te_lines"]))

        # there must be 1 le line and 2 te lines
        if len(le_line) == 1 and len(te_line) == 2:

            # TODO: classify the surfaces between the profile
            # classify the wing section
            wing_sections.append(
                {
                    "truncated": truncated_profile,
                    "profiles": [
                        profile["lines_dimtag"],
                        other_profile["lines_dimtag"],
                    ],
                    "le_line": list(le_line),
                    "te_line": list(te_line),
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
                }
            )
            return True


def classify_special_section(wing_sections):

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

    print(le_line_fus_wing)

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
            "truncated": wing_section["truncated"],
            "profiles": [],
            "le_line": [le_line_fus_wing[0]],
            "te_line": [te_line_fus_wing],
            "le_points": [le_points],
            "te_points": [te_points],
        }
    )
    return True


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

        for line_comp_other in lines_composition:

            profile_found = classify_profile(profiles, line_comp, line_comp_other)

            if profile_found:
                lines_composition.remove(line_comp_other)

    # if none of the line share the same two points, the wing is truncated
    if profiles == []:

        profile_lines = []

        # Compare two line of the wing searching for this time only one point in common
        for line_comp in lines_composition:
            for line_comp_other in lines_composition:

                profile_found = classify_trunc_profile(
                    profiles, profile_lines, line_comp, line_comp_other
                )
                if profile_found:
                    lines_composition.remove(line_comp_other)

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
            section_found = classify_wing_section(wing_sections, profile, other_profile)

            if section_found:
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
        classify_special_section(wing_sections)


# ==============================================================================
#    MAIN
# ==============================================================================
if __name__ == "__main__":
    print("Nothing to execute!")
