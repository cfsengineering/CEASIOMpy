"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

List of paths which are used in CEASIOMpy, if possible base paths must be
called only from here to avoid mistakes.
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

# /CEASIOMpy/documents/logos/ceasiompy.png
LOGOS_PATH = Path(CEASIOMPY_PATH, "documents", "logos")
CEASIOMPY_LOGO_PATH = Path(LOGOS_PATH, "ceasiompy.png")
BLACKCEASIOMPY_LOGO_PATH = Path(LOGOS_PATH, "blackceasiompy.svg")

# /CEASIOMpy/.ceasiompy/.runworkflow_history
RUNWORKFLOW_HISTORY_PATH = Path(CEASIOMPY_PATH, ".ceasiompy", ".runworkflow_history")

# /CEASIOMpy/src/app
STREAMLIT_PATH = Path(SRC_PATH, "app")

# /CEASIOMpy/test_cases/
TEST_CASES_PATH = Path(CEASIOMPY_PATH, "test_cases")

# /CEASIOMpy/geometries/vspfiles/
VSP_DIR = CEASIOMPY_PATH / "geometries" / "vspfiles"

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

    env_wkdir = os.environ.get("CEASIOMPY_WKDIR")
    if env_wkdir:
        return Path(env_wkdir)
    return WKDIR_PATH
