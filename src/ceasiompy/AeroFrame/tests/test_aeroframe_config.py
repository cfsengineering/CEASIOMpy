"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions ModuleTemplate module.

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import tempfile
import numpy as np

from ceasiompy.utils.decorators import log_test
from ceasiompy.AeroFrame.func.config import (
    poly_area,
    interpolate_leading_edge,
    compute_distance_and_moment,
)

from pathlib import Path
from unittest import main
from pandas import DataFrame
from ceasiompy.utils.ceasiompytest import CeasiompyTest


# =================================================================================================
#   CLASSES
# =================================================================================================


class TestAeroFrame(CeasiompyTest):

    @log_test
    def test_poly_area(self):
        # Unit square
        x = [0, 1, 1, 0]
        y = [0, 0, 1, 1]
        self.assertAlmostEqual(poly_area(x, y), 1.0)
        # Right triangle
        x = [0, 1, 0]
        y = [0, 0, 1]
        self.assertAlmostEqual(poly_area(x, y), 0.5)
        # Line (degenerate case)
        x = [0, 1]
        y = [0, 0]
        self.assertAlmostEqual(poly_area(x, y), 0.0)

    @log_test
    def test_interpolate_leading_edge(self) -> None:
        # Create a minimal AVL file with two Xle entries
        avl_content = """
            SURFACE
            Xle
            0.0 0.0 0.0
            Xle
            1.0 1.0 1.0
            """
        with tempfile.TemporaryDirectory() as tmpdir:
            avl_path = Path(tmpdir) / "test.avl"
            with open(avl_path, "w") as f:
                f.write(avl_content)
            wg_origin = [0.0, 0.0, 0.0]
            wg_scaling = [1.0, 1.0, 1.0]
            y_queries = [0.0, 0.5, 1.0]
            n_iter = 1
            # Call the function
            (
                xle_array,
                yle_array,
                zle_array,
                interpolated_xle,
                interpolated_yle,
                interpolated_zle,
            ) = interpolate_leading_edge(
                avl_path, tmpdir, wg_origin, wg_scaling, y_queries, n_iter
            )
            # Check original arrays
            np.testing.assert_array_almost_equal(xle_array, [0.0, 1.0])
            np.testing.assert_array_almost_equal(yle_array, [0.0, 1.0])
            np.testing.assert_array_almost_equal(zle_array, [0.0, 1.0])
            # Check interpolation at y=0.5 is (0.5, 0.5, 0.5)
            idx = y_queries.index(0.5)
            self.assertAlmostEqual(interpolated_xle[idx], 0.5)
            self.assertAlmostEqual(interpolated_yle[idx], 0.5)
            self.assertAlmostEqual(interpolated_zle[idx], 0.5)

    @log_test
    def test_compute_distance_and_moment(self) -> None:
        # Create a simple centerline DataFrame
        centerline_df = DataFrame({"x": [0.0, 1.0], "y": [0.0, 0.0], "z": [0.0, 0.0]})
        # Row with closest_centerline_index = 1, point at (2,0,0), force (0,1,0)
        row = {
            "x": 2.0,
            "y": 0.0,
            "z": 0.0,
            "Fx": 0.0,
            "Fy": 1.0,
            "Fz": 0.0,
            "closest_centerline_index": 1,
        }
        result = compute_distance_and_moment(centerline_df, row)
        # distance_vector should be (1,0,0)
        np.testing.assert_array_almost_equal(result["distance_vector"], [1.0, 0.0, 0.0])
        # moment = distance x force = (1,0,0) x (0,1,0) = (0,0,1)
        self.assertAlmostEqual(result["moment_x"], 0.0)
        self.assertAlmostEqual(result["moment_y"], 0.0)
        self.assertAlmostEqual(result["moment_z"], 1.0)


# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
