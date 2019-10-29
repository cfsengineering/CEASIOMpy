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

def test_argwhere_diff_sign():
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

def test_get_aeromap():
    """ Test function 'get_aeromap' """

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','test_getaeromap.xml')

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


def test_plot_torque_vs_angle():
    """ Test function 'plot_torque_vs_angle' """
    plot_legend = ['Legend']
    xlabel = 'xlabel'
    ylabel = 'ylabel'

    # Vertical axis on the left and horizontal axis at the bottom : |_
    plot_title = 'Vertical axis on the left and horizontal axis at the bottom : |_'
    y_axis = [[1,2,3,4]]
    x_axis = [[1,2,3,4]]
    plot_torque_vs_angle(y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel)

    # Vertical axis on the middle  and horizontal axis at the bottom  : _|_
    plot_title = 'Vertical axis on the middle  and horizontal axis at the bottom  : _|_'
    y_axis = [[1,2,3,4]]
    x_axis = [[-1,2,3,4]]
    plot_torque_vs_angle(y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel)

    # Vertical axis on the right and horizontal axis at the bottom : _|
    plot_title = 'Vertical axis on the right and horizontal axis at the bottom : _|'
    y_axis = [[1,2,3,4]]
    x_axis = [[-1,-2,-3,-4]]
    plot_torque_vs_angle(y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel)

    # Vertical  on the left and horizontal axis at the middle : |--
    plot_title = 'Vertical  on the left and horizontal axis at the middle : |--'
    y_axis = [[-1,2,3,4]]
    x_axis = [[1,2,3,4]]
    plot_torque_vs_angle(y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel)

    # Vertical axis on the middle and horizontal axis at the middle : +
    plot_title = 'Vertical axis on the middle and horizontal axis at the middle : +'
    y_axis = [[-1,2,3,4]]
    x_axis = [[-1,2,3,4]]
    plot_torque_vs_angle(y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel)

    # Vertical axis on the right and horizontal axis at the middle : --|
    plot_title = 'Vertical axis on the right and horizontal axis at the middle : --|'
    y_axis = [[-1,2,3,4]]
    x_axis = [[-1,-2,-3,-4]]
    plot_torque_vs_angle(y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel)

    # Vertical axis on the left and horizontal axis at the top : |```
    plot_title = 'Vertical axis on the left and horizontal axis at the top : |**'
    y_axis = [[-1,-2,-3,-4]]
    x_axis = [[1,2,3,4]]
    plot_torque_vs_angle(y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel)

    # Vertical axis on the middle and horizontal axis at the top : '''|'''
    plot_title = ' Vertical axis on the middle and horizontal axis at the top : **|**'
    y_axis = [[-1,-2,-3,-4]]
    x_axis = [[-1,2,3,4]]
    plot_torque_vs_angle(y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel)

    # Vertical axis on the right and horizontal axis at the top : '''|
    plot_title = 'Vertical axis on the right and horizontal axis at the top : **|'
    y_axis = [[-1,-2,-3,-4]]
    x_axis = [[-1,-2,-3,-4]]
    plot_torque_vs_angle(y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel)


def test_static_stability_analysis():
    """Test function 'staticStabilityAnalysis' """

    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolInput', 'ToolInput.xml')
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
    static_stability_analysis(cpacs_path, aeromap_uid)

    # Assert that all error messages are present
    log_path =  'r"' + MODULE_DIR + '/test_StabilityStatic.log' + '"'

    with open(log_path) as f:
        for line in f:
            reported_errors += 1

    assert reported_errors == 245


#==============================================================================
#    MAIN
#==============================================================================

if __name__ == '__main__':

    log.info('Running test_StabilityStatic')
    log.info('To run test use the following command:')
    log.info('>> pytest -v')
