"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This program stores all function needed for stability analysis (dynamic and static)

Python version: >=3.7

| Author: Loic Verdier
| Creation: 2020-02-24

TODO:

    * ...

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_DIR = Path(__file__).parent

# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_unic(vector):
    """Return a vector with the same element having only one occurrence.

    Args:
        vector (list): List of element which may contains double elements

    Returns:
        vector_unic (list): List of unic values ordered in ascending way
    """
    vector_unic = []
    for elem in vector:
        if elem not in vector_unic:
            vector_unic.append(elem)
    vector_unic.sort()

    return vector_unic


def get_index(idx_list1, idx_list2, idx_list3):
    """Function to get index list

    Function 'get_index' returns the common value between the 3 different lists

    Args:
        idx_list1 (list): list of indexes (integer)
        idx_list2 (list): list of indexes (integer)
        idx_list3 (list): list of indexes (integer)

    Returns:
        find_idx (list): list of index (integer) common in the 3 lists
    """

    # List of index of elements which have the same index in vectors list, list1, list2
    find_idx = []

    # Fill   the liste find_index
    for idx1 in idx_list1:
        for idx2 in idx_list2:
            for idx3 in idx_list3:
                if idx1 == idx2 == idx3:
                    find_idx.append(idx1)

    return find_idx


def interpolation(list, idx1, idx2, ratio):
    """Return the interpolation between list[idx1] and list[idx2] of vector "list".

    Args:
        list (vector) : List of values
        idx1 : the index of the first value in the list
        idx2 : the index of the second value in the list
        ratio : the distance of the interpolation point between the 2 values:
            e.i. : y = y1 +  x* (y2-y1)/(x2-x1) = y1 + ratio*(y2-y1)

    Returns:
        value: the interpolated value
    """
    value = list[idx1] + ratio * (list[idx2] - list[idx1])
    return value


# TODO: check function exist or change name
def extract_subelements(vector):
    """Transform multiple element list into a 1D vector

    Function 'extract_subelements' return [1,2,3,1] from an original vector
    like [[1,2,3], [1]]

    Args:
        vector (list of list): Original list of list

    Returns:
        extracted (list): Return 1D list
    """

    extracted = []
    for elem in vector:
        for value in elem:
            extracted.append(value)

    return extracted


# TODO: replace this function by "A,B = zip(*sorted(zip(X, Y)))"
def order_correctly(A, B):
    """Order list A in incresing order and moves element in B in the same way as elements in
    A have been ordered

    Args:
        A (list) : a list  of floats must be of the same length as B
        B (list) : a list  of floats must be of the same length as A

    Returns:
        X = [0,-2,-1,1,2]
        Y = [1, 2,  3,4,5]
        tri(X,Y) returns :  ([-2, -1, 0, 1, 2], [2, 3, 1, 4, 5])

        A plot with different curves if asked.
    """

    n = len(A)
    for i in range(n):
        for j in range(n):
            if A[i] > A[j] and i <= j:
                A[i], A[j] = A[j], A[i]
                B[i], B[j] = B[j], B[i]
    return A, B


