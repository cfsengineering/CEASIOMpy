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

# ==============================================================================
#   IMPORTS
# ==============================================================================
import gmsh
import numpy as np
from scipy.spatial.transform import Rotation as R
from ceasiompy.CPACS2GMSH.func.generategmesh import ModelPart, get_entities_from_volume
from ceasiompy.CPACS2SUMO.func.engineclasses import Engine
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_part_type
from ceasiompy.utils.configfiles import ConfigFile
from cpacspy.cpacspy import CPACS

log = get_logger()
# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def engine_conversion(cpacs_path, engine_uids, brep_dir_path, engines_cfg_file_path):
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
    engines_cfg_file_path : Path
        Path to the engines configuration file
    """

    # Find the brep files associated with the engine:
    engine_files_path = []
    for file in os.listdir(brep_dir_path):
        part_uid = file.split(".")[0]
        if part_uid in engine_uids:
            engine_files_path.append(Path(brep_dir_path, file))

    # Create a new engine with all the nacelle parts

    # Create a new engine that is closed with an inlet and an outlet
    closed_engine_path = close_engine(
        cpacs_path, engine_uids, engine_files_path, brep_dir_path, engines_cfg_file_path
    )

    # clean brep files from the nacelle that are no more used
    for file in brep_dir_path.iterdir():
        part_uid = (str(file)).split(".")[0].split("/")[-1]

        if part_uid in engine_uids[1:]:
            file.unlink()

    # Move the new engine to the correct location
    reposition_engine(cpacs_path, closed_engine_path, engine_uids, engines_cfg_file_path)


def close_engine(cpacs_path, engine_uids, engine_files_path, brep_dir_path, engines_cfg_file_path):
    """
    Function to close the engine nacelle fan by adding an inlet and outlet inside of the engine.
    Then the nacelle part are fused together to form only one engine that is saved as .brep file
    the engine inlet will be placed at 20% of the total engine length, same for outlet

    TODO: If TiGL in newer version fix the engine export issue (i.e. it is possible to export an
    engine like a wing or a pylon, without doing manually the translation, rotation,
    scaling and mirror of the engine) this function needs to be modified since it assume that
    the engine is oriented along the x axis and it may no more be the case since the brep files
    of the nacelle are imported as they are on the cpacs model

    ...
    Args:
    ----------
    cpacs_path : Path
        path to the cpacs of the aircraft
    engine_uid : str
        engine uid
    engine_files : list
        list of brep files associated with the engine
    brep_dir_path : Path
        Path to the directory containing the brep files
    engines_cfg_file_path : Path
        Path to the engines configuration file
    ...
    Returns:
    ----------
    closed_engine_path : Path
        Path to the closed engine
    """
    gmsh.initialize()

    # Import the part and create the Modelpart object
    print("engine_uids", engine_uids)
    print("engine_files_path", engine_files_path)
    print("brep_dir_path", brep_dir_path)
    print("engines_cfg_file_path", engines_cfg_file_path)
    engine_parts = []

    for brep_file in engine_files_path:

        # Import the part and create the aircraft part object
        part_dimtag = gmsh.model.occ.importShapes(str(brep_file), highestDimOnly=False)
        gmsh.model.occ.synchronize()

        # Create the aircraft part object
        part_obj = ModelPart(uid=brep_file.stem)
        part_obj.part_type = get_part_type(cpacs_path, part_obj.uid)
        part_obj.volume = [part_dimtag[0]]

        # Heal Fancowl : sometimes gmsh is not able to mesh correctly those
        # of part
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

    extrusion_vector = [
        -fancowl_part_axis[0] * (1 - (percent_forward + percent_backward)),
        -fancowl_part_axis[1] * (1 - (percent_forward + percent_backward)),
        -fancowl_part_axis[2] * (1 - (percent_forward + percent_backward)),
    ]

    # at this point we will save the distance between the inlet and the outlet of the engine
    # this data will be used to find the correct inlet and outlet surface
    # in the final model
    distance = np.linalg.norm(np.array(extrusion_vector))
    config_file = ConfigFile(engines_cfg_file_path)
    config_file[f"{engine_uids[0]}_DISTANCE"] = f"{distance}"
    # save this info in the engines config file
    config_file.write_file(engines_cfg_file_path, overwrite=True)

    cylinder = gmsh.model.occ.extrude(
        [disk_inlet],
        *extrusion_vector,
        numElements=[],
        heights=[],
        recombine=True,
    )
    gmsh.model.occ.synchronize()

    parts_to_fragment = [part.volume[0] for part in engine_parts]
    fragments_dimtag, _ = gmsh.model.occ.fragment(parts_to_fragment, [cylinder[1]])
    gmsh.model.occ.synchronize()

    # find the volume with the largest bounding box, it is the external part of the cylinder

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
    _ = gmsh.model.occ.fuse(
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


def reposition_engine(cpacs_path, engine_path, engine_uids, engines_cfg_file_path):
    """
    Function to move the engines to their correct position relative to the aircraft
    by using the cpacs file translation, rotation and scaling data

    the engine is imported in gmsh, moved to the correct position and then saved.
    if a mirrored version of the engine is needed, another engine is created and saved
    at the mirrored location

    TODO: If TiGL in newer version fix the engine export issue (i.e. it is possible to export an
    engine like a wing or a pylon, without doing manually the translation, rotation,
    scaling and mirror of the engine) this function can be removed without
    ...

    Args:
    ----------
    cpacs_path : Path
        path to the cpacs of the aircraft
    engine_path : Path
        Path of the engine to reposition
    engine_uids : list
        list of the uids of the engine parts
    engines_cfg_file_path : Path
        Path to the engines config file
    """
    # first retrieve the transformation data from the cpacs file
    cpacs = CPACS(str(cpacs_path))
    tixi = cpacs.tixi
    gmsh.initialize()
    xpath_engines_position = "/cpacs/vehicles/aircraft/model/engines"

    # get the engine transformation for the correct engine in the cpacs file
    engine_nb = tixi.getNamedChildrenCount(xpath_engines_position, "engine")

    for engine_index in range(engine_nb):

        xpath_engine_postition = xpath_engines_position + "/engine[" + str(engine_index + 1) + "]"
        engine = Engine(tixi, xpath_engine_postition)

        if engine_path.stem in engine.uid:
            # if it is the correct engine we can break the loop
            break

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

    # save the engine axis in the engines config file
    original_gmsh_axis = [-1, 0, 0]

    rx = R.from_euler("x", engine.transf.rotation.x, degrees=True)
    ry = R.from_euler("y", engine.transf.rotation.y, degrees=True)
    rz = R.from_euler("z", engine.transf.rotation.z, degrees=True)

    rotation = rx.apply(original_gmsh_axis)
    rotation = ry.apply(rotation)
    rotation = rz.apply(rotation)

    config_file = ConfigFile(engines_cfg_file_path)

    config_file[f"{engine_uids[0]}_NORMAL_X"] = f"{rotation[0]}"
    config_file[f"{engine_uids[0]}_NORMAL_Y"] = f"{rotation[1]}"
    config_file[f"{engine_uids[0]}_NORMAL_Z"] = f"{rotation[2]}"

    # addapt the distance with the scaling of the x axis
    distance = float(config_file[f"{engine_uids[0]}_DISTANCE"])
    config_file[f"{engine_uids[0]}_DISTANCE_SCALED"] = str(distance * engine.transf.scaling.x)

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

        # complete the config file with the mirrored engine
        # TODO: add mirror operation as a function of the plane of symmetry
        # if xz : inverse y comp. if yz : inverse x comp. if xy : inverse z comp.

        config_file[f"{engine_uids[0]}_mirrored_NORMAL_X"] = f"{rotation[0]}"
        config_file[f"{engine_uids[0]}_mirrored_NORMAL_Y"] = f"{-rotation[1]}"
        config_file[f"{engine_uids[0]}_mirrored_NORMAL_Z"] = f"{rotation[2]}"
        # with the scaling of the x axis
        config_file[f"{engine_uids[0]}_mirrored_DISTANCE_SCALED"] = str(
            distance * engine.transf.scaling.x
        )

    # save this info in the engines config file
    config_file.write_file(engines_cfg_file_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
