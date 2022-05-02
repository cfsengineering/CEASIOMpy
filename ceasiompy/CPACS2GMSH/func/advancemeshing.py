"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains diffrent functions to classify and manipulate wing elements

Python version: >=3.7

| Author: Tony Govoni
| Creation: 2022-04-07

TODO:

    -Do something better with the background field for the farfield volume
    -Add all the box /farfield/ skin parameter tunable in an advance mesh GUI?
    -get each part its bounding box and use it to define field box for each part
    -add a function to define many boxes with a deacreasing mesh size

"""


# =================================================================================================
#   IMPORTS
# =================================================================================================

import gmsh

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


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
    wing_part : ModelPart
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
    # get the wing section chord, le and te lines and the surface of the wing
    surfaces_wing = wing_part.surfaces_tags

    # for each wing section get the mean chord and le/te lines
    for wing_section in wing_part.wing_sections:

        chord_mean = wing_section["mean_chord"]
        le_line = wing_section["le_line"]
        te_line = wing_section["te_line"]
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
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "SizeMin", mesh_size_wings / refine
        )
        gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "SizeMax", mesh_size_wings)
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "DistMin", chord_percent * chord_mean
        )
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "DistMax", chord_percent * chord_mean * 1.25
        )

        # create new Restrict field
        mesh_fields["nbfields"] += 1
        gmsh.model.mesh.field.add("Restrict", mesh_fields["nbfields"])
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
        )
        gmsh.model.mesh.field.setNumbers(mesh_fields["nbfields"], "SurfacesList", surfaces_wing)
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
    fuselage_part : ModelPart
        fuselage part to set mesh size
    mesh_size_fuselage : float
        mesh size of the fuselage
    ...
    """
    # get the fuselage surface
    surfaces_tags = fuselage_part.surfaces_tags

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

    # add the new field to the list of restrict fields
    mesh_fields["restrict_fields"].append(mesh_fields["nbfields"])


def set_farfield_mesh(
    mesh_fields,
    max_size_mesh_aircraft,
    aircraft_surfaces_tags,
    skin_thickness,
    mesh_size_farfield,
    model_bb,
    domain_length,
    final_domain_volume_tag,
):
    """
    Function to define the farfield mesh with a box field around the aircraft

    Args:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model,
        each field must be created with a different index !!!
        mesh_fields["restrict_fields"] : list of the restrict fields,
        this is the list to be use for the final "Min" background field
    max_size_mesh_aircraft : float
        maximum mesh size of the aircraft
    aircraft_surfaces_tags : list
        list of the aircraft surfaces tags
    skin_thickness : float
        mesh skin thickness of the aircraft with a mesh size of max_mesh_size_aircraft
    mesh_size_farfield : float
        mesh size of the farfield
    model_bb : list
        bounding box of the model
    domain_length : float
        length of the domain
    final_domain_volume_tag : int
        tag of the final domain volume
    ...
    """
    # create new distance field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Distance", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumbers(
        mesh_fields["nbfields"], "SurfacesList", aircraft_surfaces_tags
    )
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "Sampling", 100)

    # create new threshold field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Threshold", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
    )
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "SizeMin", max_size_mesh_aircraft)
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "SizeMax", mesh_size_farfield)
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "DistMin", skin_thickness)
    mesh_fields["restrict_fields"].append(mesh_fields["nbfields"])

    # create new box field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Box", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "VIn", max_size_mesh_aircraft * 2)
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "VOut", mesh_size_farfield)
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "XMin", model_bb[0] - (model_bb[3] - model_bb[0]) * 0.1
    )
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "XMax", model_bb[3] + (model_bb[3] - model_bb[0]) * 0.5
    )
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "YMin", model_bb[1] - (model_bb[4] - model_bb[1]) * 0.1
    )
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "YMax", model_bb[4] + (model_bb[4] - model_bb[1]) * 0.1
    )
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "ZMin", model_bb[2] - (model_bb[5] - model_bb[2]) * 0.1
    )
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "ZMax", model_bb[5] + (model_bb[5] - model_bb[2]) * 0.1
    )
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "Thickness", domain_length / 10)

    # create new Restrict field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Restrict", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
    )
    gmsh.model.mesh.field.setNumbers(
        mesh_fields["nbfields"], "VolumesList", final_domain_volume_tag
    )
    # add the new field to the list of restrict fields
    mesh_fields["restrict_fields"].append(mesh_fields["nbfields"])


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
