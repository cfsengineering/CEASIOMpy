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

from ceasiompy.cpacs2gmsh.func.wingclassification import (
    classify_wing,
    exclude_lines,
)
from ceasiompy.cpacs2gmsh.func.generategmesh import (
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
from pydantic import BaseModel, Field
from ceasiompy.cpacs2gmsh.func.utils import (
    PartType,
    BoundingBox,
    MeshSettings,
    AircraftGeometry,
)

from ceasiompy import log
from ceasiompy.cpacs2gmsh.func.utils import MESH_COLORS


# Methods


class FuseEntry(BaseModel):
    name: str
    dimtag: tuple[int, int]
    part_type: PartType


class SurfacePart(BaseModel):
    uid: str
    part_type: PartType
    volume: tuple[int, int]
    surfaces: list[tuple[int, int]] = Field(default_factory=list)
    surfaces_tags: list[int] = Field(default_factory=list)
    lines: list[tuple[int, int]] = Field(default_factory=list)
    lines_tags: list[int] = Field(default_factory=list)
    points: list[tuple[int, int]] = Field(default_factory=list)
    points_tags: list[int] = Field(default_factory=list)
    wing_sections: list[dict] = Field(default_factory=list)
    mesh_size: float = 0.0


PART_TYPE_PRIORITY: tuple[PartType, ...] = (
    PartType.fuselage,
    PartType.wing,
    PartType.pylon,
)


def _resolve_merged_part_type(
    left_type: PartType,
    right_type: PartType,
) -> PartType:
    """Resolve merged part type using fixed precedence."""
    for candidate in PART_TYPE_PRIORITY:
        if left_type == candidate or right_type == candidate:
            return candidate

    raise ValueError(f"Unsupported part type merge: {left_type=} {right_type=}")



def _bounding_box(volume_tags: list[int]) -> list[float]:
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


def _fusing_parts(
    aircraft_geom: AircraftGeometry,
    max_failed_attempts: int = 20,
) -> list[FuseEntry]:
    """
    Build per-part metadata and fuse part volumes in gmsh OCC.
    """
    log.info("Start fusion of the different parts")

    # Fuse all volume entities
    wing_entries: list[FuseEntry] = [
        FuseEntry(
            name=geom.uid,
            dimtag=(3, geom.ref_volume_tag),
            part_type=PartType.wing,
        )
        for geom in aircraft_geom.wing_geoms
    ]
    pylon_entries: list[FuseEntry] = [
        FuseEntry(
            name=geom.uid,
            dimtag=(3, geom.ref_volume_tag),
            part_type=PartType.pylon,
        )
        for geom in aircraft_geom.pylon_geoms
    ]
    fuselage_entries: list[FuseEntry] = [
        FuseEntry(
            name=geom.uid,
            dimtag=(3, geom.ref_volume_tag),
            part_type=PartType.fuselage,
        )
        for geom in aircraft_geom.fuselage_geoms
    ]
    dimtags_names = wing_entries + pylon_entries + fuselage_entries

    failed_attempts = 0
    while len(dimtags_names) > 1:
        # As long as intersecting: then fuse
        pair = _get_intersecting_entites(dimtags_names)
        if pair is None:
            # Exit if no more intersecting entites
            log.info("No intersections found. Finished Fusing parts.")
            return dimtags_names

        i, j = pair
        left_name = str(dimtags_names[i].name)
        right_name = str(dimtags_names[j].name)
        merged_name = f"{left_name}+{right_name}"
        merged_part_type = _resolve_merged_part_type(
            dimtags_names[i].part_type,
            dimtags_names[j].part_type,
        )

        try:
            # Fusing 3D entities
            fused_entities, _ = gmsh.model.occ.fuse(
                [dimtags_names[i].dimtag],
                [dimtags_names[j].dimtag],
            )
            gmsh.model.occ.synchronize()

            if not fused_entities:
                failed_attempts += 1
                log.warning(f"Fuse produced no entity for pair {merged_name}; retrying.")
                continue

            for idx in sorted((i, j), reverse=True):
                dimtags_names.pop(idx)

            dimtags_names.append(FuseEntry(
                name=merged_name,
                dimtag=fused_entities[0],
                part_type=merged_part_type,
            ))

            if len(fused_entities) > 1:
                failed_attempts += 1
                log.warning(
                    f"Fuse of {merged_name} returned {len(fused_entities)} solids; keeping all."
                )
                for k, extra_dimtag in enumerate(fused_entities[1:], start=2):
                    dimtags_names.append(FuseEntry(
                        name=f"{merged_name}#part{k}",
                        dimtag=extra_dimtag,
                        part_type=merged_part_type,
                    ))

        except Exception as err:
            failed_attempts += 1
            log.warning(f"Fusion failed for pair ({i}, {j}): {err}")
            random.shuffle(dimtags_names)

        if failed_attempts > max_failed_attempts:
            remaining = [str(item.name) for item in dimtags_names]
            raise ValueError(
                "Fusion stopped after repeated failures. "
                f"Remaining disconnected groups ({len(remaining)}): {remaining}"
            )

    return dimtags_names


def _get_model_dim(model_bb: list[float]) -> list[float]:
    return [
        abs(model_bb[0] - model_bb[3]),
        abs(model_bb[1] - model_bb[4]),
        abs(model_bb[2] - model_bb[5]),
    ]


def _center_all_entities(model_bb: list[float]) -> None:
    model_dimensions = _get_model_dim(model_bb)
    gmsh.model.occ.synchronize()

    # Center EVERYTHING around the center
    all_entities = gmsh.model.getEntities(-1)
    gmsh.model.occ.translate(
        dimTags=all_entities,
        dx=-((model_bb[0]) + (model_dimensions[0] / 2)),
        dy=-((model_bb[1]) + (model_dimensions[1] / 2)),
        dz=-((model_bb[2]) + (model_dimensions[2] / 2)),
    )
    gmsh.model.occ.synchronize()


def _get_intersecting_entites(entries: list[FuseEntry]) -> tuple[int, int] | None:
    """
    Return indices of an intersecting volume pair, if any.

    The search is optimized by first testing bounding-box overlap and only
    running expensive OCC boolean intersections for candidate pairs.
    """
    if len(entries) < 2:
        return None

    def _bbox_overlap(
        bb1: BoundingBox,
        bb2: BoundingBox,
    ) -> bool:
        return (
            bb1[0] <= bb2[3] and bb1[3] >= bb2[0]
            and bb1[1] <= bb2[4] and bb1[4] >= bb2[1]
            and bb1[2] <= bb2[5] and bb1[5] >= bb2[2]
        )

    bboxes: list[BoundingBox] = [
        gmsh.model.occ.getBoundingBox(*entry.dimtag)
        for entry in entries
    ]

    for i in range(len(entries) - 1):
        entities1 = [entries[i].dimtag]
        bb1 = bboxes[i]
        for j in range(i + 1, len(entries)):
            if not _bbox_overlap(bb1, bboxes[j]):
                continue

            entities2 = [entries[j].dimtag]
            intersect = gmsh.model.occ.intersect(
                entities1,
                entities2,
                removeObject=False,
                removeTool=False,
            )[0]

            if intersect:
                log.info(f"Intersecting entry {i} and entry {j}.")
                gmsh.model.occ.remove(intersect, recursive=True)
                gmsh.model.occ.synchronize()
                return i, j

    return None


def _sort_surfaces(fused_parts: list[FuseEntry]) -> list[SurfacePart]:
    """Collect surfaces, lines and points for each fused part volume."""
    log.info("Starting surface classification.")
    gmsh.model.occ.synchronize()

    aircraft_parts: list[SurfacePart] = []
    for part in fused_parts:
        surfaces = gmsh.model.getBoundary(
            [part.dimtag],
            combined=True,
            oriented=False,
            recursive=False,
        )
        lines = gmsh.model.getBoundary(
            surfaces,
            combined=False,
            oriented=False,
            recursive=False,
        )
        points = gmsh.model.getBoundary(
            lines,
            combined=False,
            oriented=False,
            recursive=False,
        )

        aircraft_parts.append(
            SurfacePart(
                uid=part.name,
                part_type=part.part_type,
                volume=part.dimtag,
                surfaces=surfaces,
                surfaces_tags=[tag for _, tag in surfaces],
                lines=lines,
                lines_tags=[tag for _, tag in lines],
                points=points,
                points_tags=[tag for _, tag in points],
            )
        )

    return aircraft_parts


def _create_physical_groups(
    aircraft_parts: list[SurfacePart],
    model_bb: list[float],
    symmetry: bool,
) -> list[SurfacePart]:
    """Create gmsh physical groups from sorted surfaces."""
    model_dim = _get_model_dim(model_bb)

    if symmetry:
        length = max(model_dim) + 1
        bb_y_plane = (-length / 2, -0.0001, -length / 2, length / 2, 0.0001, length / 2)
        surfaces_y_plane = gmsh.model.occ.getEntitiesInBoundingBox(*bb_y_plane, 2)
        if surfaces_y_plane:
            part_group = gmsh.model.addPhysicalGroup(2, [t for (_, t) in surfaces_y_plane])
            gmsh.model.setPhysicalName(2, part_group, "y symmetry plane")
            gmsh.model.occ.synchronize()
    else:
        surfaces_y_plane = []

    surfaces_y_plane_tags = {t for (_, t) in surfaces_y_plane}
    for model_part in aircraft_parts:
        model_part.surfaces = [
            surface for surface in model_part.surfaces if surface[1] not in surfaces_y_plane_tags
        ]
        model_part.surfaces_tags = [t for (_, t) in model_part.surfaces]

        if not model_part.surfaces_tags:
            continue

        part_group = gmsh.model.addPhysicalGroup(2, model_part.surfaces_tags)
        gmsh.model.setPhysicalName(2, part_group, model_part.uid)

    return aircraft_parts


def sort_surfaces_and_create_physical_groups(
    model_bb: list[float],
    symmetry: bool,
    fused_parts: list[FuseEntry],
) -> list[SurfacePart]:
    """Sort surfaces and then create physical groups for each part."""
    aircraft_parts = _sort_surfaces(fused_parts=fused_parts)
    return _create_physical_groups(
        aircraft_parts=aircraft_parts,
        model_bb=model_bb,
        symmetry=symmetry,
    )


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
        all_volume_tags.append(geom.ref_volume_tag)

    # Get Model Bounding Box
    model_bb = _bounding_box(all_volume_tags)

    # Center all entities around this Bounding Box
    _center_all_entities(model_bb)

    # If symmetry is applied get the current symmetry box tag
    if symmetry:
        sym_box_tag = _get_symmetry_box_tag()

    # Fuse all parts of the model
    fused_parts = _fusing_parts(aircraft_geom)

    if symmetry:
        log.info("Cutting in half the model (symmetry=True).")
        dimtag_vols = gmsh.model.occ.getEntities(3)
        # Cut with symmetric box
        gmsh.model.occ.cut(dimtag_vols, [(3, sym_box_tag)])
        gmsh.model.occ.synchronize()

    aircraft_parts = sort_surfaces_and_create_physical_groups(
        model_bb=model_bb,
        symmetry=symmetry,
        fused_parts=fused_parts,
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
