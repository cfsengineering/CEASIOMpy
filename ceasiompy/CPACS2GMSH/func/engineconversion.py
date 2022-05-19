"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains diffrent functions to convert engine

Python version: >=3.7

| Author: Tony Govoni
| Creation: 2022-05-12

"""


# ==============================================================================
#   IMPORTS
# ==============================================================================
from pathlib import Path
from ceasiompy.utils.commonxpath import ENGINES_XPATH
import gmsh
import numpy as np
from ceasiompy.CPACS2SUMO.func.engineclasses import Engine
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_part_type
from ceasiompy.utils.configfiles import ConfigFile
from scipy.spatial.transform import Rotation as R


log = get_logger()

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def engine_conversion(
    cpacs, engine_uids, brep_dir_path, engines_cfg_file_path, engine_surface_percent
):
    """
    Function to convert the nacelle part in one engine by closing it and positioning it
    at the correct location, when the engine is ready it is saved as a new part with
    the cpacs uid of the engine. After the conversion the nacelle file are deleted

    Args:
    ----------
    cpacs : CPACS object
        The cpacs object from cpacspy
    engine_uids : str
        engine uids : engine uid + all the nacelle uids
    brep_dir_path : Path
        Path to the directory containing the brep files
    engines_cfg_file_path : Path
        Path to the engines configuration file
    engine_surface_percent : tuple
        Tuple containing the position percentage of the surface intake and exhaust bc
        for the engine
    """

    log.info(f"Converting engine : {engine_uids[0]}")

    # Find the brep files associated with the engine uid:
    engine_files_path = [
        file for file in list(brep_dir_path.glob("*.brep")) if file.stem in engine_uids
    ]
    # Class the brep with their respective part type
    nacelle_parts = {}
    for engine_file_path in engine_files_path:
        part_uid = engine_file_path.stem
        part_type = get_part_type(cpacs.tixi, part_uid)
        nacelle_parts[part_type] = engine_file_path

    # Create a new engine that is closed with an inlet and an outlet
    closed_engine_path = close_engine(
        nacelle_parts, engine_uids, brep_dir_path, engines_cfg_file_path, engine_surface_percent
    )

    # clean brep files from the nacelle that are no more used
    for file in brep_dir_path.iterdir():
        part_uid = (str(file)).split(".")[0].split("/")[-1]

        if part_uid in engine_uids[1:]:
            file.unlink()

    # Move the new engine to the correct location
    reposition_engine(cpacs, closed_engine_path, engine_uids, engines_cfg_file_path)

    log.info(f"Engine {engine_uids[0]} converted")


def close_engine(
    nacelle_parts, engine_uids, brep_dir_path, engines_cfg_file_path, engine_surface_percent
):
    """
    Function to close the engine nacelle fan by adding an inlet and outlet inside of the engine.
    Then the nacelle part are fused together to form only one engine that is saved as .brep file
    the engine inlet will be placed at 20% of the total engine length, same for outlet

    TODO: If TiGL in newer version fix the engine export issue (i.e. it is possible to export an
    engine like a wing or a pylon, without doing manually the translation, rotation,
    scaling and mirror of the engine) this function needs to be modified since it assume that
    the all the part are oriented along the x axis and it may no more be the case if the TiGL
    exportshape function will apply the rotation/translation/scaling operation

    In order to fix this, the part will need to be rotated back in gmsh to be again aligned with
    the x axis before to preforms engine_closing operation, then it can be rotated back in the
    final correct configuration

    ...
    Args:
    ----------
    nacelle_parts : dict
        Dictionary containing the nacelle parts part type and PATH
    engine_uids : list
        engine uids : engine uid + all the nacelle uids
    brep_dir_path : Path
        Path to the directory containing the brep files
    engines_cfg_file_path : Path
        Path to the engines configuration file
    engine_surface_percent : tuple
        Tuple containing the position percentage of the surface intake and exhaust bc
        for the engine

    ...
    Returns:
    ----------
    closed_engine_path : Path
        Path to the closed engine
    """

    # first close the FanCowl
    intake_x, exhaust_x = close_part(
        nacelle_parts["fanCowl"],
        engine_uids,
        "fanCowl",
        engines_cfg_file_path,
        engine_surface_percent,
    )
    config_file = ConfigFile(engines_cfg_file_path)
    # save the information of the future intake and exhaust position
    config_file[f"{engine_uids[0]}_fanCowl_INTAKE_X"] = f"{intake_x}"
    config_file[f"{engine_uids[0]}_fanCowl_EXHAUST_X"] = f"{exhaust_x}"
    config_file.write_file(engines_cfg_file_path, overwrite=True)

    # Second close the core cowl
    if "coreCowl" in nacelle_parts:
        intake_x, exhaust_x = close_part(
            nacelle_parts["coreCowl"],
            engine_uids,
            "coreCowl",
            engines_cfg_file_path,
            engine_surface_percent,
        )
        config_file = ConfigFile(engines_cfg_file_path)
        # save the information of the future intake and exhaust position
        config_file[f"{engine_uids[0]}_coreCowl_INTAKE_X"] = f"{intake_x}"
        config_file[f"{engine_uids[0]}_coreCowl_EXHAUST_X"] = f"{exhaust_x}"
        config_file.write_file(engines_cfg_file_path, overwrite=True)

    # Now that all the part are closed, fuse them together
    gmsh.initialize()

    part_to_fuse = []
    engine_files_path = [nacelle_parts[key] for key in nacelle_parts]
    # import all the parts
    for brep_file in engine_files_path:
        part_entities = gmsh.model.occ.importShapes(str(brep_file), highestDimOnly=False)
        gmsh.model.occ.synchronize()
        part_to_fuse.append(part_entities[0])

    # fuse them
    gmsh.model.occ.fuse(part_to_fuse[:1], part_to_fuse[1:], removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()

    closed_engine_path = Path(brep_dir_path, f"{engine_uids[0]}.brep")

    # save engine and close gmsh session
    gmsh.write(str(closed_engine_path))
    gmsh.clear()
    gmsh.finalize()

    # return the new closed engine path
    return closed_engine_path


def close_part(
    part_path,
    engine_uids,
    part_type,
    engines_cfg_file_path,
    engine_surface_percent,
):
    """
    Function to close the nacelle part by adding an inlet and outlet inside of the nacelle.
    A large cylinder is created to fill the part
    the inlet or intake will be placed at percent_forward of the total engine length
    same for outlet or exhaust with percent_backward

    Attention it is assumed that the part that will be closed is imported aligned with
    the x axis and it will close the part with surfaces normal to the x axis

    Args:
    ----------
    engine_uids : list
        engine uids : engine uid + all the nacelle uids
    part_path : Path
        Path to the brep file of the nacelle part
    part_type : str
        Type of the part (fanCowl, coreCowl)
    percent_forward : float
        percentage of the total length of the nacelle part to place the inlet
    percent_backward : float
        percentage of the total length of the nacelle part to place the outlet
    engines_cfg_file_path : Path
        Path to the engines configuration file
    engine_surface_percent : tuple
        Tuple containing the position percentage of the surface intake and exhaust bc
        for the engine
    ...
    Returns:
    ----------
    intake_x : float
        x position of the intake
    exhaust_x : float
        x position of the exhaust
    """

    # Import the part
    gmsh.initialize()

    part_dimtag = gmsh.model.occ.importShapes(str(part_path), highestDimOnly=False)
    gmsh.model.occ.synchronize()

    # Heal part : sometimes gmsh is not able to mesh correctly the fan cowl
    # and the core cowl part of the engine
    # a small heal shape is applied
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

    # find the first point and last point x wise of the part are found
    part_bb = gmsh.model.occ.getBoundingBox(*part_dimtag[0])
    part_min_x = part_bb[0]
    part_max_x = part_bb[3]

    # calculate intake and exhaust position
    intake_x = part_min_x + (engine_surface_percent[0] / 100) * (part_max_x - part_min_x)
    exhaust_x = part_min_x + (1 - (engine_surface_percent[1] / 100)) * (part_max_x - part_min_x)

    # If the part is a core cowl, the intake must be placed before the exhaust
    # of the fan cowl other wise they will be internal volumes inside of the engine
    # between the fan cowl exhaust and the core cowl intake

    if part_type == "coreCowl":
        # check the position of the fan cowl exhaust
        config_file = ConfigFile(engines_cfg_file_path)

        fancowl_exhaust_x = float(config_file[f"{engine_uids[0]}_fanCowl_EXHAUST_X"])
        if fancowl_exhaust_x < intake_x:
            intake_x = fancowl_exhaust_x

        # raise warning if the fan cowl intake is after the core cowl part
        if float(config_file[f"{engine_uids[0]}_fanCowl_INTAKE_X"]) > part_min_x:
            log.warning("The intake position of the fan cowl is inside core cowl part")
            log.error("Change the fan cowl intake position upstream")

    # find how large may the part be
    bb = gmsh.model.getBoundingBox(-1, -1)
    model_dimensions = [abs(bb[0] - bb[3]), abs(bb[1] - bb[4]), abs(bb[2] - bb[5])]
    domain_length = max(model_dimensions)

    # create a cylinder from disk_intake to disk_exhaust for the fan cowl
    disk_intake_tag = gmsh.model.occ.addDisk(*(intake_x, 0, 0), domain_length, domain_length)
    gmsh.model.occ.synchronize()
    disk_intake = (2, disk_intake_tag)

    # gmsh always create a disk in the xy plane, so we need to rotate it to the x axis
    # rotation of the disk in the right plane (y_z plane)

    gmsh.model.occ.rotate([disk_intake], *(intake_x, 0, 0), *(0, 1, 0), np.pi / 2)
    gmsh.model.occ.synchronize()

    cylinder_length = exhaust_x - intake_x

    cylinder = gmsh.model.occ.extrude(
        dimTags=[disk_intake],
        dx=cylinder_length,
        dy=0,
        dz=0,
        numElements=[],
        heights=[],
        recombine=True,
    )
    gmsh.model.occ.synchronize()

    fragments_dimtag, _ = gmsh.model.occ.fragment([part_dimtag[0]], [cylinder[1]])
    gmsh.model.occ.synchronize()

    # find the volume with the largest bounding box, it is the external part of the cylinder
    # that we want to remove
    largest_volume = [(0, 0), 0]
    for fragment in fragments_dimtag:
        # check for the largest volume (not x wise)
        bb = gmsh.model.occ.getBoundingBox(*fragment)
        fragment_dimensions = [abs(bb[1] - bb[4]), abs(bb[2] - bb[5])]
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

    # clean the fresh closed engine from remaining extra surfaces,lines and points
    # that may have been created with all the boolean operation

    for point in gmsh.model.getEntities(dim=0):
        gmsh.model.occ.remove([point], recursive=True)

    for line in gmsh.model.getEntities(dim=1):
        gmsh.model.occ.remove([line], recursive=True)

    for surface in gmsh.model.getEntities(dim=2):
        gmsh.model.occ.remove([surface], recursive=True)

    # save and close gmsh sessions
    gmsh.model.occ.synchronize()
    gmsh.write(str(part_path))
    gmsh.clear()
    gmsh.finalize()

    return intake_x, exhaust_x


def reposition_engine(cpacs, engine_path, engine_uids, engines_cfg_file_path):
    """
    Function to move the engines to their correct position relative to the aircraft
    by using the cpacs file translation, rotation and scaling data

    the engine is imported in gmsh, moved to the correct position and then saved.
    if a mirrored version of the engine is needed, another engine is created and saved
    at the mirrored location

    TODO: If TiGL in newer version fix the engine export issue (i.e. it is possible to export an
    engine like a wing or a pylon, without doing manually the translation, rotation,
    scaling and mirror of the engine) this function can be removed since normally it
    will become useless
    ...

    Args:
    ----------
    cpacs : CPACS object
        CPACS object of the aircraft
    engine_path : Path
        Path of the engine to reposition
    engine_uids : list
        list of the uids of the engine parts
    engines_cfg_file_path : Path
        Path to the engines config file
    """
    # first retrieve the transformation data from the cpacs file
    tixi = cpacs.tixi
    gmsh.initialize()

    # get the engine transformation for the correct engine in the cpacs file
    engine_nb = tixi.getNamedChildrenCount(ENGINES_XPATH, "engine")

    for engine_idx in range(1, engine_nb + 1):
        engine_xpath = ENGINES_XPATH + f"/engine[{engine_idx}]"
        engine = Engine(tixi, engine_xpath)

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

    # Save the scaling of the x axis
    config_file[f"{engine_uids[0]}_SCALING_X"] = str(engine.transf.scaling.x)

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

        # complete the config file with the mirrored engine config

        config_file[f"{engine_uids[0]}_mirrored_DOUBLE_FLUX"] = config_file[
            f"{engine_uids[0]}_DOUBLE_FLUX"
        ]
        config_file[f"{engine_uids[0]}_mirrored_fanCowl_INTAKE_X"] = config_file[
            f"{engine_uids[0]}_fanCowl_INTAKE_X"
        ]
        config_file[f"{engine_uids[0]}_mirrored_fanCowl_EXHAUST_X"] = config_file[
            f"{engine_uids[0]}_fanCowl_EXHAUST_X"
        ]
        if bool(int(config_file[f"{engine_uids[0]}_mirrored_DOUBLE_FLUX"])):
            config_file[f"{engine_uids[0]}_mirrored_coreCowl_EXHAUST_X"] = config_file[
                f"{engine_uids[0]}_coreCowl_EXHAUST_X"
            ]
        # TODO: add mirror operation as a function of the plane of symmetry
        # if xz : inverse y comp. if yz : inverse x comp. if xy : inverse z comp.

        config_file[f"{engine_uids[0]}_mirrored_NORMAL_X"] = f"{rotation[0]}"
        config_file[f"{engine_uids[0]}_mirrored_NORMAL_Y"] = f"{-rotation[1]}"
        config_file[f"{engine_uids[0]}_mirrored_NORMAL_Z"] = f"{rotation[2]}"
        # with the scaling of the x axis
        config_file[f"{engine_uids[0]}_mirrored_SCALING_X"] = str(engine.transf.scaling.x)

    # save this info in the engines config file
    config_file.write_file(engines_cfg_file_path, overwrite=True)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
