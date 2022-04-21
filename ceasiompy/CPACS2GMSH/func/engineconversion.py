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
from math import pi
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

    # import the pylon
    print(pylon)
    pylon_part = gmsh.model.occ.importShapes(
        os.path.join(brep_dir_path, pylon + ".brep"), highestDimOnly=True
    )
    gmsh.model.occ.synchronize()
    # find nacelle files corresponding to the pylon id
    nacelle_files = []
    for file in os.listdir(brep_dir_path):
        if "nacelle" in file and file[-len(pylon_id) - 5 : -5] == pylon_id:
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
    print(nacelle_files)
    for file in nacelle_files:
        print()
        print(file)
        print()
        gmsh.clear()  # remove the pylon
        nacelle_part = gmsh.model.occ.importShapes(
            os.path.join(brep_dir_path, file), highestDimOnly=True
        )
        gmsh.model.occ.translate(nacelle_part, *translation_vector)
        gmsh.model.occ.synchronize()
        # apply some healshapes since engine nacelle fan are sometimes not closed volumes
        if "fan" in file:
            gmsh.model.occ.healShapes(
                dimTags=[],
                tolerance=1e-8,
                fixDegenerated=True,
                fixSmallEdges=True,
                fixSmallFaces=True,
                sewFaces=True,
                makeSolids=True,
            )
        gmsh.model.occ.synchronize()
        gmsh.write(os.path.join(brep_dir_path, file))

    gmsh.clear()
    gmsh.finalize()


def close_engine(brep_dir_path, engine_name):
    gmsh.initialize()
    nacelle_part = gmsh.model.occ.importShapes(
        os.path.join(brep_dir_path, engine_name), highestDimOnly=False
    )
    gmsh.model.occ.synchronize()

    # find inlet and outlet points
    nacelle_lines = [dimtag for dimtag in nacelle_part if dimtag[0] == 1]
    lines_center = [gmsh.model.occ.getCenterOfMass(*dimtag) for dimtag in nacelle_lines]
    lines_x_pos = [pos[0] for pos in lines_center]
    inlet_circle = nacelle_lines[lines_x_pos.index(min(lines_x_pos))]
    outlet_circle = nacelle_lines[lines_x_pos.index(max(lines_x_pos))]
    print(inlet_circle, outlet_circle)
    # create disk with inlet and outlet circles
    gmsh.model.occ.synchronize()
    inlet_loop = gmsh.model.occ.addCurveLoop([inlet_circle[1]])
    outlet_loop = gmsh.model.occ.addCurveLoop([outlet_circle[1]])
    disk_inlet = gmsh.model.occ.addPlaneSurface([inlet_loop])
    disk_outlet = gmsh.model.occ.addPlaneSurface([outlet_loop])
    gmsh.model.occ.synchronize()
    # find adj surface between inlet and outlet
    _, adj_lines_inlet = gmsh.model.getAdjacencies(2, disk_inlet)
    _, adj_lines_outlet = gmsh.model.getAdjacencies(2, disk_outlet)

    print(adj_lines_inlet, adj_lines_outlet)
    common_line = set(adj_lines_inlet).intersection(set(adj_lines_outlet))
    print(common_line)
    # merge all with addSurfaceLoop
    surf_loop = gmsh.model.occ.addSurfaceLoop([disk_inlet, 2, disk_outlet])
    # generate volume
    gmsh.model.occ.addVolume([surf_loop])
    gmsh.model.occ.synchronize()
    # remove old nacelle
    gmsh.model.occ.remove([(3, 1)], recursive=True)
    gmsh.model.occ.synchronize()
    # export the new engine nacelle
    # gmsh.write(os.path.join(brep_dir_path, engine_name))

    gmsh.clear()
    gmsh.finalize()


brep_dir_path = "test_files/simple_pylon_engine"

file_list = os.listdir(brep_dir_path)

for file in file_list:
    if "pylon" in file:
        reposition_engine(file[:-5], brep_dir_path)
