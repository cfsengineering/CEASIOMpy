"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Use .brep files parts of an airplane to generate a fused airplane in GMSH with
the OCC kernel. Then Spherical farfield is created around the airplane and the
resulting domain is meshed using gmsh

| Author: Guido Vallifuoco
| Creation: 2024-02-01
| Modified: Leon Deligny
| Date: 2025-Feb-28
| Modified: Cassandre Renaud
| Date: 2025-May-8

TODO:

    - It may be good to move all the function and some of the code in generategmsh()
    that are related to disk actuator to another python script and import it here

    - Add mesh sizing for each aircraft part and as consequence add marker

    - Integrate other parts during fragmentation

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import random
from itertools import combinations

import gmsh
from ceasiompy.CPACS2GMSH.func.wingclassification import (
    ModelPart,
    classify_wing,
    exclude_lines,
)
from ceasiompy.CPACS2GMSH.func.generategmesh import (
    wings_size,
    fuselage_size,
    process_gmsh_log,
)
from ceasiompy import log
from ceasiompy.CPACS2GMSH.func.advancemeshing import (
    refine_wing_section,
    min_fields,
    refine_small_surfaces,
    refine_other_lines,
    refine_between_parts,
    refine_end_wing,
)
from ceasiompy.utils.ceasiompyutils import (
    get_reasonable_nb_cpu,
    get_part_type,
    run_software,
)
from ceasiompy.CPACS2GMSH.func.utils import check_path, MESH_COLORS
from pathlib import Path
from typing import Dict
from cpacspy.cpacspy import CPACS


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def generate_2d_mesh_for_pentagrow(
    cpacs: CPACS,
    brep_dir: Path,
    results_dir: Path,
    open_gmsh: bool,
    refine_factor: float = 2.0,
    refine_truncated: bool = False,
    refine_factor_angled_lines: float = 2.0,
    auto_refine: bool = False,
    n_power_factor: float = 2,
    fuselage_mesh_size_factor: float = 1,
    wing_mesh_size_factor: float = 0.5,
    mesh_size_engines: float = 0.23,
    mesh_size_propellers: float = 0.23,
    farfield_size_factor: float = 10,
):
    """
    Function to generate a surface mesh from brep files forming an airplane

    The airplane is fused with the different brep files : fuselage, wings and
    other parts are identified and fused together in order to obtain a watertight volume.
    Physical groups are also created, and some refining function are called.
    Args:
    ----------
    cpacs : CPACS
        CPACS object
    cpacs_path : Path
        Path to the directory containing CPACS object
    brep_dir : Path
        Path to the directory containing the brep files
    results_dir : Path
        Path to the directory containing the result (mesh) files
    open_gmsh : bool
        Open gmsh GUI after the mesh generation if set to true
    refine_factor : float
        Factor of refinement along le and te of wings
    refine_truncated : bool
        If set to true, the refinement can change to match the truncated
        te thickness
    refine_factor_angled_lines :float
        Factor of refinement along the edges that are sharp but not le and te
    n_power_factor : float
        Power of how much refinement on the le and te (and for now in the
        "refine acute angle" as well)
    fuselage_mesh_size_factor : float
        Factor of the fuselage mesh size : the mesh size will be the mean
        fuselage width divided by this factor
    wing_mesh_size_factor : float
        Factor of the wing mesh size : the mesh size will be the mean
        fuselage width divided by this factor
    mesh_size_engines : float
        Size of the engines mesh
    mesh_size_propellers : float
        Size of the propellers mesh
    ...
    Returns:
    ----------
    mesh_file : Path
        Path to the mesh file generated by gmsh
    """

    # Need a fix and function add_disk_actuator to make this part work
    # Determine if rotor are present in the aircraft model
    # rotor_model = False
    # if Path(brep_dir, "config_rotors.cfg").exists():
    #    rotor_model = True
    # if rotor_model:
    #    log.info("Adding disk actuator")
    #    config_file = ConfigFile(Path(brep_dir, "config_rotors.cfg"))
    #    add_disk_actuator(brep_dir, config_file)

    # Retrieve all brep
    brep_files = list(brep_dir.glob("*.brep"))
    brep_files.sort()

    # Initialize gmsh
    gmsh.initialize()
    # Stop gmsh output log in the terminal
    gmsh.option.setNumber("General.Terminal", 0)
    # Log complexity
    gmsh.option.setNumber("General.Verbosity", 5)

    log.info(f"Importing files from {brep_dir}")

    # Import shapes and get the tags and name
    fuselage_volume_dimtags = []
    aircraft_parts = []
    for brep_file in brep_files:
        # Import the part and create the aircraft part object
        part_entities = gmsh.model.occ.importShapes(str(brep_file), highestDimOnly=False)
        gmsh.model.occ.synchronize()

        # Create the aircraft part object
        part_obj = ModelPart(uid=brep_file.stem)
        part_obj.part_type = get_part_type(cpacs.tixi, part_obj.uid)
        part_obj.volume = part_entities[0]
        part_obj.volume_tag = part_entities[0][1]

        # Want to get fuselage length to size our model
        if part_obj.part_type == "fuselage":
            fuselage_volume_dimtags.append(part_entities[0])
        aircraft_parts.append(part_obj)

    if len(fuselage_volume_dimtags) < 1:
        # Don't know in which case it should happen but is here if needed
        model_bb = gmsh.model.get_bounding_box(-1, -1)
        log.info("Warning : no fuselage in this aircraft")
    elif len(fuselage_volume_dimtags) == 1:
        # Normal case of 1 fuselage
        model_bb = gmsh.model.get_bounding_box(
            fuselage_volume_dimtags[0][0], fuselage_volume_dimtags[0][1]
        )
    else:
        # If multiple fuselage, we assume the longest (so x-direction) is the "main" one
        model_bb = [0, 0, 0, 0, 0, 0]
        for fuse in fuselage_volume_dimtags:
            new_bb = gmsh.model.get_bounding_box(*fuse)
            if new_bb[3] - new_bb[0] > model_bb[3] - model_bb[0]:
                model_bb = new_bb

    # Compute dimensions of fuselage
    model_dimensions = [
        abs(model_bb[0] - model_bb[3]),
        abs(model_bb[1] - model_bb[4]),
        abs(model_bb[2] - model_bb[5]),
    ]
    gmsh.model.occ.synchronize()

    # Center everything around the center of the fuselage
    all_volumes = gmsh.model.getEntities(-1)
    gmsh.model.occ.translate(
        all_volumes,
        -((model_bb[0]) + (model_dimensions[0] / 2)),
        -((model_bb[1]) + (model_dimensions[1] / 2)),
        -((model_bb[2]) + (model_dimensions[2] / 2)),
    )
    gmsh.model.occ.synchronize()

    log.info("Start manipulation to obtain a watertight volume")
    # we have to obtain a watertight volume, needed for tetgen (otherwise just can't start)

    log.info("Start fusion of the different parts")
    # We then call the function to fuse the parts and create the named physical groups
    fusing_parts(aircraft_parts)
    sort_surfaces_and_create_physical_groups(
        aircraft_parts, brep_files, cpacs, model_bb, model_dimensions
    )
    gmsh.model.occ.synchronize()
    log.info("Manipulation finished")

    # Mesh generation
    log.info("Start of gmsh 2D surface meshing process")

    # Compute fuselage and wing size for meshing
    fuselage_maxlen, fuselage_minlen = fuselage_size(cpacs.tixi)
    wing_maxlen, wing_minlen = wings_size(cpacs.tixi)

    # Store the computed value of mesh size to use later
    mesh_size_by_group = {}
    mesh_size_by_group["fuselage"] = (
        (fuselage_maxlen + fuselage_minlen) / 2
    ) / fuselage_mesh_size_factor
    mesh_size_by_group["wing"] = ((wing_maxlen * 0.8 + wing_minlen) / 2) / wing_mesh_size_factor
    mesh_size_by_group["engine"] = mesh_size_engines
    mesh_size_by_group["rotor"] = mesh_size_propellers
    mesh_size_by_group["pylon"] = mesh_size_propellers

    mesh_size_fuselage = mesh_size_by_group["fuselage"]
    log.info(f"Mesh size fuselage={mesh_size_fuselage:.3f} m")
    log.info(
        f"Mesh size wing={((wing_maxlen * 0.8 + wing_minlen) / 2) / wing_mesh_size_factor:.3f} m"
    )
    log.info(f"Mesh size engine={mesh_size_engines:.3f} m")
    log.info(f"Mesh size rotor={mesh_size_propellers:.3f} m")

    # To keep count of the fields defined, and which are needed when we take the min
    # to construct the final mesh
    mesh_fields = {"nbfields": 0, "restrict_fields": []}

    # Now fix the mesh size for every part
    for model_part in aircraft_parts:
        # Take the right mesh size (name physical group should be wing or fuselage
        # or engine or propeller or rotor or pylon)
        lc = mesh_size_by_group[model_part.part_type]
        model_part.mesh_size = lc

        # To give the size to gmsh, we create a field with constant value containing only our
        # list of surfaces, and give it the size
        mesh_fields["nbfields"] += 1
        gmsh.model.mesh.field.add("Constant", mesh_fields["nbfields"])
        gmsh.model.mesh.field.setNumbers(
            mesh_fields["nbfields"], "SurfacesList", model_part.surfaces_tags
        )
        gmsh.model.mesh.field.setNumber(mesh_fields["nbfields"], "VIn", lc)
        gmsh.model.mesh.field.setAsBackgroundMesh(mesh_fields["nbfields"])
        # Need to be stocked for when we take the min field:
        mesh_fields["restrict_fields"].append(mesh_fields["nbfields"])
    mesh_fields = min_fields(mesh_fields)
    gmsh.model.occ.synchronize()

    # Refine the parts when two parts intersects with different mesh size
    # (i.e. a "smooth transition" on the one with the bigger mesh size)
    log.info("Refine to get smooth transition between parts with different mesh sizes")
    mesh_fields = refine_between_parts(aircraft_parts, mesh_fields)
    mesh_fields = min_fields(mesh_fields)
    log.info("End of refinement between parts")

    # Now do the refinement on the le and te and end of wing
    if refine_factor != 1:
        log.info("Start refinement of leading and trailing edge and side of wing")
        # We want the lines already refined so we don't refined them again in the second function
        mesh_fields, te_le_already_refined = refine_le_te_end(
            aircraft_parts,
            mesh_size_by_group["wing"],
            mesh_fields,
            refine_factor,
            refine_truncated=refine_truncated,
            n_power_factor=n_power_factor,
        )
        log.info("Finished refinement of leading and trailing edge and side of wing")
    else:
        te_le_already_refined = []

    # Now a function to refine all the ones that are in "non flat" places
    if refine_factor_angled_lines != 1:
        log.info("Refinement process of lines in non flat places has started")
        mesh_fields = refine_other_lines(
            te_le_already_refined,
            refine=refine_factor_angled_lines,
            aircraft_parts=aircraft_parts,
            mesh_fields=mesh_fields,
            mesh_size_by_part=mesh_size_by_group,
            n_power=n_power_factor,
        )
        mesh_fields = min_fields(mesh_fields)
        log.info("Refining process finished")
    gmsh.model.occ.synchronize()

    # Parameters for the meshing
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.LcIntegrationPrecision", 1e-6)
    gmsh.option.setNumber("Mesh.StlOneSolidPerSurface", 2)

    # Generate the mesh
    gmsh.logger.start()
    gmsh.model.mesh.generate(1)
    gmsh.model.mesh.generate(2)

    process_gmsh_log(gmsh.logger.get())
    gmsh.model.occ.synchronize()

    # Control of the mesh quality
    if refine_factor != 1 and auto_refine:
        log.info("Auto-refine process started")
        bad_surfaces = []
        final_domain_volume_tag = gmsh.model.occ.getEntities(3)[0][1]

        # Set mesh size and color of the farfield
        h_max_model = max(wing_maxlen, fuselage_maxlen)
        mesh_size_farfield = h_max_model * farfield_size_factor

        # Refine surfaces that are small and with really few triangles, to get more
        # precision in their shapes
        for part in aircraft_parts:
            refined_surfaces, mesh_fields = refine_small_surfaces(
                mesh_fields,
                part,
                mesh_size_farfield,
                max(model_dimensions),
                [final_domain_volume_tag],
                nb_min_triangle=75,
            )
            bad_surfaces.extend(refined_surfaces)

        if bad_surfaces:
            log.info(f"{len(bad_surfaces)} surface(s) need to be refined")

            # Reset the background mesh
            mesh_fields = min_fields(mesh_fields)

            if open_gmsh:
                log.info("Insufficient mesh size surfaces are displayed in red")
                log.info("GMSH GUI is open, close it to continue...")
                gmsh.fltk.run()

            log.info("Start of gmsh 2D surface remeshing process")

            gmsh.model.mesh.generate(1)
            gmsh.model.mesh.generate(2)

            for surface in bad_surfaces:
                gmsh.model.setColor([(2, surface)], *MESH_COLORS["good_surface"], recursive=False)

            log.info("Remeshing process finished")
            if open_gmsh:
                log.info("Corrected mesh surfaces are displayed in green")

    # Apply smoothing
    log.info("2D mesh smoothing process started")
    gmsh.model.mesh.optimize("Laplace2D", niter=10)
    log.info("Smoothing process finished")

    gmsh.model.occ.synchronize()

    log.info("Finished meshing surface")
    if open_gmsh:
        log.info("Result of 2D surface mesh")
        log.info("GMSH GUI is open, close it to continue...")
        gmsh.fltk.run()

    gmesh_path = Path(results_dir, "surface_mesh.stl")
    gmsh.write(str(gmesh_path))
    return gmesh_path, fuselage_maxlen


