"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/ModuleTemplate/moduletemplate.py'

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2019-08-14

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import sys

import pytest
from pytest import approx


# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH = os.path.join(MODULE_DIR, "ToolInput", "simpletest_cpacs.xml")
CPACS_OUT_PATH = os.path.join(MODULE_DIR, "ToolOutput", "ToolOutput.xml")


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def test_MyClass():
    """Test Class 'MyClass'"""

    assert 1 == 1


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Test ModuleTemplate")
    print("To run test use the following command:")
    print(">> pytest -v")
