"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Use .brep files parts of an airplane to generate a fused airplane in GMSH with
the OCC kernel. Then Spherical farfield is created around the airplane and the
resulting domain is meshed using gmsh

TODO:
    - It may be good to move all the function and some of the code in generategmsh()
    that are related to disk actuator to another python script and import it here
    - Add mesh sizing for each aircraft part and as consequence add marker
    - Integrate other parts during fragmentation
"""

# Imports

import gmsh
import random

from ceasiompy.cpacs2gmsh.func.mesh_sizing import fuselage_size
from ceasiompy.cpacs2gmsh.func.utils import (
    initialize_gmsh,
)
from ceasiompy.cpacs2gmsh.func.wingclassification import (
    classify_wing,
    exclude_lines,
)
from ceasiompy.cpacs2gmsh.func.generategmesh import (
    wings_size,
    process_gmsh_log,
)
from ceasiompy.cpacs2gmsh.func.advancemeshing import (
    refine_wing_section,
    min_fields,
    refine_small_surfaces,
    refine_other_lines,
    refine_between_parts,
    refine_end_wing,
)
from pathlib import Path
from cpacspy.cpacspy import CPACS
from itertools import combinations
from typing import TypedDict
from ceasiompy.cpacs2gmsh.func.utils import MeshSettings, AircraftGeometry, Geometry
from ceasiompy.cpacs2gmsh.func.wingclassification import ModelPart

from ceasiompy import log
from ceasiompy.cpacs2gmsh.func.utils import MESH_COLORS


# Methods


class FuseEntry(TypedDict):
    dimtag: tuple[int, int]
    name: str


def _bbox_union(volume_tags: list[int]) -> list[float]:
    """Return a union bounding box [xmin, ymin, zmin, xmax, ymax, zmax]."""
    if not volume_tags:
        raise ValueError("Cannot compute bounding box union from an empty dimtag list.")

    bboxes = [
        gmsh.model.occ.getBoundingBox(
            dim=3,
            tag=tag,
        )
        for tag in volume_tags
    ]
    return [
        min(bb[0] for bb in bboxes),
        min(bb[1] for bb in bboxes),
        min(bb[2] for bb in bboxes),
        max(bb[3] for bb in bboxes),
        max(bb[4] for bb in bboxes),
        max(bb[5] for bb in bboxes),
    ]


def _get_symmetry_box_tag() -> int:
    """Create and return the OCC box tag used to cut for symmetry.
    Returns:
        int: The gmsh OCC volume tag of the symmetry-cut box.
    """
    log.info("Preparing: symmetry operation.")
    whole_model_bb = gmsh.model.getBoundingBox(-1, -1)
    whole_model_dimensions = [
        abs(whole_model_bb[0] - whole_model_bb[3]),
        abs(whole_model_bb[1] - whole_model_bb[4]),
        abs(whole_model_bb[2] - whole_model_bb[5]),
    ]
    domain_length = max(whole_model_dimensions)
    dx, dy, dz = 2 * domain_length, domain_length, 2 * domain_length
    x, y, z = -domain_length / 2, -domain_length, -domain_length / 2
    return gmsh.model.occ.addBox(x, y, z, dx, dy, dz)


def _bbox_dimtag_volume(dimtag: tuple[int, int]) -> float:
    """Return the axis-aligned bounding-box volume for a given OCC dimtag."""
    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.occ.getBoundingBox(*dimtag)
    return max(0.0, xmax - xmin) * max(0.0, ymax - ymin) * max(0.0, zmax - zmin)


def fusing_parts(
    aircraft_geom: AircraftGeometry,
    max_failed_attempts: int = 20,
) -> None:
    """
    Build per-part metadata and fuse part volumes in gmsh OCC.
    """

    dimtags_names: list[FuseEntry] = [
        FuseEntry(
            dimtag=(3, geom.volume_tag),
            name=geom.uid,
        )
        for geom in aircraft_geom.all_geoms
    ]

    failed_attempts = 0
    while len(dimtags_names) > 1:
        i, j = intersecting_entities_for_fusing(dimtags_names)
        left_name = str(dimtags_names[i]["name"])
        right_name = str(dimtags_names[j]["name"])
        merged_name = f"{left_name}+{right_name}"

        try:
            # Fusing 3D entities
            fused_entities, _ = gmsh.model.occ.fuse(
                [dimtags_names[i]["dimtag"]],
                [dimtags_names[j]["dimtag"]],
            )
            gmsh.model.occ.synchronize()

            for idx in sorted((i, j), reverse=True):
                dimtags_names.pop(idx)

            if not fused_entities:
                failed_attempts += 1
                log.warning(f"Fuse produced no entity for pair {merged_name}; retrying.")
                continue

            dimtags_names.append(FuseEntry(
                dimtag=fused_entities[0],
                name=merged_name,
            ))

            if len(fused_entities) > 1:
                failed_attempts += 1
                log.warning(
                    f"Fuse of {merged_name} returned {len(fused_entities)} solids; keeping all."
                )
                for k, extra_dimtag in enumerate(fused_entities[1:], start=2):
                    dimtags_names.append(FuseEntry(
                        dimtag=extra_dimtag,
                        name=f"{merged_name}#part{k}",
                    ))
        except Exception as err:
            failed_attempts += 1
            log.warning(f"Fusion failed for pair ({i}, {j}): {err}")
            random.shuffle(dimtags_names)

        if failed_attempts > max_failed_attempts:
            remaining = [str(item["name"]) for item in dimtags_names]
            log.warning(
                "Fusion stopped after repeated failures. "
                f"Remaining disconnected groups ({len(remaining)}): {remaining}"
            )
            break


def sort_surfaces_and_create_physical_groups(
    model_bb: list[float],
    symmetry: bool,
    aircraft_geom: AircraftGeometry,
) -> list[ModelPart]:
    """Compute which surfaces are in which volumes and assign the physical groups

    Get all surfaces in bounding boxes of part,
    and then take care of the ones that are classified "in multiple parts".
    """
    model_dim = _get_model_dim(model_bb)
    tx = -((model_bb[0]) + (model_dim[0] / 2))
    ty = -((model_bb[1]) + (model_dim[1] / 2))
    tz = -((model_bb[2]) + (model_dim[2] / 2))

    log.info("Starting surface classification.")

    # We are after fusing parts therefore we look at overlapping surfaces.
    for geom in aircraft_geom.all_geoms:
        geom._update_surface_tags()

    gmsh.model.occ.synchronize()

    # Now we deal with the ones that are in multiple bounding box --> Find in which they belong
    all_surfaces = gmsh.model.occ.getEntities(2)
    all_surfaces_tag = [s[1] for s in all_surfaces]

    # Reimport reference volumes from in-memory geometries for ownership disambiguation.
    for geom in aircraft_geom.all_geoms:
        ref_geom = Geometry(
            uid=f"{geom.uid}__ref",
            geom=geom.geom,
        )
        gmsh.model.occ.translate(ref_geom.shape, tx, ty, tz)
        gmsh.model.occ.synchronize()
        ref_geom._update_volume_tag()

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

    if symmetry:
        length = max(model_dim) + 1
        bb_y_plane = (-length / 2, -0.0001, -length / 2, length / 2, 0.0001, length / 2)
        surfaces_y_plane = gmsh.model.occ.getEntitiesInBoundingBox(*bb_y_plane, 2)

        part_group = gmsh.model.addPhysicalGroup(2, [t for (d, t) in surfaces_y_plane])
        gmsh.model.setPhysicalName(2, part_group, "y symmetry plane")
        gmsh.model.occ.synchronize()
    else:
        surfaces_y_plane = []

    # Now add the physical group to each part and the surfaces that are now sorted
    for model_part in aircraft_parts:
        # Just add group and name (which is the brep file without ".brep") to the surfaces
        # of the part computed before
        model_part.surfaces = list(set(model_part.surfaces) - set(surfaces_y_plane))
        model_part.surfaces_tags = [t for (d, t) in model_part.surfaces]

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

    return aircraft_parts


def _get_model_dim(model_bb: list[float]) -> list[float]:
    return [
        abs(model_bb[0] - model_bb[3]),
        abs(model_bb[1] - model_bb[4]),
        abs(model_bb[2] - model_bb[5]),
    ]


# Functions

def generate_2d_mesh(
    results_dir: Path,
    mesh_settings: MeshSettings,
    aircraft_geom: AircraftGeometry,
) -> None:
    """
    Generate a surface mesh from brep files (which makes up the aircraft).

    The airplane is fused with the different brep files : (fuselage, wings, pylon engines).

    Goal: Obtain a water-tight surface.
    """
    # Define Constants
    symmetry = mesh_settings.symmetry

    # Define variables
    all_volume_tags: list[int] = []

    #
    for geom in aircraft_geom.all_geoms:
        all_volume_tags.append(geom.volume_tag)

    model_bb = _bbox_union(all_volume_tags)
    model_dimensions = _get_model_dim(model_bb)
    gmsh.model.occ.synchronize()

    # Center everything around the center
    all_entities = gmsh.model.getEntities(-1)
    gmsh.model.occ.translate(
        all_entities,
        -((model_bb[0]) + (model_dimensions[0] / 2)),
        -((model_bb[1]) + (model_dimensions[1] / 2)),
        -((model_bb[2]) + (model_dimensions[2] / 2)),
    )
    gmsh.model.occ.synchronize()

    if symmetry:
        sym_box_tag = _get_symmetry_box_tag()

    log.info("Start fusion of the different parts")
    fusing_parts(aircraft_geom)

    if symmetry:
        log.info("Start halving the model for symmetry")
        dimtag_vols = gmsh.model.occ.getEntities(3)
        # Cut with symmetric box
        gmsh.model.occ.cut(dimtag_vols, [(3, sym_box_tag)])
        gmsh.model.occ.synchronize()

    aircraft_parts = sort_surfaces_and_create_physical_groups(
        model_bb=model_bb,
        symmetry=symmetry,
        aircraft_geom=aircraft_geom,
    )
    gmsh.model.occ.synchronize()

    # Mesh generation
    log.info("Start of gmsh 2D surface meshing process")

    # Store the computed value of mesh size to use later
    mesh_size_by_group = {}
    mesh_size_by_group["fuselage"] = fuselage_mesh_size
    mesh_size_by_group["wing"] = wing_mesh_size
    mesh_size_by_group["engine"] = mesh_size_engines
    mesh_size_by_group["rotor"] = mesh_size_propellers
    mesh_size_by_group["pylon"] = mesh_size_propellers

    # mesh_size_fuselage = mesh_size_by_group["fuselage"]
    # log.info(f"Mesh size fuselage={mesh_size_fuselage:.3f} m")
    log.info(f"Mesh size fuselage={fuselage_mesh_size:.3f} m")
    log.info(f"Mesh size wing={wing_mesh_size:.3f} m")
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
        if symmetry:
            # Don't want to refine lines that have angles because they are created by
            # the y-plane cutting the airplane shape. So we take them out
            # We already computed the surfaces on the y-plane and created phys group
            dimtags_surfs_y0 = gmsh.model.getEntitiesForPhysicalName("y symmetry plane")
            lines_y0_sym = gmsh.model.getBoundary(dimtags_surfs_y0,
                                                  combined=False, oriented=False)
            te_le_already_refined.extend([t for (d, t) in lines_y0_sym])

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

    if symmetry:
        all_volumes = gmsh.model.getEntities(3)
        gmsh.model.occ.remove(all_volumes)
        gmsh.model.occ.remove(dimtags_surfs_y0)
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
        # h_max_model = max(wing_maxlen, fuselage_maxlen)
        # mesh_size_farfield = h_max_model * farfield_size_factor

        # Refine surfaces that are small and with really few triangles, to get more
        # precision in their shapes
        for part in aircraft_parts:
            refined_surfaces, mesh_fields = refine_small_surfaces(
                mesh_fields,
                part,
                farfield_mesh_size,
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
    surface_mesh_path = Path(results_dir, "surface_mesh.stl")
    log.info(f"{surface_mesh_path=}.")
    gmsh.write(str(surface_mesh_path))

    # # -----------------------------
    # # Load mesh
    # # -----------------------------
    # input_stl = Path(results_dir, "surface_mesh.stl")
    # output_stl = Path(results_dir, "surface_mesh_try.stl")

    # mesh = trimesh.load_mesh(input_stl)

    # log.info("=== MESH INFO ===")
    # log.info(f"Vertices: {len(mesh.vertices)}")
    # log.info(f"Faces:    {len(mesh.faces)}")

    # # -----------------------------
    # # Watertight check
    # # -----------------------------

    # is_watertight = mesh.is_watertight
    # log.info(f"Watertight: {is_watertight}")

    # if is_watertight:
    #     log.info("✔ Mesh is already watertight. Saving copy.")
    #     mesh.export(input_stl)
    #     return input_stl, fuselage_maxlen
    # else:
    #     # -----------------------------
    #     # Repair with PyMeshFix
    #     # -----------------------------
    #     log.warning("⚠ Mesh is NOT watertight → repairing...")

    #     vertices = np.array(mesh.vertices)
    #     faces = np.array(mesh.faces)

    #     meshfix = pymeshfix.MeshFix(vertices, faces)

    #     meshfix.repair(
    #         verbose=True,
    #         joincomp=True,     # join disconnected components
    #         remove_smallest_components=False
    #     )

    #     # -----------------------------
    #     # Create repaired mesh
    #     # -----------------------------
    #     repaired_mesh = trimesh.Trimesh(
    #         vertices=meshfix.v,
    #         faces=meshfix.f,
    #         process=True
    #     )

    #     # -----------------------------
    #     # Post-repair checks
    #     # -----------------------------
    #     log.info("\n=== POST-REPAIR INFO ===")
    #     log.info(f"Vertices: {len(repaired_mesh.vertices)}")
    #     log.info(f"Faces:    {len(repaired_mesh.faces)}")
    #     log.info(f"Watertight: {repaired_mesh.is_watertight}")
    #     log.info(f"Euler number: {repaired_mesh.euler_number}")

    #     # -----------------------------
    #     # Save result
    #     # -----------------------------
    #     repaired_mesh.export(output_stl)
    #     log.info(f"{output_stl=}")
    #     gmsh.write(str(output_stl))
    #     log.info(f"{fuselage_maxlen=}")

    gmsh.clear()
    gmsh.finalize()

    return surface_mesh_path


def intersecting_entities_for_fusing(
    dimtags_names: list[FuseEntry],
) -> tuple[int, int]:
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
                        f"Found the end of wing in {model_part.uid}, refining lines {line1,line2}")
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
