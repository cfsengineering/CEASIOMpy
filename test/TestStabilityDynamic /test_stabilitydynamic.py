"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'StabbilityDynamic/dynamicstability.py'

Python version: >=3.6


| Author : Verdier Loïc
| Creation: 2019-10-24
| Last modifiction: 2019-11-21 (AJ)

"""

#==============================================================================
#   IMPORTS
#==============================================================================

import os
import sys
import numpy as np
import pytest
from pytest import approx
from ceasiompy.utils.cpacsfunctions import open_tixi, open_tigl, close_tixi,   \
                                           create_branch, copy_branch, add_uid,\
                                           get_value, get_value_or_default,    \
                                           add_float_vector, get_float_vector, \
                                           add_string_vector,get_string_vector,\
                                           get_path, aircraft_name
from ceasiompy.utils.apmfunctions import AeroCoefficient, get_aeromap_uid_list,\
                                            create_empty_aeromap, check_aeromap,  \
                                            save_parameters, save_coefficients,   \
                                            get_aeromap, merge_aeroMap,           \
                                            aeromap_from_csv, aeromap_to_csv,     \
                                            delete_aeromap
from ceasiompy.StabilityDynamic.func import get_unic,                \
                                            extract_subelements,     \
                                            change_sign,             \
                                            get_index,               \
                                            speed_derivative_at_trim,\
                                            dynamic_stability_analysis, \
                                            short_period, phugoid, \
                                            roll, spiral, dutch_roll
from ceasiompy.StabilityDynamic.dynamicstability import dynamic_stability_analysis
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

# idx_cml_0 = [i for i in range(len(cml)) if cml[i] == 0][0]

def test_short_period():
    u0 =
    qs =
    i_yy = 100
    mac =
    m_alpha =
    cd0 =
    cl_alpha =
    cm_q =
    assert np.array_equal(short_period(u0, qs, i_yy, mac, m_alpha,  cd0, cl_alpha, cm_q), [1,2])

def test_phugoid():
    u0 =
    cd0 =
    cl0 =
    g =
    assert np.array_equal(phugoid( u0, cd0, cl0, g),[])

def test_roll():
    u0 =
    qs =
    i_xx = 100
    i_zz =
    b =
    cl_p =
    cn_p =
    assert np.array_equal(roll(u0, qs, i_xx, i_zz, b, cl_p, cn_p), [1,2])

def test_spiral() :
    u0 =
    qs =
    b =
    i_xx = 100
    i_yy = 100
    cn_r =
    cl_r =
    cl_beta =
    cn_beta =
    assert np.array_equal(spiral(u0, qs, b, i_xx, i_yy, cn_r, cl_r, cl_beta, cn_beta), [])

def test_dutch_roll():
    u0 =
    qs =
    b =
    i_xx = 100
    i_zz = 100
    cl_p =
    cl_r =
    cl_beta =
    n_p =
    n_r =
    cn_beta =
    assert np.array_equal(dutch_roll(u0, qs, b,i_xx, i_zz, cl_p, cl_r, cl_beta , n_p, n_r, cn_beta), [1,2])

def test_get_unic():
    """ Test function 'get_unic' """
    assert get_unic([1,1,1,1,1,1,1,2,2,2,2,2]) == [1, 2]


def test_extract_subelements():
    """ from a oririginal vector [[1,2,3],[1]] return [1,2,3,1] """
    assert extract_subelements([[1,2,3], [1]]) == [1,2,3,1]


def test_polyfit():
    """ Test function 'np.polyfit' """
    fit = np.polyfit([-1, 1], [-1, 1], 1)  # returns [a,b] of y=ax+b
    intercept = -fit[1]/fit[0]    # Cml = 0 for y = 0  hence cruise agngle = -b/a
    slope = fit[0]

    assert intercept == approx(0.0)
    assert slope == approx(1.0)


def test_change_sign() :
    """Test function 'change_sign' """
    # to simplify understanfing of ARWHERE
    'find index of 0 or the one of element just befor sign change'
    vect1= [-3,-2,-1,1,2,3]
    vect2= [-3,-2,-1,0,1,2,3]
    vect3= [-3,-2,-1,0,0,-1,-3]

    result1 = np.argwhere(np.diff(np.sign(vect1)))
    result2 = np.argwhere(np.diff(np.sign(vect2)))
    result3 = np.argwhere(np.diff(np.sign(vect3)))

    assert np.array_equal(result1,[[2]])
    assert np.array_equal(result2,[[2],[3]])
    assert np.array_equal(result3,[[2],[4]])

    # If all Cml values are 0:
    assert np.array_equal(change_sign(10,[1,2,3,4,5,6],[0,0,0,0,0,0]), ['','',False])
    # If cml curve does not cross the 0
    assert np.array_equal(change_sign(10,[1,2,3,4,5,6],[1,2,3,4,5,6]), ['','',False])
    assert np.array_equal(change_sign(10,[1,2,3,4,5,6],[-1,-2,-3,-4,-5,-6]), ['','',False])
    # If cml Curve crosses the 0 line more than once no stability analysis can be performed
    assert np.array_equal(change_sign(10,[1,2,3,4,5,6],[-1,-2,0,0,-1,-2]), ['','',False])
    assert np.array_equal(change_sign(10,[1,2,3,4,5,6],[-1,-2,0,-1,2,3]), ['','',False])
    # If cml Curve crosses the 0 line twice
    assert np.array_equal(change_sign(10,[1,2,3,4,5,6],[-1,-2,1,2,-1,-2]), ['','',False])
    assert np.array_equal(change_sign(10,[1,2,3,4,5,6],[-1,-2,0,-1,2,3]), ['','',False])



    """ Test function 'np.polyfit' which  find if  Coefficeint Moments, cm, crosse the 0 line only once and return the corresponding angle and the cm derivative at cm=0 """
    [cruise_angle, moment_derivative, crossed] = change_sign(10, [1,2,3] , [0,-1,-4])
    assert [cruise_angle, moment_derivative, crossed] == [1,-1, True]

    [cruise_angle, moment_derivative, crossed] = change_sign(10, [1,2,3] , [4,1,0])
    assert [cruise_angle, moment_derivative, crossed] == [3,-1, True]

    [cruise_angle, moment_derivative, crossed] = change_sign(10, [1,2,3] , [1,0,-1])
    assert [cruise_angle, moment_derivative, crossed] == [2,-1, True]

    [cruise_angle, moment_derivative, crossed] = change_sign(10, [1,2,3] , [2,1,-1])
    assert [cruise_angle, moment_derivative, crossed] == [approx(2.5),approx(-2), True]

    # [cruise_angle, moment_derivative, crossed] = change_sign([1,2,3] , [2,1,1])
    # assert [cruise_angle, moment_derivative, crossed] == ['','', False]

def test_get_index():
    """Test Function 'get_index' """
    list1 = [0,1,3,11,22,30]
    list2 = [0,1,2,3,5]
    list3 = [0,1,0,1,0,1,0,1]

    assert np.array_equal(get_index(list3,1,list1,list2) , [1,3])

def speed_derivative_at_trim():
    alt_list      = [0,0,0,0,0,0,  0,0,0,0,0,0,  1,1,1,1,1,1,  1,1,1,1,1,1]
    mach_list = [0,0,1,1,2,2,  0,0,1,1,2,2,  0,0,1,1,2,2,  0,0,1,1,2,2]
    aoa_list    = [1,2,1,2,1,2,  1,2,1,2,1,2,  1,2,1,2,1,2,  1,2,1,2,1,2]
    aos_list    = [0,0,0,0,0,0,  1,1,1,1,1,1,  0,0,0,0,0,0,  1,1,1,1,1,1]
    cd_list      = [1,2,2,3,3,4,  2,3,2,3,2,3,  1,2,1,2,1,2,  2,3,2,3,2,3]

    idx_alt = [0,1,2,3,4,5,7,8,9,10,11]
    aos = 0
    mach_unic_list = [0,1,2]
    idx_trim_before=0
    idx_trim_after=1
    ratio = 0.5

    left = speed_derivative_at_trim(cd_list,0,idx_alt,aoa_list,aos,aos_list,mach_unic_list,idx_trim_before, idx_trim_after, ratio)
    middle = speed_derivative_at_trim(cd_list,1,idx_alt,aoa,aoa_list,aos,aos_list,mach_unic_list,idx_trim_before, idx_trim_after, ratio)
    right = speed_derivative_at_trim(cd_list,2,idx_alt,aoa,aoa_list,aos,aos_list,mach_unic_list,idx_trim_before, idx_trim_after, ratio)
    assert left == approx(1)
    assert middle == approx(1)
    assert right == approx(1)


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running test_StabilityStatic')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
