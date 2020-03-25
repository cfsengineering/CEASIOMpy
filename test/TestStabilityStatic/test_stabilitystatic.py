"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'StabbilityStatic/staticstability.py'

Python version: >=3.6

| Author: Loic Verdier
| Creation: 2019-10-24
| Last modifiction: 2020-03-24 (AJ)

TODO:

    * ...

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

from ceasiompy.StabilityStatic.func_static import get_unic, get_index, extract_subelements,\
                                            order_correctly, trim_derivative, plot_multicurve,\
                                            trim_condition, interpolation
from ceasiompy.StabilityStatic.staticstability import static_stability_analysis

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


def test_get_index():
    """Test Function 'get_index'"""
    list1 = [0,1,3,11,22,30]
    list2 = [0,1,2,3,5]
    list3 = [1,3,4,5,6,7]
    assert np.array_equal(get_index(list1,list2,list3) , [1,3])


def test_extract_subelements():
    """ from a oririginal vector [[1,2,3],[1]] return [1,2,3,1] """
    assert extract_subelements([[1,2,3], [1]]) == [1,2,3,1]


def test_order_correctly():
    """ Order list X in incresing order and moves element in Y in the same way as elements in X have been ordered"""
    X = [0,-2,-1,1,2]
    Y = [1, 2,  3,4,5]
    assert np.array_equal(order_correctly(X,Y), ([-2, -1, 0, 1, 2], [2, 3, 1, 4, 5] ))





def test_polyfit():
    """ Test function 'np.polyfit' """
    fit = np.polyfit([-1, 1], [-1, 1], 1)  # returns [a,b] of y=ax+b
    intercept = -fit[1]/fit[0]    # Cml = 0 for y = 0  hence cruise agngle = -b/a
    slope = fit[0]

    assert intercept == approx(0.0)
    assert slope == approx(1.0)


def test_trim_condition():
    """Find the required aoa for level flight and return index """
    alt = 0
    mach = 0.6
    cl_required = 1.3182950297023035
    aoa =  [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    cl = [0.12369, 0.25968, 0.39544, 0.53093, 0.66608, 0.80082, 0.93512, 1.06889, 1.20208, 1.33464,\
             1.46649, 1.59758, 1.72786, 1.85724, 1.98569, 2.11312]
    (trim_aoa, idx_trim_before, idx_trim_after, ratio) = trim_condition(alt, mach, cl_required, cl, aoa)
    assert((trim_aoa, idx_trim_before, idx_trim_after, ratio) == (3.876697568665536,8,9,0.876697568665536))


def test_interpolation():
    """Return the interpolation between list[idx1] and list[idx2] of vector "list"."""
    list = [0,1,2]
    idx1 = 1
    idx2 = 2
    ratio = 0.5
    assert interpolation(list, idx1, idx2, ratio) == 1.5


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


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running test_StabilityStatic')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
