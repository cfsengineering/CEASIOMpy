"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions and constants for CPACS2GMSH module.
"""

# Futures

from __future__ import annotations

# Imports
import gmsh
import tempfile

import numpy as np

from cpacspy.cpacsfunctions import get_value
from tigl3.import_export_helper import export_shapes
from ceasiompy.utils.ceasiompyutils import is_symmetric

from enum import StrEnum
from pathlib import Path
from typing import TypeAlias
from pydantic import BaseModel
from cpacspy.cpacspy import CPACS
from tixi3.tixi3wrapper import Tixi3
from tigl3.geometry import CNamedShape
from OCC.Core.TopoDS import TopoDS_Shape
from ceasiompy.utils.configfiles import ConfigFile

from ceasiompy import log
from ceasiompy.cpacs2gmsh import (
    GMSH_AUTO_REFINE_XPATH,
    GMSH_N_POWER_FACTOR_XPATH,
    GMSH_N_POWER_FIELD_XPATH,
    GMSH_MESH_SIZE_PYLON_XPATH,
    GMSH_MESH_SIZE_FUSELAGE_XPATH,
    GMSH_MESH_SIZE_WING_XPATH,
    GMSH_REFINE_FACTOR_XPATH,
    GMSH_REFINE_TRUNCATED_XPATH,
    GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH,
    GMSH_ADD_BOUNDARY_LAYER_XPATH,
    GMSH_NUMBER_LAYER_XPATH,
    GMSH_H_FIRST_LAYER_XPATH,
    GMSH_MAX_THICKNESS_LAYER_XPATH,
    GMSH_GROWTH_FACTOR_XPATH,
    GMSH_GROWTH_RATIO_XPATH,
    GMSH_FEATURE_ANGLE_XPATH,
    GMSH_MESH_SIZE_FARFIELD_XPATH,
    GMSH_Y_LENGTH_XPATH,
    GMSH_Z_LENGTH_XPATH,
    GMSH_WAKE_LENGTH_XPATH,
    GMSH_UPSTREAM_LENGTH_XPATH,
)
from ceasiompy.utils.commonxpaths import (
    WINGS_XPATH,
    PYLONS_XPATH,
    FUSELAGES_XPATH,
)


# =================================================================================================
#   CONSTANTS
# =================================================================================================

# Define mesh color for GMSH, only use in GUI (red, green, blue, brightness)
MESH_COLORS = {
    "farfield": (255, 200, 0, 100),
    "symmetry": (153, 255, 255, 100),
    "wing": (0, 200, 200, 100),
    "fuselage": (255, 215, 0, 100),
    "pylon": (255, 15, 255, 100),
    "engine": (127, 0, 255, 100),
    "rotor": (0, 0, 0, 100),
    "bad_surface": (255, 0, 0, 255),
    "good_surface": (0, 255, 0, 100),
}


def _import_geom(geom: CNamedShape | TopoDS_Shape) -> list[tuple[int, int]]:
    """Returns: [(dim1, tag1), (dim2, tag2), ...], where,
    
    dim = topological dimension (0 point, 1 curve, 2 surface, 3 volume)
    tag = gmsh ID for that entity in the OCC model

    """
    geom = _extract_topods(geom)
    with tempfile.TemporaryDirectory(prefix="ceasiompy_occ_") as tmpdir:
        brep_path = Path(tmpdir) / "shape.brep"
        export_shapes([geom], str(brep_path))
        shape = gmsh.model.occ.importShapes(str(brep_path), highestDimOnly=False)
        gmsh.model.occ.synchronize()

    if not shape:
        raise RuntimeError(f"Failed to import {geom=} into gmsh OpenCASCADE model.")

    return shape


def _extract_topods(geom: CNamedShape | TopoDS_Shape) -> TopoDS_Shape:
    if isinstance(geom, CNamedShape):
        return geom.shape()

    if isinstance(geom, TopoDS_Shape):
        return geom

    raise TypeError(f"Unsupported geometry type: {type(geom)}")


def _get_bounding_box(volume_tag: int, bbox_margin: float) -> list[float]:
    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.occ.getBoundingBox(3, volume_tag)
    return [
        xmin - bbox_margin, ymin - bbox_margin,
        zmin - bbox_margin, xmax + bbox_margin,
        ymax + bbox_margin, zmax + bbox_margin,
    ]


# Types

BoundingBox: TypeAlias = tuple[float, float, float, float, float, float]

# Classes

class PartType(StrEnum):
    wing = "wing"
    pylon = "pylon"
    fuselage = "fuselage"


class Geometry:
    bbox_margin = 0.01
    def __init__(
        self: Geometry,
        uid: str,
        geom: CNamedShape | TopoDS_Shape,
    ) -> None:
        self.uid = uid
        self.ref_geom = _extract_topods(geom)
        self.ref_shape = _import_geom(self.ref_geom)

        # Volume
        self._update_volume_tag()

    def _update_volume_tag(self: Geometry) -> list[int]:
        dimtags_volumes: list[tuple[int, int]] = [dt for dt in self.ref_shape if dt[0] == 3]
        if not dimtags_volumes or len(dimtags_volumes) == 0 or len(dimtags_volumes) > 1:
            raise RuntimeError(f"""Imported {len(dimtags_volumes)=} entities.
                Imported dimTags: {self.ref_shape}. There should be exactly 1 Volume.""")

        self.ref_volume_tag = dimtags_volumes[0][1]
        self.ref_bounding_box = _get_bounding_box(
            volume_tag=self.ref_volume_tag,
            bbox_margin=self.bbox_margin,
        )

    def _update_surface_tags(self: Geometry) -> list[int]:
        surfaces_dimtags = gmsh.model.getEntitiesInBoundingBox(*self.ref_bounding_box, 2)
        self.ref_surface_tags = [tag for _, tag in surfaces_dimtags]


class AircraftGeometry:
    def __init__(
        self: AircraftGeometry,
        wing_geoms: list[Geometry],
        pylon_geoms: list[Geometry],
        fuselage_geoms: list[Geometry],
    ) -> None:
        self.wing_geoms = wing_geoms
        self.pylon_geoms = pylon_geoms
        self.fuselage_geoms = fuselage_geoms

        self.all_geoms: list[Geometry] = self.wing_geoms + self.pylon_geoms + self.fuselage_geoms


class MeshSettings(BaseModel):
    symmetry: bool
    add_boundary_layer: bool

    wing_mesh_size: dict[str, float]
    pylon_mesh_size: dict[str, float]
    fuselage_mesh_size: dict[str, float]


class FarfieldSettings(BaseModel):
    y_length: float
    z_length: float
    wake_length: float
    upstream_length: float

    farfield_mesh_size: float
    

# Functions

def _get_mesh_size_by_uid(
    tixi: Tixi3,
    components_xpath: str,
    component_name: str,
    mesh_size_xpath: str,
) -> dict[str, float]:
    """Read mesh-size values stored at `<mesh_size_xpath>/<part_uid>`."""
    mesh_sizes: dict[str, float] = {}

    if not tixi.checkElement(components_xpath):
        return mesh_sizes

    component_count = tixi.getNamedChildrenCount(components_xpath, component_name)
    for i_comp in range(component_count):
        component_xpath = f"{components_xpath}/{component_name}[{i_comp + 1}]"
        component_uid = tixi.getTextAttribute(component_xpath, "uID")
        value_xpath = f"{mesh_size_xpath}/{component_uid}"

        if not tixi.checkElement(value_xpath):
            continue

        mesh_sizes[component_uid] = float(get_value(tixi, value_xpath))

    return mesh_sizes


def process_gmsh_log(gmsh_log: list[str]) -> None:
    """
    Function to process the gmsh log file.
    It is used to retrieve the mesh quality
    and the time needed to mesh the model
    """

    # Find last logs about mesh quality
    quality_log = [log for log in gmsh_log if "< quality <" in log]
    final_quality_log = quality_log[-10:]

    log.info("Final mesh quality :")
    for log_line in final_quality_log:
        log.info(log_line)

    total_time = 0
    time_log = [log for log in gmsh_log if "CPU" in log]
    for message in time_log:
        total_time += float(message.split("CPU")[1].split("s")[0])

    log.info(f"Total meshing time : {round(total_time, 2)}s")


def get_farfield_settings(tixi: Tixi3) -> FarfieldSettings:
    return FarfieldSettings(
        y_length=get_value(tixi, xpath=GMSH_Y_LENGTH_XPATH),
        z_length=get_value(tixi, xpath=GMSH_Z_LENGTH_XPATH),
        wake_length=get_value(tixi, xpath=GMSH_WAKE_LENGTH_XPATH),
        upstream_length=get_value(tixi, xpath=GMSH_UPSTREAM_LENGTH_XPATH),

        farfield_mesh_size=get_value(tixi, xpath=GMSH_MESH_SIZE_FARFIELD_XPATH),
    )


def get_2d_mesh_settings(cpacs: CPACS) -> MeshSettings:
    """
    Returns input values from CEASIOMpy's GUI interface.
    Note: This function is only used for 3D mesh generation.
    """
    tixi = cpacs.tixi
    # Retrieve value from the GUI Setting
    mesh_settings = MeshSettings(
        symmetry=is_symmetric(cpacs),
        add_boundary_layer=get_value(tixi, GMSH_ADD_BOUNDARY_LAYER_XPATH),

        # Set Mesh Sizes
        wing_mesh_size=_get_mesh_size_by_uid(
            tixi=tixi,
            components_xpath=WINGS_XPATH,
            component_name="wing",
            mesh_size_xpath=GMSH_MESH_SIZE_WING_XPATH,
        ),
        pylon_mesh_size=_get_mesh_size_by_uid(
            tixi=tixi,
            components_xpath=PYLONS_XPATH,
            component_name="enginePylon",
            mesh_size_xpath=GMSH_MESH_SIZE_PYLON_XPATH,
        ),
        fuselage_mesh_size=_get_mesh_size_by_uid(
            tixi=tixi,
            components_xpath=FUSELAGES_XPATH,
            component_name="fuselage",
            mesh_size_xpath=GMSH_MESH_SIZE_FUSELAGE_XPATH,
        ),
    )

    n_power_field = get_value(tixi, GMSH_N_POWER_FIELD_XPATH)
    n_power_factor = get_value(tixi, GMSH_N_POWER_FACTOR_XPATH)

    refine_factor = get_value(tixi, GMSH_REFINE_FACTOR_XPATH)
    refine_truncated = get_value(tixi, GMSH_REFINE_TRUNCATED_XPATH)

    auto_refine = get_value(tixi, GMSH_AUTO_REFINE_XPATH)

    return mesh_settings


def cfg_rotors(brep_dir: Path) -> bool:
    rotor_model = False
    if Path(brep_dir, "config_rotors.cfg").exists():
        rotor_model = True

        log.info("Adding disk actuator")
        config_file = ConfigFile(Path(brep_dir, "config_rotors.cfg"))

        add_disk_actuator(brep_dir, config_file)

    return rotor_model


def add_disk_actuator(brep_dir: Path, config_file: ConfigFile):
    """
    Creates a 2D disk in a given location to represent a rotor as a disk actuator.

    Args:
        brep_dir (Path): brep files of the aircraft that contains the rotor config file.
        config_file (Configfile): Propellers configuration on the aircraft.

    """

    nb_rotor = int(config_file["NB_ROTOR"])

    for k in range(1, nb_rotor + 1):
        # get the rotor configuration from cfg file
        rotor_uid = config_file[f"UID_{k}"]
        radius = float(config_file[f"{rotor_uid}_ROTOR_RADIUS"])
        sym = int(config_file[f"{rotor_uid}_SYMMETRIC"])
        trans_vector = (
            float(config_file[f"{rotor_uid}_TRANS_X"]),
            float(config_file[f"{rotor_uid}_TRANS_Y"]),
            float(config_file[f"{rotor_uid}_TRANS_Z"]),
        )
        rot_vector = (
            float(config_file[f"{rotor_uid}_ROT_X"]),
            float(config_file[f"{rotor_uid}_ROT_Y"]),
            float(config_file[f"{rotor_uid}_ROT_Z"]),
        )

        # Adding rotating disk
        gmsh.initialize()
        # generate the inlet_disk (gmsh always create a disk in the xy plane)
        disk_tag = gmsh.model.occ.addDisk(*trans_vector, radius, radius)
        disk_dimtag = (2, disk_tag)

        # y axis 180deg flip to make the inlet of the disk face forward
        gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 0, 1, 0, np.radians(180))
        gmsh.model.occ.synchronize()

        # rotation given in the cpacs file
        gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 1, 0, 0, np.radians(rot_vector[0]))
        # y axis
        gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 0, 1, 0, np.radians(rot_vector[1]))
        # z axis
        gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 0, 0, 1, np.radians(rot_vector[2]))

        gmsh.model.occ.synchronize()

        path_disk = Path(brep_dir, f"{rotor_uid}.brep")
        gmsh.write(str(path_disk))

        gmsh.clear()
        gmsh.finalize()

        if sym == 2:
            # Adding the symmetric
            gmsh.initialize()
            # generate the inlet_disk (gmsh always create a disk in the xy plane)
            disk_tag = gmsh.model.occ.addDisk(*trans_vector, radius, radius)
            disk_dimtag = (2, disk_tag)

            # y axis 180deg flip to make the inlet of the disk face forward is not necessary for
            # the mirrored part, and for now the symmetry is not implemented correctly since
            # the symmetry does not take into account the orientation of the rotor and the plane
            # of symmetry is assume to be the xz plane
            # When the face of the disk actuator are not oriented well the simulation shows
            # increasing cd and will probably diverge

            # rotation given in the cpacs file
            gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 1, 0, 0, np.radians(rot_vector[0]))
            # y axis
            gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 0, 1, 0, np.radians(rot_vector[1]))
            # z axis
            gmsh.model.occ.rotate([disk_dimtag], *trans_vector, 0, 0, 1, np.radians(rot_vector[2]))

            gmsh.model.occ.synchronize()

            gmsh.model.occ.mirror([disk_dimtag], 0, 1, 0, 0)
            gmsh.model.occ.synchronize()
            path_disk = Path(brep_dir, f"{rotor_uid}_mirrored.brep")
            gmsh.write(str(path_disk))

            gmsh.clear()
            gmsh.finalize()


def write_gmsh(results_dir: str, file: str) -> Path:
    su2mesh_path = Path(results_dir, file)
    gmsh.write(str(su2mesh_path))
    return Path(su2mesh_path)


def initialize_gmsh() -> None:
    # Reset any stale model so each run starts clean.
    # Avoid finalize() here: re-finalizing/re-initializing in embedded runtimes can be unstable.
    if gmsh.isInitialized():
        gmsh.clear()
    else:
        gmsh.initialize()
        gmsh.clear()

    # Stop gmsh output log in the terminal
    gmsh.option.setNumber("General.Terminal", 0)
    # Log complexity
    gmsh.option.setNumber("General.Verbosity", 5)


# 

class BoundaryLayerSettings(BaseModel):
    n_layer: int
    max_layer_thickness: float
    
    growth_ratio: float
    growth_factor: float
    
    h_first_layer: float
    
    feature_angle: float
    refine_factor_angled_lines: float

    height_itrations: int = 8
    normal_iterations: int = 8
    max_crit_iterations: int = 128
    laplace_iterations: int = 8


def retrieve_rans_gui_values(tixi: Tixi3):
    return BoundaryLayerSettings(
        n_layer=get_value(tixi, GMSH_NUMBER_LAYER_XPATH),
        growth_ratio=get_value(tixi, GMSH_GROWTH_RATIO_XPATH),
        h_first_layer=get_value(tixi, GMSH_H_FIRST_LAYER_XPATH),
        growth_factor=get_value(tixi, GMSH_GROWTH_FACTOR_XPATH),
        feature_angle=get_value(tixi, GMSH_FEATURE_ANGLE_XPATH),
        max_layer_thickness=get_value(tixi, GMSH_MAX_THICKNESS_LAYER_XPATH),
        refine_factor_angled_lines=get_value(tixi, GMSH_REFINE_FACTOR_ANGLED_LINES_XPATH),
    )
