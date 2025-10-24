"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions utils to run ceasiompy workflows
| Author : Leon Deligny
| Creation: 21 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import unittest

from pytest import approx

from pathlib import Path
from typing import Tuple
from typing import Callable
from cpacspy.cpacspy import CPACS

from ceasiompy import CPACS_FILES_PATH


# =================================================================================================
#   CLASSES
# =================================================================================================


class CeasiompyTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cpacs_in = Path(CPACS_FILES_PATH, "D150_simple.xml")
        cls.test_cpacs = CPACS(cpacs_in)

    def assert_equal_function(self, f: Callable, input_args: Tuple, expected: Tuple) -> None:
        actual = f(*input_args)
        # When the function to test f returns a single value
        # then it is not of type tuple.
        # We make the following adjustment.
        if not isinstance(actual, tuple) and isinstance(expected, tuple):
            actual = (actual,)

        self.assertEqual(len(actual), len(expected), "Number of outputs does not match.")
        for act, exp in zip(actual, expected):
            self.assertEqual(act, approx(exp))
