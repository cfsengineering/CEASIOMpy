"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for CEASIOMpy.
    1. Log initialization.
"""

# Imports

import sys
import logging
import os

from pathlib import Path
from logging import Logger

from pydantic import (
    BaseModel,
    ConfigDict,
)

def _find_repo_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").is_file() and (candidate / "src").is_dir():
            return candidate
    return None


# /.../site-packages/ceasiompy (or <repo>/src/ceasiompy)
PACKAGE_DIR_PATH = Path(__file__).resolve().parent

_env_repo_root = os.environ.get("CEASIOMPY_HOME")
_REPO_ROOT = (
    Path(_env_repo_root).expanduser().resolve()
    if _env_repo_root
    else _find_repo_root(PACKAGE_DIR_PATH)
)

if _REPO_ROOT:
    # /CEASIOMpy/src
    SRC_PATH = _REPO_ROOT / "src"
    # /CEASIOMpy/
    CEASIOMPY_PATH = _REPO_ROOT
    # ===== Include Module's path =====
    UTILS_PATH = SRC_PATH / "ceasiompy" / "utils"
else:
    # site-packages layout
    SRC_PATH = PACKAGE_DIR_PATH.parent
    CEASIOMPY_PATH = SRC_PATH
    UTILS_PATH = PACKAGE_DIR_PATH / "utils"


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


# Functions

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

def redirect_print_to_logger(enable: bool = True) -> None:
    """Optionally redirect `print()` calls to the CEASIOMpy logger.

    This used to be enabled unconditionally, but overriding `builtins.print` can break
    third-party libraries and test tooling. Keep it opt-in.
    """

    if not enable:
        return

    import builtins as _builtins

    def _print(*args, **kwargs):  # type: ignore[override]
        sep = kwargs.get("sep", " ")
        msg = sep.join(map(str, args))
        log.info(msg)

    _builtins.print = _print


_redirect_print = os.environ.get("CEASIOMPY_REDIRECT_PRINT", "").strip().lower()
if _redirect_print in {"1", "true", "yes", "y", "on"}:
    redirect_print_to_logger(True)


# Ignore arbitrary types
ceasiompy_cfg = CustomConfig.model_config