# Function derivative, or more trim condition function
def trim_derivative(alt, mach, list1, list2):
    """Find if a moments coefficient cm cross the 0 line, once or more
        Find if a moment coefficient cm. crosse the 0 line only once and return
        the corresponding angle and the cm derivative at cm=0

    Args:
        alt (float): Altitude [m]
        mach (float) : Mach Number [-]
        list1 cm (list): Moment coefficient [-]
        list2 angle (list): Angle of attack (or sideslip) [deg]

    Returns:
        cruise_angle (float): Angle to get cm. = 0
        trim_parameter (float): Moment derivative at cruise_angle
        cross (boolean): List of unique value
    """

    crossed = True
    trim_value = 0
    trim_parameter = 0
    idx_trim_before = 0
    idx_trim_after = 0
    ratio = 0

    # Check moment coefficient list
    if len(np.argwhere(np.diff(np.sign(list1)))) == 0:
        crossed = False
        # If all list1. values are 0:
        if list1.count(0) == len(list1):
            log.warning(
                "Alt = {}, mach = {} moment coefficients list is composed of 0 only.".format(
                    alt, mach
                )
            )
        # If cm curve does not cross the 0 line
        else:
            log.error(
                "Alt = {}, mach = {} moment coefficients list does not cross the 0 line, aircraft not stable, trimm conditions not achieved.".format(
                    alt, mach
                )
            )
    # If list1. Curve crosses the 0 line more than once no stability analysis can be performed
    elif len(np.argwhere(np.diff(np.sign(list1)))) > 2 or list1.count(0) > 1:
        log.error(
            "Alt = {}, mach = {} moment coefficients list crosses more than once the 0 line, no stability analysis performed".format(
                alt, mach
            )
        )
        crossed = False
    # If list1. Curve crosses the 0 line twice
    elif 0 not in np.sign(list1) and len(np.argwhere(np.diff(np.sign(list1)))) == 2:
        log.error(
            "Alt = {}, mach = {} moment coefficients list crosses the 0 line twice, no stability analysis performed".format(
                alt, mach
            )
        )
        crossed = False
    # If   0 is in list1
    elif 0 in np.sign(list1) and list1.count(0) == 1 and crossed:
        idx_list1_0 = [i for i in range(len(list1)) if list1[i] == 0][0]
        # If 0 is the first element in list1
        if idx_list1_0 == 0:
            idx_trim_before = idx_list1_0
            idx_trim_after = idx_list1_0 + 1

            # Angles and coeffs before and after crossing the 0 line
            value_before = list2[idx_trim_before]
            value_after = list2[idx_trim_after]
            list1_before = list1[idx_trim_before]
            list1_after = list1[idx_trim_after]

            trim_value = value_before
            trim_parameter = (list1_after - list1_before) / (value_after - value_before)
            ratio = trim_value / (value_after - value_before)

        # If 0 is the last element in list1
        elif idx_list1_0 == len(list1) - 1:
            idx_trim_before = idx_list1_0 - 1
            idx_trim_after = idx_list1_0

            # values and coeffs before and after crossing the 0 line
            value_before = list2[idx_trim_before]
            value_after = list2[idx_trim_after]
            list1_before = list1[idx_trim_before]
            list1_after = list1[idx_trim_after]

            trim_value = value_after
            trim_parameter = (list1_after - list1_before) / (value_after - value_before)
            ratio = trim_value / (value_after - value_before)

        # If  0 is nor the first nor the last element in list1
        elif 0 < idx_list1_0 < len(list1) - 1:
            idx_trim_before = idx_list1_0 - 1
            idx_trim_after = idx_list1_0 + 1

            # Angles and coeffs before and after crossing the 0 line
            value_before = list2[idx_trim_before]
            value_after = list2[idx_trim_after]
            list1_before = list1[idx_trim_before]
            list1_after = list1[idx_trim_after]

            trim_value = list2[idx_list1_0]
            trim_parameter = (list1_after - list1_before) / (value_after - value_before)
            ratio = trim_value / (value_after - value_before)

    # If list1 crosse the 0 line and 0 is not in list1
    elif len(np.argwhere(np.diff(np.sign(list1)))) == 1 and 0 not in np.sign(list1) and crossed:
        # Make the linear equation between the 2 point before and after crossing the 0 ine y=ax+b
        idx_list1_0 = np.argwhere(np.diff(np.sign(list1)))[0][0]
        idx_trim_before = idx_list1_0
        idx_trim_after = idx_list1_0 + 1

        # Angles and coeffs before and after crossing the 0 line
        value_before = list2[idx_trim_before]
        value_after = list2[idx_trim_after]
        list1_before = list1[idx_trim_before]
        list1_after = list1[idx_trim_after]

        fit = np.polyfit(
            [value_before, value_after], [list1_before, list1_after], 1
        )  # returns [a,b] of y=ax+b

        trim_value = -fit[1] / fit[0]  # list1. = 0 for y = 0  hence cruise angle = -b/a
        trim_parameter = fit[0]
        ratio = trim_value / (value_after - value_before)

    return (trim_value, trim_parameter, idx_trim_before, idx_trim_after, ratio)


