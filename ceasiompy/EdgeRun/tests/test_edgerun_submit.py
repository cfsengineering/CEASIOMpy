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

from pathlib import Path

# Add the ceasiompy module to the PYTHONPATH
# ceasiompy_path = Path("/home/mengmeng/Documents/CEASIOMpy23/CEASIOMpy/ceasiompy")
# sys.path.append(str(ceasiompy_path))

# Now you can import and use the ceasiompy module
# import ceasiompy
from ceasiompy.EdgeRun.func.edgeconfig import edge_cfd
import os

# from ceasiompy.EdgeRun.func.edgeutils import get_edge_que_script_template
# from ceasiompy.utils.create_ainpfile import CreateAinp

MODULE_DIR = Path(__file__).parent
# input_que_script_path = get_edge_que_script_template()

# cpacs_in_path = Path(MODULE_DIR / "ToolInput" / "ToolInput.xml")
cpacs_in_path = Path(
    "/home/mengmeng/Documents/CEASIOMpy23/CEASIOMpy/WKDIR/CPACS_selected_from_GUI.xml"
)
cpacs_out_path = MODULE_DIR / "ToolOutput.xml"
wkdir = MODULE_DIR / "Results"


if not os.path.exists(wkdir):
    os.makedirs(wkdir)

edge_cfd(cpacs_in_path, cpacs_out_path, wkdir)
