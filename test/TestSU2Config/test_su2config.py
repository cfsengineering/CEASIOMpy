"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'lib/SU2Config/su2config.py'

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2019-08-13
| Last modifiction: 2019-08-13

TODO:

    * Refactor this tests for the new /toolspecific structure
    * This test procedure could be imporve

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys

import pytest
from pytest import approx
import filecmp

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           get_value
from ceasiompy.SU2Config.su2config import get_mesh_marker, create_config

log = get_logger(__file__.split('.')[0])

# Default CPACS file to test
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CPACS_IN_PATH = MODULE_DIR + '/ToolInput/D150_AGILE_Hangar_v3.xml'
CPACS_OUT_PATH = MODULE_DIR + '/ToolOutput/ToolOutput.xml'


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def test_get_mesh_marker():
    """Test function 'get_largest_wing_dim' """

    # Test no marker
    su2_mesh_path = MODULE_DIR + '/ToolInput/NoMarkerMesh.su2'
    marker_list_shoud_get = []
    marker_list = get_mesh_marker(su2_mesh_path)
    assert marker_list_shoud_get == marker_list

    # Test Marker list
    su2_mesh2_path = MODULE_DIR + '/ToolInput/SimpleMesh.su2'
    marker_list_shoud_get = ['Fuselage','Wing']
    marker_list = get_mesh_marker(su2_mesh2_path)

    assert marker_list_shoud_get == marker_list


def test_create_config():
    """Test function 'create_config' """

    cpacs_path = MODULE_DIR + '/ToolInput/simpletest_cpacs.xml'
    cpacs_out_path = MODULE_DIR + '/ToolOutput/ToolOutput.xml'
    su2_mesh_path = MODULE_DIR + '/ToolInput/SimpleMesh.su2'
    config_output_path = MODULE_DIR + '/ToolOutput/ToolOutput.cfg'

    create_config(cpacs_path, cpacs_out_path, su2_mesh_path, config_output_path)

    config_should_get_path = MODULE_DIR + '/ToolInput/ToolOutput_ShouldGet.cfg'

    # If there is a difference between the two files, it will not indicate
    # where, so you should try to make a diff of the two file (e.g. with kdiff3)
    # (outside of CEASIOM)

    assert filecmp.cmp(config_should_get_path, config_output_path)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running Test Math Functions')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