def intersecting_entities_for_fusing(dimtags_names):
    """
    Function to find two entities (volumes) in the list that have a non-zero intersection.
    If volumes are not next to each other, they do not fuse and so, create problems
    Args:
    ----------
    dimtags_names : list of dict
        List of the dimtag and names of all the volumes we want to search in
    ...
    Returns:
    ----------
    (i,j) : tuple (int,int)
        indices in the list of the two volumes we want to fuse (by default return 0,1)
    """
    # For every surfaces i and j, check if they intersect. If yes, return i,j
    for i in range(len(dimtags_names) - 1):
        entities1 = [dimtags_names[i]["dimtag"]]
        for j in range(i + 1, len(dimtags_names)):
            entities2 = [dimtags_names[j]["dimtag"]]
            intersect = gmsh.model.occ.intersect(
                entities1, entities2, removeObject=False, removeTool=False
            )[0]
            gmsh.model.occ.synchronize()
            # What's missing is that he sadly doesn't recognize the intersection by a face (only
            # volume) (but rarely a problem)

            # Check if there is an intersection (i.e. there will be a dimtag in intersect)
            if len(intersect):
                # Remove the intersection so it doesn't cause problems for meshing and others
                gmsh.model.occ.remove(intersect, recursive=True)
                gmsh.model.occ.synchronize()
                return (i, j)
    # There if doesn't find intersection (usually bug bc intersection of surfaces, and unlikely)
    return (0, 1)


