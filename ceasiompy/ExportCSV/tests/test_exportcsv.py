"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/ExportCSV/exportcsv.py'


| Author : Aidan Jungo
| Creation: 2021-12-09

| Modified: Leon Deligny
| Date: 25 March 2025

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.decorators import log_test
from ceasiompy.utils.ceasiompyutils import current_workflow_dir
from ceasiompy.ExportCSV.exportcsv import main as export_aeromaps

from pathlib import Path
from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

# =================================================================================================
#   CLASS
# =================================================================================================


class TestExportCSV(CeasiompyTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wkdir = current_workflow_dir()
        cls.csv_path = Path(cls.wkdir, "test_apm.csv")

    @log_test
    def test_export_aeromaps(self):
        """Test function 'exportcsv' function."""

        export_aeromaps(self.test_cpacs, self.wkdir)

        # Read and check csv file
        with open(self.csv_path, "r") as csv_file:
            lines = csv_file.readlines()

        features_str = "altitude,machNumber,angleOfSideslip,angleOfAttack"
        assert lines[0] == f"{features_str},cd,cl,cs,cmd,cml,cms\n"
        assert lines[1] == "0,0.3,0,0,0.01,0.1,0.001,NaN,NaN,NaN\n"
        assert lines[2] == "0,0.3,0,10,0.01,0.1,0.001,NaN,NaN,NaN\n"
        assert lines[3] == "0,0.3,10,0,0.01,0.1,0.001,NaN,NaN,NaN\n"
        assert lines[4] == "0,0.3,10,10,0.01,0.1,0.001,NaN,NaN,NaN\n"


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    main(verbosity=0)
