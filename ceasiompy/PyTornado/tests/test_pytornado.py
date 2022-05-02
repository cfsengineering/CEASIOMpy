"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/PyTornado/runpytornado.py'

Python version: >=3.7

| Author : Aaron Dettmann
| Creation: 2019-09-11

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import importlib
import os
import shutil
from contextlib import contextmanager
from pathlib import Path

PYTORNADO_MAIN_MODULE = "ceasiompy.PyTornado.runpytornado"

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name
CPACS_TEST_FILE = Path(MODULE_DIR, "cpacs_test_file.xml")


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


@contextmanager
def run_module_test_locally(module_name, test_dir):
    """Context manager which copies a single module

    Args:
        module_name (str): Full 'path' of module which is to be loaded
        test_dir (Path): Dictionary in which we run the local test
    """

    module = importlib.import_module(module_name)
    orig_module_file = Path(module.__file__)
    local_module_file = Path(test_dir, orig_module_file.name)
    shutil.copy(src=orig_module_file, dst=local_module_file)
    try:
        yield local_module_file
    finally:
        local_module_file.unlink()


def test_basic_run():
    """Make sure that the PyTornado run successfully"""

    shutil.copy(src=CPACS_TEST_FILE, dst=Path(MODULE_DIR, "ToolInput", "ToolInput.xml"))

    with run_module_test_locally(PYTORNADO_MAIN_MODULE, MODULE_DIR) as main:
        os.system(f"python {main}")


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Running Test PyTornado")
    print("To run test use the following command:")
    print(">> pytest -v")
