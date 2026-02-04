"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for create_data functions in SMTrain module.

"""

# Imports

import numpy as np

from numpy.testing import assert_array_equal
from ceasiompy.utils.decorators import log_test
from ceasiompy.SMTrain.func.utils import (
    collect_level_data,
    concatenate_if_not_none,
)

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestConfig(CeasiompyTest):

    @log_test
    def test_concatenate_if_not_none_basic(self):
        arr1 = np.array([[1, 2], [3, 4]])
        arr2 = np.array([[5, 6]])
        result = concatenate_if_not_none([arr1, arr2])
        expected = np.concatenate([arr1, arr2], axis=0)
        assert_array_equal(result, expected)

    @log_test
    def test_concatenate_if_not_none_with_none(self):
        arr1 = np.array([[1, 2]])
        arr2 = None
        arr3 = np.array([[3, 4]])
        result = concatenate_if_not_none([arr1, arr2, arr3])
        expected = np.concatenate([arr1, arr3], axis=0)
        assert_array_equal(result, expected)

    @log_test
    def test_concatenate_if_not_none_all_none(self):
        with self.assertRaises(ValueError):
            concatenate_if_not_none([None, None])

    @log_test
    def test_collect_level_data_none(self):
        result = collect_level_data(None)
        self.assertEqual(result, (None, None, None, None, None, None))


# Main

if __name__ == "__main__":
    main(verbosity=0)
