"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'StabbilityDynamic/dynamicstability.py'

Python version: >=3.6

| Author: Loic Verdier
| Creation: 2019-10-24
| Last modifiction: 2020-04-07 (AJ)

TODO:

    * Create more tests

"""


#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import numpy as np
import pytest
from pytest import approx

import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf

from ceasiompy.StabilityDynamic.func_dynamic import get_unic, interpolation, get_index, \
                                            speed_derivative_at_trim, adimensionalise,\
                                            speed_derivative_at_trim_lat, concise_derivative_longi, concise_derivative_lat,\
                                            longi_root_identification, direc_root_identification,\
                                            check_sign_longi, check_sign_lat,\
                                            short_period_damping_rating, short_period_frequency_rating, cap_rating, \
                                            phugoid_rating, roll_rating, spiral_rating, dutch_roll_rating, plot_splane,\
                                            longi_mode_characteristic, direc_mode_characteristic, trim_condition

from ceasiompy.utils.ceasiomlogger import get_logger
import ceasiompy.__init__
LIB_DIR = os.path.dirname(ceasiompy.__init__.__file__)

log = get_logger(__file__.split('.')[0])

#==============================================================================
#   CLASSES
#==============================================================================


#==============================================================================
#   FUNCTIONS
#==============================================================================

def test_get_unic():
    """ Test function 'get_unic' """

    assert get_unic([1,1,1,1,1,1,1,2,2,2,2,2]) == [1, 2]


def test_interpolation():
    """Return the interpolation between list[idx1] and list[idx2] of vector "list"."""

    list = [0,1,2]
    idx1 = 1
    idx2 = 2
    ratio = 0.5

    assert interpolation(list, idx1, idx2, ratio) == 1.5


def test_get_index():
    """Test Function 'get_index'"""

    list1 = [0,1,3,11,22,30]
    list2 = [0,1,2,3,5]
    list3 = [1,3,4,5,6,7]

    assert np.array_equal(get_index(list1,list2,list3) , [1,3])


def test_speed_derivative_at_trim():
    """ Gives the speed derivative of coefficient Cd for trim conditions given by:
    idx_trim_before , idx_trim_after and ratio '"""

    alt_list      = [0,0,0,0,0,0,  0,0,0,0,0,0,  1,1,1,1,1,1,  1,1,1,1,1,1]
    mach_list = [0,0,1,1,2,2,  0,0,1,1,2,2,  0,0,1,1,2,2,  0,0,1,1,2,2]
    aoa_list    = [1,2,1,2,1,2,  1,2,1,2,1,2,  1,2,1,2,1,2,  1,2,1,2,1,2]
    aos_list    = [0,0,0,0,0,0,  1,1,1,1,1,1,  0,0,0,0,0,0,  1,1,1,1,1,1]
    cd_list      = [1,2,2,3,3,4,  2,3,2,3,2,3,  1,2,1,2,1,2,  2,3,2,3,2,3]

    mach =2
    idx_alt = [0,1,2,3,4,5,7,8,9,10,11]
    aos = 0
    mach_unic = [0,1,2]
    idx_trim_before=0
    idx_trim_after=1
    ratio = 0.5
    parameter_list = cd_list

    #cd_u = speed_derivative_at_trim(parameter_list,mach,mach_list,idx_alt,aoa_list,aos,aos_list,mach_unic_list,idx_trim_before, idx_trim_after, ratio)
    cd_u = speed_derivative_at_trim(parameter_list , mach, mach_list, mach_unic, idx_alt, aoa_list, aos_list, idx_trim_before, idx_trim_after, ratio)

    assert cd_u == 1


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running test_StabilityStatic')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
