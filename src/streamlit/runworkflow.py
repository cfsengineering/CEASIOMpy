import sys
from pathlib import Path
from ceasiompy.utils.workflowclasses import Workflow

config = sys.argv[1]

workflow = Workflow()
workflow.from_config_file(Path(config))
workflow.set_workflow()
workflow.run_workflow()
