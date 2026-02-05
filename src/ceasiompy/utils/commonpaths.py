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

def _find_repo_root(start: Path) -> Path | None:
    """Best-effort detection of the CEASIOMpy repo root.

    Works for editable installs where `ceasiompy` lives in `<repo>/src/ceasiompy`.
    For regular site-packages installs, it typically returns `None`.
    """

    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "src").is_dir():
            return candidate
    return None


# /.../site-packages/ceasiompy (or <repo>/src/ceasiompy)
PACKAGE_DIR_PATH = Path(ceasiompy.__file__).resolve().parent

_env_repo_root = os.environ.get("CEASIOMPY_HOME")
_REPO_ROOT = Path(_env_repo_root).expanduser().resolve() if _env_repo_root else _find_repo_root(PACKAGE_DIR_PATH)

if _REPO_ROOT:
    # /CEASIOMpy/
    CEASIOMPY_PATH = _REPO_ROOT
    # /CEASIOMpy/src
    SRC_PATH = _REPO_ROOT / "src"
    # /CEASIOMpy/src/ceasiompy/
    MODULES_DIR_PATH = SRC_PATH / "ceasiompy"
else:
    # For non-editable installs, the best "root" we have is the python environment's
    # site-packages directory that contains both `ceasiompy/` and (optionally) `app/`.
    SRC_PATH = PACKAGE_DIR_PATH.parent
    CEASIOMPY_PATH = SRC_PATH
    MODULES_DIR_PATH = PACKAGE_DIR_PATH

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

# /CEASIOMpy/src/app
STREAMLIT_PATH = Path(SRC_PATH, "app")

# /CEASIOMpy/test_cases/
TEST_CASES_PATH = Path(CEASIOMPY_PATH, "test_cases")

# /CEASIOMpy/test_files/CPACSfiles/
CPACS_FILES_PATH = Path(CEASIOMPY_PATH, "test_files", "CPACSfiles")

# /CEASIOMpy/test_files/ResultsFiles/
TEST_RESULTS_FILES_PATH = Path(CEASIOMPY_PATH, "test_files", "ResultsFiles")

# /CEASIOMpy/WKDIR/
WKDIR_PATH = Path(CEASIOMPY_PATH, "WKDIR")

# /CEASIOMpy/INSTALLDIR/
INSTALLDIR_PATH = Path(CEASIOMPY_PATH, "INSTALLDIR")

# /CEASIOMpy/src/ceasiompy/SU2Run/files/default_paraview_state.pvsm
DEFAULT_PARAVIEW_STATE = Path(MODULES_DIR_PATH, "SU2Run", "files", "default_paraview_state.pvsm")


# Functions
def get_wkdir() -> Path:
    """Return working directory passed from ceasiompy_exec, or the default."""

    env_wkdir = os.environ.get("CEASIOMPY_WKDIR")
    if env_wkdir:
        return Path(env_wkdir)
    return WKDIR_PATH


def get_repo_root() -> Path | None:
    """Return the CEASIOMpy repository root if detectable."""

    return _REPO_ROOT


def require_repo_root() -> Path:
    """Return repo root or raise with a helpful message."""

    if _REPO_ROOT:
        return _REPO_ROOT
    raise RuntimeError(
        "CEASIOMpy repository root not found. "
        "If you are running from a packaged install, set `CEASIOMPY_HOME` to a clone of the repo "
        "to use features that rely on `test_cases/`, `test_files/`, or `documents/`."
    )
