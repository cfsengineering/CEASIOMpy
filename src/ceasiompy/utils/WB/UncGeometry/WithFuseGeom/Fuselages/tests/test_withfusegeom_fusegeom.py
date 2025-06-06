import unittest
import numpy as np

from ceasiompy.utils.WB.UncGeometry.WithFuseGeom.Fuselages.fusegeom import (
    check_segment_connection,
    rel_dist,
)


class MockTigl:
    def __init__(self):
        # Simulate a fuselage with 2 segments and 3 sections
        self.points = {
            (1, 1, 0.0, 0.0): (0.0, 0.0, 0.0),
            (1, 2, 0.0, 0.0): (1.0, 0.0, 0.0),
            (1, 1, 1.0, 0.0): (0.5, 0.0, 0.0),
            (1, 2, 1.0, 0.0): (1.5, 0.0, 0.0),
        }
        self.start_sections = {(1, 1): (1, 0), (1, 2): (2, 0)}
        self.end_sections = {(1, 1): (2, 0), (1, 2): (3, 0)}

    def fuselageGetStartSectionAndElementIndex(self, i, j):
        return self.start_sections[(i, j)]

    def fuselageGetEndSectionAndElementIndex(self, i, j):
        return self.end_sections[(i, j)]

    def fuselageGetPoint(self, i, j, eta, zeta):
        # Return a simple linear mapping for test
        return self.points.get((i, j, eta, zeta), (float(j), eta, zeta))


class TestWithFuseGeomFuseGeom(unittest.TestCase):

    def test_check_segment_connection(self):
        fus_nb = 1
        fuse_seg_nb = [2]
        fuse_sec_nb = [3]
        tigl = MockTigl()
        sec_nb, start_index, seg_sec_reordered, sec_index = check_segment_connection(
            fus_nb, fuse_seg_nb, fuse_sec_nb, tigl
        )
        self.assertEqual(sec_nb[0], 3)
        self.assertEqual(start_index[0], 1)
        self.assertEqual(seg_sec_reordered.shape, (2, 1, 3))
        self.assertEqual(sec_index.shape, (3, 1))

    def test_rel_dist(self):
        i = 1
        sec_nb = 3
        seg_nb = 2
        tigl = MockTigl()
        seg_sec = np.array([
            [1, 2, 1],
            [2, 3, 2]
        ])
        start_index = 1
        rel_distances, rel_indices = rel_dist(i, sec_nb, seg_nb, tigl, seg_sec, start_index)
        self.assertEqual(len(rel_distances), 3)
        self.assertEqual(len(rel_indices), 3)
        self.assertAlmostEqual(rel_distances[0], 0.0)


if __name__ == "__main__":
    unittest.main()
