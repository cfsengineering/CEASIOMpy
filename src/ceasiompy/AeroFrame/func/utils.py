"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Utily functions for aeroframe.

| Author: Romain Gauthier
| Creation: 2024-06-17

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import numpy as np

from shapely.geometry import Polygon

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def poly_area(x, y):
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def compute_centroid(x_coords, y_coords):
    polygon = Polygon(zip(x_coords, y_coords))
    centroid = polygon.centroid
    return centroid.x, centroid.y


def second_moments_of_area(x, y):
    Ix = 0
    Iy = 0
    x_centr, y_centr = compute_centroid(x, y)
    x = [xi - x_centr for xi in x]
    y = [yi - y_centr for yi in y]

    n = len(x)
    for i in range(n):
        j = (i + 1) % n
        Ix += (y[i]**2 + y[i] * y[j] + y[j]**2) * (x[i] * y[j] - x[j] * y[i])
        Iy += (x[i]**2 + x[i] * x[j] + x[j]**2) * (x[i] * y[j] - x[j] * y[i])

    Ix /= 12
    Iy /= 12

    return Ix, Iy


def linear_interpolation(x1, y1, z1, x2, y2, z2, y_query):
    t = (y_query - y1) / (y2 - y1)
    interpolated_x = x1 + t * (x2 - x1)
    interpolated_z = z1 + t * (z2 - z1)
    return interpolated_x, y_query, interpolated_z


def interpolate_leading_edge_points(Xle_array, Yle_array, Zle_array, y_queries):
    interpolated_points = []
    for y_query in y_queries:
        # if y_query < Yle_array[0] - 1e-2 or y_query > Yle_array[-1] + 1e-2:
        #     raise ValueError(
        #         f"y_query value {y_query} is too far outside the range of
        #         the leading edge points.")

        if y_query < Yle_array[0]:  # Extrapolate before the first point
            interpolated_points.append(
                linear_interpolation(
                    Xle_array[0], Yle_array[0], Zle_array[0],
                    Xle_array[1], Yle_array[1], Zle_array[1],
                    y_query
                )
            )
        elif y_query > Yle_array[-1]:  # Extrapolate after the last point
            interpolated_points.append(
                linear_interpolation(
                    Xle_array[-2], Yle_array[-2], Zle_array[-2],
                    Xle_array[-1], Yle_array[-1], Zle_array[-1],
                    y_query
                )
            )
        else:
            for i in range(len(Yle_array) - 1):  # Iterate through segments
                if Yle_array[i] <= y_query <= Yle_array[i + 1]:
                    interpolated_points.append(
                        linear_interpolation(
                            Xle_array[i], Yle_array[i], Zle_array[i],
                            Xle_array[i + 1], Yle_array[i + 1], Zle_array[i + 1],
                            y_query
                        )
                    )
                    break

    return np.array(interpolated_points)
