"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains diffrent functions to classify and manipulate wing elements

Python version: >=3.7

| Author: Tony Govoni
| Creation: 2022-04-07

TODO:

    -

"""


# ==============================================================================
#   IMPORTS
# ==============================================================================
import gmsh

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def refine_wing_section(
    mesh_fields,
    wing_part,
    mesh_size_wings,
    refine,
    chord_percent,
):
    """
    Function to refine the trailling and leading edge of an wing section,
    a field is created with a refinement size equivalent to the wing mesh size divided by the
    refinement factor (le/te_refine)

    This refinement take place from the leading or trailing edge until a distance equivalent
    to a percentage of the chord
    if the wing section is not constant chordwise, the mean chord of the wing section is used

    the "Threshold" + "Distance" field that is used work like the following :


    // We then define a `Threshold' field, which uses the return value of the
    // `Distance' field 1 in order to define a simple change in element size
    // depending on the computed distances
    //
    // SizeMax -                     /------------------
    //                              /
    //                             /
    //                            /
    // SizeMin -o----------------/
    //          |                |    |
    //        Point         DistMin  DistMax

    with :  SizeMin = wing_mesh_size/refine,
            SizeMax = wing_mesh_size
            DistMin = chord_mean * chord_percent, DistMax = DistMin* 1.1
    ...

    Args:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model,
        each field must be created with a different index !!!
        mesh_fields["restrict_fields"] : list of the restrict fields,
        this is the list to be use for the final "Min" background field
    wing_part : Aircraftpart
        wing part to refine
    mesh_size_wings : float
        mesh size of the wing
    wing_section : wing_section (see wingclassification.py)
        wing_section to refine
    refine : float
        refinement factor for the le/te edge
    chord_percent : float
        percentage of the chord to refine from le/te edge
    ...
    """
    # get the wing section chord, le and te lines and the surface of the wing section

    sigmoid = False
    include_boundary = True
    for wing_section in wing_part.wing_sections:
        chord_mean = wing_section["mean_chord"]
        le_line = wing_section["le_line"]
        te_line = wing_section["te_line"]
        surfaces = wing_section["surfaces"]
        adj_lines = []
        for surface in surfaces:
            _, adj_lin = gmsh.model.getAdjacencies(2, surface)
            adj_lines.extend(adj_lin)

        adj_surfaces = []
        for line in adj_lines:
            adj_surf, _ = gmsh.model.getAdjacencies(1, line)
            adj_surfaces.extend(adj_surf)
        adj_surfaces = list(set(adj_surfaces))

        lines_to_refine = [*le_line, *te_line]

        # create new distance field
        mesh_fields["nbfields"] += 1
        gmsh.model.mesh.field.add("Distance", mesh_fields["nbfields"])
        gmsh.model.mesh.field.setNumbers(mesh_fields["nbfields"], "CurvesList", lines_to_refine)
        gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "Sampling", 100)

        # create new threshold field
        mesh_fields["nbfields"] += 1
        gmsh.model.mesh.field.add("Threshold", mesh_fields["nbfields"])
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
        )
        gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "Sigmoid", sigmoid)
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "SizeMin", mesh_size_wings / refine
        )
        gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "SizeMax", mesh_size_wings)
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "DistMin", chord_percent * chord_mean
        )
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "DistMax", chord_percent * chord_mean * 1.2
        )

        # create new Restrict field
        mesh_fields["nbfields"] += 1
        gmsh.model.mesh.field.add("Restrict", mesh_fields["nbfields"])
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
        )
        gmsh.model.mesh.field.setNumbers(mesh_fields["nbfields"], "SurfacesList", adj_surfaces)
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "IncludeBoundary", include_boundary
        )
        # add the new field to the list of restrict fields
        mesh_fields["restrict_fields"].append(mesh_fields["nbfields"])


def set_fuselage_mesh(mesh_fields, fuselage_part, mesh_size_fuselage):
    """
    Function to refine the fuselage mesh

    Args:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model,
        each field must be created with a different index !!!
        mesh_fields["restrict_fields"] : list of the restrict fields,
        this is the list to be use for the final "Min" background field
    fuselage_part : Aircraftpart
        fuselage part to set mesh size
    mesh_size_fuselage : float
        mesh size of the fuselage
    ...
    """
    # get the fuselage surface
    surfaces = fuselage_part.surfaces
    surfaces_tags = [dimtag[1] for dimtag in surfaces]
    include_boundary = True

    # create new distance field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Distance", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumbers(mesh_fields["nbfields"], "SurfacesList", surfaces_tags)
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "Sampling", 100)

    # create new threshold field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Threshold", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
    )
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "SizeMin", mesh_size_fuselage)

    # create new Restrict field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Restrict", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
    )
    gmsh.model.mesh.field.setNumbers(mesh_fields["nbfields"], "SurfacesList", surfaces_tags)
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "IncludeBoundary", include_boundary)
    # add the new field to the list of restrict fields
    mesh_fields["restrict_fields"].append(mesh_fields["nbfields"])


def set_farfield_mesh(
    mesh_fields, model_center, domain_length, min_mesh_size, farfield_surfaces, mesh_size_farfield
):
    """
    Function to define the farfield mesh

    Args:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model,
        each field must be created with a different index !!!
        mesh_fields["restrict_fields"] : list of the restrict fields,
        this is the list to be use for the final "Min" background field
    farfield_surfaces : list
        list of the farfield surfaces to set mesh size
    mesh_size_fuselage : float
        mesh size of the farfield
    ...
    """
    # get the farfield surface
    surfaces_tags = [dimtag[1] for dimtag in farfield_surfaces]
    include_boundary = True

    # create new distance field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Distance", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumbers(mesh_fields["nbfields"], "SurfacesList", surfaces_tags)
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "Sampling", 100)

    # create new threshold field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Threshold", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
    )
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "SizeMin", mesh_size_farfield)
    # create new Restrict field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Restrict", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
    )
    gmsh.model.mesh.field.setNumbers(mesh_fields["nbfields"], "SurfacesList", surfaces_tags)
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "IncludeBoundary", include_boundary)
    # add the new field to the list of restrict fields
    mesh_fields["restrict_fields"].append(mesh_fields["nbfields"])

    # create new distance field
    # temp_center = gmsh.model.occ.addPoint(*model_center, 0)

    # gmsh.model.occ.remove([(0, temp_center)])
    # gmsh.model.occ.synchronize()

    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Distance", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumbers(mesh_fields["nbfields"], "PointsList", [12])

    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("MathEval", mesh_fields["nbfields"])
    xc, yc, zc = round(model_center[0], 3), round(model_center[1], 3), round(model_center[2], 3)
    gmsh.model.mesh.field.setString(
        mesh_fields["nbfields"],
        "F",
        "Max(((("
        + str(xc)
        + "-x)^2 +("
        + str(yc)
        + "-y)^2+("
        + str(zc)
        + "-z)^2)^0.5)/10 ,"
        + str(min_mesh_size)
        + ")",
    )
    mesh_fields["restrict_fields"].append(mesh_fields["nbfields"])


# ==============================================================================
#    MAIN
# ==============================================================================
if __name__ == "__main__":
    print("Nothing to execute!")
