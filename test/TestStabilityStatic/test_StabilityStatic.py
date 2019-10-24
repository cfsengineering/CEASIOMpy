"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'StabbilityStatic/staticstability.py'

Python version: >=3.6


| Author : Aidan Jungo
| Creation: 2019-07-24
| Last modifiction: 2019-09-27
"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import numpy as np
import pytest
from pytest import approx

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import open_tixi, get_value
from ceasiompy.CLCalculator.clcalculator import calculate_cl, get_cl

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================


# np.sign(cml)
# len(find_idx)
# list_legend.append(curve_legend)
# cml.count(0)
# idx_cml_0 = [i for i in range(len(cml)) if cml[i] == 0][0]

def test_Argwhere_Diff_Sign():
    'find index of 0 or the one of element just befor sign change'
    vect1= [-3,-2,-1,1,2,3]
    vect2= [-3,-2,-1,0,1,2,3]
    vect3= [-3,-2,-1,0,1,2,3]
    vect4= [-3,-2,-1,0,0,1,3]
    vect5= [-3,-2,-1,0,0,-1,-3]
    assert np.argwhere(np.diff(np.sign(vect1))) == [[3]]
    assert np.argwhere(np.diff(np.sign(vect2))) == [[2]]

def test_polyfit():
    """ Test function 'np.polyfit' """
    fit = np.polyfit([-1, 1], [-1, 1], 1)  # returns [a,b] of y=ax+b
    intercept = -fit[1]/fit[0]    # Cml = 0 for y = 0  hence cruise agngle = -b/a
    slope = fit[0]

    assert intercept == 0
    assert slope == 2

# Fill the lists of unique different values
def Find_Unic(vector, vector_unic=[]):
    """ Return vector with  all the different element of the initial vector  but having only one occurence  """
    for element in vector :
        if element not in vector_unic :
            vector_unic.append(element)
    return vector_unic

def test_Find_Unic():
    """ Test function 'Find_Unic' """
    AOA=[-1,-1,0,1,1,1,1,1,2]
    aoa_unic = Find_Unic(AOA)
    assert aoa_unic == [-1,0,1,2]


def test_get_aeromap():
    """ Test function 'get_aeromap' """

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','cpacs_test_file.xml')

    tixi = open_tixi(cpacs_path)
    Coeffs = get_aeromap(tixi, "aeroMap_pyTornado")

    ALT = Coeffs.alt
    MACH = Coeffs.mach
    AOA = Coeffs.aoa
    CML = Coeffs.cml
    AOS = Coeffs.aos
    CMS = Coeffs.cms

    assert ALT == [1,2,3]
    assert AOA == [1,2,3]
    assert MACH == [1,2,3]
    assert CML == [1,2,3]
    assert AOS == [1,2,3]
    assert CMS == [1,2,3]

#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running test_StabilityStatic')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
