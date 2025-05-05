"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains different functions to classify and manipulate wing elements

Python version: >=3.8

| Author: Tony Govoni
| Creation: 2022-04-07

TODO:

    -Add a parameter to let the user tune the powerlaw for the wing surface mesh

"""


# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.CPACS2GMSH.func.gmsh_utils import MESH_COLORS
import gmsh
import numpy as np
import math
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

    # Create new distance field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Distance", mesh_fields["nbfields"])
    if dim == 1:
        dim_list = "CurvesList"
    elif dim == 2:
        dim_list = "SurfacesList"
    else:
        raise ValueError("Dimension must be 1 or 2")
    gmsh.model.mesh.field.setNumbers(
        mesh_fields["nbfields"], dim_list, object_tags)

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

    # Create new Restrict field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Restrict", mesh_fields["nbfields"])

    if infield is None:
        infield = mesh_fields["nbfields"] - 1

    gmsh.model.mesh.field.setNumber(
        mesh_fields["nbfields"], "InField", infield)
    if dim == 2:
        dim_list = "SurfacesList"
    elif dim == 3:
        dim_list = "VolumesList"
    else:
        raise ValueError("Dimension must be 2 or 3")

    gmsh.model.mesh.field.setNumbers(
        mesh_fields["nbfields"], dim_list, object_tags)

    # Add the new field to the list of restrict fields
    mesh_fields["restrict_fields"].append(mesh_fields["nbfields"])

    return mesh_fields


def min_fields(mesh_fields):
    """
    This function creates a Min field:

    A min field take a FieldsList of all the restrict field
    Then it compute the minimum mesh constraint of all the different fields
    This field is set as the background field for the model and it is the "final"
    field that is used by gmsh to compute the mesh

    Args:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model,
        each field must be created with a different index !!!

    Returns:
    ----------
    mesh_fields : dict
    """

    # Add a minimal background mesh field
    mesh_fields["nbfields"] += 1
    gmsh.model.mesh.field.add("Min", mesh_fields["nbfields"])
    gmsh.model.mesh.field.setNumbers(
        mesh_fields["nbfields"], "FieldsList", mesh_fields["restrict_fields"]
    )
    # log.info(f"Set min field with {mesh_fields["restrict_fields"]}")
    gmsh.model.mesh.field.setAsBackgroundMesh(mesh_fields["nbfields"])

    # When background mesh is used those options must be set to zero
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

    return mesh_fields


def compute_area(surface_tag):
    """
    Function to compute the area of a surface using gmsh plugin

    first create a physical group with the surface, its mandatory to have a physical group
    to compute the area since its the input for the plugin function

    Args:
    ----------
    surface_tag : int
        tag of the surface to compute the area
    """

    # Create a physical group with the surface
    surface_groupe = gmsh.model.addPhysicalGroup(2, [surface_tag])

    # Call the plugin
    gmsh.plugin.setNumber("MeshVolume", "Dimension", 2)
    gmsh.plugin.setNumber("MeshVolume", "PhysicalGroup", surface_groupe)
    gmsh.plugin.run("MeshVolume")

    # Retrieve the area in the views data
    views = gmsh.view.getTags()
    _, _, data = gmsh.view.getListData(views[-1])
    area = data[-1][-1]

    # clean the views and the physical group
    for v in views:
        gmsh.view.remove(v)
    gmsh.model.removePhysicalGroups([(2, surface_groupe)])

    return area


def refine_wing_section(
    mesh_fields,
    final_domain_volume_tag,
    aircraft,
    wing_part,
    mesh_size_wings,
    refine,
    refine_truncated,
    chord_percent=0.25,
    n_power=2,
):
    """
    Function to refine the trailing and leading edge of an wing section,
    2 field are created, a threshold and matheval field

    The threshold field is used to keep the element on the wing to a max size of mesh_size_wings

    A Math eval field is used to define a refinement from the leading /or trailing edge of the wing
    with the following function:

        MeshSize (x_le) = mesh_w/r + mesh_w"(1-1/r)*(x_le/x_chord)^n_power

    with :
        - mesh_w : the mesh size of the wing = mesh_size_wings
        - r : the refine factor = refine
        - x_chord : the distance at which the refinement function stop = chord_percent*chord_length
        - n_power : the power of the refinement function = n_power

        x_le is computed automatically by a distance field F, and give the distance (x,y,z)
        from the leading edge curve

    If the profile is truncated, the refinement for the trailing edge will be set such that
    the value of the mesh size will match the 2 times distance between the two trailing edge curves

    Args:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model,
        each field must be created with a different index !!!
        mesh_fields["restrict_fields"] : list of the restrict fields,
        this is the list to be use for the final "Min" background field
    aircraft : ModelPart
        the aircraft model part
    final_domain_volume_tag : list
        list of the tag(s) of the final domain volume (usually one)
    wing_part : ModelPart
        wing part to refine
    mesh_size_wings : float
        mesh size of the wing
    wing_section : wing_section (see wingclassification.py)  --> Not an arg ? aaaah
        wing_section to refine
    refine : float
        refinement factor for the le/te edge
    refine_truncated : bool
        if the wing is truncated, the trailing edge will be refined to match the te thickness
    chord_percent : float
        percentage of the chord to refine from le/te edge
    ...
    """

    log.info(f"Set mesh refinement of {wing_part.uid}")

    original_refine = refine

    # Get the wing section chord, le and te lines and the surface of the wing
    surfaces_wing = wing_part.surfaces_tags

    # For each wing section get the mean chord and le/te lines
    for wing_section in wing_part.wing_sections:
        chord_mean = wing_section["mean_chord"]
        x_chord = chord_mean * chord_percent
        lines_to_refine = wing_section["lines_tags"]
        # If the wing is truncated:
        if len(lines_to_refine) == 3:
            # Find the trailing edge thickness
            x1, y1, z1 = gmsh.model.occ.getCenterOfMass(1, lines_to_refine[0])
            x2, y2, z2 = gmsh.model.occ.getCenterOfMass(1, lines_to_refine[1])
            x3, y3, z3 = gmsh.model.occ.getCenterOfMass(1, lines_to_refine[2])

            d12 = np.linalg.norm([x2 - x1, y2 - y1, z2 - z1])
            d13 = np.linalg.norm([x3 - x1, y3 - y1, z3 - z1])
            d23 = np.linalg.norm([x3 - x2, y3 - y2, z3 - z2])

            te_thickness = min(d12, d13, d23)

            # Overwrite the trailing edge refinement
            if (mesh_size_wings / te_thickness > refine) and refine_truncated:
                refine = mesh_size_wings / te_thickness

        # 1 : Math eval field

        mesh_fields = distance_field(mesh_fields, 1, lines_to_refine)
        distance_field_tag = mesh_fields["nbfields"]

        # Create a mesh function for the leading edge
        mesh_fields["nbfields"] += 1
        math_eval_field = mesh_fields["nbfields"]
        gmsh.model.mesh.field.add("MathEval", mesh_fields["nbfields"])

        gmsh.model.mesh.field.setString(
            mesh_fields["nbfields"],
            "F",
            f"({mesh_size_wings}/{refine}) + "
            f"{mesh_size_wings}*(1-(1/{refine}))*"
            f"(F{distance_field_tag}/{x_chord})^{n_power}",
        )

        mesh_fields = restrict_fields(mesh_fields, 2, aircraft.surfaces_tags)
        mesh_fields = restrict_fields(
            mesh_fields, 3, final_domain_volume_tag, infield=math_eval_field)

        # 2 : Threshold field

        # Create the threshold field
        mesh_fields["nbfields"] += 1
        gmsh.model.mesh.field.add("Threshold", mesh_fields["nbfields"])
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "InField", distance_field_tag)
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "SizeMax", mesh_size_wings)
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "SizeMin", mesh_size_wings)

        mesh_fields = restrict_fields(mesh_fields, 2, surfaces_wing)

    if original_refine != refine:
        log.info(
            f"{wing_part.uid} is truncated : refinement factor was increased from "
            f"{original_refine} to " + str(round(refine, 2))
        )

    if refine > 20:
        log.warning("Refinement factor is high !")
        log.info(
            f"Consider reducing the wing mesh size from {mesh_size_wings} to "
            "{:.2e}".format(mesh_size_wings * 20 / refine)
        )


def set_domain_mesh(
    mesh_fields,
    aircraft_parts,
    mesh_size_farfield,
    aircraft_charact_length,
    final_domain_volume_tag,
    n_power_factor,
    n_power_field,
):
    """
    Function to define the domain mesh between the farfield and the aircraft

    A threshold field is used to keep the element on the farfield to a maximum size
    of mesh_size_farfield.

    Each part get a threshold field with the part mesh size on its surface

    A Math eval field is used to extend the mesh of each part of the aircraft in the fluid domain
    with the following function:

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
        # 1 : Math eval field between the part surface and the farfield

        mesh_fields = distance_field(mesh_fields, 2, part.surfaces_tags)
        distance_field_tag = mesh_fields["nbfields"]

        # Create a mesh function
        mesh_fields["nbfields"] += 1
        gmsh.model.mesh.field.add("MathEval", mesh_fields["nbfields"])
        gmsh.model.mesh.field.setString(
            mesh_fields["nbfields"],
            "F",
            f"{part.mesh_size} + ({mesh_size_farfield} - {part.mesh_size})*"
            f"(F{distance_field_tag}/{aircraft_charact_length})^{n_power_factor}",
        )
        mesh_fields = restrict_fields(mesh_fields, 3, final_domain_volume_tag)

        # 2 : Threshold field for constant mesh on the part surface

        # Create the threshold field
        mesh_fields["nbfields"] += 1
        gmsh.model.mesh.field.add("Threshold", mesh_fields["nbfields"])
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "InField", distance_field_tag)
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "SizeMax", part.mesh_size)
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "SizeMin", part.mesh_size * n_power_field
        )

        mesh_fields = restrict_fields(mesh_fields, 2, part.surfaces_tags)

        # 3 : Threshold field for the farfield surface

        # Create the threshold field
        mesh_fields["nbfields"] += 1
        gmsh.model.mesh.field.add("Threshold", mesh_fields["nbfields"])
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "InField", distance_field_tag)

        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "SizeMax", mesh_size_farfield)
        gmsh.model.mesh.field.setNumber(
            mesh_fields["nbfields"], "SizeMin", mesh_size_farfield * 0.9
        )

        mesh_fields = restrict_fields(mesh_fields, 3, final_domain_volume_tag)


