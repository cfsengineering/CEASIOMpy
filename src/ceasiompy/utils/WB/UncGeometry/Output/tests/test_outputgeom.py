import os
import tempfile
import shutil
import numpy as np
import unittest

from ceasiompy.utils.WB.UncGeometry.Output.outputgeom import (
    produce_wing_output_txt,
    produce_geom_output_txt,
)


class MockAWG:
    def __init__(self):
        self.wing_nb = 2
        self.wing_sym = [1, 0]
        self.wing_sec_nb = [3, 2]
        self.wing_seg_nb = [2, 2]
        self.wing_span = [10.0, 8.0]
        self.wing_mac = np.array([[2.5, 2.0], [1.0, 0.5], [0.0, 0.0], [0.0, 0.0]])
        self.wing_sec_thickness = [[0.2, 0.3], [0.1, 0.2]]
        self.wing_sec_mean_thick = [[0.25, 0.15], [0.12, 0.18]]
        self.wing_seg_length = [[5.0, 5.0], [4.0, 4.0]]
        self.wing_max_chord = [3.0, 2.5]
        self.wing_min_chord = [1.0, 1.2]
        self.wing_plt_area = [20.0, 16.0]
        self.main_wing_surface = 30.0
        self.tail_wings_surface = 10.0
        self.wing_plt_area_main = 18.0
        self.cabin_area = 5.0
        self.wing_vol = [12.0, 10.0]
        self.wing_tot_vol = 22.0
        self.cabin_vol = 3.0
        self.fuse_vol = 7.0
        self.fuse_fuel_vol = 2.0
        self.wing_fuel_vol = 6.0
        self.fuel_vol_tot = 8.0


class MockAFG:
    def __init__(self):
        self.fuse_nb = 1
        self.fuse_sec_nb = [3]
        self.fuse_seg_nb = [2]
        self.cabin_seg = [1]
        self.fuse_length = 15.0
        self.fuse_nose_length = 2.0
        self.fuse_cabin_length = 8.0
        self.fuse_tail_length = 5.0
        self.tot_length = 16.0
        self.fuse_sec_per = [3.0, 3.5, 4.0]
        self.fuse_sec_rel_dist = [0.0, 5.0, 10.0]
        self.fuse_seg_length = [5.0, 10.0]
        self.fuse_mean_width = 2.5
        self.fuse_sec_width = [2.0, 2.5, 3.0]
        self.fuse_sec_height = [1.5, 1.8, 2.0]
        self.cabin_area = 12.0
        self.fuse_surface = 40.0
        self.fuse_seg_vol = [10.0, 12.0]
        self.fuse_cabin_vol = [6.0]
        self.fuse_vol = [22.0]
        self.fuse_fuel_vol = [4.0]


class TestOutputGeom(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory and patch ToolOutput to point there
        self.tmpdir = tempfile.mkdtemp()
        self.name = "TestAircraft"
        self.outdir = os.path.join(self.tmpdir, "ToolOutput", self.name)
        os.makedirs(self.outdir)
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        shutil.rmtree("ToolOutput", ignore_errors=True)

    def test_produce_wing_output_txt_creates_file_and_content(self):
        awg = MockAWG()
        produce_wing_output_txt(awg, self.name)
        outpath = os.path.join("ToolOutput", self.name, f"{self.name}_Aircraft_Geometry.out")
        self.assertTrue(os.path.isfile(outpath))
        with open(outpath, "r") as f:
            content = f.read()
        self.assertIn("Number of Wings", content)
        self.assertIn(str(awg.wing_nb), content)

    def test_produce_geom_output_txt_creates_file_and_content(self):
        awg = MockAWG()
        afg = MockAFG()
        produce_geom_output_txt(afg, awg, self.name)
        outpath = os.path.join("ToolOutput", self.name, f"{self.name}_Aircraft_Geometry.out")
        self.assertTrue(os.path.isfile(outpath))
        with open(outpath, "r") as f:
            content = f.read()
        self.assertIn("Number of fuselages", content)
        self.assertIn(str(afg.fuse_nb), content)
        self.assertIn("Number of Wings", content)
        self.assertIn(str(awg.wing_nb), content)


if __name__ == "__main__":
    unittest.main()
