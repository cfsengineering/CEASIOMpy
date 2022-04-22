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
    -Engine nacelle fan cowl are not always well defined and close geometry
    -incorporate this script function to generatemesh.py



"""


# ==============================================================================
#   IMPORTS
# ==============================================================================
import gmsh
import os
import pickle
import numpy as np
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.CPACS2GMSH.func.generategmesh import AircraftPart, get_entities_from_volume

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


def close_engine(center_file, fan_file):
    """
    Function to close the engine nacelle fan by adding an inlet and outlet inside of the engine.
    Then the nacelle part are fused together to form only one engine that is saved as .brep file
    ...
    Args:
    ----------
    center_file : str
        Name of the engine nacelle center part .brep file
    fan_file : str
        Name of the engine nacelle fan part .brep file
    """
    engine_id = center_file[19:]
    print(engine_id)
    gmsh.initialize()

    # Import the part and create the aircraft part object

    fan_dimtag = gmsh.model.occ.importShapes(
        os.path.join(brep_dir_path, fan_file), highestDimOnly=True
    )
    gmsh.model.occ.healShapes(
        dimTags=[],
        tolerance=1e-8,
        fixDegenerated=True,
        fixSmallEdges=True,
        fixSmallFaces=True,
        sewFaces=True,
        makeSolids=True,
    )

    center_dimtag = gmsh.model.occ.importShapes(
        os.path.join(brep_dir_path, center_file), highestDimOnly=True
    )

    nacelle_fan = AircraftPart("nacelle_fan")
    nacelle_fan.volume = fan_dimtag
    nacelle_center = AircraftPart("nacelle_center")
    nacelle_center.volume = center_dimtag

    gmsh.model.occ.synchronize()

    # find the first point and last point x wise of the nacelle_center
    surfaces_dimtags, lines_dimtags, points_dimtags = get_entities_from_volume(
        nacelle_center.volume
    )
    nacelle_center.surfaces = surfaces_dimtags
    nacelle_center.lines = lines_dimtags
    nacelle_center.points = points_dimtags

    points_pos = [gmsh.model.occ.getBoundingBox(*dimtag) for dimtag in nacelle_center.points]
    point_x_pos = [pos[0] for pos in points_pos]

    p1 = nacelle_center.points[point_x_pos.index(min(point_x_pos))]
    p2 = nacelle_center.points[point_x_pos.index(max(point_x_pos))]
    p1_x, p1_y, p1_z, _, _, _ = gmsh.model.occ.getBoundingBox(*p1)
    p2_x, p2_y, p2_z, _, _, _ = gmsh.model.occ.getBoundingBox(*p2)
    nacelle_center_axis = [p1_x - p2_x, p1_y - p2_y, p1_z - p2_z]

    disk_inlet_center = [
        p1_x - nacelle_center_axis[0] * 0.45,
        p1_y - nacelle_center_axis[1] * 0.45,
        p1_z - nacelle_center_axis[2] * 0.45,
    ]

    bb = gmsh.model.getBoundingBox(-1, -1)
    model_dimensions = [abs(bb[0] - bb[3]), abs(bb[1] - bb[4]), abs(bb[2] - bb[5])]

    domain_length = max(model_dimensions)
    # create a cylinder from 45% to 55% of the nacelle_center to cut the nacelle volume
    disk_inlet = gmsh.model.occ.addDisk(*disk_inlet_center, domain_length, domain_length)

    disk_inlet = (2, disk_inlet)

    # generate the disk (gmsh always create a disk in the xy plane)
    xy_vector = [0, 0, 1]

    if nacelle_center_axis != xy_vector:
        rotation_axis = np.cross(nacelle_center_axis, xy_vector)
        gmsh.model.occ.rotate([disk_inlet], *disk_inlet_center, *rotation_axis, np.pi / 2)
        gmsh.model.occ.synchronize()
    cylinder = gmsh.model.occ.extrude(
        [disk_inlet],
        -nacelle_center_axis[0] * 0.1,
        -nacelle_center_axis[1] * 0.1,
        -nacelle_center_axis[2] * 0.1,
        numElements=[],
        heights=[],
        recombine=True,
    )
    gmsh.model.occ.synchronize()
    fragments_dimtag, childs_dimtag = gmsh.model.occ.fragment(
        [*fan_dimtag, *center_dimtag], [cylinder[1]]
    )
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
    gmsh.fltk.run()
    gmsh.write(os.path.join(brep_dir_path, "engine" + engine_id))

    gmsh.clear()
    gmsh.finalize()


"""
__________________________________________________
TO BE REMOVED

"""
"""
engine reposition testing
"""
# reposition of the engine nacelle
# brep_dir_path = "test_files/simple_pylon_engine"

# file_list = os.listdir(brep_dir_path)

# for file in file_list:
#     if "pylon" in file:
#         reposition_engine(file[:-5], brep_dir_path)

"""
Close the engine testing 
"""
# brep_dir_path = "test_files/converted_engine"

# file_list = os.listdir(brep_dir_path)

# close_engine("nacelle_center_cowl1_m.brep", "nacelle_fan_cowl1_m.brep")