def refine_small_surfaces(
    mesh_fields,
    part,
    mesh_size_farfield,
    aircraft_charact_length,
    final_domain_volume_tag,
    n_power=1.5,
    nb_min_triangle=150,
):
    """
    Function to refine the mesh

    Each surface of the part is inspected :

    - if the surface area is very small compare to the mesh size of the part mesh
    the surface is remeshed with a smaller mesh size
    --> With parameters by default, if with mesh size we have less than 150 triangles in the surface, we set the mesh size to have 150 triangles


    Args:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model,
        each field must be created with a different index !!!
        mesh_fields["restrict_fields"] : list of the restrict fields,
        this is the list to be use for the final "Min" background field
    part : ModelPart
        part inspect
    mesh_size_farfield : float
        mesh size of the farfield
    aircraft_charact_length : float
        characteristic length of the aircraft : max(x_length, y_length, z_length) of the aircraft
    final_domain_volume_tag : list
        list of tag of the final domain volume (usually one)
    n_power : float
        power of the power law for the mesh extend function
    nb_min_triangle : int
        number of minimum triangle in a mesh surface to trigger the mesh refinement
    ...
    Returns:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model
    part : ModelPart
        part to check and refine if necessary


    """

    # Get the area of an equilateral triangle with the expected mesh size of the part
    mesh_triangle_surf = (3**0.5 / 4) * (part.mesh_size**2)

    refined_surfaces = []

    for surface_tag in part.surfaces_tags:
        area = compute_area(surface_tag)

        if area < nb_min_triangle * mesh_triangle_surf:
            refined_surfaces.append(surface_tag)

            # Refine the surface
            new_mesh_size = ((area / (nb_min_triangle)) / 0.43301270) ** 0.5
            # computation : we want areaoftriangle to be totalarea/nbtriangle, and area of triangle = sqrt(3)/4 * (side = mesh size)^2

            # Set the color to indicate the bad surfaces
            gmsh.model.setColor([(2, surface_tag)],
                                * MESH_COLORS["bad_surface"], recursive=False)

            mesh_fields = distance_field(mesh_fields, 2, [surface_tag])
            distance_field_tag = mesh_fields["nbfields"]

            # Create new threshold field
            mesh_fields["nbfields"] += 1
            gmsh.model.mesh.field.add("Threshold", mesh_fields["nbfields"])
            gmsh.model.mesh.field.setNumber(
                mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1
            )
            gmsh.model.mesh.field.setNumber(
                mesh_fields["nbfields"], "SizeMin", new_mesh_size)
            gmsh.model.mesh.field.setNumber(
                mesh_fields["nbfields"], "SizeMax", new_mesh_size)

            mesh_fields = restrict_fields(mesh_fields, 2, [surface_tag])

            # Math eval field
            mesh_fields["nbfields"] += 1
            gmsh.model.mesh.field.add("MathEval", mesh_fields["nbfields"])
            gmsh.model.mesh.field.setString(
                mesh_fields["nbfields"],
                "F",
                f"{new_mesh_size} + ({mesh_size_farfield} - {new_mesh_size})*"
                f"(F{distance_field_tag}/{aircraft_charact_length})^{n_power}",
            )
            log.info(f"refine surface {surface_tag}")

            mesh_fields = restrict_fields(
                mesh_fields, 3, final_domain_volume_tag)

    log.info(f"Surface mesh of {part.uid} was insufficient")

    return refined_surfaces, mesh_fields


