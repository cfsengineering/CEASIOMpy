#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Main module of CEASIOMpy to launch workflow by different way.

Python version: >=3.8

| Author: Aidan Jungo
| Creation: 2022-03-29

Todo:
    *

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import argparse
import os
from pathlib import Path

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.commonpaths import CPACS_FILES_PATH, TEST_CASES_PATH, STREAMLIT_PATH
from ceasiompy.utils.workflowclasses import Workflow

log = get_logger()

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def testcase_message(testcase_nb):
    """Top message to show when a test case is run."""

    log.info(f"CEASIOMpy as been started from test case {testcase_nb}")

    print("\n")
    print("#" * 30)
    print(f"### CEASIOMpy: Test case {testcase_nb} ###")
    print("#" * 30)
    print("More information about this test case at:")
    print(
        "https://github.com/cfsengineering/CEASIOMpy/blob/main/"
        f"test_cases/test_case_{testcase_nb}/README.md"
    )
    print("\n")


def run_testcase(testcase_nb):
    """Run a test case."""

    if testcase_nb == 1:

        testcase_message(1)

        test_case_1_path = Path(TEST_CASES_PATH, "test_case_1")
        test_case_1_cfg = Path(test_case_1_path, "testcase1.cfg")

        workflow = Workflow()
        workflow.from_config_file(test_case_1_cfg)
        workflow.working_dir = Path().cwd()
        workflow.cpacs_in = Path(CPACS_FILES_PATH, "D150_simple.xml")

        workflow.set_workflow()
        workflow.run_workflow()

        print("\nCongratulation, this Test case is now finished!")
        print(f"\nYou can check your results in: {workflow.current_wkflow_dir}/Results")

    elif testcase_nb == 2:
        testcase_message(2)
        print("\nUse the GUI to create your workflow.")
        run_gui()
        print("\nCongratulation, this Test case is now finished!")

    elif testcase_nb == 3:
        testcase_message(3)
        print("\nUse the GUI to create your workflow.")
        run_gui()
        print("\nCongratulation, this Test case is now finished!")

    elif testcase_nb == 4:
        testcase_message(4)

        print(
            "To run this test case, you will need to open a terminal"
            "and run the following command:"
        )
        print(">> conda activate ceasiompy")
        print(">> cd WKDIR")
        print(
            ">> ceasiompy_run -m ../test_files/CPACSfiles/D150_simple.xml "
            "PyTornado SkinFriction SaveAeroCoefficients"
        )

    elif testcase_nb == 5:
        testcase_message(5)
        print("Sorry, this test case is not implemented yet!")

    else:
        print("\nTest case number must be 1,2 or 3")


def run_modules_list(args_list):
    """Run a workflow from a CPACS file and a list of modules."""

    if len(args_list) < 2:
        print(
            "\nAt least 2 arguments are required to run a CEASIOMpy, the first onw must be the"
            "CPACS file and the modules to run. You can add as many modules as you want."
        )
        return

    cpacs_path = Path(args_list[0])

    if cpacs_path.suffix != ".xml":
        print(
            'The first argument of "-m/--modules" option must be the path to a CPACS file.',
        )
        return

    if not cpacs_path.exists():
        print(f"The CPACS file {cpacs_path} does not exist.")
        return

    modules_list = args_list[1:]

    log.info("CEASIOMpy as been started from a command line")

    workflow = Workflow()
    workflow.cpacs_in = cpacs_path
    workflow.modules_list = modules_list
    workflow.module_optim = ["NO"] * len(modules_list)
    workflow.write_config_file()

    workflow.set_workflow()
    workflow.run_workflow()


def run_config_file(config_file):
    """Run a workflow from a config file"""

    log.info("CEASIOMpy as been started from a config file")

    config_file_path = Path(config_file)

    if not config_file_path.exists():
        print(f"The config file {config_file_path} does not exist.")
        return

    workflow = Workflow()
    workflow.from_config_file(config_file_path)

    workflow.set_workflow()
    workflow.run_workflow()


def run_gui():
    """Create an run a workflow from a GUI."""

    log.info("CEASIOMpy as been started from the GUI")

    os.system(f"cd {STREAMLIT_PATH} && streamlit run CEASIOMpy.py")


# =================================================================================================
#    MAIN
# =================================================================================================


def main():

    parser = argparse.ArgumentParser(
        description="CEASIOMpy: Conceptual Aircraft Design Environment",
        usage=argparse.SUPPRESS,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=80, width=99),
    )

    parser.add_argument(
        "-c",
        "--cfg",
        type=str,
        metavar="PATH",
        help="create a CEASIOMpy workflow from a configuration file [PATH to the config file]",
    )
    parser.add_argument(
        "-g",
        "--gui",
        action="store_true",
        help="create a CEASIOMpy workflow with the Graphical user interface",
    )
    parser.add_argument(
        "-m",
        "--modules",
        nargs="+",
        metavar="",
        default=[],
        help="create a CEASIOMpy workflow by giving the CPACS file and the list of module to run"
        " [Path to the CPACS] [Module list]",
    )
    parser.add_argument(
        "--testcase",
        type=int,
        metavar="NB",
        help="run a test case [1, 2, or 3]",
    )

    args = parser.parse_args()

    if args.testcase:

        run_testcase(args.testcase)
        return

    if args.modules:

        run_modules_list(args.modules)
        return

    if args.cfg:

        run_config_file(args.cfg)

        return

    if args.gui:

        run_gui()
        return

    # If no argument is given, print the help
    parser.print_help()


if __name__ == "__main__":

    main()
