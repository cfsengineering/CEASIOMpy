# Imports

from dataclasses import (
    field,
    dataclass,
)

from pydantic import BaseModel
from ceasiompy.cpacs2gmsh.utility.utils import PartType


# Classes

class FuseEntry(BaseModel):
    name: str
    dimtag: tuple[int, int]
    part_type: PartType


@dataclass
class SurfacePart:
    uid: str
    part_type: PartType
    volume: tuple[int, int]
    surfaces: list[tuple[int, int]] = field(default_factory=list)
    surfaces_tags: list[int] = field(default_factory=list)
    lines: list[tuple[int, int]] = field(default_factory=list)
    lines_tags: list[int] = field(default_factory=list)
    points: list[tuple[int, int]] = field(default_factory=list)
    points_tags: list[int] = field(default_factory=list)
    wing_sections: list[dict] = field(default_factory=list)
    mesh_size: float = 0.0
