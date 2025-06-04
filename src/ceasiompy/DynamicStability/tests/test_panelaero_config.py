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
from ceasiompy.DynamicStability.func.panelaeroconfig import (
    AeroModel,
    DetailedPlots,
)

from unittest.mock import patch

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestAeroModel(unittest.TestCase):
    def setUp(self):
        # Minimal wing definition for testing
        self.wings_list = [
            {
                "EID": 1,
                "CP": 1,
                "n_span": 1,
                "n_chord": 1,
                "X1": np.array([0.0, 0.0, 0.0]),
                "length12": 1.0,
                "X4": np.array([0.0, 1.0, 0.0]),
                "length43": 1.0,
            }
        ]
        self.model = AeroModel(self.wings_list)
        self.model.build_aerogrid()
        self.plots = DetailedPlots(self.model)

    def test_read_CAERO(self):
        grids, panels, caerocards = self.model.read_CAERO(0)
        self.assertIn("ID", grids)
        self.assertIn("offset", grids)
        self.assertIn("ID", panels)
        self.assertIn("cornerpoints", panels)
        self.assertIsInstance(caerocards, list)
        self.assertGreater(len(grids["ID"]), 0)
        self.assertGreater(len(panels["ID"]), 0)

    def test_build_aerogrid(self):
        self.model.build_aerogrid()
        self.assertIsNotNone(self.model.aerogrid)
        self.assertIn("A", self.model.aerogrid)
        self.assertIn("N", self.model.aerogrid)
        self.assertEqual(self.model.aerogrid["coord_desc"], "bodyfixed")
        self.assertEqual(self.model.aerogrid["n"], len(self.model.aerogrid["ID"]))

    def test_plot_aerogrid_runs(self):
        # Patch plt.show so it doesn't block the test
        with patch("matplotlib.pyplot.show"):
            try:
                self.plots.plot_aerogrid()
            except Exception as e:
                self.fail(f"plot_aerogrid raised an exception: {e}")


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":
    main(verbosity=0)
