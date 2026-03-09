"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# Imports

import unittest
import tempfile
import numpy as np

from ceasiompy.utils.geometryfunctions import (
    prod_points,
    elements_number,
)
from ceasiompy.pyavl.func.cpacs2avl import compute_fuselage_coords
from ceasiompy.utils.ceasiompyutils import (
    current_workflow_dir,
    get_results_directory,
    update_cpacs_from_specs,
)

from pathlib import Path
from ceasiompy.pyavl.func.cpacs2avl import Avl
from ceasiompy.utils.ceasiompytest import CeasiompyTest
from ceasiompy.utils.generalclasses import (
    Point,
    Transformation,
)
from ceasiompy.utils.commonxpaths import FUSELAGES_XPATH

from ceasiompy.pyavl import MODULE_NAME

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestWriteFuselage(CeasiompyTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wkdir = current_workflow_dir()
        cls.results_dir = get_results_directory(
            module_name=MODULE_NAME,
            create=True,
            wkflow_dir=cls.wkdir,
        )

    def test_compute_fuselage_coords(self):
        i_sec = 0
        elem_transf = Transformation()
        elem_transf.translation.x = 1
        sec_transf = Transformation()
        sec_transf.translation.x = 3
        fus_transf = Transformation()
        pos_x_list = [5]
        pos_z_list = [7]
        prof_size_y = 0.5
        prof_size_z = 0.25
        fus_radius_vec = np.zeros(1)
        x_fuselage = np.zeros(1)
        y_fuselage_top = np.zeros(1)
        y_fuselage_bottom = np.zeros(1)

        body_frm_width, body_frm_height = compute_fuselage_coords(
            i_sec,
            elem_transf,
            sec_transf,
            fus_transf,
            pos_x_list,
            pos_z_list,
            prof_size_y,
            prof_size_z,
            fus_radius_vec,
            x_fuselage,
            y_fuselage_top,
            y_fuselage_bottom,
        )

        _, y, z = prod_points(elem_transf.scaling, sec_transf.scaling, fus_transf.scaling)
        expected_width = 2 * prof_size_y * y
        expected_height = 2 * prof_size_z * z

        np.testing.assert_almost_equal(body_frm_width, expected_width)
        np.testing.assert_almost_equal(body_frm_height, expected_height)

    def test_wing_clipping_disabled_by_default(self):
        update_cpacs_from_specs(
            self.test_cpacs,
            MODULE_NAME,
            True,
        )
        avl = Avl(self.test_cpacs.tixi, results_dir=self.results_dir)
        assert avl.clip_wing_inside_fuselage is False

    def test_write_fuselage_coords(self):
        update_cpacs_from_specs(
            self.test_cpacs,
            MODULE_NAME,
            True,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            fus_dat_path = str(Path(tmpdir) / "fuselage.dat")
            avl = Avl(self.test_cpacs.tixi, results_dir=Path(tmpdir))
            x_fuselage = [0.0, 1.0, 2.0]
            y_fuselage_top = [0.5, 0.6, 0.7]
            y_fuselage_bottom = [-0.5, -0.6, -0.7]
            avl.write_fuselage_coords(
                fus_dat_path, 0, x_fuselage, y_fuselage_bottom, y_fuselage_top
            )
            # Check fuselage file content
            with open(fus_dat_path) as f:
                lines = f.read().splitlines()
            assert lines[0] == "fuselage1"
            # Top surface (reversed, all sections)
            assert lines[1] == "2.000\t0.700"
            assert lines[2] == "1.000\t0.600"
            assert lines[3] == "0.000\t0.500"
            # Bottom surface (all sections)
            assert lines[4] == "0.000\t-0.500"
            assert lines[5] == "1.000\t-0.600"
            assert lines[6] == "2.000\t-0.700"
            # Check avl file content
            with open(avl.avl_path) as f:
                avl_lines = f.read().splitlines()
            bfile_indices = [i for i, line in enumerate(avl_lines) if line == "BFILE"]
            assert bfile_indices
            assert avl_lines[bfile_indices[-1] + 1] == str(fus_dat_path)

    def test_write_fuselage_settings(self):
        update_cpacs_from_specs(
            self.test_cpacs,
            MODULE_NAME,
            True,
        )
        avl = Avl(self.test_cpacs.tixi, results_dir=self.results_dir)
        scaling = Point(1.0, 2.0, 3.0)
        translation = Point(4.0, 5.0, 6.0)
        avl.write_fuselage_settings(scaling, translation)
        with open(avl.avl_path) as f:
            content = f.read()
        assert "SCALE\n1.0\t2.0\t3.0" in content
        assert "TRANSLATE\n4.0\t5.0\t6.0" in content

    def test_write_fuselage_settings_with_custom_nbody(self):
        update_cpacs_from_specs(
            self.test_cpacs,
            MODULE_NAME,
            True,
        )
        avl = Avl(self.test_cpacs.tixi, results_dir=self.results_dir)
        avl.write_fuselage_settings(
            scaling=Point(1.0, 1.0, 1.0),
            translation=Point(0.0, 0.0, 0.0),
            nbody=68,
        )
        with open(avl.avl_path) as f:
            content = f.read()
        assert "!Nbody  Bspace\n68\t1.0" in content

    def test_convert_cpacs_to_avl_writes_bfile_once_per_fuselage(self):
        update_cpacs_from_specs(
            self.test_cpacs,
            MODULE_NAME,
            True,
        )
        avl = Avl(self.test_cpacs.tixi, results_dir=self.results_dir)
        avl_path = avl.convert_cpacs_to_avl()

        with open(avl_path) as f:
            avl_lines = f.read().splitlines()

        bfile_count = sum(line.strip() == "BFILE" for line in avl_lines)
        fuselage_count = elements_number(self.test_cpacs.tixi, FUSELAGES_XPATH, "fuselage")

        assert bfile_count == fuselage_count


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":
    unittest.main(verbosity=0)