def fusing_parts(aircraft_parts):
    """
    Function to fuse all of the different aircraft parts to get a single volume.
    To work, we need to fuse volume by two, and volumes that intersect. That's why we first take
    two volumes that intersect, fuse them and do that until we're left with only one volume.

    There are sometimes some problems (ex : with propellers), and sometimes the intersection
    doesn't work (like if only intersect by a surface),
    so we try again after shuffling the list. There is a stop after 20 failed attemps.
    Args:
    ----------
    aircraft_parts : list of ModelPart
        List of all the parts in the airplane
    ...
    Returns:
    ----------
    nothing
    """

    # First we take the bounding boxes of each part
    for model_part in aircraft_parts:
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.occ.getBoundingBox(*model_part.volume)
        # Added a small margin, bc sometimes causes problem when retrieving surfaces
        # "at the limit"
        model_part.bounding_box = [
            xmin - 0.01,
            ymin - 0.01,
            zmin - 0.01,
            xmax + 0.01,
            ymax + 0.01,
            zmax + 0.01,
        ]
    # Take all the dimtag of the parts volume (vector that we will empty)
    dimtags_names = [
        {"dimtag": model_part.volume, "name": model_part.uid} for model_part in aircraft_parts
    ]

    # Secondly we take care of the fusion to create the airfoil

    # Keep count of how many times it didn't work (if error or some seperate part,
    # it could loop forever)
    counter = 0
    while len(dimtags_names) > 1:
        # Choose two entities to fuse
        i, j = intersecting_entities_for_fusing(dimtags_names)
        try:
            # Fuse them
            fused_entities, _ = gmsh.model.occ.fuse(
                [dimtags_names[i]["dimtag"]], [dimtags_names[j]["dimtag"]]
            )
            gmsh.model.occ.synchronize()
            # Look for problems
            if len(fused_entities) > 1:
                # in this case, either the pieces are not connected
                # or the order was wrong and we took a non connected piece
                counter += 1
                log.info(
                    "Warning : the fusion did not give only one piece (will still try to see\
                        if it's a question of order)"
                )
                dimtags_names = (
                    [
                        {
                            "dimtag": fused_entities[0],
                            "name": " errorwhen"
                            + dimtags_names[i]["name"]
                            + "+"
                            + dimtags_names[j]["name"],
                        }
                    ]
                    + [{dimtags_names[k]} for k in range(len(dimtags_names)) if k != j and k != i]
                    + [
                        {
                            "dimtag": fused_entities[k],
                            "name": "errorwhen "
                            + dimtags_names[i]["name"]
                            + dimtags_names[j]["name"],
                        }
                        for k in range(1, len(fused_entities))
                    ]
                )
            elif len(fused_entities) == 0:
                counter += 1
                namei, namej = dimtags_names[i]["name"], dimtags_names[j]["name"]
                log.info(f"Warning : error, no fused entity (fused {namei} and {namej})")
                # put them in the end to try again
                dimtags_names = [
                    {dimtags_names[k]} for k in range(len(dimtags_names)) if k != j and k != i
                ] + [dimtags_names[i], dimtags_names[j]]
            else:
                # Update the vectors of remaining entities
                dimtags_names = [
                    {
                        "dimtag": fused_entities[0],
                        "name": dimtags_names[i]["name"] + "+" + dimtags_names[j]["name"],
                    }
                ] + [dimtags_names[k] for k in range(len(dimtags_names)) if k != j and k != i]

        # Handle the cases where it didn't work
        except Exception as e:
            log.info(f"Fusion failed for entities {0} and {j}: {e}")
            counter += 1
            random.shuffle(dimtags_names)
        if counter > 20:
            # If here we have multiples times had problems with fusion and won't give one piece
            names = [dimtags_names[k]["name"] for k in len(dimtags_names)]
            log.info(f"Warning : the end result is not in one piece. Parts by group : {names}")
            break


