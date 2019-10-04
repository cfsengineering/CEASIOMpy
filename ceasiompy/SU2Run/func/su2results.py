"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Ectract reults from SU2 calculations

Python version: >=3.6

| Author: Aidan Jungo
| Creation: 2019-10-02
| Last modifiction: 2019-10-03

TODO:

    * Modify and improvre
    * Gather of reults function here

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import math
import pandas
import matplotlib

import vtk
import numpy as np
from scipy.sparse import csr_matrix
from six import iteritems
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           add_uid, create_branch, copy_branch,\
                                           get_value, get_value_or_default,    \
                                           aircraft_name
from ceasiompy.utils.mathfunctions import euler2fix, fix2euler
from ceasiompy.utils.standardatmosphere import get_atmosphere, plot_atmosphere
from ceasiompy.utils.moduleinterfaces import check_cpacs_input_requirements

from ceasiompy.utils.su2functions import read_config

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def get_wetted_area(wkdir):
    """ Function get the wetted area calculated by SU2

    Function 'get_wetted_area' finds the SU2 logfile and returns the wetted
    area value previously calculated by SU2.

    Args:
        wkdir (str): Path to the working directory

    Returns:
        wetted_area (float): Wetted area calculated by SU2 [m^2]

    """

    wetted_area = None
    su2_logfile_path = ''

    # Find a logfile in wkdir
    for (root, dirs, files) in os.walk(wkdir):
        for file in files:
            if file == 'logfileSU2_CFD.log':
                su2_logfile_path = os.path.join(root, file)
                break

    if su2_logfile_path == '':
        log.warning('No logfile has been found for working directory!')

    # Read the logfile
    with open(su2_logfile_path) as f:
        for line in f.readlines():
            if 'Wetted area =' in line:
                wetted_area = float(line.split(' ')[3])
                break

    if wetted_area is None:
        # raise ValueError('No value has been found for the wetted area!')
        log.warning('No value has been found for the wetted area!')
        return 0

    else:
        log.info('Wetted area value has been found and is equal to '
                  + str(wetted_area) + ' [m^2]')
        return wetted_area


# This function should be modified
def get_efficiency(force_path):
    """Function to get efficiency (CL/CD)

    Function 'get_efficiency' the CL/CD ratio in the results file
    (forces_breakdown.dat)

    Args:
        force_path (str): Path to the Force Breakdown result file

    Returns:
        cl_cd (float): CL/CD ratio [-]

    """

    cl_cd = None

    with open(force_path) as f:
        for line in f.readlines():
            if 'CL/CD' in line:
                cl_cd = float(line.split(':')[1].split('|')[0])
                break
    if cl_cd is None:
        raise ValueError('No value has been found for the CL/CD ratio!')
    else:
        log.info('CL/CD ratio has been found and is equal to: ' \
                  + str(cl_cd) + '[-]')
        return cl_cd


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Nothing to execute!')
