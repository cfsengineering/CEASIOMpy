"""
CEASIOMpy
Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Logging method use by other CEASIOMpy modules

| Author : Aidan Jungo
| Creation: 2018-09-26
| Modified: Leon Deligny
| Date: 25 March 2025

"""

# Futures
from __future__ import annotations

# Imports

from pathlib import Path
from datetime import datetime

from ceasiompy.utils.commonpaths import RUNWORKFLOW_HISTORY_PATH

# Functions

def add_to_runworkflow_history(working_dir: Path, comment: str = "") -> None:
    """Add a line to the runworkflow history"""

    RUNWORKFLOW_HISTORY_PATH.parent.mkdir(exist_ok=True)
    RUNWORKFLOW_HISTORY_PATH.touch(exist_ok=True)

    if comment:
        comment = " - " + comment

    with open(RUNWORKFLOW_HISTORY_PATH, "a") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} - {working_dir}{comment}\n")


def get_last_runworkflow() -> Path | None:
    """Return the last working directory used"""

    if not RUNWORKFLOW_HISTORY_PATH.exists():
        return None

    with open(RUNWORKFLOW_HISTORY_PATH, "r") as f:
        lines = f.readlines()

    if not lines:
        return None

    return Path(lines[-1].split(" - ")[1].strip())
