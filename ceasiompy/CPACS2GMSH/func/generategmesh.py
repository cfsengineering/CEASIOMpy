"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Use .brep files parts of an airplane to generate a fused airplane in GMSH with
the OCC kernel. Then Spherical farfield is created arround the airplane and the
resulting domain is meshed using gmsh

Python version: >=3.7

| Author: Tony Govoni
| Creation: 2022-03-22

TODO:

    -

"""


# ==============================================================================
#   IMPORTS
# ==============================================================================
import gmsh
import os
import warnings
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])


# ==============================================================================
#   CLASSES
# ==============================================================================
class Part_airplane:
    """
    A class to represent part of the airplane in order to keep track of each gmsh
    part entities and their location in space

    For each Part_airplane, its surfaces,lines and points locations are stored
    in order to remap them correctly when gmsh boolean operations are performed
    ...

    Attributes
    ----------
    dim_tag : tuple
        tuple (dim,tag) is the dim and tag of the gmsh volume of the airplane part
    name : str
        name of the part which correspond to its .brep file name
    """

    def __init__(self, dim_tag, name):
        self.dim_tag = dim_tag
        self.name = name
        self.bb, self.sizes = get_visual_bounding_box(self.dim_tag)
        self.points = []
        self.lines = []
        self.surfaces = []

    def get_entities(self):
        """
        Function to grab the points,lines and surfaces entites of the part
        ...
        """

        self.points = set(gmsh.model.getEntitiesInBoundingBox(*self.bb, dim=0))
        self.lines = set(gmsh.model.getEntitiesInBoundingBox(*self.bb, dim=1))
        self.surfaces = set(gmsh.model.getEntitiesInBoundingBox(*self.bb, dim=2))


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def generategmesh(brep_dir_path, results_dir, UI_gmsh=False):
    """Function to generate a mesh from brep files forming an airplane

    Function 'generategmesh' is a subfunction of CPACS2GMSH which return a
    mesh file.
    The airplane is fused with the different brep files : fuselage, wings and
    other parts are identified anf fused together, then a farfield is generated
    and the airplane is substracted to him to generate the final fluid domain
    marker of each airplane part and farfield surfaces is reported in the mesh
    file.

    Args:
        brep_dir_path (path):  Path to the directory containing the brep files

    .. warning:
        Unmatching number of entities in the current model : This warning
        indcate that something went wrong during the remapping process,
        either surfaces,lines or points get duplicated or are missing.
        This is likely to result in corrupted marker in the mesh file.

    """

    gmsh.initialize()
    airplane_parts = []
    for file in os.listdir(brep_dir_path):
        if ".brep" in file:
            log.info(f"Importing :{file[:-5]}")
            part = gmsh.model.occ.importShapes(
                os.path.join(brep_dir_path, file), highestDimOnly=True
            )
            gmsh.model.occ.synchronize()
            part_obj = Part_airplane(*part, file[:-5])
            gmsh.model.occ.synchronize()
            airplane_parts.append(part_obj)

    # Fuse operation
    part_to_fuse = [part.dim_tag for part in airplane_parts]
    log.info(f"Start Fusing process, {len(part_to_fuse)} parts to fuse")
    # return the [dim_tag] of the fused airplane volume
    airplane, side = gmsh.model.occ.fuse(
        [part_to_fuse[0]], part_to_fuse[1:], removeObject=True, removeTool=True
    )
    gmsh.model.occ.synchronize()

    # store the entites forming by the fusion of the plane
    airplane_points = gmsh.model.getEntities(dim=0)
    airplane_lines = gmsh.model.getEntities(dim=1)
    airplane_surfaces = gmsh.model.getEntities(dim=2)

    # find airplane bounding box
    airplane_bb, airplane_sizes = get_visual_bounding_box(*airplane)

    # create external domain for the farfield
    center_airplane = (
        airplane_bb[0] + 0.5 * airplane_sizes[0],
        airplane_bb[1] + 0.5 * airplane_sizes[1],
        airplane_bb[2] + 0.5 * airplane_sizes[2],
    )

    ext_domain = gmsh.model.occ.addSphere(*center_airplane, 5 * max(airplane_sizes))
    gmsh.model.occ.synchronize()

    # cut the fluid with the airplane
    final_domain, side = gmsh.model.occ.cut(
        [(3, ext_domain)],
        [*airplane],
        removeObject=True,
        removeTool=True,
    )
    gmsh.model.occ.synchronize()

    # remap entities to their originial part
    for part in airplane_parts:
        part.get_entities()
        # log.info(part.name, ":\n")
        # log.info("points", part.points, "\n")
        # log.info("lines", part.lines, "\n")
        # log.info("surf", part.surfaces, "\n\n")

    """
    In general when a wing is fused to the fuselage ,some points and lines are in both fuselage and wing entities list
    by conventions, those points and lines will be removed of the fuselage part and left to the wings one

    """
    wings_parts = [part for part in airplane_parts if "wing" in part.name]
    fuselage = [part for part in airplane_parts if "fuselage" in part.name]
    # normally there is only one fuselage
    fuselage = fuselage[0]
    twin_points = set.union(*[fuselage.points & wings_part.points for wings_part in wings_parts])
    twin_lines = set.union(*[fuselage.lines & wings_part.lines for wings_part in wings_parts])
    twin_surfaces = set.union(
        *[fuselage.surfaces & wings_part.surfaces for wings_part in wings_parts]
    )
    # log.info("twin points", twin_points, "\n")
    # log.info("twin lines", twin_lines, "\n")
    # log.info("twin surfaces", twin_surfaces, "\n\n")

    fuselage.points = fuselage.points.difference(twin_points)
    fuselage.lines = fuselage.lines.difference(twin_lines)
    fuselage.surfaces = fuselage.surfaces.difference(twin_surfaces)

    # check sum:
    check_points = sum([len(part.points) for part in airplane_parts])
    check_lines = sum([len(part.lines) for part in airplane_parts])
    check_surfaces = sum([len(part.surfaces) for part in airplane_parts])

    if (
        (len(airplane_points) != check_points)
        or (len(airplane_lines) != check_lines)
        or (len(airplane_surfaces) != check_surfaces)
    ):
        warnings.warn("Unmatching number of entities in the current model", DeprecationWarning)
    else:
        log.info("Remaping of the airplane parts as been successfull")

    # log.info("Fuselage correction :\n")
    # log.info("fuselage points", fuselage.points, "\n")
    # log.info("fuselage lines", fuselage.lines, "\n")
    # log.info("fuselage surf", fuselage.surfaces, "\n\n")

    # Reform the new airplane entities set with the corrected parts set :
    airplane_points = set.union(*[part.points for part in airplane_parts])
    airplane_lines = set.union(*[part.lines for part in airplane_parts])
    airplane_surfaces = set.union(*[part.surfaces for part in airplane_parts])

    # remap the entities of the farfield:
    final_domain_points = gmsh.model.getEntities(dim=0)
    final_domain_lines = gmsh.model.getEntities(dim=1)
    final_domain_surfaces = gmsh.model.getEntities(dim=2)
    # find the entites belonging to the farfield
    farfield_points = set([point for point in final_domain_points if point not in airplane_points])
    farfield_lines = set([line for line in final_domain_lines if line not in airplane_lines])
    farfield_surfaces = set(
        [surface for surface in final_domain_surfaces if surface not in airplane_surfaces]
    )

    # check sum number 2 n:
    check_points = len(airplane_points) + len(farfield_points)
    check_lines = len(airplane_lines) + len(farfield_lines)
    check_surfaces = len(airplane_surfaces) + len(farfield_surfaces)

    if (
        (len(final_domain_points) != check_points)
        or (len(final_domain_lines) != check_lines)
        or (len(final_domain_surfaces) != check_surfaces)
    ):
        raise ValueError("Unmatching number of entities in the current model")
    else:
        log.info("Remaping of the external domain as been successfull")

    gmsh.model.occ.synchronize()
    # Form physical groups

    # get the tags list
    airplane_surfaces_tags = [surface[1] for surface in airplane_surfaces]
    farfield_surfaces_tags = [surface[1] for surface in farfield_surfaces]
    # Form physical groups
    bc_airplane = gmsh.model.addPhysicalGroup(2, airplane_surfaces_tags)
    gmsh.model.setPhysicalName(2, bc_airplane, "airfoil")

    farfield = gmsh.model.addPhysicalGroup(2, farfield_surfaces_tags)
    gmsh.model.setPhysicalName(2, farfield, "farfield")

    ps = gmsh.model.addPhysicalGroup(3, [final_domain[0][1]])
    gmsh.model.setPhysicalName(3, ps, "fluid")

    gmsh.model.occ.synchronize()

    for part in airplane_parts:
        if "wing" in part.name:
            gmsh.model.mesh.setSize(list(part.points), 0.5)
        if "fuselage" in part.name:
            gmsh.model.mesh.setSize(list(part.points), 0.5)

    gmsh.model.mesh.setSize(list(farfield_points), 10)
    gmsh.model.occ.synchronize()
    gmsh.model.mesh.generate(1)
    gmsh.model.mesh.generate(2)
    if UI_gmsh:
        log.info("Result of 2D surface mesh")
        gmsh.fltk.run()
    gmsh.model.mesh.generate(3)
    gmsh.model.occ.synchronize()
    if UI_gmsh:
        log.info("Result of the 3D mesh")
        gmsh.fltk.run()
    gmsh.write(os.path.join(results_dir, "mesh.su2"))
    gmsh.finalize()


def get_visual_bounding_box(dim_tag):
    """
    Function to find the bounding box (bb) of a gmsh object
    The bounding box is extend by a fraction of its size in order to prevent
    non detection of entites on the boundary of the original bb
    ...

    Args:
    ----------
    dim_tag : tuple
        tuple (dim,tag) is the dim and tag of the gmsh volume of the airplane part
    name : str
        name of the part which correspond to its .brep file name
    ...

    Return :
    ----------
    bb : tuple
        tuple containing the bottom right and top left location of the bb
    size : tuple
        tuple  containing the size of the bb in each dimention
    """

    bb = list(gmsh.model.getBoundingBox(*dim_tag))
    size_x = abs(bb[0] - bb[3])
    size_y = abs(bb[1] - bb[4])
    size_z = abs(bb[2] - bb[5])
    # extend a bit the bounding_box
    bb[0] = bb[0] - 1e-3 * size_x
    bb[1] = bb[1] - 1e-3 * size_y
    bb[2] = bb[2] - 1e-3 * size_z
    bb[3] = bb[3] + 1e-3 * size_x
    bb[4] = bb[4] + 1e-3 * size_y
    bb[5] = bb[5] + 1e-3 * size_z
    # update size due to the extend
    size_x = abs(bb[0] - bb[3])
    size_y = abs(bb[1] - bb[4])
    size_z = abs(bb[2] - bb[5])

    return (bb[0], bb[1], bb[2], bb[3], bb[4], bb[5]), (size_x, size_y, size_z)


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
