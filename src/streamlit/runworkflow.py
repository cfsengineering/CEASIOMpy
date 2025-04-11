"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Initialize CEASIOMpy's workflow.


| Author : Leon Deligny
| Creation: 2025-Mar-04

"""

# =================================================================================================
#    IMPORTS
# =================================================================================================

import sys

from pathlib import Path
from ceasiompy.utils.workflowclasses import Workflow

# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":
    config = sys.argv[1]

    workflow = Workflow()
    workflow.from_config_file(Path(config))
    workflow.set_workflow()
    workflow.run_workflow()