def sort_surfaces_and_create_physical_groups(
    aircraft_parts, brep_files, cpacs, model_bb, model_dimensions
):
    """
    Function to  compute which surfaces are in which volumes and assign the physical groups

    Get all surfaces in bounding boxes of part, and then take care of the ones that are classified
    "in multiple parts"
    Args:
    ----------
    aircraft_parts : list of ModelPart
        List of all the parts in the airplane
    brep_files : Path
        Path of where are stocked the brep files for the airplane
    cpacs : CPACS
        CPACS object
    model_bb : list
        Contains [xmin,ymin,zmin,xmax,ymax,zmax] of bounding box of fuselage
    model_dimensions : list
        Contains [width (x-axis), length (y-axis), height (z-axis)] of fuselage
    ...
    Returns:
    ----------
    nothing
    """
    # Now we sort the surfaces by part (to name them & set mesh size)

    # Get all the surfaces, classified by part with bounding boxes (might take too many,
    # will be dealt with after)

    log.info("Start the classification of surfaces by parts")
    for model_part in aircraft_parts:
        surfaces_dimtags = gmsh.model.getEntitiesInBoundingBox(*model_part.bounding_box, 2)
        surface_tags = [tag for dim, tag in surfaces_dimtags]
        model_part.surfaces = surfaces_dimtags
        model_part.surfaces_tags = surface_tags
    gmsh.model.occ.synchronize()

    # Now we deal with the ones that are in multiple bounding box --> Find in which they belong
    all_surfaces = gmsh.model.occ.getEntities(2)
    all_surfaces_tag = [s[1] for s in all_surfaces]

    # First reimport all the shapes, get their new tags and names
    new_aircraft_parts = []
    for brep_file in brep_files:
        # Import the part and create the aircraft part object (and translate them as the
        # original were translated)
        part_entities = gmsh.model.occ.importShapes(str(brep_file), highestDimOnly=False)
        gmsh.model.occ.translate(
            [part_entities[0]],
            -((model_bb[0]) + (model_dimensions[0] / 2)),
            -((model_bb[1]) + (model_dimensions[1] / 2)),
            -((model_bb[2]) + (model_dimensions[2] / 2)),
        )
        gmsh.model.occ.synchronize()

        part_obj = ModelPart(uid=brep_file.stem)
        part_obj.part_type = get_part_type(cpacs.tixi, part_obj.uid, print_info=False)
        part_obj.volume = part_entities[0]
        part_obj.volume_tag = part_entities[0][1]

        new_aircraft_parts.append(part_obj)

    # Reorder the imported shape so that it is in same order than our previous ones
    # (i.e. vectors surfaces by part and newpart name tag type have save brep name at same index)
    for i, old_part in enumerate(aircraft_parts):
        for j, new_part in enumerate(new_aircraft_parts):
            if old_part.uid == new_part.uid:
                new_aircraft_parts[i], new_aircraft_parts[j] = \
                    new_aircraft_parts[j], new_aircraft_parts[i]
                break

    # Now for each surface count in how many different part it is
    for surf in all_surfaces_tag:
        # Count all the parts surf is in
        parts_in = []
        for i, model_part in enumerate(aircraft_parts):
            for surff in model_part.surfaces_tags:
                if surff == surf:
                    parts_in.append(i)

        # Now deal with it if in more than one part
        if len(parts_in) > 1:
            aircraft_parts = choose_correct_part(
                parts_in, surf, aircraft_parts, new_aircraft_parts
            )

    # Remove the parts we re-imported, to get a clean result (we won't need them anymore)
    gmsh.model.occ.remove([model_part.volume for model_part in new_aircraft_parts], recursive=True)
    gmsh.model.occ.synchronize()

    # Now add the physical group to each part and the surfaces that are now sorted
    for model_part in aircraft_parts:
        # Just add group and name (which is the brep file without ".brep") to the surfaces
        # of the part computed before
        part_group = gmsh.model.addPhysicalGroup(2, model_part.surfaces_tags)
        name_group = model_part.uid
        gmsh.model.setPhysicalName(2, part_group, name_group)

        # Compute the linesand points in each part by taking the boundary of surfaces
        # (need them later for wing refinement)
        model_part.lines = gmsh.model.getBoundary(
            model_part.surfaces, combined=False, oriented=False
        )
        model_part.lines_tags = [li[1] for li in model_part.lines]
        model_part.points = gmsh.model.getBoundary(
            model_part.lines, combined=False, oriented=False
        )
        model_part.points_tags = [po[1] for po in model_part.points]


