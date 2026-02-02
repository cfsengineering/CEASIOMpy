"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Utily functions for aeroframe.

| Author: Romain Gauthier
| Creation: 2024-06-17

"""

# Imports

import math
import numpy as np

from shapely.geometry import Polygon
from typing import Any, Dict, List, Tuple, Sequence

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def compute_delta_a(row: Dict[str, Any]) -> np.ndarray:
    delta_s = row["delta_S_mapped"]
    distance_vector = row["distance_vector"]
    omega_s = row["omega_S_mapped"]
    cross_product = np.cross(distance_vector, omega_s)
    return delta_s + cross_product


def poly_area(x: Sequence[float], y: Sequence[float]) -> float:
    """Calculate the area of a polygon given x and y coordinates."""
    x = np.asarray(x)
    y = np.asarray(y)
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def compute_centroid(x_coords: Sequence[float], y_coords: Sequence[float]) -> Tuple[float, float]:
    """Compute the centroid of a polygon."""
    polygon = Polygon(zip(x_coords, y_coords))
    centroid = polygon.centroid
    return centroid.x, centroid.y


def second_moments_of_area(x: Sequence[float], y: Sequence[float]) -> Tuple[float, float]:
    """Calculate the second moments of area (Ix, Iy) for a polygon."""
    ix, iy = 0.0, 0.0
    x_centr, y_centr = compute_centroid(x, y)
    x_shifted = [xi - x_centr for xi in x]
    y_shifted = [yi - y_centr for yi in y]

    n = len(x_shifted)
    for i in range(n):
        j = (i + 1) % n
        common = x_shifted[i] * y_shifted[j] - x_shifted[j] * y_shifted[i]
        ix += (y_shifted[i] ** 2 + y_shifted[i] * y_shifted[j] + y_shifted[j] ** 2) * common
        iy += (x_shifted[i] ** 2 + x_shifted[i] * x_shifted[j] + x_shifted[j] ** 2) * common

    ix /= 12
    iy /= 12

    return ix, iy


def linear_interpolation(
    x1: float, y1: float, z1: float, x2: float, y2: float, z2: float, y_query: float
) -> Tuple[float, float, float]:
    """Linearly interpolate (x, z) at a given y_query between two points."""
    if y2 == y1:
        raise ValueError("y1 and y2 cannot be the same value for interpolation.")
    t = (y_query - y1) / (y2 - y1)
    interpolated_x = x1 + t * (x2 - x1)
    interpolated_z = z1 + t * (z2 - z1)
    return interpolated_x, y_query, interpolated_z


def interpolate_leading_edge_points(
    xle_array: Sequence[float],
    yle_array: Sequence[float],
    zle_array: Sequence[float],
    y_queries: Sequence[float],
) -> np.ndarray:
    """Interpolate or extrapolate leading edge points at given y locations."""
    interpolated_points: List[Tuple[float, float, float]] = []
    for y_query in y_queries:
        if y_query < yle_array[0]:  # Extrapolate before the first point
            interpolated_points.append(
                linear_interpolation(
                    xle_array[0],
                    yle_array[0],
                    zle_array[0],
                    xle_array[1],
                    yle_array[1],
                    zle_array[1],
                    y_query,
                )
            )
        elif y_query > yle_array[-1]:  # Extrapolate after the last point
            interpolated_points.append(
                linear_interpolation(
                    xle_array[-2],
                    yle_array[-2],
                    zle_array[-2],
                    xle_array[-1],
                    yle_array[-1],
                    zle_array[-1],
                    y_query,
                )
            )
        else:
            for i in range(len(yle_array) - 1):  # Iterate through segments
                if yle_array[i] <= y_query <= yle_array[i + 1]:
                    interpolated_points.append(
                        linear_interpolation(
                            xle_array[i],
                            yle_array[i],
                            zle_array[i],
                            xle_array[i + 1],
                            yle_array[i + 1],
                            zle_array[i + 1],
                            y_query,
                        )
                    )
                    break

    return np.array(interpolated_points)


def calculate_angle(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    cos_theta = dot_product / (norm_v1 * norm_v2)
    angle = np.arccos(cos_theta)

    if math.isnan(angle):
        angle = 0

    return np.degrees(angle)
