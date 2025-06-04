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

# =================================================================================================
#   IMPORTS
# =================================================================================================

import ceasiompy.__init__

from pathlib import Path

from ceasiompy import log

# =================================================================================================
#   CSTS
# =================================================================================================

# /CEASIOMpy/
CEASIOMPY_PATH = Path(ceasiompy.__file__).parents[1]

# /CEASIOMpy/ceasiompy/
MODULES_DIR_PATH = Path(ceasiompy.__file__).parent

# /CEASIOMpy/ceasiompy/Database/databases/ceasiompy.db
CEASIOMPY_DB_PATH = Path(MODULES_DIR_PATH, "Database", "databases", "ceasiompy.db")

# /CEASIOMpy/ceasiompy/Database/tests/databases/testceasiompy.db
TESTCEASIOMPY_DB_PATH = Path(
    MODULES_DIR_PATH,
    "Database",
    "tests",
    "databases",
    "testceasiompy.db",
)

# /CEASIOMpy/documents/logos/CEASIOMpy_main_logos.png
CEASIOMPY_LOGO_PATH = Path(CEASIOMPY_PATH, "documents", "logos", "CEASIOMpy_512px.png")

# /CEASIOMpy/ceasiompy.log
LOGFILE = Path(CEASIOMPY_PATH, "ceasiompy.log")

# /CEASIOMpy/.ceasiompy/.runworkflow_history
RUNWORKFLOW_HISTORY_PATH = Path(CEASIOMPY_PATH, ".ceasiompy", ".runworkflow_history")

# /CEASIOMpy/src/streamlit
STREAMLIT_PATH = Path(CEASIOMPY_PATH, "src", "streamlit")

# /CEASIOMpy/test_cases/
TEST_CASES_PATH = Path(CEASIOMPY_PATH, "test_cases")

# /CEASIOMpy/test_files/CPACSfiles/
CPACS_FILES_PATH = Path(CEASIOMPY_PATH, "test_files", "CPACSfiles")

# /CEASIOMpy/test_files/ResultsFiles/
TEST_RESULTS_FILES_PATH = Path(CEASIOMPY_PATH, "test_files", "ResultsFiles")

# /CEASIOMpy/ceasiompy/WKDIR/
WKDIR_PATH = Path(CEASIOMPY_PATH, "WKDIR")

# /CEASIOMpy/ceasiompy/SU2Run/files/default_paraview_state.pvsm
DEFAULT_PARAVIEW_STATE = Path(MODULES_DIR_PATH, "SU2Run", "files", "default_paraview_state.pvsm")


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    log.info("Nothing to execute!")
