"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test  for 'ceasiomlogger.py' function

| Author : Aidan Jungo
| Creation: 2018-09-27

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import tempfile
import unittest

from ceasiompy.utils.ceasiompylogger import get_last_runworkflow

from pathlib import Path

from ceasiompy import log
from unittest.mock import patch
from ceasiompy.utils.commonpaths import LOGFILE

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestCeasiompyLogger(unittest.TestCase):

    def test_logger(self):
        """Test if ceasiompy logger returns the correct lines in the log file."""
        # Use the 5 log levels
        log.debug("Test debug")
        log.info("Test info")
        log.warning("Test warning")
        log.error("Test error")
        log.critical("Test critical")

        # Open and read (last five lines of) the logfile
        with open(LOGFILE) as file:
            data = file.readlines()
        last_lines = data[-5:]

        # Use correct module name and check substring (ignore timestamp)
        self.assertIn("DEBUG - test_ceasiompylogger - Test debug", last_lines[0])
        self.assertIn("INFO - test_ceasiompylogger - Test info", last_lines[1])
        self.assertIn("WARNING - test_ceasiompylogger - Test warning", last_lines[2])
        self.assertIn("ERROR - test_ceasiompylogger - Test error", last_lines[3])
        self.assertIn("CRITICAL - test_ceasiompylogger - Test critical", last_lines[4])

    def test_get_last_runworkflow_exists_and_has_lines(self):
        # Create a fake history file
        with tempfile.TemporaryDirectory() as tmpdirname:
            history_path = Path(tmpdirname) / "runworkflow_history.txt"
            first_run = str(Path(tmpdirname) / "first_run")
            second_run = str(Path(tmpdirname) / "second_run")
            lines = [
                f"2024-06-01 12:00:00 - {first_run}\n",
                f"2024-06-02 13:00:00 - {second_run}\n",
            ]
            history_path.write_text("".join(lines))

            with patch("ceasiompy.utils.ceasiompylogger.RUNWORKFLOW_HISTORY_PATH", history_path):
                result = get_last_runworkflow()
                self.assertEqual(result, Path(second_run))

    def test_get_last_runworkflow_file_missing(self):
        with patch(
            "ceasiompy.utils.ceasiompylogger.RUNWORKFLOW_HISTORY_PATH",
            Path("/non/existing/path.txt")
        ):
            self.assertIsNone(get_last_runworkflow())

    def test_get_last_runworkflow_empty_file(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            history_path = Path(tmpdirname) / "runworkflow_history.txt"
            history_path.write_text("")
            with patch(
                "ceasiompy.utils.ceasiompylogger.RUNWORKFLOW_HISTORY_PATH",
                history_path
            ):
                self.assertIsNone(get_last_runworkflow())


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":
    unittest.main()
