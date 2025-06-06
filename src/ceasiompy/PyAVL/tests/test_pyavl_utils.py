"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pytest

from ceasiompy.utils.decorators import log_test
from ceasiompy.PyAVL.func.utils import (
    duplicate_elements,
    convert_dist_to_avl_format,
)

from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest


# =================================================================================================
#   FUNCTION
# =================================================================================================


@pytest.mark.parametrize("vortex_dist,expected", [
    ("cosine", 1),
    ("sine", 2),
    ("other", 3),
    ("", 3),
])
def test_convert_dist_to_avl_format(vortex_dist, expected):
    assert convert_dist_to_avl_format(vortex_dist) == expected


# =================================================================================================
#   CLASSES
# =================================================================================================


class TestAvlResults(CeasiompyTest):

    @log_test
    def test_duplicate_elements_no_expand(self):
        # Should just repeat the last list's first value for the last three lists
        a = [1, 2]
        b = [3, 4]
        c = [5]
        result = duplicate_elements(False, a, b, c)
        assert result[0] == a
        assert result[1] == b
        assert result[2] == [5, 5]
        assert result[3] == [5, 5]
        assert result[4] == [5, 5]

    @log_test
    def test_duplicate_elements_expand(self):
        # Should create all unique combinations and zero-independent last three lists
        a = [1, 2]
        b = [10]
        c = [5, 0.0]
        result = duplicate_elements(True, a, b, c)
        # There are 2*1=2 combinations for a and b, and 2 values in c
        # For value=5: 3 combinations per (a,b)
        # For value=0.0: 1 combination per (a,b)
        # So total: (2*3) + (2*1) = 8 rows
        assert len(result[0]) == 8
        assert len(result[1]) == 8
        assert len(result[2]) == 8
        assert len(result[3]) == 8
        assert len(result[4]) == 8

        assert result[2][-1] == 0.0 and result[3][-1] == 0.0 and result[4][-1] == 5


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    main(verbosity=0)
