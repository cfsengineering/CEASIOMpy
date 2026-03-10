"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Integration test for some typical CEASIOMpy workflows.
"""

# Imports
import shutil
import pytest

from pathlib import Path
from ceasiompy.utils.workflowclasses import Workflow

from ceasiompy.utils.commonpaths import (
    CPACS_FILES_PATH,
)

from ceasiompy.to3d import MODULE_NAME as TO3D
from ceasiompy.pyavl import MODULE_NAME as PYAVL
from ceasiompy.su2run import MODULE_NAME as SU2RUN
from ceasiompy.smtrain import MODULE_NAME as SMTRAIN
from ceasiompy.aeroframe import MODULE_NAME as AEROFRAME
from ceasiompy.cpacs2gmsh import MODULE_NAME as CPACS2GMSH
from ceasiompy.airfoil2gmsh import MODULE_NAME as AIRFOIL2GMSH


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