# Function derivative, or more trim condition function
def trim_condition(
    alt,
    mach,
    cl_required,
    cl,
    aoa,
):
    """Find if a moments coefficient cm cross the 0 line, once or more
        Find if a moment coefficient cm. crosse the 0 line only once and return
        the corresponding angle and the cm derivative at cm=0
    Args:
        alt (float): Altitude [m]
        mach (float) : Mach Number [-]
        cl (list): Lift coefficient list [-]
        aoa (list): Angle of attack (or sideslip) list [deg]
    Returns:
        None if the lift is not enough to fly
        Aoa at which the lift compensate the weight
        pitch moment at this (aoa, alt, mach)
    """

    list1 = []
    for element in cl:
        list1.append(element - cl_required)

    # Check moment coefficient list
    if len(np.argwhere(np.diff(np.sign(list1)))) == 0:
        # If list1 does not cross the 0 line
        log.info(
            "Alt = {}, mach = {} not enough lift to fly, cl_max= {} and required_cl = {}".format(
                alt, mach, max(cl), cl_required
            )
        )
        return (None, None, None, None)

        #  COMPUTE cms derivatives and check if the slope is negative.
    # If  0 is in list1
    elif 0 in np.sign(list1) and list1.count(0) == 1:
        idx_list1_0 = [i for i in range(len(list1)) if list1[i] == 0][0]
        # If 0 is the first element in list1
        if idx_list1_0 == 0:
            idx_trim_before = idx_list1_0
            idx_trim_after = idx_list1_0 + 1

            # Angles and coeffs before and after crossing the 0 line
            aoa_before = aoa[idx_trim_before]
            aoa_after = aoa[idx_trim_after]

            trim_aoa = aoa_before
            ratio = (trim_aoa - aoa_before) / (aoa_after - aoa_before)

        # If 0 is the last element in list1
        elif idx_list1_0 == len(list1) - 1:
            idx_trim_before = idx_list1_0 - 1
            idx_trim_after = idx_list1_0

            # aoa and coeffs before and after crossing the 0 line
            aoa_before = aoa[idx_trim_before]
            aoa_after = aoa[idx_trim_after]

            trim_aoa = aoa_after
            ratio = (trim_aoa - aoa_before) / (aoa_after - aoa_before)

        # If  0 is nor the first nor the last element in list1
        elif 0 < idx_list1_0 < len(list1) - 1:
            idx_trim_before = idx_list1_0 - 1
            idx_trim_after = idx_list1_0 + 1

            # Angles and coeffs before and after crossing the 0 line
            aoa_before = aoa[idx_trim_before]
            aoa_after = aoa[idx_trim_after]

            trim_aoa = aoa[idx_list1_0]
            ratio = (trim_aoa - aoa_before) / (aoa_after - aoa_before)

    # If list1 crosse the 0 line and 0 is not in list1
    # elif  len(np.argwhere(np.diff(np.sign(list1)))) == 1 and 0 not in np.sign(list1) and crossed:
    else:
        # Make the linear equation between the 2 point before and after crossing the 0 ine y=ax+b
        idx_list1_0 = np.argwhere(np.diff(np.sign(list1)))[0][0]
        idx_trim_before = idx_list1_0
        idx_trim_after = idx_list1_0 + 1

        # Angles and coeffs before and after crossing the 0 line
        aoa_before = aoa[idx_trim_before]
        aoa_after = aoa[idx_trim_after]
        list1_before = list1[idx_trim_before]
        list1_after = list1[idx_trim_after]

        fit = np.polyfit(
            [aoa_before, aoa_after], [list1_before, list1_after], 1
        )  # returns [a,b] of y=ax+b

        trim_aoa = -fit[1] / fit[0]  # list1. = 0 for y = 0  hence cruise angle = -b/a
        ratio = (trim_aoa - aoa_before) / (aoa_after - aoa_before)

    return (trim_aoa, idx_trim_before, idx_trim_after, ratio)


