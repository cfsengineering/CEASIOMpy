"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This script contains diffrent functions to classify and manipulate wing elements

Python version: >=3.7

| Author: Tony Govoni
| Creation: 2022-04-20

TODO:

    -Update tigle to get the engine position
    -Try to better handle the way to get the engine nacelle coordinates
    -Rework the engine to "close" with inlet and outlet surface
    -Fuse nacelle with pylon ?
    -Engine seems to make gmsh laggy, no more response to kill command ctrl+c



"""


# ==============================================================================
#   IMPORTS
# ==============================================================================
import gmsh
import os
import pickle
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])
# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def reposition_engine(pylon, brep_dir_path):
    """
    Function to move the engines nacelle to their position relative to the pylon
    and replace the .brep files with the new ones in the correct coordinate
    ...

    Args:
    ----------
    pylon : str
        pylon name associated with the engine
    brep_dir_path : (path)
        Path to the directory containing the brep files
    """
    gmsh.initialize()

    pylon_id = pylon[5:]
    log.info(f"Repositioning of engine {pylon_id}")

    # import the pylon and all the engine nacelle parts

    nacelle_files = []

    for file in os.listdir(brep_dir_path):
        if file[:-5] == pylon:
            pylon_part = gmsh.model.occ.importShapes(
                os.path.join(brep_dir_path, file), highestDimOnly=True
            )
            gmsh.model.occ.synchronize()
        if "nacelle" in file and pylon_id in file:
            nacelle_files.append(file)

    if nacelle_files == []:
        log.error(f"No nacelle files found for engine {pylon_id}")
        gmsh.clear()
        gmsh.finalize()
        return

    # get the engine nacelle coordinates relative to the pylon
    position_rel_2_pylon = pickle.load(open(os.path.join(brep_dir_path, "engine_coord.txt"), "rb"))

    # get the pylon coordinates
    """
    This should be reworked to get the engine coordinates correctly
    because it is not clear wich point in the pylon is used to define the
    engine coordinates wrt the pylon
    """

    pylon_bb = gmsh.model.getBoundingBox(*pylon_part[0])
    pylon_dimensions = [
        abs(pylon_bb[0] - pylon_bb[3]),
        abs(pylon_bb[1] - pylon_bb[4]),
        abs(pylon_bb[2] - pylon_bb[5]),
    ]
    pylon_ref_point = [  # @TODO: this is bullshit and should be reworked
        pylon_bb[0],
        pylon_bb[1] + pylon_dimensions[1] / 2,
        pylon_bb[2] - pylon_dimensions[2] / 4,
    ]

    translation_vector = [position_rel_2_pylon[i] + pylon_ref_point[i] for i in range(0, 3)]

    # import each nacelle part and move it to the correct position then replace the nacelle file
    gmsh.clear()
    for file in nacelle_files:

        nacelle_part = gmsh.model.occ.importShapes(
            os.path.join(brep_dir_path, file), highestDimOnly=True
        )
        gmsh.model.occ.translate(nacelle_part, *translation_vector)
        gmsh.model.occ.synchronize()

    gmsh.fltk.run()
    gmsh.write(os.path.join(brep_dir_path, "engine" + pylon_id + ".brep"))

    gmsh.clear()
    gmsh.finalize()


def close_engine(brep_dir_path, engine_name):
    gmsh.initialize()
    nacelle_part = gmsh.model.occ.importShapes(
        os.path.join(brep_dir_path, engine_name), highestDimOnly=False
    )
    gmsh.model.occ.synchronize()
    gmsh.fltk.run()

    # find inlet and outlet points
    nacelle_lines = [dimtag for dimtag in nacelle_part if dimtag[0] == 1]
    print(nacelle_lines)
    lines_center = [gmsh.model.occ.getCenterOfMass(*dimtag) for dimtag in nacelle_lines]
    lines_x_pos = [pos[0] for pos in lines_center]
    inlet_circle = nacelle_lines[lines_x_pos.index(min(lines_x_pos))]
    outlet_circle = nacelle_lines[lines_x_pos.index(max(lines_x_pos))]

    # create disk with inlet and outlet circles

    # merge all with addSurfaceLoop
    print(inlet_circle, outlet_circle)

    # export the engine nacelle and test it =)


close_engine("test_files/simple_pylon_engine", "nacelle_fan_cowl1.brep")
