"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Test functions for 'StabilityStatic/staticstability.py'

Python version: >=3.7

| Author: Loic Verdier
| Creation: 2019-10-24

TODO:

    * Create better tests, especially for 'test_static_stability_analysis'
    * Check if these tests are really useful

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import numpy as np
from pytest import approx

from cpacspy.cpacsfunctions import get_string_vector, get_value, open_tixi

from ceasiompy.StabilityStatic.staticstability import static_stability_analysis
from ceasiompy.StabilityStatic.func_static import (
    get_unic,
    get_index,
    extract_subelements,
    order_correctly,
    trim_derivative,
    plot_multicurve,
    trim_condition,
    interpolation,
)


import ceasiompy.__init__

LIB_DIR = os.path.dirname(ceasiompy.__init__.__file__)


# ==============================================================================
#   CLASSES
# ==============================================================================


# ==============================================================================
#   FUNCTIONS
# ==============================================================================

# idx_cml_0 = [i for i in range(len(cml)) if cml[i] == 0][0]

# Some of the following test should be remove
# (bulltin function should be use instead)
def test_get_unic():
    """Test function 'get_unic'"""
    assert get_unic([1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2]) == [1, 2]


def test_get_index():
    """Test Function 'get_index'"""
    list1 = [0, 1, 3, 11, 22, 30]
    list2 = [0, 1, 2, 3, 5]
    list3 = [1, 3, 4, 5, 6, 7]
    assert np.array_equal(get_index(list1, list2, list3), [1, 3])


def test_extract_subelements():
    """from a original vector [[1,2,3],[1]] return [1,2,3,1]"""
    assert extract_subelements([[1, 2, 3], [1]]) == [1, 2, 3, 1]


def test_order_correctly():
    """Order list X in incresing order and moves element in Y in the same way as elements in X have been ordered"""
    X = [0, -2, -1, 1, 2]
    Y = [1, 2, 3, 4, 5]
    assert np.array_equal(order_correctly(X, Y), ([-2, -1, 0, 1, 2], [2, 3, 1, 4, 5]))


def test_polyfit():
    """Test function 'np.polyfit'"""
    fit = np.polyfit([-1, 1], [-1, 1], 1)  # returns [a,b] of y=ax+b
    intercept = -fit[1] / fit[0]  # Cml = 0 for y = 0  hence cruise angle = -b/a
    slope = fit[0]

    assert intercept == approx(0.0)
    assert slope == approx(1.0)


def test_trim_condition():
    """Find the required aoa for level flight and return index"""
    alt = 0
    mach = 0.6
    cl_required = 1.3182950297023035
    aoa = [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    cl = [
        0.12369,
        0.25968,
        0.39544,
        0.53093,
        0.66608,
        0.80082,
        0.93512,
        1.06889,
        1.20208,
        1.33464,
        1.46649,
        1.59758,
        1.72786,
        1.85724,
        1.98569,
        2.11312,
    ]
    (trim_aoa, idx_trim_before, idx_trim_after, ratio) = trim_condition(
        alt, mach, cl_required, cl, aoa
    )
    assert (trim_aoa, idx_trim_before, idx_trim_after, ratio) == (
        3.876697568665536,
        8,
        9,
        0.876697568665536,
    )


def test_interpolation():
    """Return the interpolation between list[idx1] and list[idx2] of vector "list"."""
    list = [0, 1, 2]
    idx1 = 1
    idx2 = 2
    ratio = 0.5
    assert interpolation(list, idx1, idx2, ratio) == 1.5


def test_static_stability_analysis():
    """Test function 'staticStabilityAnalysis'"""

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = os.path.join(MODULE_DIR, "ToolInput", "CPACSTestStability.xml")
    cpacs_out_path = os.path.join(MODULE_DIR, "ToolOutput", "CPACSTestStability.xml")
    csv_path = MODULE_DIR + "/ToolInput/csvtest.csv"

    tixi = open_tixi(cpacs_path)
    # Get Aeromap UID list

    # aeromap_uid = uid_list[0]
    # # Import aeromap from the CSV to the xml

    # close_tixi(tixi, cpacs_out_path)

    # Make the static stability analysis, on the modified xml file
    static_stability_analysis(cpacs_path, cpacs_out_path)

    tixi = open_tixi(cpacs_out_path)
    static_xpath = "/cpacs/toolspecific/CEASIOMpy/stability/static"
    long_static_stable = get_value(tixi, static_xpath + "/results/longitudinalStaticStable")
    lat_static_stable = get_value(tixi, static_xpath + "/results/lateralStaticStable")
    dir_static_stable = get_value(tixi, static_xpath + "/results/directionnalStaticStable")

    assert long_static_stable
    assert lat_static_stable
    assert not dir_static_stable

    trim_longi_alt = get_value(tixi, static_xpath + "/trimConditions/longitudinal/altitude")
    trim_longi_mach = get_value(tixi, static_xpath + "/trimConditions/longitudinal/machNumber")
    trim_longi_aoa = get_value(tixi, static_xpath + "/trimConditions/longitudinal/angleOfAttack")
    trim_longi_aos = get_value(tixi, static_xpath + "/trimConditions/longitudinal/angleOfSideslip")

    assert trim_longi_alt == 1400
    assert trim_longi_mach == 0.6
    assert trim_longi_aoa == 3.25808
    assert trim_longi_aos == 0

    trim_dir_alt = get_string_vector(tixi, static_xpath + "/trimConditions/directional/altitude")
    trim_dir_mach = get_string_vector(
        tixi, static_xpath + "/trimConditions/directional/machNumber"
    )
    trim_dir_aoa = get_string_vector(
        tixi, static_xpath + "/trimConditions/directional/angleOfAttack"
    )
    trim_dir_aos = get_string_vector(
        tixi, static_xpath + "/trimConditions/directional/angleOfSideslip"
    )

    assert trim_dir_alt == ["2400", "2500", "2600", "2700"]
    assert trim_dir_mach == ["0.6", "0.5", "0.5", "0.5"]
    assert trim_dir_aoa == ["1", "2", "4", "2.5"]
    assert trim_dir_aos == ["0", "0", "0", "0"]

    tixi.save(cpacs_out_path)


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Running test_StabilityStatic")
    print("To run test use the following command:")
    print(">> pytest -v")
