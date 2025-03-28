"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/ExportCSV/exportcsv.py'

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2021-12-09

| Modified: Leon Deligny
| Date: 25 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================


from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.ExportCSV.exportcsv import main as export_aeromaps
import pytest
import shutil
from pathlib import Path
from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.utils.decorators import log_test
from ceasiompy.ExportCSV.exportcsv import main as export_csv
from ceasiompy.utils.ceasiompyutils import current_workflow_dir


# =================================================================================================
#   CLASS
# =================================================================================================

class TestExportCSV(CeasiompyTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wkdir = current_workflow_dir()
        cls.csv_path = Path(cls.wkdir, f"test_apm.csv")

    @log_test
    def test_main(self):
        """Test function 'exportcsv' function."""

        export_csv(self.test_cpacs, self.wkdir)

        # Read and check csv file
        with open(self.csv_path, "r") as csv_file:
            lines = csv_file.readlines()

        assert lines[0] == "altitude,machNumber,angleOfSideslip,angleOfAttack,cd,cl,cs,cmd,cml,cms\n"
        assert lines[1] == "0,0.3,0,0,0.01,0.1,0.001,NaN,NaN,NaN\n"
        assert lines[2] == "0,0.3,0,10,0.01,0.1,0.001,NaN,NaN,NaN\n"
        assert lines[3] == "0,0.3,10,0,0.01,0.1,0.001,NaN,NaN,NaN\n"
        assert lines[4] == "0,0.3,10,10,0.01,0.1,0.001,NaN,NaN,NaN\n"


MODULE_DIR = Path(__file__).parent
CPACS_IN_PATH = Path(MODULE_DIR, "D150_simple.xml")


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


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


# =================================================================================================
#    MAIN
# =================================================================================================
if __name__ == "__main__":

    main(verbosity=0)


print("Running Test ExportCSV")
print("To run test use the following command:")
print(">> pytest -v")
