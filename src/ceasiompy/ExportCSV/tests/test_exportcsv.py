"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.decorators import log_test
from ceasiompy.utils.ceasiompyutils import (
    create_branch,
)
from ceasiompy.utils.guisettings import current_workflow_dir
from ceasiompy.ExportCSV.exportcsv import main as export_aeromaps

from pathlib import Path
from unittest import main
from ceasiompy.utils.ceasiompytest import CeasiompyTest

from ceasiompy.utils.guixpaths import AEROMAP_TO_EXPORT_XPATH

# =================================================================================================
#   CLASS
# =================================================================================================


class TestExportCSV(CeasiompyTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wkdir = current_workflow_dir()
        cls.csv_empty_path = Path(cls.wkdir, "aeromap_empty.csv")
        cls.csv_path = Path(cls.wkdir, "test_apm.csv")
        cls.tixi = cls.test_cpacs.tixi

    @log_test
    def test_export_aeromaps(self):
        """Test function 'exportcsv' function."""

        create_branch(self.tixi, AEROMAP_TO_EXPORT_XPATH, True)
        self.tixi.updateTextElement(AEROMAP_TO_EXPORT_XPATH, "test_apm")

        export_aeromaps(self.test_cpacs, self.wkdir)

        # Read and check csv file
        with open(self.csv_path, "r") as csv_file:
            lines = csv_file.readlines()
            features_str = "altitude,machNumber,angleOfSideslip,angleOfAttack"
            assert lines[0] == f"{features_str},cd,cl,cs,cmd,cml,cms\n"
            assert lines[1] == "0,0.3,0,0,0.01,0.1,0.001,0.002,0.002,0.004\n"
            assert lines[2] == "0,0.3,0,10,0.01,0.1,0.001,0.002,0.002,0.002\n"
            assert lines[3] == "0,0.3,10,0,0.01,0.1,0.001,0.004,0.004,0.004\n"
            assert lines[4] == "0,0.3,10,10,0.01,0.1,0.001,0.004,0.002,0.002\n"

    @log_test
    def test_export_aeromaps_not_valid(self):
        """Test function 'exportcsv' function."""

        self.tixi.updateTextElement(AEROMAP_TO_EXPORT_XPATH, "")

        export_aeromaps(self.test_cpacs, self.wkdir)

        # Read and check csv file
        with open(self.csv_empty_path, "r") as csv_file:
            lines = csv_file.readlines()
            features_str = "altitude,machNumber,angleOfSideslip,angleOfAttack"
            assert lines[0] == f"{features_str},cd,cl,cs,cmd,cml,cms\n"
            assert lines[1] == "0,0.3,0,0,NaN,NaN,NaN,NaN,NaN,NaN\n"


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    main(verbosity=0)
