"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'StabbilityStatic/staticstability.py'

Python version: >=3.6


| Author : Verdier Loïc
| Creation: 2019-10-24
| Last modifiction: 2019-10-24

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
                                                      change_sign_once,        \
                                                      unexpected_sign_change,  \
                                                      static_stability_analysis\

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


def test_change_sign_once() :
    """ Test function 'np.polyfit' which  find if  Coefficeint Moments, cm, crosse the 0 line only once and return the corresponding angle and the cm derivative at cm=0 """
    [cruise_angle, moment_derivative, crossed] = change_sign_once([1,2,3] , [0,-1,-4], False)
    assert [cruise_angle, moment_derivative, crossed] == [1,-1, True]

    [cruise_angle, moment_derivative, crossed] = change_sign_once([1,2,3] , [4,1,0], False)
    assert [cruise_angle, moment_derivative, crossed] == [3,-1, True]

    [cruise_angle, moment_derivative, crossed] = change_sign_once([1,2,3] , [1,0,-1], False)
    assert [cruise_angle, moment_derivative, crossed] == [2,-1, True]

    [cruise_angle, moment_derivative, crossed] = change_sign_once([1,2,3] , [2,1,-1], False)
    assert [cruise_angle, moment_derivative, crossed] == [approx(2.5),approx(-2), True]


def test_unexpected_sign_change() :
    """Test function 'unexpected_sign_change' """
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
    assert unexpected_sign_change(10,[0,0,0,0,0,0], stability = True) == False
    # If cml curve does not cross the 0
    assert unexpected_sign_change(10,[1,2,3,4,5,6], stability = True) == False
    assert unexpected_sign_change(10,[-1,-2,-3,-4,-5,-6], stability = True) == False
    # If cml Curve crosses the 0 line more than once no stability analysis can be performed
    assert unexpected_sign_change(10,[-1,-2,0,0,-1,-2], stability = True) == False
    assert unexpected_sign_change(10,[-1,-2,0,-1,2,3], stability = True) == False
    # If cml Curve crosses the 0 line twice
    assert unexpected_sign_change(10,[-1,-2,1,2,-1,-2], stability = True) == False
    assert unexpected_sign_change(10,[-1,-2,0,-1,2,3], stability = True) == False


def test_static_stability_analysis():
    """Test function 'staticStabilityAnalysis' """

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','CPACSTestStability.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolInput', 'CPACSTestStability.xml')
    csv_path = MODULE_DIR + '/ToolInput/csvtest.csv'
    # Open tixi Handle
    tixi = open_tixi(cpacs_path)
    # Get Aeromap UID list
    uid_list = get_aeromap_uid_list(tixi)
    aeromap_uid = uid_list[0]
    # Import aeromap from the CSV to the xml
    aeromap_from_csv( tixi, aeromap_uid, csv_path)
    # Save the xml file
    close_tixi(tixi, cpacs_out_path)

    # Make the static stability analysis, on the modified xml file
    plot = False
    static_stability_analysis(cpacs_path, cpacs_out_path, plot)

    # Assert that all error messages are present
    log_path = os.environ['PYTHONPATH'] + '/ceasiompy/StabilityStatic/staticstability.log'

    graph_cruising = False
    error_type = [1200,1300, 1400, 1500,1600,1700,1800, 2200, 2300, 2400,2500,2600, 2700, 2800, 4000, 5000,  6000, 7000, 8000, 9000]
    error_list =   [      2,     2 ,       1,       1,       1,     1,      1,       2,       2,       1,       1,      1,      1,       1,       1,        1,        1,      1,       1,       1]
    occurence = np.zeros((len(error_type)), dtype=int)

    # Open  log file
    with open(log_path, "r") as f :
        # For each line in the log file
        for line in f :
            # if the info insureing that the graph of cruising aoa VS mach has been generated.
            if 'graph : cruising aoa vs mach genrated' in line :
                graph_cruising = True
            # if 'warning' or 'error ' is in line
            if  'ERROR' in line :
                # check if error type (altitude) is in line
                for index, error in enumerate(error_type, 0) :
                    # if error type is in line, add +1 in occurence fitting to error type position
                    if str(error) in line :
                        occurence[index] += 1
    # Compare if
    # Assert that all error type happend only once.
    assert graph_cruising == True
    assert np.array_equal(error_list,occurence)
    # assert occurence == error_list



#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    print(os.environ['PYTHONPATH']+ '/ceasiompy/StabilityStatic/staticstability.log')

    log.info('Running test_StabilityStatic')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
