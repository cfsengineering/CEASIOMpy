"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for CEASIOMpy.
    1. Log initialization.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import sys
import logging
import builtins

from pathlib import Path
from logging import Logger

from pydantic import (
    BaseModel,
    ConfigDict,
)

# =================================================================================================
#   IMPORTS
# =================================================================================================

# /CEASIOMpy/src
SRC_PATH = Path(__file__).parents[1]

# /CEASIOMpy/
CEASIOMPY_PATH = SRC_PATH.parent

# /CEASIOMpy/WKDIR/
WKDIR_PATH = Path(CEASIOMPY_PATH, "WKDIR")

# /CEASIOMpy/WKDIR/
GEOMETRIES_PATH = Path(WKDIR_PATH, "GEOMETRIES")

# /CEASIOMpy/ceasiompy.log
LOGFILE = Path(CEASIOMPY_PATH, "ceasiompy.log")

# /CEASIOMpy/src/ceasiompy/
MODULES_DIR_PATH = Path(SRC_PATH, "ceasiompy")

# /CEASIOMpy/src/ceasiompy/Database/databases/ceasiompy.db
CEASIOMPY_DB_PATH = Path(MODULES_DIR_PATH, "Database", "databases", "ceasiompy.db")

# /CEASIOMpy/src/ceasiompy/Database/tests/databases/testceasiompy.db
TESTCEASIOMPY_DB_PATH = Path(
    MODULES_DIR_PATH,
    "Database",
    "tests",
    "databases",
    "testceasiompy.db",
)

# /CEASIOMpy/documents/logos/CEASIOMpy_main_logos.png
CEASIOMPY_LOGO_PATH = Path(CEASIOMPY_PATH, "documents", "logos", "CEASIOMpy_512px.png")

# /CEASIOMpy/.ceasiompy/.runworkflow_history
RUNWORKFLOW_HISTORY_PATH = Path(CEASIOMPY_PATH, ".ceasiompy", ".runworkflow_history")

# /CEASIOMpy/src/streamlit_app
STREAMLIT_PATH = Path(SRC_PATH, "streamlit_app")

# /CEASIOMpy/src/streamlit_app/pages
STREAMLIT_PAGES_PATH = Path(STREAMLIT_PATH, "pages")

# /CEASIOMpy/test_cases/
TEST_CASES_PATH = Path(CEASIOMPY_PATH, "test_cases")

# /CEASIOMpy/test_files/CPACSfiles/
CPACS_FILES_PATH = Path(CEASIOMPY_PATH, "test_files", "CPACSfiles")

# /CEASIOMpy/test_files/ResultsFiles/
TEST_RESULTS_FILES_PATH = Path(CEASIOMPY_PATH, "test_files", "ResultsFiles")

# /CEASIOMpy/WKDIR/
WKDIR_PATH = Path(CEASIOMPY_PATH, "WKDIR")

# /CEASIOMpy/ceasiompy.log
LOGFILE = Path(CEASIOMPY_PATH, "ceasiompy.log")

# /CEASIOMpy/src/ceasiompy/SU2Run/files/default_paraview_state.pvsm
DEFAULT_PARAVIEW_STATE = Path(MODULES_DIR_PATH, "SU2Run", "files", "default_paraview_state.pvsm")

# =================================================================================================
#   CLASSES
# =================================================================================================


class IgnoreSpecificError(logging.Filter):
    def filter(self, record):
        # List of error messages to ignore
        ignore_errors = [
            "QWidget::repaint: Recursive repaint detected",
            "Can not add element to document. Document already saved.",
            "Info    : Increasing process stack size (8192 kB < 16 MB)",
        ]
        # Check if the log message contains any of the ignore errors
        return not any(error in record.getMessage() for error in ignore_errors)


class CustomConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_logger() -> Logger:
    """
    Creates a logger, sets format and level of logfile and console log.
    """

    logger = logging.getLogger("CEASIOMpy")
    logger.setLevel(logging.DEBUG)

    # Check if the logger already has handlers to avoid duplicates
    if len(logger.handlers) > 0:
        return logger

    # Prevent propagation to root logger to avoid duplicates
    logger.propagate = False

    # Add file handler
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)8s - %(module)18s - %(message)s")
    file_handler = logging.FileHandler(filename=LOGFILE, mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(IgnoreSpecificError())  # Add the custom filter
    logger.addHandler(file_handler)

    # Add console handler regardless of environment
    # (we need output to be visible in both terminal and Streamlit)
    console_formatter = logging.Formatter("%(levelname)8s - %(module)18s - %(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(IgnoreSpecificError())  # Add the custom filter
    logger.addHandler(console_handler)

    # Ignore root logger error messages
    root_logger = logging.getLogger()
    root_logger.addFilter(IgnoreSpecificError())

    return logger


# ==============================================================================
#   INITIALIZATION
# ==============================================================================

# Log
log = get_logger()

# Override the built-in print function to use the logger


def custom_print(*args, **kwargs):
    log.info(" ".join(map(str, args)))


builtins.print = custom_print

# Constants
NO_YES_LIST = ["NO", "YES"]

# Ignore arbitrary types
ceasiompy_cfg = CustomConfig.model_config
