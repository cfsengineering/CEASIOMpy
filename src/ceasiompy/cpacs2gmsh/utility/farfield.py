# Imports

from typing import Final

# Constants

EDGES: Final[list[tuple[float, float]]] = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    ]


# Functions
def box_edges(
    x_min: float,
    y_min: float,
    z_min: float,
    x_max: float,
    y_max: float,
    z_max: float,
    symmetry: bool,
) -> tuple[list[float | None], list[float | None], list[float | None]]:
    if symmetry:
        y_min = 0.0

    corners = [
        (x_min, y_min, z_min),
        (x_max, y_min, z_min),
        (x_max, y_max, z_min),
        (x_min, y_max, z_min),
        (x_min, y_min, z_max),
        (x_max, y_min, z_max),
        (x_max, y_max, z_max),
        (x_min, y_max, z_max),
    ]
    edges = EDGES

    x_coords, y_coords, z_coords = [], [], []
    for start, end in edges:
        x_coords.extend([corners[start][0], corners[end][0], None])
        y_coords.extend([corners[start][1], corners[end][1], None])
        z_coords.extend([corners[start][2], corners[end][2], None])

    return x_coords, y_coords, z_coords
