"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/ExportCSV/exportcsv.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2021-12-09

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import shutil
import pytest
from pathlib import Path
from ceasiompy.ExportCSV.exportcsv import export_aeromaps
from ceasiompy.utils.ceasiompyutils import get_results_directory

# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH = os.path.join(MODULE_DIR, "D150_simple.xml")


@pytest.fixture(autouse=True)
def change_test_dir(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname)

    global CSV_FILE_PATH
    results_dir = get_results_directory("ExportCSV")
    CSV_FILE_PATH = Path(results_dir, "test_apm.csv")

    yield

    # Clean up
    shutil.rmtree(CSV_FILE_PATH.parent.parent)


def test_export_aeromaps():
    """Test function 'exportcsv' function."""

    export_aeromaps(CPACS_IN_PATH, CPACS_IN_PATH)

    # Read and check csv file

    with open(CSV_FILE_PATH, "r") as csv_file:
        lines = csv_file.readlines()

    assert lines[0] == "altitude,machNumber,angleOfSideslip,angleOfAttack,cd,cl,cs,cmd,cml,cms\n"
    assert lines[1] == "0,0.3,0,0,0.01,0.1,0.001,NaN,NaN,NaN\n"
    assert lines[2] == "0,0.3,0,10,0.01,0.1,0.001,NaN,NaN,NaN\n"
    assert lines[3] == "0,0.3,10,0,0.01,0.1,0.001,NaN,NaN,NaN\n"
    assert lines[4] == "0,0.3,10,10,0.01,0.1,0.001,NaN,NaN,NaN\n"
