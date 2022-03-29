#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Main module of CEASIOMpy to launch workflow by different way.

Python version: >=3.7

| Author: Aidan Jungo
| Creation: 2022-03-29

Todo:
    *

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import argparse
from pathlib import Path
from ceasiompy.WorkflowCreator.workflowcreator import create_wf_gui
from ceasiompy.utils.workflowclasses import Workflow


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


# =================================================================================================
#    MAIN
# =================================================================================================


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-g",
        "--gui",
        action="store_true",
        help="Create a CEASIOMpy workflow with the Graphical user interface",
    )
    parser.add_argument(
        "-c",
        "--cfg",
        type=str,
        metavar="PATH",
        help="Create a CEASIOMpy workflow from a configuration file [PATH to the config file]",
    )

    args = parser.parse_args()

    if args.cfg is not None:

        config_file_path = Path(args.cfg)

        workflow = Workflow()
        workflow.from_config_file(config_file_path)

    else:

        workflow = create_wf_gui()
        workflow.write_config_file()

    # Set and run the workflow
    workflow.set_workflow()
    workflow.run_workflow()


if __name__ == "__main__":

    main()
