"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Function to deformed mesh from a surface file with SU2 mesh deformation

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2020-11-25
| Last modifiction: 2020-11-25

TODO:

    *

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import shutil
import numpy as np
import pandas as pd

import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.su2functions as su2f

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

REF_XPATH = '/cpacs/vehicles/aircraft/model/reference'
WINGS_XPATH = '/cpacs/vehicles/aircraft/model/wings'
SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def generate_fromfile_meshdef_config(cpacs_path,cpacs_out_path,skip_config=False,skip_su2=False):
    """Function to generate all deform meshes with SU2 from CPACS data

    Function 'generate_fromfile_meshdef_config' reads data in the CPACS file
    and generate the corresponding directory and config file which allow to
    generate meshes deformed from a surface file.

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file
        skip_config (bool):
        skip_su2 (bool):

    """

    print('TODO')
