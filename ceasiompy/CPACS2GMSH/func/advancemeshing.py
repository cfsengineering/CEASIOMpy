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
import numpy as np
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def distance_field(mesh_fields, dim, object_tags):
    """
    This function creates a distance field and add it to the list of mesh fields

    Args:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model,
        each field must be created with a different index !!!

    dim : int
        dimension of the object to apply the distance field on
    object_tags : list
        list of the tags of the object ti apply the distance field on

    Returns:
    ----------
    mesh_fields : dict
    """

    # create new distance field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Distance", mesh_fields["nbfields"])
    if dim == 1:
        dim_list = "CurvesList"
    elif dim == 2:
        dim_list = "SurfacesList"
    else:
        raise ValueError("Dimension must be 1 or 2")
    gmsh.model.mesh.field.setNumbers(mesh_fields["nbfields"], dim_list, object_tags)

    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "Sampling", 100)

    return mesh_fields


def restrict_fields(mesh_fields, dim, object_tags, infield=None):
    """
    This function creates a restrict field on the last field in mesh_fields

    Args:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model,
        each field must be created with a different index !!!

    dim : int
        dimension of the object to apply the restrict field on
    object_tags : list
        list of the tags of the object to apply the restrict field on
    infield : int
        index of the field to restrict if needed to be specified

    Returns:
    ----------
    mesh_fields : dict
    """
    # create new Restrict field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Restrict", mesh_fields["nbfields"])

    if infield is None:
        infield = mesh_fields["nbfields"] - 1

    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "InField", infield)
    if dim == 2:
        dim_list = "SurfacesList"
    elif dim == 3:
        dim_list = "VolumesList"
    else:
        raise ValueError("Dimension must be 2 or 3")
    gmsh.model.mesh.field.setNumbers(mesh_fields["nbfields"], dim_list, object_tags)

    # add the new field to the list of restrict fields

    mesh_fields["restrict_fields"].append(mesh_fields["nbfields"])
    return mesh_fields


def refine_wing_section(
    mesh_fields,
    final_domain_volume_tag,
    aircraft,
    wing_part,
    mesh_size_wings,
    refine,
    chord_percent=0.3,
    n_power=1.25,
):
    """
    Function to refine the trailling and leading edge of an wing section,
    2 field are created, a treshold and matheval field

    The treshold field is used to keep the element on the wing to a maximum size of mesh_size_wings

    A Math eval field is used to define a refinement from the leading /or trailing edge of the wing
    with the folowing function:

        MeshSize (x_le) = mesh_w/r + mesh_w"(1-1/r)*(x_le/x_chord)^n_power

    with :
        - mesh_w : the mesh size of the wing = mesh_size_wings
        - r : the refine factor = refine
        - x_chord : the distance at which the refinement function stop = chord_percent*chord_length
        - n_power : the power of the refinement function = n_power

        x_le is computed automatically by a distance field F, and give the distance (x,y,z)
        from the leading edge curve

    If the profile is truncated, the refinement for the trailing edge will be set such that
    the value of the mesh size will match the distance between the two trailing edge curves

    Args:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model,
        each field must be created with a different index !!!
        mesh_fields["restrict_fields"] : list of the restrict fields,
        this is the list to be use for the final "Min" background field
    aircraft : ModelPart
        the aircraft model part
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

    log.info(f"Set mesh refinement of {wing_part.uid}")

    original_refine = refine
    # get the wing section chord, le and te lines and the surface of the wing
    surfaces_wing = wing_part.surfaces_tags

    # for each wing section get the mean chord and le/te lines
    for wing_section in wing_part.wing_sections:

        chord_mean = wing_section["mean_chord"]
        x_chord = chord_mean * chord_percent
        lines_to_refine = wing_section["lines_tags"]

        if len(lines_to_refine) == 3:
            # if the wing is truncated:
            # first find the trailing edge thinkness
            x1, y1, z1 = gmsh.model.occ.getCenterOfMass(1, lines_to_refine[0])
            x2, y2, z2 = gmsh.model.occ.getCenterOfMass(1, lines_to_refine[1])
            x3, y3, z3 = gmsh.model.occ.getCenterOfMass(1, lines_to_refine[2])

            d12 = np.linalg.norm([x2 - x1, y2 - y1, z2 - z1])
            d13 = np.linalg.norm([x3 - x1, y3 - y1, z3 - z1])
            d23 = np.linalg.norm([x3 - x2, y3 - y2, z3 - z2])

            te_thickness = min(d12, d13, d23)

            # then overwrite the trailing edge refinement
            if mesh_size_wings / te_thickness > refine:
                refine = mesh_size_wings / te_thickness

        # 1 : Math eval field
        # distance field
        mesh_fields = distance_field(mesh_fields, 1, lines_to_refine)
        # create a mesh function for the leading edge
        mesh_fields["nbfields"] += 1
        math_eval_field = mesh_fields["nbfields"]
        gmsh.model.mesh.field.add("MathEval", mesh_fields["nbfields"])
        distance_field_tag = mesh_fields["nbfields"] - 1
        gmsh.model.mesh.field.setString(
            mesh_fields["nbfields"],
            "F",
            f"({mesh_size_wings}/{refine}) + "
            f"{mesh_size_wings}*(1-(1/{refine}))*"
            f"(F{distance_field_tag}/{x_chord})^{n_power}",
        )
        # restrict field
        mesh_fields = restrict_fields(mesh_fields, 2, aircraft.surfaces_tags)
        mesh_fields = restrict_fields(
            mesh_fields, 3, final_domain_volume_tag, infield=math_eval_field
        )

        # 2 : Treshold field
        # distance field
        mesh_fields = distance_field(mesh_fields, 1, lines_to_refine)
        # create the treshold field
        mesh_fields["nbfields"] += 1
        gmsh.model.mesh.field.add("Threshold", mesh_fields["nbfields"])
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
        )
        gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "SizeMax", mesh_size_wings)
        gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "SizeMin", mesh_size_wings)
        # restrict field
        mesh_fields = restrict_fields(mesh_fields, 2, surfaces_wing)

    if original_refine != refine:
        log.info(
            f"{wing_part.uid} is truncated : refinement factor was increase from "
            f"{original_refine} to " + str(round(refine, 2))
        )
    if refine > 20:
        log.warning("Refinement factor is high !")
        log.info(
            f"Consider reducing the wing mesh size from {mesh_size_wings} to "
            "{:.2e}".format(mesh_size_wings * 20 / refine)
        )


def set_fuselage_mesh(mesh_fields, fuselage_part, mesh_size_fuselage):
    """
    Function to refine the fuselage mesh, apply a constant mesh size to the fuselage

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

    log.info(f"Set mesh refinement of {fuselage_part.uid}")

    # create new distance field
    mesh_fields = distance_field(mesh_fields, 2, fuselage_part.surfaces_tags)

    # create new threshold field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Threshold", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
    )
    gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "SizeMin", mesh_size_fuselage)

    # restrict field
    mesh_fields = restrict_fields(mesh_fields, 2, fuselage_part.surfaces_tags)


