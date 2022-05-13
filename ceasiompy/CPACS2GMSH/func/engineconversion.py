"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains diffrent functions to convert engine

Python version: >=3.7

| Author: Tony Govoni
| Creation: 2022-05-12

"""


import os
from pathlib import Path
from ceasiompy.CPACS2SUMO.func.engineclasses import Engine
import numpy as np

# ==============================================================================
#   IMPORTS
# ==============================================================================
import gmsh
import numpy as np
from ceasiompy.CPACS2GMSH.func.generategmesh import ModelPart, get_entities_from_volume
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_part_type
from ceasiompy.utils.generalclasses import Transformation
from cpacspy.cpacspy import CPACS

log = get_logger()
# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def engine_conversion(cpacs_path, engine_uids, brep_dir_path):
    """
    Function to convert the nacelle part in one engine

    Args:
    ----------
    cpacs_path : Path
        path to the cpacs of the aircraft
    engine_uids : str
        engine uids : engine uid + all the nacelle uids
    brep_dir_path : Path
        Path to the directory containing the brep files
    """

    # Find the brep files associated with the engine:
    engine_files_path = []
    for file in os.listdir(brep_dir_path):
        part_uid = file.split(".")[0]
        if part_uid in engine_uids:
            engine_files_path.append(Path(brep_dir_path, file))

    # Create a new engine with all the nacelle parts
    closed_engine_path = close_engine(cpacs_path, engine_uids, engine_files_path, brep_dir_path)

    # clean brep files from the nacelle that are no more used
    for file in brep_dir_path.iterdir():
        part_uid = (str(file)).split(".")[0].split("/")[-1]

        if part_uid in engine_uids[1:]:
            file.unlink()

    # Move the engine to the correct location
    reposition_engine(cpacs_path, closed_engine_path, brep_dir_path)


def close_engine(cpacs_path, engine_uids, engine_files_path, brep_dir_path):
    """
    Function to close the engine nacelle fan by adding an inlet and outlet inside of the engine.
    Then the nacelle part are fused together to form only one engine that is saved as .brep file
    the engine inlet will be placed at 20% of the total engine length, same for outlet

    ...
    Args:
    ----------
    cpacs_path : Path
        path to the cpacs of the aircraft
    engine_uid : str
        engine uid
    engine_files : list
        list of brep files associated with the engine
    """
    gmsh.initialize()

    # Import the part and create the Modelpart object

    engine_parts = []

    for brep_file in engine_files_path:

        # Import the part and create the aircraft part object
        part_dimtag = gmsh.model.occ.importShapes(str(brep_file), highestDimOnly=False)
        gmsh.model.occ.synchronize()

        # Create the aircraft part object
        part_obj = ModelPart(uid=brep_file.stem)
        part_obj.part_type = get_part_type(cpacs_path, part_obj.uid)
        part_obj.volume = [part_dimtag[0]]

        # Heal Fancowl : sometimes gmsh is not able to mesh correctly those type of part
        if part_obj.part_type == "fanCowl":
            gmsh.model.occ.healShapes(
                dimTags=[part_dimtag[0]],
                tolerance=1e-8,
                fixDegenerated=True,
                fixSmallEdges=True,
                fixSmallFaces=True,
                sewFaces=True,
                makeSolids=True,
            )
            gmsh.model.occ.synchronize()

        # Add to the list of engine_parts
        engine_parts.append(part_obj)

    for part in engine_parts:
        if part.part_type == "fanCowl":
            fancowl_part = part

    # find the first point and last point x wise of the nacelle_center
    surfaces_dimtags, lines_dimtags, points_dimtags = get_entities_from_volume(fancowl_part.volume)
    fancowl_part.surfaces = surfaces_dimtags
    fancowl_part.lines = lines_dimtags
    fancowl_part.points = points_dimtags

    points_pos = [gmsh.model.occ.getBoundingBox(*dimtag) for dimtag in fancowl_part.points]
    point_x_pos = [pos[0] for pos in points_pos]

    p1 = fancowl_part.points[point_x_pos.index(min(point_x_pos))]
    p2 = fancowl_part.points[point_x_pos.index(max(point_x_pos))]
    p1_x, p1_y, p1_z, _, _, _ = gmsh.model.occ.getBoundingBox(*p1)
    p2_x, p2_y, p2_z, _, _, _ = gmsh.model.occ.getBoundingBox(*p2)
    fancowl_part_axis = [p1_x - p2_x, p1_y - p2_y, p1_z - p2_z]

    percent_forward = 0.2
    percent_backward = 0.2

    disk_inlet_center = [
        p1_x - fancowl_part_axis[0] * percent_forward,
        p1_y - fancowl_part_axis[1] * percent_forward,
        p1_z - fancowl_part_axis[2] * percent_forward,
    ]

    bb = gmsh.model.getBoundingBox(-1, -1)
    model_dimensions = [abs(bb[0] - bb[3]), abs(bb[1] - bb[4]), abs(bb[2] - bb[5])]

    domain_length = max(model_dimensions)
    # create a cylinder from 45% to 55% of the nacelle_center to cut the nacelle volume
    disk_inlet = gmsh.model.occ.addDisk(*disk_inlet_center, domain_length, domain_length)
    gmsh.model.occ.synchronize()

    disk_inlet = (2, disk_inlet)

    # generate the disk (gmsh always create a disk in the xy plane)
    xy_vector = [0, 0, 1]

    if fancowl_part_axis != xy_vector:
        rotation_axis = np.cross(fancowl_part_axis, xy_vector)
        gmsh.model.occ.rotate([disk_inlet], *disk_inlet_center, *rotation_axis, np.pi / 2)
        gmsh.model.occ.synchronize()
    cylinder = gmsh.model.occ.extrude(
        [disk_inlet],
        -fancowl_part_axis[0] * (1 - (percent_forward + percent_backward)),
        -fancowl_part_axis[1] * (1 - (percent_forward + percent_backward)),
        -fancowl_part_axis[2] * (1 - (percent_forward + percent_backward)),
        numElements=[],
        heights=[],
        recombine=True,
    )
    gmsh.model.occ.synchronize()

    parts_to_fragment = [part.volume[0] for part in engine_parts]
    fragments_dimtag, _ = gmsh.model.occ.fragment(parts_to_fragment, [cylinder[1]])
    gmsh.model.occ.synchronize()

    """
    find the volume with the largest bounding box, it is the external part of the cylinder
    """
    largest_volume = [(0, 0), 0]
    for fragment in fragments_dimtag:
        bb = gmsh.model.occ.getBoundingBox(*fragment)
        fragment_dimensions = [abs(bb[0] - bb[3]), abs(bb[1] - bb[4]), abs(bb[2] - bb[5])]
        fragment_length = max(fragment_dimensions)
        if fragment_length > largest_volume[1]:
            largest_volume = [fragment, fragment_length]

    # remove the extra part of the cylinder

    gmsh.model.occ.remove([largest_volume[0]], recursive=True)
    fragments_dimtag.remove(largest_volume[0])
    gmsh.model.occ.synchronize()

    # fuse everything together
    fused_dimtag = gmsh.model.occ.fuse(
        fragments_dimtag[:1], fragments_dimtag[1:], removeObject=True, removeTool=True
    )

    gmsh.model.occ.synchronize()

    # clean engine from remaining surfaces

    domain_points = gmsh.model.getEntities(dim=0)
    domain_lines = gmsh.model.getEntities(dim=1)
    domain_surfaces = gmsh.model.getEntities(dim=2)

    for point in domain_points:
        gmsh.model.occ.remove([point], recursive=True)

    for line in domain_lines:
        gmsh.model.occ.remove([line], recursive=True)

    for surface in domain_surfaces:
        gmsh.model.occ.remove([surface], recursive=True)

    gmsh.model.occ.synchronize()

    closed_engine_path = Path(brep_dir_path, f"{engine_uids[0]}.brep")

    gmsh.write(str(closed_engine_path))

    gmsh.clear()
    gmsh.finalize()

    return closed_engine_path


def reposition_engine(cpacs_path, engine_path, brep_dir_path):
    """
    Function to move the engines to their correct position relative to the aircraft
    by using the cpacs file translation, rotation and scaling data

    the engine is imported in gmsh, moved to the correct position and then saved.
    if a mirrored version of the engine is needed, another engine is created and saved
    at the mirrored location
    ...

    Args:
    ----------
    cpacs_path : Path
        path to the cpacs of the aircraft
    engine_path : Path
        Path of the engine to reposition
    """
    # first retrieve the transformation data from the cpacs file
    cpacs = CPACS(str(cpacs_path))
    tixi = cpacs.tixi
    gmsh.initialize()

    xpath = "/cpacs/vehicles/aircraft/model/engines/engine"

    engine = Engine(tixi, xpath)

    # import the engine

    engine_dimtags = gmsh.model.occ.importShapes(str(engine_path), highestDimOnly=True)
    gmsh.model.occ.synchronize()

    # Apply the transformations

    # scaling
    gmsh.model.occ.dilate(
        [engine_dimtags[0]],
        0,
        0,
        0,
        engine.transf.scaling.x,
        engine.transf.scaling.y,
        engine.transf.scaling.z,
    )
    # rotation
    # x axis
    gmsh.model.occ.rotate(
        [engine_dimtags[0]], 0, 0, 0, 1, 0, 0, np.radians(engine.transf.rotation.x)
    )
    # y axis
    gmsh.model.occ.rotate(
        [engine_dimtags[0]], 0, 0, 0, 0, 1, 0, np.radians(engine.transf.rotation.y)
    )
    # z axis
    gmsh.model.occ.rotate(
        [engine_dimtags[0]], 0, 0, 0, 0, 0, 1, np.radians(engine.transf.rotation.z)
    )

    # translation
    gmsh.model.occ.translate(
        [engine_dimtags[0]],
        engine.transf.translation.x,
        engine.transf.translation.y,
        engine.transf.translation.z,
    )
    gmsh.model.occ.synchronize()

    # save the new engine in its new position
    gmsh.write(str(engine_path))
    gmsh.clear()
    gmsh.finalize()

    # Search for a possible mirrored engine

    if engine.sym:
        gmsh.initialize()
        # create a new engine and make a mirror transformation
        engine_dimtags = gmsh.model.occ.importShapes(str(engine_path), highestDimOnly=True)
        gmsh.model.occ.synchronize()

        # mirror the engine
        gmsh.model.occ.mirror([engine_dimtags[0]], 0, 1, 0, 0)
        gmsh.model.occ.synchronize()

        # add the mirrored tag and save the engine
        engine_path = (str(engine_path)).split(".")[0]
        engine_path = engine_path + "_mirrored.brep"
        gmsh.write(engine_path)

        gmsh.clear()
        gmsh.finalize()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
