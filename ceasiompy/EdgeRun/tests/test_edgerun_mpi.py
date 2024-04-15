"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by Airinnova AB, Stockholm, Sweden

Test functions of 'ceasiompy/EdgeRun/func/edgeconfig.py'

Python version: >=3.8


| Author : Mengmeng Zhang
| Creation: 2024-01-05

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import unittest

from pathlib import Path

# Add the ceasiompy module to the PYTHONPATH
# ceasiompy_path = Path("/home/mengmeng/Documents/CEASIOMpy23/CEASIOMpy/ceasiompy")
# sys.path.append(str(ceasiompy_path))

# Now you can import and use the ceasiompy module
# import ceasiompy
from ceasiompy.EdgeRun.func.edgeconfig import generate_edge_cfd_ainp
import os

# from ceasiompy.utils.create_ainpfile import CreateAinp

MODULE_DIR = Path(__file__).parent

# input_que_script_path = get_edge_queScript_template()

# =================================================================================================
#   CLASSES
# =================================================================================================


class TestEdgeConfig(unittest.TestCase):
    """Test class for 'ceasiompy/EdgeRun/func/edgerun.py'"""

    def test_run_edge_cfd(self):
        # cpacs_in_path = Path(MODULE_DIR / "ToolInput" / "ToolInput.xml")
        cpacs_in_path = Path(
            "/home/mengmeng/Documents/CEASIOMpy23/CEASIOMpy/WKDIR/labARstraight_toolInput.xml"
        )

        cpacs_out_path = MODULE_DIR / "ToolOutput.xml"
        wkdir = MODULE_DIR / "Results/Edge"

        if not os.path.exists(wkdir):
            os.makedirs(wkdir)

        generate_edge_cfd_ainp(cpacs_in_path, cpacs_out_path, wkdir)
        # run_edge_multi(wkdir,input_que_script_path )


# =================================================================================================
#    MAIN
# =================================================================================================
"""
if __name__ == "__main__":
    print("Test configfile.py")
    print("To run test use the following command:")
    print(">> pytest -v")
"""
