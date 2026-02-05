"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for create_data functions in SMTrain module.

"""

# Imports

import shutil
import tempfile
import numpy as np
import pandas as pd

from pandas import read_csv
from ceasiompy.utils.ceasiompyutils import current_workflow_dir
from ceasiompy.utils.decorators import log_test
from ceasiompy.smtrain.func.sampling import (
    new_points,
    lh_sampling,
)

from pathlib import Path
from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

# =================================================================================================
#   CLASSES
# =================================================================================================


class DummyModel:
    def __init__(self, variances):
        self._variances = variances

    def predict_variances(self, x_array):
        # Return the provided variances, one per row in x_array
        return np.array(self._variances[:len(x_array)])


class TestCreateData(CeasiompyTest):

    def test_new_points_first_iteration(self):
        x_array = np.array([
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
            [13, 14, 15, 16],
            [17, 18, 19, 20],
            [21, 22, 23, 24],
            [25, 26, 27, 28],
            [29, 30, 31, 32],
        ])
        variances = [0.1, 0.5, 0.2, 0.8, 0.3, 0.7, 0.4, 0.6]
        model = DummyModel(variances)
        high_var_pts = []
        tmpdir = tempfile.mkdtemp()
        try:
            results_dir = Path(tmpdir)
            df = new_points(x_array, model, results_dir, high_var_pts)
            self.assertIsInstance(df, pd.DataFrame)
            assert df is not None
            self.assertEqual(len(df), 7)
            # Check that the highest variance points are selected
            sorted_indices = np.argsort(variances)[::-1][:7]
            expected_points = [tuple(x_array[idx]) for idx in sorted_indices]
            actual_points = [tuple(row) for row in df.values]
            self.assertEqual(set(expected_points), set(actual_points))
            # Check file written
            out_file = results_dir / "new_points.csv"
            self.assertTrue(out_file.is_file())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_new_points_next_iteration(self):
        x_array = np.array([
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
        ])
        variances = [0.1, 0.5, 0.2]
        model = DummyModel(variances)
        # First two points already selected
        high_var_pts = [tuple(x_array[1]), tuple(x_array[2])]
        tmpdir = tempfile.mkdtemp()
        try:
            results_dir = Path(tmpdir)
            df = new_points(x_array, model, results_dir, high_var_pts)
            self.assertIsInstance(df, pd.DataFrame)
            assert df is not None
            self.assertEqual(len(df), 1)
            old_high_var_pts = [tuple(x_array[1]), tuple(x_array[2])]
            self.assertTrue(tuple(df.values[0]) not in old_high_var_pts)
            # Check file written
            out_file = results_dir / "new_points.csv"
            self.assertTrue(out_file.is_file())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_new_points_all_selected(self):
        x_array = np.array([
            [1, 2, 3, 4],
            [5, 6, 7, 8],
        ])
        variances = [0.1, 0.5]
        model = DummyModel(variances)
        high_var_pts = [tuple(x_array[0]), tuple(x_array[1])]
        tmpdir = tempfile.mkdtemp()
        try:
            results_dir = Path(tmpdir)
            df = new_points(x_array, model, results_dir, high_var_pts)
            self.assertIsNone(df)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    @log_test
    def test_lh_sampling(self) -> None:
        MAX_ALT = 1000.0
        MAX_MACH = 0.3
        MAX_AOA = MAX_AOS = 15.0
        lh_sampling_path = lh_sampling(
            n_samples=2,  # Run AVL at least once
            ranges={
                "altitude": [0, MAX_ALT],
                "machNumber": [0.1, MAX_MACH],
                "angleOfAttack": [0, MAX_AOA],
                "angleOfSideslip": [0, MAX_AOS],
            },
            results_dir=current_workflow_dir(),  # Where to store AVL results
            random_state=42,
        )

        assert lh_sampling_path is not None
        self.assertTrue(lh_sampling_path.is_file(), "Sampling CSV file was not created.")
        # Read the csv at lh_sampling_path and check if values are specific ones
        # Read the csv at lh_sampling_path and check if values are within the specified ranges
        df = read_csv(lh_sampling_path)
        self.assertIn("altitude", df.columns)
        self.assertIn("machNumber", df.columns)
        self.assertIn("angleOfAttack", df.columns)
        self.assertIn("angleOfSideslip", df.columns)

        # Check the ranges
        self.assertGreaterEqual(df["altitude"].iloc[0], 0)
        self.assertLessEqual(df["altitude"].iloc[0], MAX_ALT)
        self.assertGreaterEqual(df["machNumber"].iloc[0], 0.1)
        self.assertLessEqual(df["machNumber"].iloc[0], MAX_MACH)
        self.assertGreaterEqual(df["angleOfAttack"].iloc[0], 0)
        self.assertLessEqual(df["angleOfAttack"].iloc[0], MAX_AOA)
        self.assertGreaterEqual(df["angleOfSideslip"].iloc[0], 0)
        self.assertLessEqual(df["angleOfSideslip"].iloc[0], MAX_AOS)

        # Check values
        self.assertEqual(np.isclose(df["altitude"][0], 387, atol=0.1), True)
        self.assertEqual(np.isclose(df["altitude"][1], 547, atol=0.1), True)

        self.assertEqual(np.isclose(df["machNumber"][0], 0.3, atol=0.1), True)
        self.assertEqual(np.isclose(df["machNumber"][1], 0.14, atol=0.1), True)

        self.assertEqual(np.isclose(df["angleOfAttack"][0], 13.21, atol=0.1), True)
        self.assertEqual(np.isclose(df["angleOfAttack"][1], 6.44, atol=0.1), True)

        self.assertEqual(np.isclose(df["angleOfSideslip"][0], 5.23, atol=0.1), True)
        self.assertEqual(np.isclose(df["angleOfSideslip"][1], 13.4, atol=0.1), True)


# Main

if __name__ == "__main__":
    main(verbosity=0)
