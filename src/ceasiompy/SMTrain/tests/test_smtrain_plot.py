"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for create_data functions in SMTrain module.

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import shutil
import unittest
import tempfile
import numpy as np
import ceasiompy.SMTrain.func.plot as smtrain_plot

from ceasiompy.SMTrain.func.plot import plot_validation

from pathlib import Path

# =================================================================================================
#   CLASSES
# =================================================================================================


class DummyModel:
    def predict_values(self, x):
        # Simple identity prediction for testing
        return x.sum(axis=1, keepdims=True)


class TestPlotValidation(unittest.TestCase):

    def setUp(self):
        def dummy_compute_rmse(model, x, y):
            # Dummy RMSE for logging
            return 0.0

        # Patch compute_rmse and log for the test
        self.orig_compute_rmse = smtrain_plot.compute_rmse
        smtrain_plot.compute_rmse = dummy_compute_rmse

    def tearDown(self):
        smtrain_plot.compute_rmse = self.orig_compute_rmse

    def test_plot_validation_creates_file(self):
        model = DummyModel()
        x_test = np.array([[1, 2], [3, 4]])
        y_test = np.array([[3], [7]])
        sets = {"x_test": x_test, "y_test": y_test}
        label = "TestLabel"
        tmpdir = tempfile.mkdtemp()
        try:
            results_dir = Path(tmpdir)
            plot_validation(model, sets, label, results_dir)
            expected_file = results_dir / f"validation_plot_{label}.png"
            self.assertTrue(expected_file.is_file())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    unittest.main()
