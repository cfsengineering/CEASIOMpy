"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'ceasiompy/ExportCSV/exportcsv.py'

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2021-12-09
| Last modifiction: 2021-12-09

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os

from cpacspy.cpacspy import CPACS

from ceasiompy.ExportCSV.exportcsv import export_aeromaps

from cpacspy.cpacsfunctions import open_tixi

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH =  os.path.join(MODULE_DIR,'..','CPACSfiles','D150_simple.xml')
CPACS_OUT_PATH = os.path.join(MODULE_DIR,'D150_simple_clcalulator_test.xml')


def test_export_aeromaps():
    """Test function 'exportcsv' """
    
    # cpacs = CPACS(CPACS_OUT_PATH)
    # aeromap = cpacs.get_aeromap_by_uid("test_apm")
    
    # export_aeromaps(cpacs_path, cpacs_out_path):
    
    # TODO Continue when WorkingDir will be refactored
    # then add a working directory for test
    pass