"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

List of paths which are used in CEASIOMpy, if possible base paths must be
called only from here to avoid mistakes.

| Author: Aidan jungo
| Creation: 2022-04-28
| Modified: Leon Deligny
| Date: 25 March 2025

"""

# Imports

import os
import ceasiompy

from pathlib import Path

# =================================================================================================
#   CSTS
# =================================================================================================

# /CEASIOMpy/src
SRC_PATH = Path(ceasiompy.__file__).parents[1]

# /CEASIOMpy/
CEASIOMPY_PATH = SRC_PATH.parent

# /CEASIOMpy/src/ceasiompy/
MODULES_DIR_PATH = Path(SRC_PATH, "ceasiompy")

# /CEASIOMpy/src/ceasiompy/Database/databases/ceasiompy.db
CEASIOMPY_DB_PATH = Path(MODULES_DIR_PATH, "database", "databases", "ceasiompy.db")

# /CEASIOMpy/src/ceasiompy/Database/tests/databases/testceasiompy.db
TESTCEASIOMPY_DB_PATH = Path(
    MODULES_DIR_PATH,
    "database",
    "tests",
    "databases",
    "testceasiompy.db",
)

# /CEASIOMpy/documents/logos/CEASIOMpy_main_logos.png
CEASIOMPY_LOGO_PATH = Path(CEASIOMPY_PATH, "documents", "logos", "CEASIOMpy_512px.png")

# /CEASIOMpy/.ceasiompy/.runworkflow_history
RUNWORKFLOW_HISTORY_PATH = Path(CEASIOMPY_PATH, ".ceasiompy", ".runworkflow_history")

# /CEASIOMpy/src/app
STREAMLIT_PATH = Path(SRC_PATH, "app")

# /CEASIOMpy/test_cases/
TEST_CASES_PATH = Path(CEASIOMPY_PATH, "test_cases")

# /CEASIOMpy/geometries/cpacsfiles/
CPACS_FILES_PATH = Path(CEASIOMPY_PATH, "geometries", "cpacsfiles")

# /CEASIOMpy/geometries/ResultsFiles/
TEST_RESULTS_FILES_PATH = Path(CEASIOMPY_PATH, "geometries", "ResultsFiles")

# /CEASIOMpy/wkdir/
WKDIR_PATH = Path(CEASIOMPY_PATH, "wkdir")

# /CEASIOMpy/installdir/
INSTALLDIR_PATH = Path(CEASIOMPY_PATH, "installdir")

# /CEASIOMpy/src/ceasiompy/SU2Run/files/default_paraview_state.pvsm
DEFAULT_PARAVIEW_STATE = Path(MODULES_DIR_PATH, "SU2Run", "files", "default_paraview_state.pvsm")


# Functions
def get_wkdir() -> Path:
    """Return working directory passed from ceasiompy_exec, or the default."""

    env_wkdir = os.environ.get("CEASIOMPY_wkdir")
    if env_wkdir:
        return Path(env_wkdir)
    return WKDIR_PATH
