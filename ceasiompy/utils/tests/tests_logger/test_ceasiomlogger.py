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

from ceasiompy import log
from ceasiompy.utils.commonpaths import LOGFILE

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def test_logger():
    """Test if ceasiompy logger return the correct lines on the
    log file.
    """

    # Set logger name and create a logger with this name

    # Use the 5 log level
    log.debug("Test debug")
    log.info("Test info")
    log.warning("Test warning")
    log.error("Test error")
    log.critical("Test critical")

    # Open and read (last five line of) the logfile
    with open(LOGFILE) as file:
        data = file.readlines()
    last_lines = data[-5:]

    # Set default line for each level
    debug_line_default = "-    DEBUG - test_ceasiomlogger - Test debug"
    info_line_default = "-     INFO - test_ceasiomlogger - Test info"
    warning_line_default = "-  WARNING - test_ceasiomlogger - Test warning"
    error_line_default = "-    ERROR - test_ceasiomlogger - Test error"
    critical_line_default = "- CRITICAL - test_ceasiomlogger - Test critical"

    # Check if default line of each level are in the logfile
    assert debug_line_default in last_lines[0]
    assert info_line_default in last_lines[1]
    assert warning_line_default in last_lines[2]
    assert error_line_default in last_lines[3]
    assert critical_line_default in last_lines[4]


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    print("Running Test CEASIOMLogger")
    print("To run test use the following command:")
    print(">> pytest -v")
