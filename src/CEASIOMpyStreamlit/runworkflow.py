"""
Helper script to run a CEASIOMpy workflow from a config file.

This script is launched from the Streamlit GUI so that the workflow runs in a
separate process which can be terminated independently from the GUI.
"""

# Futures
from __future__ import annotations

# Imports
import sys

from pathlib import Path
from ceasiompy.utils.workflowclasses import Workflow


# Main
def main(config_path_str: str) -> None:
    """Run a workflow using the given config file path."""

    config_path = Path(config_path_str).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    workflow = Workflow()
    workflow.from_config_file(config_path)
    workflow.set_workflow()
    workflow.run_workflow()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        msg = "Usage: runworkflow.py <path_to_ceasiompy.cfg>"
        raise SystemExit(msg)

    main(sys.argv[1])