def choose_correct_part(parts_in, surf, aircraft_parts, new_aircraft_parts):
    """
    Function to chose the correct part for a surface still in multiple bounding boxes

    Args:
    ----------
    parts_in : list of int
        List of the parts such that the surface is in the bounding box
    surf : int
        tag of the surface
    aircraft_parts : list of ModelPart
        List of all the parts in the airplane
    new_aircraft_parts : list of ModelPart
        List of all the parts in the airplane but the reimported new ones.
        The numerotation is the same as in aircraft_parts
    ...
    Returns:
    ----------
    aircraft_parts : list of ModelPart
        Return the aircraft parts with updated list of surfaces
    """
    for i in parts_in:
        # This is maybe overcomplicated, but gmsh doesn't keep the tags of surfaces when
        # fused so we have to find a way to rematch them to their original part
        # Compute intersection (which is a surface) of surface with the original
        # shape/part. If there is an intersection, it means that it is the shape
        # that the surface was on.
        # (Precision : gmsh doesn't compute curves (or in general entity of smaller dim)
        # at intersection for some reason, which is why it works.
        # We only get intersection if the surface is really along/inside the volume,
        # which only happens if it is the volume it comes from.)
        intersection = gmsh.model.occ.intersect(
            [(2, surf)],
            [new_aircraft_parts[i].volume],
            removeObject=False,
            removeTool=False,
        )[0]
        # Remove intersection to have a clean result
        gmsh.model.occ.remove(intersection, recursive=True)

        if len(intersection) > 0:
            # If found, remove the tag from the others parts, and we have finished
            # for this surface
            p = aircraft_parts[i].uid
            log.info(f"Surface {surf} was in multiple volumes and is classified into part {p}")
            for j in parts_in:
                if j != i:
                    aircraft_parts[j].surfaces.remove((2, surf))
                    aircraft_parts[j].surfaces_tags.remove(surf)
            break
        elif i == parts_in[-1]:
            # If we are here, we have found no part st the part is in, so there
            # is a problem. We choose a part and hope for the best
            log.info(
                f"Surface {surf} still in parts\
                    {[aircraft_parts[i].uid for i in parts_in]}, take off randomly"
            )
            for k in range(len(parts_in) - 1):
                aircraft_parts[parts_in[k]].surfaces.remove((2, surf))
                aircraft_parts[parts_in[k]].surfaces_tags.remove(surf)

    return aircraft_parts