def find_max_min(list1, list2):  # fin values max and mi in list of lists
    """Find the max and the min of 2 lists of lists
    Args:
        list1 : list of lists e.i. : list1 = [[1,2],[3,4]]
        list2 : list of lists e.i. : list2 = [[0,1],[2,3]]

    Returns:
        x_max : max of list 1
        x_min : min of list 1
        y_max : max of list2
        y_min : min of list2
        e.i. : [4,1,3,0]
    """
    for n in range(
        min([len(list1), len(list2)])
    ):  # take the minimum length even if the vectors are supposed to have the same length
        # Find x and y axis limits
        if n == 0:
            x_max = max(list1[0])
            x_min = min(list1[0])
            y_max = max(list2[0])
            y_min = min(list2[0])
        if n > 0 and max(list2[n]) > y_max:
            y_max = max(list2[n])
        if n > 0 and min(list2[n]) < y_min:
            y_min = min(list2[n])
        if n > 0 and max(list1[n]) > x_max:
            x_max = max(list1[n])
        if n > 0 and min(list1[n]) < x_min:
            x_min = min(list1[n])
    return (x_max, x_min, y_max, y_min)


def plot_multicurve(
    y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel, show_plots, save_plots
):
    """Function to plot graph with different curves for a varying parameter

    Function 'plot_multicurve' can plot few curves ...

    Args:
        x_axis (list): List of vector of each curve's X coordinates
        y axis (list): List of vector of each curve's Y coordinates
        plot_legend (list): List of the leggends of all the different curves
        plot_title (str): Tile of the plot
        xlabel (str): Label of the x axis
        ylabel (str): Label of the y axis
        show_plot (boolean): To show plots on screen or not
        save_plot (boolean): To save plots in the /ToolOutput dir or not

    Returns:
        A plot with different curves if asked.
    """

    # Avoid to do the rest of the function if nothing to plot or save
    if not show_plots and not save_plots:
        return None

    fig = plt.figure(figsize=(9, 3))

    plt.title(plot_title, fontdict=None, loc="center", pad=None)

    for n in range(len(x_axis)):
        plt.plot(x_axis[n], y_axis[n], marker="o", markersize=4, linewidth=1)
        # Find x and y axis limits
        if n == 0:
            y_max = max(y_axis[0])
            y_min = min(y_axis[0])
            x_max = max(x_axis[0])
            x_min = min(x_axis[0])
        if n > 0 and max(y_axis[n]) > y_max:
            y_max = max(y_axis[n])
        if n > 0 and min(y_axis[n]) < y_min:
            y_min = min(y_axis[n])
        if n > 0 and max(x_axis[n]) > x_max:
            x_max = max(x_axis[n])
        if n > 0 and min(x_axis[n]) < x_min:
            x_min = min(x_axis[n])
    ax = plt.gca()

    plt.grid(True)
    # Remove Top and right axes
    ax.spines["right"].set_color("none")
    ax.spines["top"].set_color("none")

    # Locate horizontal axis in a coherent way
    if y_max < 0:
        ax.spines["bottom"].set_position(("axes", 1))
    elif y_min > 0:
        ax.spines["bottom"].set_position(("axes", 0))
    elif len(np.argwhere(np.diff(np.sign([y_min, y_max])))) != 0:
        ax.spines["bottom"].set_position(("data", 0))

    # Locate vertical axis in a coherent way
    if x_max < 0:
        ax.spines["left"].set_position(("axes", 1))
    elif x_min > 0:
        ax.spines["left"].set_position(("axes", 0))
    elif len(np.argwhere(np.diff(np.sign([x_min, x_max])))) != 0:
        ax.spines["left"].set_position(("data", 0))

    ax.legend(plot_legend, loc="upper right")
    ax.annotate(xlabel, xy=(x_max, 0), ha="right", va="bottom", xycoords="data", fontsize=12)
    ax.annotate(ylabel, xy=(0, y_max), ha="left", va="center", xycoords="data", fontsize=12)

    if save_plots:
        fig_title = plot_title.replace(" ", "_")
        fig_path = Path(MODULE_DIR, "ToolOutput", f"{fig_title}.svg")
        plt.savefig(fig_path)

    if show_plots:
        plt.show()


# ==================================================================================================
#    MAIN
# ==================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
