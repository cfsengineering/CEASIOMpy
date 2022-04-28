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

# /CEASIOMpy/ceasiompy/test_cases/
TEST_CASES_PATH = Path(CEASIOMPY_PATH, "test_cases")

# /CEASIOMpy/ceasiompy/test_files/CPACSfiles/
CPACS_FILE_PATH = Path(CEASIOMPY_PATH, "test_files", "CPACSfiles")
