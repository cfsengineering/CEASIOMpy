"""
CEASIOMpy
Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Logging method use by other CEASIOMpy modules

Python version: >=3.8

| Author : Aidan Jungo
| Creation: 2018-09-26

TODO:

    * Do we want one big logfile (global) or many small (local for each module)?

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import logging
from datetime import datetime
from pathlib import Path

from ceasiompy.utils.commonpaths import LOGFILE, RUNWORKFLOW_HISTORY_PATH

# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_logger():
    """Function to create a logger

    Function 'get_logger' create a logger, it sets the format and the level of
    the logfile and console log.

    Returns:
        logger (logger): Logger
    """

    logger = logging.getLogger("CEASIOMpy")

    # NOTE: Multiple calls to getLogger() with the same name will return a
    # reference to the same logger object. However, there can be any number of
    # handlers (!) If a logger already as one or more handlers, none will be added
    if len(logger.handlers) > 0:
        return logger

    logger.setLevel(logging.DEBUG)

    # Write logfile
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)8s - %(module)18s - %(message)s")
    file_handler = logging.FileHandler(filename=LOGFILE, mode="w")
    file_handler.setLevel(logging.DEBUG)  # Level for the logfile
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Write log messages on the console
    console_formatter = logging.Formatter("%(levelname)-8s - %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Level for the console log
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def add_to_runworkflow_history(working_dir: Path, comment: str = "") -> None:
    """Add a line to the runworkflow history"""

    RUNWORKFLOW_HISTORY_PATH.parent.mkdir(exist_ok=True)
    RUNWORKFLOW_HISTORY_PATH.touch(exist_ok=True)

    if comment:
        comment = " - " + comment

    with open(RUNWORKFLOW_HISTORY_PATH, "a") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} - {working_dir}{comment}\n")


def get_last_runworkflow() -> Path:
    """Return the last working directory used"""

    if not RUNWORKFLOW_HISTORY_PATH.exists():
        return None

    with open(RUNWORKFLOW_HISTORY_PATH, "r") as f:
        lines = f.readlines()

    if not lines:
        return None

    return Path(lines[-1].split(" - ")[1].strip())


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