def set_farfield_mesh(
    mesh_fields,
    aircraft_parts,
    mesh_size_farfield,
    aircraft_charact_length,
    final_domain_volume_tag,
    n_power=1.5,
):
    """
    Function to define the farfield mesh with a treshold and matheval field

    The treshold field is used to keep the element in the farfield to a maximum size
    of mesh_size_farfield.

    A Math eval field is used to extend the mesh of each part of the aircraft in the fluid domain
    with the folowing function:

        MeshSize (x) = mesh_p + (mesh_f - mesh_p)*(x/d_char)^n_power

    with :
        - mesh_p : the mesh size of the aircraft part = part.mesh_size
        - mesh_f : the mesh size of the farfield = mesh_size_farfield
        - d_char : the characteristic length of the aircraft = aircraft_charact_length
        - n_power : the power of the power law for the mesh extend function = n_power

        x is the distance from the part surfaces computed automatically by a distance field F

    Args:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model,
        each field must be created with a different index !!!
        mesh_fields["restrict_fields"] : list of the restrict fields,
        this is the list to be use for the final "Min" background field
    aircraft_parts : list(ModelPart)
        list of the aircraft parts in the model
    mesh_size_farfield : float
        mesh size of the farfield
    aircraft_charact_length : float
        characteristic length of the aircraft : max(x_length, y_length, z_length) of the aircraft
    final_domain_volume_tag : int
        tag of the final domain volume
    ...
    """

    log.info("Set mesh refinement of fluid domain")

    for part in aircraft_parts:

        # 1 : Math eval field
        # distance field
        mesh_fields = distance_field(mesh_fields, 2, part.surfaces_tags)
        # create a mesh function
        mesh_fields["nbfields"] += 1
        gmsh.model.mesh.field.add("MathEval", mesh_fields["nbfields"])
        distance_field_tag = mesh_fields["nbfields"] - 1
        gmsh.model.mesh.field.setString(
            mesh_fields["nbfields"],
            "F",
            f"{part.mesh_size} + ({mesh_size_farfield} - {part.mesh_size})*"
            f"(F{distance_field_tag}/{aircraft_charact_length})^{n_power}",
        )
        # restrict field
        mesh_fields = restrict_fields(mesh_fields, 3, final_domain_volume_tag)

        # 2 : Treshold field
        # distance field
        mesh_fields = distance_field(mesh_fields, 2, part.surfaces_tags)
        # create the treshold field
        mesh_fields["nbfields"] += 1
        gmsh.model.mesh.field.add("Threshold", mesh_fields["nbfields"])
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
        )
        gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "SizeMax", mesh_size_farfield)
        gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "SizeMin", mesh_size_farfield)
        # restrict field
        mesh_fields = restrict_fields(mesh_fields, 3, final_domain_volume_tag)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
