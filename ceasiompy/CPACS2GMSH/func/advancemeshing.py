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
    # get current state of the mesh_fields
    # get the wing section chord, le and te lines and the surface of the wing section

    sigmoid = False
    include_boundary = True
    for wing_section in wing_part.wing_sections:
        chord_mean = wing_section["mean_chord"]
        le_line = wing_section["le_line"]
        te_line = wing_section["te_line"]
        surfaces = wing_section["surfaces"]
        lines_to_refine = [*le_line, *te_line]

        for line in lines_to_refine:
            # create new distance field
            mesh_fields["nbfields"] += 1
            gmsh.model.mesh.field.add("Distance", mesh_fields["nbfields"])
            gmsh.model.mesh.field.setNumbers(mesh_fields["nbfields"], "CurvesList", [line])
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
            gmsh.model.mesh.field.setNumbers(mesh_fields["nbfields"], "SurfacesList", surfaces)
            gmsh.model.mesh.field.setNumber(
                mesh_fields["nbfields"], "IncludeBoundary", include_boundary
            )
            # add the new field to the list of restrict fields
            mesh_fields["restrict_fields"].append(mesh_fields["nbfields"])


# ==============================================================================
#    MAIN
# ==============================================================================
if __name__ == "__main__":
    print("Nothing to execute!")