def refine_lines_with_acute_angles(
    te_le_already_refined, refine, aircraft_parts, mesh_fields, mesh_size_by_part, n_power
):
    """
    Function to refine the mesh along edges with really small angles (as done for the leading and trailing edges, but for others)

    Each line is inspected :

    - if the angle between the adjacent surfaces is smaller than 72 degrees, we refine along this line
    --> To compute the angle, we get the nodes along the line, then the normal at these nodes for each surface and compute the scalar product which is the cosinus


    Args:
    ----------
    te_le_already_refined : list of int
        list of the tags of the lines already refined in the function "refine_le_te"
    refine : float
        refinement factor
    aircraft_parts : list of ModelPart
        list of all the parts in the aircraft
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model,
        each field must be created with a different index !!!
        mesh_fields["restrict_fields"] : list of the restrict fields,
        this is the list to be use for the final "Min" background field
    mesh_size_by_part : dict
        dictionary of the mesh size depending on the type of part
    n_power : float
        power of the power law for the refinement
    ...
    Returns:
    ----------
    mesh_fields : dict
        mesh_fields["nbfields"] : number of existing mesh field in the model

    """

    # Need a mesh to create the nodes along the lines
    log.info("Must first generate a 1D mesh")
    gmsh.model.mesh.generate(1)
    gmsh.model.occ.synchronize()
    # First we need to find which lines are the ones we want to refine
    log.info(f"Now finding which lines need refinement")
    lines = gmsh.model.getEntities(1)
    lines_with_angles_tag = []
    total = len(lines)
    step_lines = len(lines) // 10

    for (dim, line) in lines:
        # Show progress
        if line % step_lines == 0:
            log.info(f"{math.floor(line/total*100)}% done")

        foundbigangle = False
        # Get the adjacent surface, and the nodes
        surfs, points = gmsh.model.getAdjacencies(dim, line)
        tags, coord, param = gmsh.model.mesh.getNodes(1, line)
        nbpoints = len(coord) // 3
        # Select at most 40 nodes (but 20 evenly spaces if too big)
        step = nbpoints // 20
        if nbpoints < 40:
            coord_small = coord
        else:
            coord_small = []
            for i in range(20):
                coord_small.extend(
                    [coord[step * 3 * i], coord[step * 3 * i + 1], coord[step * 3 * i + 2]])

        # Now test for every 2 surfaces along line (usually always one or two surfaces total)
        # And if one, can't be a weird angle
        for k in range(len(surfs)):
            i = surfs[k]
            params_i = gmsh.model.getParametrization(2, i, coord_small)
            for l in range(k + 1, len(surfs)):
                j = surfs[l]
                params_j = gmsh.model.getParametrization(2, j, coord_small)
                for a in range(len(coord_small) // 3):
                    # For each point, get the normal to the surface
                    normal_i = gmsh.model.getNormal(
                        i, [params_i[2 * a], params_j[2 * a + 1]])
                    normal_j = gmsh.model.getNormal(
                        j, [params_i[2 * a], params_j[2 * a + 1]])
                    # Compute cos of the angle between the normals (their norms are 1, so is equal to scalar product)
                    cosalpha = (
                        normal_i[0] * normal_j[0] + normal_i[1] * normal_j[1] + normal_i[2] * normal_j[2])
                    if cosalpha < -0.3:  # (more than 72 degrees from being flat)
                        lines_with_angles_tag.append(line)
                        foundbigangle = True
                        break
                if foundbigangle:
                    break
            if foundbigangle:
                break

    # Old version kept because the new one doesn't work
    # But is really really slow and inefficient
    '''
    for (dim, line) in lines:
        if line % step == 0:
            log.info(f"{math.floor(line/total*100)}% done")
        foundbigangle = False
        surfs, points = gmsh.model.getAdjacencies(dim, line)
        tags_coords_params = {-1: "yay"}
        for i in surfs:
            tags, coord, param = gmsh.model.mesh.getNodes(2, i, True)
            dict = {'tags': tags, 'coord': coord, 'param': param}
            tags_coords_params[i] = dict
        for k in range(len(surfs)):
            i = surfs[k]
            coordi = tags_coords_params[i]['coord']
            for l in range(k + 1, len(surfs)):
                j = surfs[l]
                coordj = tags_coords_params[j]['coord']

                for a in range(len(coordi) // 3):
                    for b in range(len(coordj) // 3):
                        if coordi[3 * a] == coordj[3 * b] and coordi[3 * a + 1] == coordj[3 * b + 1] and coordi[3 * a + 2] == coordj[3 * b + 2]:
                            normal_i = gmsh.model.getNormal(
                                i, [tags_coords_params[i]['param'][2 * a], tags_coords_params[i]['param'][2 * a + 1]])
                            normal_j = gmsh.model.getNormal(
                                j, [tags_coords_params[j]['param'][2 * b], tags_coords_params[j]['param'][2 * b + 1]])
                            norm_of_i = math.sqrt(
                                normal_i[0]**2 + normal_i[1]**2 + normal_i[2]**2)  # is it always one?
                            norm_of_j = math.sqrt(
                                normal_j[0]**2 + normal_j[1]**2 + normal_j[2]**2)
                            cosalpha = (
                                normal_i[0] * normal_j[0] + normal_i[1] * normal_j[1] + normal_i[2] * normal_j[2]) / (norm_of_i * norm_of_j)
                            # print(a, b, cosalpha)
                            if cosalpha < -0.3:  # (more than 45 degrees from being flat)
                                lines_with_angles_tag.append(line)
                                foundbigangle = True
                                break
                    if foundbigangle:
                        break
                if foundbigangle:
                    break
            if foundbigangle:
                break
    '''

    lines_with_angles_tag = [l for l in lines_with_angles_tag if l not in te_le_already_refined]
    log.info(f"Lines to be refined are {lines_with_angles_tag}")
    log.info("Now start setting refinement")

    for part in aircraft_parts:
        surfaces_tags = part.surfaces_tags
        mesh_size = mesh_size_by_part[part.part_type]
        bb = part.bounding_box
        size = [abs(bb[3] - bb[0]), abs(bb[4] - bb[1]), abs(bb[5] - bb[2])]
        size.sort()
        # Choose refinement to go on 1/4 of the length of the second smallest size (somehow usually the correct length)
        m = size[1] / 4
        for s in surfaces_tags:
            # Get all the lines that are adjacent and need refinement
            [adjacent_vols, adjacent_lines] = gmsh.model.getAdjacencies(2, s)
            lines_to_refine = list(set(adjacent_lines) & set(lines_with_angles_tag))
            for l in lines_to_refine:
                log.info(f"Refining line {l} in surface {s} in part {part.uid}")

                # 1 : Math eval field
                mesh_fields["nbfields"] += 1
                gmsh.model.mesh.field.add("Distance", mesh_fields["nbfields"])
                gmsh.model.mesh.field.setNumbers(
                    mesh_fields["nbfields"], "CurvesList", [l])
                gmsh.model.mesh.field.setNumber(
                    mesh_fields["nbfields"], "Sampling", 200)

                # 2 : Create a mesh function for the line (Matheval field)
                mesh_fields["nbfields"] += 1
                gmsh.model.mesh.field.add("MathEval", mesh_fields["nbfields"])
                gmsh.model.mesh.field.setString(
                    mesh_fields["nbfields"],
                    "F",
                    f"({mesh_size}/{refine}) + "
                    f"{mesh_size}*(1-(1/{refine}))*"
                    f"(F{mesh_fields['nbfields']-1}/{m})^{n_power}",
                )

                # 3 : Create the restrict field
                mesh_fields["nbfields"] += 1
                gmsh.model.mesh.field.add("Restrict", mesh_fields["nbfields"])
                gmsh.model.mesh.field.setNumbers(
                    mesh_fields["nbfields"], "SurfacesList", [s])
                gmsh.model.mesh.field.setNumber(
                    mesh_fields["nbfields"], "InField", mesh_fields["nbfields"] - 1)
                mesh_fields["restrict_fields"].append(mesh_fields["nbfields"])
                gmsh.model.mesh.field.setAsBackgroundMesh(mesh_fields["nbfields"])
                gmsh.model.occ.synchronize()

    return mesh_fields


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    print("Nothing to execute!")
