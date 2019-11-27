"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'StabbilityStatic/staticstability.py'

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

from ceasiompy.utils.ceasiomlogger import get_logger
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

from ceasiompy.StabilityStatic.staticstability import get_unic,                \
                                                      extract_subelements,     \
                                                      change_sign,             \
                                                      change_sign,             \
                                                      get_index,               \
                                                      static_stability_analysis

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
    """Test Function 'get_index'"""
    list1 = [0,1,3,11,22,30]
    list2 = [0,1,2,3,5]
    list3 = [0,1,0,1,0,1,0,1]

    assert np.array_equal(get_index(list3,1,list1,list2) , [1,3])


def test_static_stability_analysis():
    """Test function 'staticStabilityAnalysis' """

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','CPACSTestStability.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolInput', 'CPACSTestStability.xml')
    csv_path = MODULE_DIR + '/ToolInput/csvtest.csv'

    tixi = open_tixi(cpacs_path)
    # Get Aeromap UID list
    uid_list = get_aeromap_uid_list(tixi)
    aeromap_uid = uid_list[0]
    # Import aeromap from the CSV to the xml
    aeromap_from_csv(tixi, aeromap_uid, csv_path)
    close_tixi(tixi, cpacs_out_path)

    # Make the static stability analysis, on the modified xml file
    static_stability_analysis(cpacs_path, cpacs_out_path)

    # Assert that all error messages are present
    log_path = os.path.join(LIB_DIR,'StabilityStatic','staticstability.log')

    graph_cruising = False
    errors = ''
    #Open  log file
    with open(log_path, "r") as f :
        # For each line in the log file
        for line in f :
            # if the info insureing that the graph of cruising aoa VS mach has been generated.
            if 'graph : cruising aoa vs mach genrated' in line :
                graph_cruising = True
            # if 'warning' or 'error ' is in line
            if  'ERROR' in line :
                # check if error type (altitude) is in line
                errors += line

    # Assert that all error type happend only once.
    assert graph_cruising == True

    ERR = ['ERROR - Alt = 1200.0Cm does not cross the 0 line, aircraft not stable',
           'ERROR - Alt = 1210.0Cm does not cross the 0 line, aircraft not stable',
           'ERROR - Alt = 1300.0The Cm curves crosses more than once the 0 line, no stability analysis performed',
           'ERROR - Alt = 1310.0The Cm curves crosses more than once the 0 line, no stability analysis performed',
           'ERROR - Alt = 1400.0Vehicle *NOT* longitudinaly staticaly stable',
           'ERROR - Alt = 1500.0Vehicle *NOT* longitudinaly staticaly stable',
           'ERROR - Alt = 1600.0Vehicle *NOT* longitudinaly staticaly stable',
           'ERROR - Alt = 1700.0Vehicle *NOT* longitudinaly staticaly stable',
           'ERROR - Alt = 1800.0 , at least 2 aoa values are equal',
           'ERROR - Alt = 1800.0 , at least 2 aos values are equal',
           'ERROR - Alt = 2200.0Cm does not cross the 0 line, aircraft not stable',
           'ERROR - Alt = 2210.0Cm does not cross the 0 line, aircraft not stable',
           'ERROR - Alt = 2300.0The Cm curves crosses more than once the 0 line, no stability analysis performed',
           'ERROR - Alt = 2310.0The Cm curves crosses more than once the 0 line, no stability analysis performed',
           'ERROR - Alt = 2400.0Vehicle *NOT* directionnaly staticaly stable',
           'ERROR - Alt = 2500.0Vehicle *NOT* directionnaly staticaly stable',
           'ERROR - Alt = 2600.0Vehicle *NOT* directionnaly staticaly stable',
           'ERROR - Alt = 2700.0Vehicle *NOT* directionnaly staticaly stable',
           'ERROR - Alt = 2800.0 , at least 2 aoa values are equal',
           'ERROR - Alt = 2800.0 , at least 2 aos values are equal',
           'ERROR - Alt = 4000.0Vehicle *NOT* longitudinaly staticaly stable',
           'ERROR - Alt = 5000.0Vehicle *NOT* longitudinaly staticaly stable',
           'ERROR - Alt = 6000.0Vehicle *NOT* longitudinaly staticaly stable',
           'ERROR - Alt = 7000.0Vehicle *NOT* directionnaly staticaly stable',
           'ERROR - Alt = 7000.0Vehicle *NOT* directionnaly staticaly stable',
           'ERROR - Alt = 8000.0Vehicle *NOT* directionnaly staticaly stable',
           'ERROR - Alt = 9000.0Vehicle *NOT* directionnaly staticaly stable']
    for the_error in ERR:
        assert the_error in errors , 'Reffer to the the altitude in the .odt & .cvs files'
    # TODO, change the way it is tested
    #assert np.array_equal(error_list,occurence)
    # print(errors)

#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running test_StabilityStatic')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