def refine_le_te_end(
    aircraft_parts,
    mesh_size_wing,
    mesh_fields,
    refine_factor,
    refine_truncated,
    n_power_factor,
):
    """
    Function to refine the border of the wings (le, te, and tip of the wing).

    First find the le and te lines, then refine them, then compute the tip lines, and refine them
    Args:
    ----------
    aircraft_parts : list of ModelPart
        List of all the parts in the airplane
    mesh_size_wing : float
        size of the wing mesh
    mesh_fields : dictionary
        Contains the updated number of biggest used field and the tag of the fields already used
        and needed for the final min field (under name "nbfields" and "restrict_fields")
    refine_factor : float
        factor of the refinement for le and te
    refine_truncated : bool
        If set to true, the refinement can change to match the truncated te thickness
    n_power_factor : float
        Power of how much refinement on the le and te
    ...
    Returns:
    ----------
    mesh_fields : dictionnary
        Contains the updated number of biggest used field and the tag of the fields already used
        and needed for the final min field (under name "nbfields" and "restrict_fields")
    """
    aircraft = ModelPart("aircraft")
    lines_already_refined_lete = []
    # tag of the main volume constituing the aicraft, and of all the surfaces
    aircraft.volume_tag = gmsh.model.occ.getEntities(3)[0][1]
    # (there should be only one volume in the model)
    aircraft.surfaces_tags = [tag for (dim, tag) in gmsh.model.occ.getEntities(2)]
    aircraft.lines_tags = [tag for (dim, tag) in gmsh.model.occ.getEntities(1)]

    # For all the wing, we call the function classify that will detect the le and te between all
    # the lines and compute the mean chord length
    for model_part in aircraft_parts:
        if model_part.part_type == "wing":
            classify_wing(model_part, aircraft_parts)
            log.info(
                f"Classification of {model_part.uid} done"
                f" {len(model_part.wing_sections)} section(s) found "
            )
            new_lines = [x["lines_tags"] for x in model_part.wing_sections]
            for new_line in new_lines:
                # Stock all of the already refined lines to not do it twice with the other fct
                lines_already_refined_lete.extend(new_line)

    for model_part in aircraft_parts:
        if model_part.part_type == "wing":
            # Refine will set fields to have smaller mesh size along te and le
            refine_wing_section(
                mesh_fields,
                [aircraft.volume_tag],
                aircraft,
                model_part,
                mesh_size_wing,
                refine=refine_factor,
                refine_truncated=refine_truncated,
                n_power=n_power_factor,
            )

    # Refine also the end of the wing
    for model_part in aircraft_parts:
        if model_part.part_type == "wing":
            # Want the same w_chord as the tip of the wing, which is the smallest one
            x_chord = 1000000
            for wing_section in model_part.wing_sections:
                chord_mean = wing_section["mean_chord"]
                x_chord = min(x_chord, chord_mean * 0.25)

            # Now need to find the tip of the wing. We know it is not a line that touch
            # another part, or one found in le and te, so take thouse out
            lines_in_other_parts = exclude_lines(model_part, aircraft_parts)
            lines_to_take_out = set(lines_already_refined_lete).union(set(lines_in_other_parts))
            lines_left = sorted(list(set(model_part.lines_tags) - lines_to_take_out))
            surfaces_in_wing = model_part.surfaces_tags
            for (line1, line2) in list(combinations(lines_left, 2)):
                # We know the two lines at the end of the wing share 2 points and 1 surface
                # And no other lines in wing share this structure
                surfaces1, points1 = gmsh.model.getAdjacencies(1, line1)
                surfaces2, points2 = gmsh.model.getAdjacencies(1, line2)
                common_points = list(set(points1) & set(points2))
                common_surfaces = list(set(surfaces1) & set(
                    surfaces2) & set(surfaces_in_wing))
                if len(common_points) == 2 and len(common_surfaces) == 1:
                    log.info(
                        f"Found the end of wing in {model_part.uid}, "
                        f"refining lines {line1, line2}"
                    )
                    refine_end_wing(
                        [line1, line2],
                        aircraft,
                        x_chord,
                        model_part.surfaces_tags,
                        refine_factor,
                        mesh_size_wing,
                        n_power_factor,
                        [aircraft.volume_tag],
                        mesh_fields,
                    )
                    gmsh.model.setColor([(1, line1), (1, line2)], 0, 180, 180)  # to see
                    lines_already_refined_lete.extend([line1, line2])

            for line1, line2, line3 in list(combinations(lines_left, 3)):
                surfaces1, points1 = gmsh.model.getAdjacencies(1, line1)
                surfaces2, points2 = gmsh.model.getAdjacencies(1, line2)
                surfaces3, points3 = gmsh.model.getAdjacencies(1, line3)
                common_points12 = list(set(points1) & set(points2))
                common_points13 = list(set(points1) & set(points3))
                common_points23 = list(set(points3) & set(points2))
                common_surfaces = list(
                    set(surfaces1) & set(surfaces2) & set(surfaces3) & set(surfaces_in_wing)
                )
                if (
                    len(common_points12) == 1
                    and len(common_points13) == 1
                    and len(common_points23) == 1
                    and len(common_surfaces) == 1
                ):
                    mod = model_part.uid
                    log.info(
                        f"Found the end of wing in {mod}, refining lines {line1, line2, line3}"
                    )
                    refine_end_wing(
                        [line1, line2, line3],
                        aircraft,
                        x_chord,
                        model_part.surfaces_tags,
                        refine_factor,
                        mesh_size_wing,
                        n_power_factor,
                        [aircraft.volume_tag],
                        mesh_fields,
                    )
                    gmsh.model.setColor(
                        [(1, line1), (1, line2), (1, line3)], 0, 180, 180
                    )  # to see
                    lines_already_refined_lete.extend([line1, line2, line3])

    # Generate the minimal background mesh field
    mesh_fields = min_fields(mesh_fields)
    return mesh_fields, lines_already_refined_lete


def pentagrow_3d_mesh(
    result_dir: str,
    cfg_params: Dict,
    surf: str = None,
    angle: str = None,
) -> Path:
    """
    Runs pentagrow.

    Args:
        result_dir (str): Results directory.
        cfg_params (Dict): Configuration parameters for ConfigFile.

    """

    # Create the config file for pentagrow
    config_penta_path = Path(result_dir, "config.cfg")

    # Add cfg_params in config file
    with open(config_penta_path, "w") as file:
        for key, value in cfg_params.items():
            file.write(f"{key} = {value}\n")

    check_path("surface_mesh.stl")
    check_path("config.cfg")

    command = ["surface_mesh.stl", "config.cfg"]

    # Specify the file path
    file_path = "command.txt"

    with open(file_path, "w") as file:
        file.write(" ".join(command))

    # Running command = "pentagrow surface_mesh.stl config.cfg"
    run_software(
        software_name="pentagrow",
        arguments=command,
        wkdir=result_dir,
        with_mpi=False,
        nb_cpu=get_reasonable_nb_cpu(),
    )

    return Path(result_dir, "hybrid.su2")
