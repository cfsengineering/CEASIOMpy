"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/ExportCSV/exportcsv.py'

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2021-12-09
| Last modifiction: 2021-12-15

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import shutil
from ceasiompy.ExportCSV.exportcsv import export_aeromaps


# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH = os.path.join(MODULE_DIR, "D150_simple.xml")


def test_export_aeromaps():
    """Test function 'exportcsv' """

    WKDIR = os.path.join(MODULE_DIR, "WKDIR_test")
    csv_dir_path = os.path.join(WKDIR, "CSVresults")
    csv_file_path = os.path.join(csv_dir_path, "test_apm.csv")

    # Remove directory in the WKDIR if exists and create it empty
    if os.path.isdir(WKDIR):
        shutil.rmtree(WKDIR)
    os.mkdir(WKDIR)

    # Run the function
    export_aeromaps(CPACS_IN_PATH, CPACS_IN_PATH, csv_dir_path)

    # Read and check csv file
    with open(csv_file_path, "r") as csv_file:
        lines = csv_file.readlines()

    assert lines[0] == "altitude,machNumber,angleOfSideslip,angleOfAttack,cd,cl,cs,cmd,cml,cms\n"
    assert lines[1] == "0,0.3,0,0,0.01,0.1,0.001,NaN,NaN,NaN\n"
    assert lines[2] == "0,0.3,0,10,0.01,0.1,0.001,NaN,NaN,NaN\n"
    assert lines[3] == "0,0.3,10,0,0.01,0.1,0.001,NaN,NaN,NaN\n"
    assert lines[4] == "0,0.3,10,10,0.01,0.1,0.001,NaN,NaN,NaN\n"
