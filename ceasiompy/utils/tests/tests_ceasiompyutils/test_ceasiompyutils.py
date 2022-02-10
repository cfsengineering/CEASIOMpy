"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'utils/ceasiompyfunctions.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-02-10

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import os
import pytest
from pathlib import Path
from ceasiompy.utils.ceasiompyutils import get_results_directory

# MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
# CPACS_PATH = os.path.join(MODULE_DIR, "D150_simple.xml")
# CPACS_PATH_OUT = os.path.join(MODULE_DIR, "D150_simple_out.xml")

# =================================================================================================
#   CLASSES
# =================================================================================================


def test_get_results_directory():

    results_dir = get_results_directory("ExportCSV")
    assert results_dir == Path(Path.cwd(), "Results", "Aeromaps")

    results_dir = get_results_directory("CPACS2SUMO")
    assert results_dir == Path(Path.cwd(), "Results", "SUMO")

    with pytest.raises(ValueError):
        results_dir = get_results_directory("NotExistingModule")


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
