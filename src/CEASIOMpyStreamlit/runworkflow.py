"""
Helper script to run a workflow outside of the Streamlit process.

It reads the workflow configuration file path from the CLI arguments,
constructs the workflow, and streams module status updates into a JSON
file within the workflow directory. This makes it possible for the UI
to monitor and, if needed, terminate the run by killing this process.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on the path when executed directly
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from ceasiompy.utils.workflowclasses import Workflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CEASIOMpy workflow (Streamlit helper).")
    parser.add_argument("config_path", type=Path, help="Path to ceasiompy.cfg")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg_path = args.config_path.resolve()

    workflow = Workflow()
    workflow.from_config_file(cfg_path)
    workflow.set_workflow()

    status_file = Path(workflow.current_wkflow_dir, "workflow_status.json")

    def write_status(status_list: list) -> None:
        try:
            with status_file.open("w", encoding="utf-8") as f:
                json.dump(status_list, f, indent=2)
        except OSError:
            # If the workflow is being stopped, the file may be gone; ignore errors.
            pass

    workflow.run_workflow(progress_callback=write_status)


if __name__ == "__main__":
    main()
