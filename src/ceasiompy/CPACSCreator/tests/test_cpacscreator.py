"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test for CPACSCreator.
"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import unittest
import tempfile

from ceasiompy.CPACSCreator.cpacscreator import main

from pathlib import Path
from unittest.mock import MagicMock

from unittest.mock import patch

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestCPACSCreator(unittest.TestCase):

    @patch("ceasiompy.CPACSCreator.cpacscreator.run_software")
    @patch("ceasiompy.CPACSCreator.cpacscreator.get_install_path")
    @patch("ceasiompy.CPACSCreator.cpacscreator.log")
    def test_main_runs_cpacscreator(self, mock_log, mock_get_install_path, mock_run_software):
        mock_cpacs = MagicMock()
        mock_cpacs.cpacs_file = "dummy_cpacs.xml"
        with tempfile.TemporaryDirectory() as tmpdir:
            wkdir = Path(tmpdir)
            mock_get_install_path.side_effect = [None, None, "/usr/bin/CPACSCreator"]
            main(mock_cpacs, wkdir)
            mock_run_software.assert_called_once_with(
                software_name="CPACSCreator",
                arguments=["dummy_cpacs.xml"],
                wkdir=wkdir
            )
            mock_log.warning.assert_not_called()

    @patch("ceasiompy.CPACSCreator.cpacscreator.run_software")
    @patch("ceasiompy.CPACSCreator.cpacscreator.get_install_path")
    @patch("ceasiompy.CPACSCreator.cpacscreator.log")
    def test_main_cpacscreator_not_installed(self, mock_log, mock_get_install_path, mock_run_software):
        mock_cpacs = MagicMock()
        mock_cpacs.cpacs_file = "dummy_cpacs.xml"
        with tempfile.TemporaryDirectory() as tmpdir:
            wkdir = Path(tmpdir)
            mock_get_install_path.side_effect = [None, None, None]
            main(mock_cpacs, wkdir)
            mock_log.warning.assert_called_once_with(
                "CPACSCreator is not installed on your computer."
            )
            mock_run_software.assert_not_called()


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
