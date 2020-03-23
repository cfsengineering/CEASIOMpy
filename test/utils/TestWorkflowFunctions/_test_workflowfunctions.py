"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Module to test the workflowfunctions module

Python version: >=3.6

| Author: Vivien Riolo
| Creation: 26-02-2020
| Last modification: 26-02-2020

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os

from ceasiompy.utils.workflowfunctions import copy_module_to_module

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

import ceasiompy.__init__
LIB_DIR = os.path.dirname(ceasiompy.__init__.__file__)

# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
CPACS_OUT_PATH = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

#==============================================================================
#   FUNCTIONS
#==============================================================================

def test_copy_module_to_module():
    """
    Tests the copy_module_to_module function
    """

    module_from = MODULE_DIR
    module_to = MODULE_DIR
    io_from = "in"
    io_to = "out"

    copy_module_to_module(module_from, io_from, module_to, io_to)

    # Read Input and Ouput CPACS file as text, to compare them
    with open(CPACS_IN_PATH) as file_in:
        lines_cpacs_in = file_in.readlines()
    with open(CPACS_OUT_PATH) as file_out:
        lines_cpacs_out = file_out.readlines()

    assert lines_cpacs_in == lines_cpacs_out

# def test_run_subworkflow():
#     """
#     Tests the run_subworkflow function
#     """

#     module_list = []

#     run_subworkflow(module_list)

#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Test WorkflowFunctions')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
