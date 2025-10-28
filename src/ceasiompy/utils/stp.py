# =================================================================================================
#    IMPORTS
# =================================================================================================

from pathlib import Path
from cpacspy.cpacspy import AeroMap

from OCC.Core.Bnd import Bnd_Box
from OCC.Core.GProp import GProp_GProps
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.STEPControl import STEPControl_Reader

from typing import (
    List,
    Final,
)

from ceasiompy import log
from OCC.Core.BRepBndLib import brepbndlib_Add
from OCC.Core.BRepGProp import brepgprop_SurfaceProperties

# =================================================================================================
#    CLASSES
# =================================================================================================


class STP:
    def __init__(self: "STP", stp_path: Path) -> None:
        #
        self.stp_path: Final[Path] = stp_path

        # Attributes deduced from geometry path
        self.name: Final[str] = stp_path.name
        self.aeromaps: List[AeroMap] = []

        self.shape: Final[TopoDS_Shape] = self._get_step()
        self.area: Final[float] = self._compute_area()
        self.bounding_box: Final[dict] = self._compute_bounding_box()

        self.span: float = self.bounding_box["length_y"]
        self.area_wing: float = self.area / 10.0
        self.reference_chord: float = self.area_wing / self.span

    def _get_step(self: "STP") -> TopoDS_Shape:
        reader = STEPControl_Reader()
        path_str = f'{self.stp_path}'
        status = reader.ReadFile(path_str)
        if status != 1:
            raise RuntimeError(f"Failed to read STEP: {path_str=} ({status=})")
        reader.TransferRoots()
        return reader.OneShape()

    def _compute_area(self: "STP") -> float:
        props = GProp_GProps()
        brepgprop_SurfaceProperties(self.shape, props)  # computes surface properties
        return props.Mass()  # for surface props, Mass() returns area

    def _compute_bounding_box(self: "STP") -> dict:
        box = Bnd_Box()
        brepbndlib_Add(self.shape, box)
        xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
        length_x, length_y, length_z = xmax - xmin, ymax - ymin, zmax - zmin
        if length_x == 0.0 or length_y == 0.0 or length_z == 0.0:
            raise ValueError("Could not assess the dimensions of the geometry.")

        return dict(
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
            zmin=zmin,
            zmax=zmax,
            length_x=length_x,
            length_y=length_y,
            length_z=length_z,
        )

    def create_aeromap(
        self: "STP",
        new_aeromap_uid: str,
    ) -> AeroMap:
        new_aeromap = AeroMap(
            tixi=None,
            uid=new_aeromap_uid,
            create_new=True,
        )
        self.aeromaps.append(new_aeromap)
        return new_aeromap

    def remove_aeromap(
        self: "STP",
        aeromap_uid: str,
    ) -> None:
        for aeromap in self.aeromaps:
            if aeromap.uid == aeromap_uid:
                self.aeromaps.pop(aeromap)
                log.info(f"Removed {aeromap_uid=}")
                return None

    def get_aeromap_by_uid(
        self: "STP",
        aeromap_uid: str,
    ) -> AeroMap:
        for aeromap in self.aeromaps:
            if aeromap.uid == aeromap_uid:
                return aeromap

    def get_aeromaps_uid(self: "STP") -> List[str]:
        aeromap_uids: List[str] = []
        for aeromap in self.aeromaps:
            aeromap_uids.append(aeromap.uid)

        return aeromap_uids

    def get_fuselage_size(self: "STP") -> tuple[float, float]:
        plane_yz = self.bounding_box["length_y"] * self.bounding_box["length_z"]
        return plane_yz / 10.0, plane_yz / 100.0

    def get_wing_size(self: "STP") -> tuple[float, float]:
        return 0.15 * self.reference_chord, 0.08 * self.span
