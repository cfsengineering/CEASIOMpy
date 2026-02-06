"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for create_data functions in SMTrain module.

"""

# Imports

import shutil
import unittest
import tempfile
import numpy as np
import ceasiompy.smtrain.func.plot as smtrain_plot

from ceasiompy.smtrain.func.plot import plot_validation
from ceasiompy.smtrain.func.utils import DataSplit
from ceasiompy.smtrain.func.config import TrainingSettings

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
        level1_split = DataSplit(
            x_train=x_test,
            y_train=y_test,
            x_val=x_test,
            y_val=y_test,
            x_test=x_test,
            y_test=y_test,
        )
        training_settings = TrainingSettings(
            sm_models=["KRG"],
            objective="TestLabel",
            direction="max",
            n_samples=1,
            fidelity_level="level1",
            data_repartition=0.8,
        )
        tmpdir = tempfile.mkdtemp()
        try:
            results_dir = Path(tmpdir)
            plot_validation(model, results_dir, level1_split, training_settings)
            expected_file = results_dir / "test_plot_TestLabel.html"
            self.assertTrue(expected_file.is_file())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# Main
if __name__ == "__main__":
    unittest.main()
