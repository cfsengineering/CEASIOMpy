"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import unittest
import numpy as np

from unittest import main
from unittest.mock import MagicMock

from ceasiompy.utils.WB.ConvGeometry.Fuselage.fusegeom import (
    fuselage_check_segment_connection,
    rel_dist,
)

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestFuselageGeom(unittest.TestCase):
    def setUp(self):
        # Setup a mock tigl object with predictable behavior
        self.tigl = MagicMock()
        # For 2 segments, always return (start_section, element) = (1, 0), (2, 0)
        self.tigl.fuselageGetStartSectionAndElementIndex.side_effect = lambda fus_nb, j: (j, 0)
        self.tigl.fuselageGetEndSectionAndElementIndex.side_effect = lambda fus_nb, j: (j + 1, 0)
        # For fuselageGetPoint, return x = j for each segment, y=0, z=0
        self.tigl.fuselageGetPoint.side_effect = lambda fus_nb, j, u, v: (float(j), 0.0, 0.0)

    def test_fuselage_check_segment_connection(self):
        fus_nb = 1
        fuse_seg_nb = np.array([2])  # 2 segments for fuselage 1
        # The function expects fuse_seg_nb to be an array
        sec_nb, start_index, seg_sec_reordered = fuselage_check_segment_connection(
            fus_nb, fuse_seg_nb, self.tigl
        )
        self.assertIsInstance(sec_nb, list)
        self.assertIsInstance(start_index, list)
        self.assertIsInstance(seg_sec_reordered, np.ndarray)
        self.assertEqual(sec_nb[0], 3)
        self.assertEqual(start_index[0], 1)
        self.assertEqual(seg_sec_reordered.shape[0], 2)  # nbmax
        self.assertEqual(seg_sec_reordered.shape[1], 1)  # fus_nb
        self.assertEqual(seg_sec_reordered.shape[2], 3)  # 3 columns

    def test_rel_dist(self):
        fus_nb = 1
        sec_nb = 3  # Should match the number of unique sections
        seg_nb = 2
        start_index = 1
        seg_sec = np.array(
            [
                [1, 2, 1],
                [2, 3, 2],
            ]
        )
        self.tigl.fuselageGetPoint.side_effect = lambda fus_nb, k, u, v: (float(k), 0.0, 0.0)
        rel_distances, rel_indices = rel_dist(
            fus_nb, sec_nb, seg_nb, self.tigl, seg_sec, start_index
        )
        self.assertEqual(len(rel_distances), sec_nb)
        self.assertEqual(len(rel_indices), sec_nb)
        self.assertEqual(rel_distances[0], 0.0)
        self.assertEqual(rel_indices[0], 0)


# =================================================================================================
#   MAIN
# =================================================================================================


if __name__ == "__main__":
    main(verbosity=0)
