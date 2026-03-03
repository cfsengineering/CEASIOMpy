"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialization for CEASIOMpy.
    1. Log initialization.

| Author: Leon Deligny
| Creation: 18-Mar-2025

"""

# Imports

import sys
import logging
import builtins

from pathlib import Path
from logging import Logger

from pydantic import (
    BaseModel,
    ConfigDict,
)

# Imports

# /CEASIOMpy/src
SRC_PATH = Path(__file__).parents[1]

# /CEASIOMpy/
CEASIOMPY_PATH = SRC_PATH.parent

# ===== Include Module's path =====
UTILS_PATH = SRC_PATH / "ceasiompy" / "utils"


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

# Override the built-in print function to use the logger


def custom_print(*args, **kwargs):
    log.info(" ".join(map(str, args)))


builtins.print = custom_print


# Ignore arbitrary types
ceasiompy_cfg = CustomConfig.model_config
