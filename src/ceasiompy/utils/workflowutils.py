# =================================================================================================
#    IMPORTS
# =================================================================================================

import re

from pathlib import Path
from typing import (
    List,
)

from ceasiompy import (
    log,
    WKDIR_PATH,
)

# =================================================================================================
#    FUNCTIONS
# =================================================================================================


def current_workflow_dir() -> Path:
    """
    Get the current workflow directory.
    """

    # collect numeric suffixes only (defensive against unexpected folder names)
    idx_list: List[int] = []

    # Make sure WKDIR_PATH exists as a dir
    WKDIR_PATH.mkdir(exist_ok=True)

    pattern = re.compile(r"Workflow_(\d+)$")
    for p in WKDIR_PATH.iterdir():
        if not p.is_dir():
            log.warning(f"There should be only Directories in {WKDIR_PATH=}")
            continue

        m = pattern.match(p.name)
        if m:
            try:
                idx_list.append(int(m.group(1)))
            except ValueError as e:
                log.error(f"Could not process pattern of workflows {e=}")

    if idx_list:
        max_idx = max(idx_list)
        last_wkflow_dir = WKDIR_PATH / get_workflow_idx(max_idx)
        has_subdirs = any(p.is_dir() for p in last_wkflow_dir.iterdir())

        # If the last workflow contains the toolinput file, we increment index
        if has_subdirs:
            new_idx = max_idx + 1
        else:
            new_idx = max_idx
    else:
        new_idx = 1

    current_wkflow_dir = WKDIR_PATH / get_workflow_idx(new_idx)
    current_wkflow_dir.mkdir(parents=True, exist_ok=True)

    return current_wkflow_dir


def get_workflow_idx(wkflow_idx: int) -> str:
    return f"Workflow_{str(wkflow_idx).rjust(3, '0')}"
