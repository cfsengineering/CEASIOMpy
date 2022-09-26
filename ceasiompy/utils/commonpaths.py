"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

List of paths which are used in CEASIOMpy, if possible base paths must be
called only from here to avoid mistakes.

Python version: >=3.7

| Author: Aidan jungo
| Creation: 2022-04-28

TODO:

    *

"""

from pathlib import Path

import ceasiompy.__init__

# /CEASIOMpy/
CEASIOMPY_PATH = Path(ceasiompy.__init__.__file__).parents[1]

# /CEASIOMpy/ceasiompy/
MODULES_DIR_PATH = Path(ceasiompy.__init__.__file__).parent

# /CEASIOMpy/documents/logos/CEASIOMpy_main_logos.png
CEASIOMPY_LOGO_PATH = Path(CEASIOMPY_PATH, "documents", "logos", "CEASIOMpy_512px.png")

# /CEASIOMpy/ceasiompy.log
LOGFILE = Path(CEASIOMPY_PATH, "ceasiompy.log")

# /CEASIOMpy/.ceasiompy/.runworkflow_history
RUNWORKFLOW_HISTORY_PATH = Path(CEASIOMPY_PATH, ".ceasiompy", ".runworkflow_history")

# /CEASIOMpy/src/streamlit
STREAMLIT_PATH = Path(CEASIOMPY_PATH, "src", "streamlit")

# /CEASIOMpy/ceasiompy/test_cases/
TEST_CASES_PATH = Path(CEASIOMPY_PATH, "test_cases")

# /CEASIOMpy/ceasiompy/test_files/CPACSfiles/
CPACS_FILES_PATH = Path(CEASIOMPY_PATH, "test_files", "CPACSfiles")

# /CEASIOMpy/ceasiompy/WKDIR/
WKDIR_PATH = Path(CEASIOMPY_PATH, "WKDIR")
