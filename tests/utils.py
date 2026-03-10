"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Integration test for some typical CEASIOMpy workflows.
"""

# Imports
from pathlib import Path
from ceasiompy.utils.workflowclasses import Workflow

from ceasiompy.utils.commonpaths import CPACS_FILES_PATH


# Methods

def run_workflow_test(
    modules_to_run: list[str],
    cpacs_path: Path = Path(CPACS_FILES_PATH, "onera_m6.xml"),
) -> None:
    """Run a workflow test with the given modules and optional CPACS path."""
    workflow = Workflow()
    workflow.cpacs_in = cpacs_path
    workflow.modules_list = modules_to_run
    workflow.module_optim = ["NO"] * len(modules_to_run)
    workflow.write_config_file()
    workflow.set_workflow()
    workflow.run_workflow(test=True)
