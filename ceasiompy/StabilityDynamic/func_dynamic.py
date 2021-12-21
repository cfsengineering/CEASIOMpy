"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This programm stors all function needed for stability analysis (dynamic and static)

Python version: >=3.6

| Author: Loic Verdier
| Creation: 2020-02-24

TODO:

    * ...

"""

# =============================================================================
#   IMPORTS
# =============================================================================

import os
import sys
from math import sqrt

import numpy as np
from numpy import log as ln
from numpy import linalg  # For eigen values and aigen voectors

import matplotlib.patheffects
import matplotlib.pyplot as plt
from matplotlib import rcParams, cycler
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import ScalarFormatter

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
#   CLASSES
# =============================================================================


# =============================================================================
#   FUNCTIONS
# =============================================================================

# 'MILF-8785C ShortPeriod natual frequency requirements for flight phase A'
def plot_sp_level_a(x_axis, y_axis, legend, show_plots, save_plots):
    # Create figure
    fig, ax = plt.subplots()

    # Plot data:
    for n in range(len(x_axis)):
        x = x_axis[n]
        y = y_axis[n]
        plt.plot(x, y, marker="o", markersize=4, linestyle="None")

    plot_title = (
        r"MILF-8785C ShortPeriod natual frequency $\omega_{N}$ requirements for flight phase A"
    )

    # Graphic Sttelement
    plt.title(plot_title, fontdict=None, loc="center")
    ax.legend(legend, loc="upper right")
    plt.xlabel(r"n/$\alpha  \backsim$ g's/rad")
    plt.ylabel(r"$\omega_{N}$  [rad/s]")
    # Axes format and Limit:
    ax.loglog()  # Loglog axes
    for axis in [ax.xaxis, ax.yaxis]:  # Ful number and not scientific notaion on axes
        formatter = ScalarFormatter()
        formatter.set_scientific(False)
        axis.set_major_formatter(formatter)
    axes = plt.gca()
    (x_min, x_max, y_min, y_max) = (1, 100, 0.1, 100)
    axes.set_xlim([x_min, x_max])
    axes.set_ylim([y_min, y_max])
    plt.grid(True, which="both", ls="-")

    # Stability Levels
    # Level 1 sup.
    x_level_one_sup = [1, 100]
    y_level_one_sup = [1.9, 20]
    plt.plot(x_level_one_sup, y_level_one_sup, color="green", linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l1_sup = np.array((11, 5.2))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_sup.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l1_sup[0], l1_sup[1], "Level 1", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    # Level 2 sup.
    x_level_two_sup = [1, 100]
    y_level_two_sup = [3.2, 33]
    plt.plot(x_level_two_sup, y_level_two_sup, color="orange", linewidth=1.5)
    # Plot text : "Level1" on garpah
    l2_sup = np.array((11, 8.7))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_sup.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l2_sup[0], l2_sup[1], "Level 2", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    # Level 1 inf.
    x_level_one_inf1 = [1, 3.7]
    y_level_one_inf1 = [1, 1]
    plt.plot(x_level_one_inf1, y_level_one_inf1, color="green", linewidth=1.5)
    x_level_one_inf2 = [3.7, 100]
    y_level_one_inf2 = [1, 5.6]
    plt.plot(x_level_one_inf2, y_level_one_inf2, color="green", linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l1_inf = np.array((11, 1.9))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_inf.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l1_inf[0], l1_inf[1], "Level 1", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    # Level 2 inf.
    x_level_two_inf1 = [1, 2.4]
    y_level_two_inf1 = [0.6, 0.6]
    plt.plot(x_level_two_inf1, y_level_two_inf1, color="orange", linewidth=1.5)
    #  Plot text : "Level2" on garpah
    l2_inf1 = np.array((1.1, 0.62))  # Location
    angle = 0  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_inf1.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l2_inf1[0], l2_inf1[1], "Level 2", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    x_level_two_inf2 = [2.4, 100]
    y_level_two_inf2 = [0.6, 4.1]
    plt.plot(x_level_two_inf2, y_level_two_inf2, color="orange", linewidth=1.5)
    #  Plot text : "Level2 & 3" on garpah
    l2_inf = np.array((11, 1.35))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_inf.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l2_inf[0], l2_inf[1], "Level 2 & 3", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    # Level 3 inf.
    x_level_three_inf1 = [1, 2.4]
    y_level_three_inf1 = [0.39, 0.6]
    plt.plot(x_level_three_inf1, y_level_three_inf1, color="red", linewidth=1.5)
    #  Plot text : "Level 3" on garpah
    l3_inf = np.array((1.1, 0.33))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_inf.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l3_inf[0], l3_inf[1], "Level 3", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    if save_plots:
        fig_title = plot_title.replace(" ", "_")
        fig_path = os.path.join(MODULE_DIR, "ToolOutput", fig_title) + ".svg"
        plt.savefig(fig_path)

    if show_plots:
        plt.show()


# 'MILF-8785C ShortPeriod natual frequency requirements for flight phase B'
def plot_sp_level_b(x_axis, y_axis, legend, show_plots, save_plots):
    # Create figure
    fig, ax = plt.subplots()

    # Plot data:
    for n in range(len(x_axis)):
        x = x_axis[n]
        y = y_axis[n]
        plt.plot(x, y, marker="o", markersize=4, linestyle="None")

    plot_title = (
        r"MILF-8785C ShortPeriod natual frequency $\omega_{N}$ requirements for flight phase B"
    )

    # Graphic Sttelement
    plt.title(plot_title, fontdict=None, loc="center")
    ax.legend(legend, loc="upper right")
    plt.xlabel(r"n/$\alpha  \backsim$ g's/rad")
    plt.ylabel(r"$\omega_{N}  \backsim$ rad/s")
    # Axes format and Limit:
    ax.loglog()  # Loglog axes
    for axis in [ax.xaxis, ax.yaxis]:  # Ful number and not scientific notaion on axes
        formatter = ScalarFormatter()
        formatter.set_scientific(False)
        axis.set_major_formatter(formatter)
    axes = plt.gca()
    (x_min, x_max, y_min, y_max) = (1, 100, 0.1, 100)
    axes.set_xlim([x_min, x_max])
    axes.set_ylim([y_min, y_max])
    # grid
    plt.grid(True, which="both", ls="-")

    # Stability Levels
    # Level 1 sup.
    x_level_one_sup = [1, 100]
    y_level_one_sup = [1.9, 18]
    plt.plot(x_level_one_sup, y_level_one_sup, color="green", linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l1_sup = np.array((11, 5.1))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_sup.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l1_sup[0], l1_sup[1], "Level 1", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    # Level 2 sup.
    x_level_two_sup = [1, 100]
    y_level_two_sup = [3.1, 28]
    plt.plot(x_level_two_sup, y_level_two_sup, color="orange", linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l2_sup = np.array((11, 8.4))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_sup.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l2_sup[0], l2_sup[1], "Level 2", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    # Level 1 inf.
    x_level_one_inf1 = [1, 100]
    y_level_one_inf1 = [0.3, 2.8]
    plt.plot(x_level_one_inf1, y_level_one_inf1, color="green", linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l1_inf = np.array((11, 1))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_inf.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l1_inf[0], l1_inf[1], "Level 1", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    # Level 2 inf.
    x_level_two_inf1 = [1, 100]
    y_level_two_inf1 = [0.2, 1.9]
    plt.plot(x_level_two_inf1, y_level_two_inf1, color="orange", linewidth=1.5)
    #  Plot text : "Level2 & 3" on garpah
    l2_inf = np.array((11, 0.68))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_inf.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l2_inf[0], l2_inf[1], "Level 2 & 3", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    if save_plots:
        fig_title = plot_title.replace(" ", "_")
        fig_path = os.path.join(MODULE_DIR, "ToolOutput", fig_title) + ".svg"
        plt.savefig(fig_path)

    # Show Plots
    if show_plots:
        plt.show()


#'MILF-8785C ShortPeriod natual frequency requirements for flight phase C
def plot_sp_level_c(x_axis, y_axis, legend, show_plots, save_plots):

    fig, ax = plt.subplots()

    # Plot data:
    for n in range(len(x_axis)):
        x = x_axis[n]
        y = y_axis[n]
        plt.plot(x, y, marker="o", markersize=4, linestyle="None")

    plot_title = (
        r"MILF-8785C ShortPeriod natual frequency $\omega_{N}$ requirements for flight phase C"
    )

    # Graphic Sttelement
    plt.title(plot_title, fontdict=None, loc="center")
    ax.legend(legend, loc="upper right")
    plt.xlabel(r"n/$\alpha  \backsim$ g's/rad")
    plt.ylabel(r"$\omega_{N}  \backsim$ rad/s")
    # Axes format and Limit:
    ax.loglog()  # Loglog axes
    for axis in [ax.xaxis, ax.yaxis]:  # Ful number and not scientific notaion on axes
        formatter = ScalarFormatter()
        formatter.set_scientific(False)
        axis.set_major_formatter(formatter)
    axes = plt.gca()
    (x_min, x_max, y_min, y_max) = (1, 100, 0.1, 100)
    axes.set_xlim([x_min, x_max])
    axes.set_ylim([y_min, y_max])
    # grid
    plt.grid(True, which="both", ls="-")

    # Stability Levels
    # Level 1 sup.
    x_level_one_sup = [2, 100]
    y_level_one_sup = [2.7, 18]
    plt.plot(x_level_one_sup, y_level_one_sup, color="green", linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l1_sup = np.array((11, 5.3))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_sup.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l1_sup[0], l1_sup[1], "Level 1", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    # Level 2 sup.
    x_level_two_sup = [1, 100]
    y_level_two_sup = [3.1, 32]
    plt.plot(x_level_two_sup, y_level_two_sup, color="orange", linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l2_sup = np.array((11, 8.8))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_sup.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l2_sup[0], l2_sup[1], "Level 2", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    # Level 1 inf.
    x_level_one_inf1 = [2.9, 100]
    y_level_one_inf1 = [0.7, 3.9]
    plt.plot(x_level_one_inf1, y_level_one_inf1, color="green", linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l1_inf = np.array((11, 1.4))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_inf.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l1_inf[0], l1_inf[1], "Level 1", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text
    # Level 1 inf2
    x_level_one_inf2 = [2.6, 4.5]
    y_level_one_inf2 = [0.88, 0.88]
    plt.plot(x_level_one_inf2, y_level_one_inf2, color="green", linewidth=1.5)
    # Level 1 inf3
    x_level_one_inf3 = [2, 2.9]
    y_level_one_inf3 = [0.7, 0.7]
    plt.plot(x_level_one_inf3, y_level_one_inf3, color="green", linewidth=1.5)
    # Level 1 Vertical 1
    x_level_one_vert1 = [2.6, 2.6]
    y_level_one_vert1 = [0.88, 3]
    plt.plot(x_level_one_vert1, y_level_one_vert1, color="green", linewidth=1.5)
    #  Plot text : "Classes I & IV" on garpah
    l1_vert1 = np.array((3, 0.93))  # Location
    angle = 90  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_vert1.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l1_vert1[0],
        l1_vert1[1],
        "Classes I & IV",
        fontsize=6,
        rotation=angle,
        rotation_mode="anchor",
    )  # Plot text
    # Level 1 Vertical 2
    x_level_one_vert2 = [2, 2]
    y_level_one_vert2 = [0.7, 2.7]
    plt.plot(x_level_one_vert2, y_level_one_vert2, color="green", linewidth=1.5)
    #  Plot text : "Classes II & III" on garpah
    l1_vert2 = np.array((2.2, 0.8))  # Location
    angle = 90  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_vert1.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l1_vert2[0],
        l1_vert2[1],
        "Classes II & III",
        fontsize=6,
        rotation=angle,
        rotation_mode="anchor",
    )  # Plot text

    # Level 2 inf.
    x_level_two_inf1 = [1.4, 100]
    y_level_two_inf1 = [0.39, 3]
    plt.plot(x_level_two_inf1, y_level_two_inf1, color="orange", linewidth=1.5)
    #  Plot text : "Level2 & 3" on garpah
    l2_inf = np.array((11, 1.08))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_inf.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l2_inf[0], l2_inf[1], "Level 2 & 3", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    # Level2 inf 2
    x_level_two_inf2 = [1.7, 3.5]
    y_level_two_inf2 = [0.6, 0.6]
    plt.plot(x_level_two_inf2, y_level_two_inf2, color="orange", linewidth=1.5)
    # Level2 Vert1
    x_level_two_vert1 = [1.7, 1.7]
    y_level_two_vert1 = [0.6, 4]
    plt.plot(x_level_two_vert1, y_level_two_vert1, color="orange", linewidth=1.5)
    #  Plot text : "Classes I & IV" on garpah
    l2_vert1 = np.array((1.64, 0.63))  # Location
    angle = 90  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_vert1.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l2_vert1[0],
        l2_vert1[1],
        "Level2, Classes I & IV",
        fontsize=6,
        rotation=angle,
        rotation_mode="anchor",
    )  # Plot text
    # Level2 Vert2
    x_level_two_vert2 = [1.01, 1.01]
    y_level_two_vert2 = [0.39, 3]
    plt.plot(x_level_two_vert2, y_level_two_vert2, color="orange", linewidth=1.5)
    #  Plot text : "Classes I & IV" on garpah
    l2_vert2 = np.array((1.09, 0.48))  # Location
    angle = 90  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_vert2.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l2_vert2[0],
        l2_vert2[1],
        "Level2, Classes II & III",
        fontsize=6,
        rotation=angle,
        rotation_mode="anchor",
    )  # Plot text

    # Level2 inf 3
    x_level_two_inf3 = [1, 1.4]
    y_level_two_inf3 = [0.39, 0.39]
    plt.plot(x_level_two_inf3, y_level_two_inf3, color="orange", linewidth=1.5)

    # Level 3 inf.
    x_level_three_inf = [1, 1.4]
    y_level_three_inf = [0.33, 0.39]
    plt.plot(x_level_three_inf, y_level_three_inf, color="red", linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l3_inf = np.array((1.04, 0.27))  # Location
    angle = 18  # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l3_inf.reshape((1, 2)))[
        0
    ]  # Position+ Rotation
    plt.text(
        l3_inf[0], l3_inf[1], "Level 3", fontsize=6, rotation=angle, rotation_mode="anchor"
    )  # Plot text

    if save_plots:
        fig_title = plot_title.replace(" ", "_")
        fig_path = os.path.join(MODULE_DIR, "ToolOutput", fig_title) + ".svg"
        plt.savefig(fig_path)

    if show_plots:
        plt.show()


def get_unic(vector):
    """Return a vector with the same element having only one occurence.

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


def interpolation(list, idx1, idx2, ratio):
    """Return the interpolation between list[idx1] and list[idx2] of vector "list".

    Args:
        list (vector) : List of values
        idx1 (float): the index of the first value in the list
        idx2 (float): the index of the second value in the list
        ratio (float) : the distance of the interpolation point between the 2 values:
            e.i. : y = y1 +  x* (y2-y1)/(x2-x1) = y1 + ratio*(y2-y1)

    Returns:
        value (float): the interpolated value
    """
    value = list[idx1] + ratio * (list[idx2] - list[idx1])

    return value


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


# TODO: maybe could be remove
def trim_derivative(alt, mach, list1, list2):
    """Find if a moments coefficeint cm cross the 0 line, once or more
        Find if a moment coefficeint cm. crosse the 0 line only once and return
        the corresponding angle and the cm derivative at cm=0

    Args:
        alt (float): Altitude [m]
        mach (float) : Mach Number [-]
        list1 (list): List of coefficient (e.g. Moment coefficient)
        list2 (list): List of parameter (e.g. Angle of attack (or sideslip))

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
        # Make the linear equation btween the 2 point before and after crossing the 0 ine y=ax+b
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

        trim_value = -fit[1] / fit[0]  # list1. = 0 for y = 0  hence cruise agngle = -b/a
        trim_parameter = fit[0]
        ratio = trim_value / (value_after - value_before)

    return (trim_value, trim_parameter, idx_trim_before, idx_trim_after, ratio)


# Function derivative, or more trim condition function
def trim_condition(alt, mach, cl_required, cl, aoa):
    """Find if a moments coefficeint cm cross the 0 line, once or more
        Find if a moment coefficeint cm. crosse the 0 line only once and return
        the corresponding angle and the cm derivative at cm=0

    Args:
        alt (float): Altitude [m]
        mach (float) : Mach Number [-]
        cl_required (float): Lift coefficient required
        cl (list): Lift coefficient list [-]  # TODO: rename cl_list
        aoa (list): Angle of attack list (or sideslip) [deg]  # TODO: rename aoa_list

    Returns:
        None if the lift is not enough to fly
        Aoa at which the lift compensate the weight
        pitch moement at this (aoa, alt, amch)
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

            # aoas and coeffs before and after crossing the 0 line
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

    else:
        # Make the linear equation btween the 2 point before and after crossing the 0 ine y=ax+b
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

        trim_aoa = -fit[1] / fit[0]  # list1. = 0 for y = 0  hence cruise agngle = -b/a
        ratio = (trim_aoa - aoa_before) / (aoa_after - aoa_before)

    return (trim_aoa, idx_trim_before, idx_trim_after, ratio)


def adimensionalise(a, mach, rho, s, b, mac, m, I_xx, I_yy, I_zz, I_xz):
    """Adimensionalise mass, moment of inertia and get velocity

    Args:
        a (float): Speed of sounf at the given altitude [m/s]
        mach (float) : the Mach number [-],
        rho (float) : air density at the given altitude [kg/m^3]
        s (flaot) : the wing surface area [m^2]
        b (float) : the wing span [m]
        mac (flaot) : the Mean Aerodynamic chord [m]
        m (float) : The aircraft mass [kg]
        I_xx (float) : moment of inertia about x axis [kg m^2]
        I_yy (float) : moment of inertia about y axis [kg m^2]
        I_zz (float) : moment of inertia about z axis [kg m^2]
        I_xz (float) : product of inertia [kg m^2]

    Returns:
        u0 (float) : aircraft trimm speed [m/s]
        q (float) : dynamic pressure [Pa]
        i_xx (float) : dimensionless moment of inertia about x axis [-]
        i_yy (float) : dimensionless moment of inertia about y axis [-]
        i_zz (float) : dimensionless moment of inertia about z axis [-]
        i_xz (float) : dimensionless product of inertia [-]

    """

    u0 = a * mach  # Trimm speed
    q = 0.5 * rho * u0 ** 2  # Static pressure
    m_adim = m / (0.5 * rho * u0 * s)
    i_xx = I_xx / (0.5 * rho * u0 * s * b)
    i_yy = I_yy / (0.5 * rho * u0 * s * mac)
    i_zz = I_zz / (0.5 * rho * u0 * s * b)
    i_xz = I_xz / (0.5 * rho * u0 * s * b)

    return (u0, m_adim, i_xx, i_yy, i_zz, i_xz)


def check_sign_longi(Cd_alpha, M_w, Cl_alpha, M_dotw, Z_dotw, M_q, Z_q, Cm_eta, Z_eta):
    """Find if  longitudinal aerodynamic coef and derivative have normal sign according to
    Thomas Yechout Book, P289
    cd_u, cm_u, cl_u, X_wdot, cd_q, cd_eta are not tested beacause theire sign might vary according
    to Thomas Yechout

    Args:
        Cd_alpha (): ..
        TODO

    """

    if Cd_alpha < 0:
        log.warning(
            "X_w coefficient : Cd_alpha (dcd/daoa) should be positive according to Thomas Yechout Book, P289"
        )
    if M_w > 0:
        log.warning(
            "M_w coefficient : Cm_alpha (dcms/daoa) should be negative according to Thomas Yechout Book, P2894"
        )
    if Cl_alpha < 0:
        log.warning(
            "Z_w coefficient : Cl_alpha (dcl/daoa) should be positive according to Thomas Yechout Book, P289"
        )
    # X_dotw : approx 0
    if M_dotw > 0:
        log.warning(
            "M_wdot coefficient : (Thumb rule), should be negative according to Thomas Yechout Book, P289"
        )
    if Z_dotw > 0:
        log.warning(
            "Z_wdot coefficient : (Thumb rule), should be negative according to Thomas Yechout Book, P289"
        )
    # cd_q approx 0
    if M_q > 0:
        log.warning(
            "M_q coefficient : Cm_q (dcmsdqstar), should be negative according to Thomas Yechout Book, P289"
        )
    if Z_q > 0:
        log.warning(
            "Z_q coefficient : -Cl_q (dcldqstar), should be negative according to Thomas Yechout Book, P289"
        )
    # cd_eta approx 0
    if Cm_eta > 0:
        log.warning(
            "M_eta coefficient : Cm_eta (), should be negative according to Thomas Yechout Book, P289"
        )
    if Z_eta > 0:
        log.warning(
            "Z_eta coefficient : -Cl_eta (), should be negative according to Thomas Yechout Book, P289"
        )


def check_sign_lat(Y_v, L_v, N_v, Y_p, L_p, Y_r, L_r, N_r, L_xi, Y_zeta, L_zeta, N_zeta):
    """Find if aerodynamic have normal sign according to Thomas Yechout Book, P304
        N_p, Y_xi and N_xi are not tested beacause theire sign might vary according to Thomas Yechout
        Non dimensional lateral-directional aerodynamic derivatives, exected N_p, Y_xi and N_xi

    Args:
        Y_v (float): ..
        TODO

    Returns:
        ....

    """
    if Y_v > 0:
        log.warning(
            "Y_v coefficient : Cy_beta (dcs/daos) should be negative according to Thomas Yechout Book, P304"
        )
    if L_v > 0:
        log.warning(
            "L_v coefficient : Cl_beta (dcmd/daos) should be negative according to Thomas Yechout Book, P304"
        )
    if N_v < 0:
        log.warning(
            "L_v coefficient : Cn_beta (dcml/daos) should be positive according to Thomas Yechout Book, P304"
        )
    if Y_p > 0:
        log.warning(
            "Y_p coefficient : Cy_p (dcsdpstar) should be negative according to Thomas Yechout Book, P304"
        )
    if L_p > 0:
        log.warning(
            "L_p coefficient : Cl_p (dcmddpstar) should be negative according to Thomas Yechout Book, P304"
        )
    # N_p : + or -
    if Y_r < 0:
        log.warning(
            "Y_r coefficient : Cy_r (dcsdrstar) should be positive according to Thomas Yechout Book, P304"
        )
    if L_r < 0:
        log.warning(
            "L_r coefficient : Cl_r (dcmddrstar) should be positive according to Thomas Yechout Book, P304"
        )
    if N_r > 0:
        log.warning(
            "L_r  coefficient : Cn_r (dcmldrstar) should be negative according to Thomas Yechout Book, P304"
        )
    # Y_xi : approx 0
    if L_xi < 0:
        log.warning(
            "L_xi coefficient : Cl_xi () should be positive according to Thomas Yechout Book, P304"
        )
    # N_xi : + or -
    if Y_zeta < 0:
        log.warning(
            "Y_zeta coefficient : Cy_xi () should be positive according to Thomas Yechout Book, P304"
        )
    if L_zeta < 0:
        log.warning(
            "L_zeta coefficient : Cl_xi () should be positive  according to Thomas Yechout Book, P304"
        )
    if N_zeta > 0:
        log.warning(
            "L_zeta  coefficient : Cn_xi () should be negative according to Thomas Yechout Book, P304"
        )


def plot_splane(eg_value_longi, plot_title, legend, show_plots, save_plots):
    """TODO

    Args:
        Y_v (float): ..
        TODO

    """
    # S-plane Longi Mode
    fig, ax = plt.subplots()
    # S-plane, with all modes
    plt.plot(
        eg_value_longi[0].real,
        eg_value_longi[0].imag,
        marker="*",
        color="g",
        markersize=7,
        linestyle="None",
    )
    plt.plot(
        eg_value_longi[1].real,
        eg_value_longi[1].imag,
        marker="*",
        color="g",
        markersize=7,
        linestyle="None",
    )
    plt.plot(
        eg_value_longi[2].real,
        eg_value_longi[2].imag,
        marker="*",
        color="b",
        markersize=7,
        linestyle="None",
    )
    plt.plot(
        eg_value_longi[3].real,
        eg_value_longi[3].imag,
        marker="*",
        color="b",
        markersize=7,
        linestyle="None",
    )

    plt.ylabel("Im")
    plt.xlabel("Re")

    # Graphic Sttelement
    plt.title(plot_title, fontdict=None, loc="center")
    ax.legend(legend, loc="upper left")
    plt.xlabel(r"$R_e$")
    plt.ylabel(r"$I_m$")
    plt.grid(True)  # ,which="both",ls="-")

    if save_plots:
        fig_title = plot_title.replace(" ", "_")
        fig_path = os.path.join(MODULE_DIR, "ToolOutput", fig_title) + ".svg"
        plt.savefig(fig_path)

    if show_plots:
        plt.show()


def concise_derivative_longi(
    X_u,
    Z_u,
    M_u,
    X_w,
    Z_w,
    M_w,
    X_q,
    Z_q,
    M_q,
    X_dotw,
    Z_dotw,
    M_dotw,
    X_eta,
    Z_eta,
    M_eta,
    X_tau,
    Z_tau,
    M_tau,
    g,
    theta_e,
    u0,
    We,
    Ue,
    mac,
    m_adim,
    i_yy,
):
    """TODO

    Args:
        X_u (float): ..
        TODO

    Returns:

    """

    # Concise derivatives in body axes coordinates
    x_u = X_u / m_adim + (mac / u0 * X_dotw * Z_u) / (m_adim * (m_adim - mac / u0 * Z_dotw))
    z_u = Z_u / (m_adim - mac / u0 * Z_dotw)
    m_u = M_u / i_yy + (mac / u0 * M_dotw * Z_u) / (i_yy * (m_adim - mac / u0 * Z_dotw))

    x_w = X_w / m_adim + (mac / u0 * X_dotw * Z_w) / (m_adim * (m_adim - mac / u0 * Z_dotw))
    z_w = Z_w / (m_adim - mac / u0 * Z_dotw)
    m_w = M_w / i_yy + (mac / u0 * M_dotw * Z_w) / (i_yy * (m_adim - mac / u0 * Z_dotw))

    x_q = (mac * X_q - m_adim * We) / m_adim + ((mac * Z_q + m_adim * Ue) * mac / u0 * X_dotw) / (
        m_adim * (m_adim - mac / u0 * Z_dotw)
    )
    z_q = (mac * Z_q + m_adim * Ue) / (m_adim - mac / u0 * Z_dotw)
    m_q = (mac * M_q) / i_yy + ((mac * Z_q + m_adim * Ue) * mac / u0 * M_dotw) / (
        i_yy * (m_adim - mac / u0 * Z_dotw)
    )

    x_theta = -g * np.cos(theta_e) - (mac / u0 * X_dotw * g * np.sin(theta_e)) / (
        m_adim - mac / u0 * Z_dotw
    )  # g is not dimensionlessss!!!!!!!!
    z_theta = -(m_adim * g * np.sin(theta_e)) / (
        m_adim - mac / u0 * Z_dotw
    )  # g is not dimensionlessss!!!!!!!!
    m_theta = -(mac / u0 * M_dotw * m_adim * g * np.sin(theta_e)) / (
        i_yy * (m_adim - mac / u0 * Z_dotw)
    )  # g is not dimensionlessss!!!!!!!!

    x_eta = (u0 * X_eta) / m_adim + (mac / u0 * X_dotw * Z_eta) / (m_adim - mac / u0 * Z_dotw)
    z_eta = (u0 * Z_eta) / (m_adim - mac / u0 * Z_dotw)
    m_eta = (u0 * M_eta) / i_yy + (mac * M_dotw * Z_eta) / (i_yy * (m_adim - mac / u0 * Z_dotw))

    x_tau = (u0 * X_tau) / m_adim + (mac / u0 * X_dotw * Z_tau) / (m_adim - mac / u0 * Z_dotw)
    z_tau = (u0 * Z_tau) / (m_adim - mac / u0 * Z_dotw)
    m_tau = (u0 * M_tau) / i_yy + (mac * M_dotw * Z_tau) / (i_yy * (m_adim - mac / u0 * Z_dotw))

    A_longi = np.array(
        [
            [x_u, x_w, x_q, x_theta],
            [z_u, z_w, z_q, z_theta],
            [m_u, m_w, m_q, m_theta],
            [0, 0, 1, 0],
        ]
    )

    B_longi = np.array([[x_eta, x_tau], [z_eta, z_tau], [m_eta, m_tau], [0, 0]])

    return (
        A_longi,
        B_longi,
        x_u,
        z_u,
        m_u,
        x_w,
        z_w,
        m_w,
        x_q,
        z_q,
        m_q,
        x_theta,
        z_theta,
        m_theta,
        x_eta,
        z_eta,
        m_eta,
        x_tau,
        z_tau,
        m_tau,
    )


def concise_derivative_lat(
    Y_v,
    L_v,
    N_v,
    Y_p,
    L_p,
    N_p,
    Y_r,
    L_r,
    N_r,
    Y_xi,
    L_xi,
    N_xi,
    Y_zeta,
    L_zeta,
    N_zeta,
    g,
    b,
    theta_e,
    u0,
    We,
    Ue,
    m_adim,
    i_xx,
    i_zz,
    i_xz,
):
    """TODO

    Args:
        Y_v (float): ..
        TODO

    """

    # Concise derivatives in body axes coordinates
    y_v = Y_v / m_adim
    y_p = (b * Y_p + m_adim * We) / m_adim
    y_r = (b * Y_r - m_adim * Ue) / m_adim
    y_phi = g * np.cos(theta_e)
    y_psi = g * np.sin(theta_e)

    l_v = (i_zz * L_v + i_xz * N_v) / (i_xx * i_zz - i_xz ** 2)
    l_p = b * (i_zz * L_p + i_xz * N_p) / (i_xx * i_zz - i_xz ** 2)
    l_r = b * (i_zz * L_r + i_xz * N_r) / (i_xx * i_zz - i_xz ** 2)
    l_phi = 0
    l_psi = 0

    n_v = (i_xx * N_v + i_xz * L_v) / (i_xx * i_zz - i_xz ** 2)
    n_p = b * (i_xx * N_p + i_xz * L_p) / (i_xx * i_zz - i_xz ** 2)
    n_r = b * (i_xx * N_r + i_xz * L_r) / (i_xx * i_zz - i_xz ** 2)
    n_phi = 0
    n_psi = 0

    # Controls
    y_xi = u0 * Y_xi / m_adim
    l_xi = u0 * (i_zz * L_xi + i_xz * N_xi) / (i_xx * i_zz - i_xz ** 2)
    n_xi = u0 * (i_xx * N_xi + i_xz * L_xi) / (i_xx * i_zz - i_xz ** 2)

    y_zeta = u0 * Y_zeta / m_adim
    l_zeta = (
        u0 * (i_zz * L_zeta + i_xz * N_zeta) / (i_xx * i_zz - i_xz ** 2)
    )  # A mon avis il y a une faute, il ne doit surement pas il y avoir 2 fois L_zeta au numerateur et il devrait il y avoir i_xx en comparaison, les l et n_xi
    n_zeta = u0 * (i_xx * N_zeta + i_xz * L_zeta) / (i_xx * i_zz - i_xz ** 2)

    # Lateral-directional state and input matrix in concise form
    A_direc = np.array(
        [
            [y_v, y_p, y_r, y_phi, y_psi],
            [l_v, l_p, l_r, l_phi, l_psi],
            [n_v, n_p, n_r, n_phi, n_psi],
            [0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0],
        ]
    )

    B_direc = np.array([[y_xi, y_zeta], [l_xi, l_zeta], [n_xi, n_zeta], [0, 0], [0, 0]])

    return (
        A_direc,
        B_direc,
        y_v,
        l_v,
        n_v,
        y_p,
        y_phi,
        y_psi,
        l_p,
        l_phi,
        l_psi,
        n_p,
        y_r,
        l_r,
        n_r,
        n_phi,
        n_psi,
        y_xi,
        l_xi,
        n_xi,
        y_zeta,
        l_zeta,
        n_zeta,
    )


def speed_derivative_at_trim(
    parameter_list,
    mach,
    mach_list,
    mach_unic_list,
    idx_alt,
    aoa_list,
    aos_list,
    idx_trim_before,
    idx_trim_after,
    ratio,
):

    """Find the speed derivative of "parameter" at trim conditions
    Args:
        parameter_list (): list of parameter's values : e.i. Cd (dragg coefficient)
        mach (): the mach at trim conditions
        mach_list (): ...
        mach_unic_list (): list of unic values of mach
        TODO: complete args
        idx_trim_before (): index

    Returns:
        parameter_speed_derivative: parameter speed derivaive at trim condtion ei cd@ aoa=4.22
    """
    idx_mach_left = []
    idx_mach_right = []
    # if Mach first value,of Mach unic hence make a right derivative
    if mach == mach_unic_list[0]:
        mach_left = mach
        mach_right = mach_unic_list[1]
        idx_mach_left = [j for j in range(len(mach_list)) if mach_list[j] == mach_left]
        idx_mach_right = [j for j in range(len(mach_list)) if mach_list[j] == mach_right]
    # if Mach last value,of Mach_unic hence make a left derivative
    elif mach == mach_unic_list[-1]:
        mach_left = mach_unic_list[-2]
        mach_right = mach
        idx_mach_left = [j for j in range(len(mach_list)) if mach_list[j] == mach_left]
        idx_mach_right = [j for j in range(len(mach_list)) if mach_list[j] == mach_right]
    # else,  Mach  value is nor the first nor the last value, of Mach_unic hence make middle derivative
    else:
        idx_mach_in_mach_unic = [
            j for j in range(len(mach_unic_list)) if mach_unic_list[j] == mach
        ][
            0
        ]  # Find index oh mach in mach_unic_list
        mach_left = mach_unic_list[idx_mach_in_mach_unic - 1]
        mach_right = mach_unic_list[idx_mach_in_mach_unic + 1]
        idx_mach_left = [j for j in range(len(mach_list)) if mach_list[j] == mach_left]
        idx_mach_right = [j for j in range(len(mach_list)) if mach_list[j] == mach_right]

    idx_aoa_left = [j for j in range(len(aoa_list)) if aoa_list[j] == aoa_list[idx_trim_before]]
    idx_aoa_right = [j for j in range(len(aoa_list)) if aoa_list[j] == aoa_list[idx_trim_after]]
    idx_aos = [j for j in range(len(aos_list)) if aos_list[j] == 0]  # at trim, aos = 0

    # Cd @ trim AOA @mach_left
    idx_parameter_left_left = get_index(
        get_index(idx_aoa_left, idx_mach_left, idx_aos), idx_alt, idx_alt
    )[
        0
    ]  # left index of left  value
    idx_parameter_left_right = get_index(
        get_index(idx_aoa_right, idx_mach_left, idx_aos), idx_alt, idx_alt
    )[
        0
    ]  # right index of left value
    parameter_left = (
        parameter_list[idx_parameter_left_left]
        + (parameter_list[idx_parameter_left_right] - parameter_list[idx_parameter_left_left])
        * ratio
    )

    # Cd @ trim AOA @mach_right
    idx_parameter_right_left = get_index(
        get_index(idx_aoa_left, idx_mach_right, idx_aos), idx_alt, idx_alt
    )[
        0
    ]  # left index of rightvalue
    idx_parameter_right_right = get_index(
        get_index(idx_aoa_right, idx_mach_right, idx_aos), idx_alt, idx_alt
    )[
        0
    ]  # right index of right value
    parameter_right = (
        parameter_list[idx_parameter_right_left]
        + (parameter_list[idx_parameter_right_right] - parameter_list[idx_parameter_right_left])
        * ratio
    )

    # Cd  derivative @ trim AOA
    parameter_speed_derivative = (parameter_left - parameter_right) / (mach_left - mach_right)

    return parameter_speed_derivative


def speed_derivative_at_trim_lat(
    parameter_list,
    aos_list,
    aos_unic_list,
    idx_alt,
    idx_mach,
    aoa_list,
    idx_trim_before,
    idx_trim_after,
    ratio,
):
    """Find the speed derivative of "parameter" at trim conditions, at trom: aos =0

    Args:
        parameter_list : list of parameter's values : e.i. Cd (dragg coefficient)
        aos : the aos at trim conditions
        aos_unic_list : list of unic values of aos
        idx_trim_before : index
        TODO: complte

    Returns:
        parameter_speed_derivative: parameter speed derivaive at trim condtion ei cd@ aoa=4.22
    """

    idx_aos_left = []
    idx_aos_right = []
    # if aos first value,of aos unic hence make a right derivative
    if 0 == aos_unic_list[0]:
        aos_left = 0
        aos_right = aos_unic_list[1]
        idx_aos_left = [j for j in range(len(aos_list)) if aos_list[j] == aos_left]
        idx_aos_right = [j for j in range(len(aos_list)) if aos_list[j] == aos_right]
    # if aos last value,of aos_unic hence make a left derivative
    elif 0 == aos_unic_list[-1]:
        aos_left = aos_unic_list[-2]
        aos_right = 0
        idx_aos_left = [j for j in range(len(aos_list)) if aos_list[j] == aos_left]
        idx_aos_right = [j for j in range(len(aos_list)) if aos_list[j] == aos_right]
    # else,  aos  value is nor the first nor the last value, of aos_unic hence make middle derivative
    else:
        idx_aos_in_aos_unic = [j for j in range(len(aos_unic_list)) if aos_unic_list[j] == 0][0]
        aos_left = aos_unic_list[idx_aos_in_aos_unic - 1]
        aos_right = aos_unic_list[idx_aos_in_aos_unic + 1]
        idx_aos_left = [j for j in range(len(aos_list)) if aos_list[j] == aos_left]
        idx_aos_right = [j for j in range(len(aos_list)) if aos_list[j] == aos_right]

    idx_aoa_left = [j for j in range(len(aoa_list)) if aoa_list[j] == aoa_list[idx_trim_before]]
    idx_aoa_right = [j for j in range(len(aoa_list)) if aoa_list[j] == aoa_list[idx_trim_after]]

    # Cs @ trim AOA @aos_left   (interpolation)
    idx_parameter_left_left = get_index(
        get_index(idx_aoa_left, idx_aos_left, idx_mach), idx_alt, idx_alt
    )  # left index of left value
    idx_parameter_left_right = get_index(
        get_index(idx_aoa_right, idx_aos_left, idx_mach), idx_alt, idx_alt
    )  # right index of left value

    if idx_parameter_left_left == [] or idx_parameter_left_right == []:
        return
    else:
        idx_parameter_left_left = idx_parameter_left_left[0]  # left value
        idx_parameter_left_right = idx_parameter_left_right[0]  # right value

    parameter_left = (
        parameter_list[idx_parameter_left_left]
        + (parameter_list[idx_parameter_left_right] - parameter_list[idx_parameter_left_left])
        * ratio
    )

    # Cd @ trim AOA @aos_right  (interpolation)
    idx_parameter_right_left = get_index(
        get_index(idx_aoa_left, idx_aos_right, idx_mach), idx_alt, idx_alt
    )  # left index of right value
    idx_parameter_right_right = get_index(
        get_index(idx_aoa_right, idx_aos_right, idx_mach), idx_alt, idx_alt
    )  # right index of right  value

    # if no value found for the left parameters, the function returns: None
    if idx_parameter_right_left == [] or idx_parameter_right_right == []:
        return
    else:
        idx_parameter_right_left = idx_parameter_right_left[0]  # left value
        idx_parameter_right_right = idx_parameter_right_right[0]  # right value

    parameter_right = (
        parameter_list[idx_parameter_right_left]
        + (parameter_list[idx_parameter_right_right] - parameter_list[idx_parameter_right_left])
        * ratio
    )

    # Cd  derivative @ trim AOA
    parameter_speed_derivative = (parameter_left - parameter_right) / (aos_left - aos_right)

    return parameter_speed_derivative


def longi_root_identification(A_longi):
    """Identifies the root of the longitudinal charcateristic equation

    Args:
        A_longi (2D matrix) : State space matrix in CONCISE form

    Returns:
        If roots are not complex conjugate the finction returns:
            None
        If roots are well complex conjugate the function returns:
            sp1 : first complex root of the short period mode
            sp2 : complex conjugate root of the short period mode
            ph1 : first complex root of the phugoid mode
            ph2 : complex conjugate root of the phugoid mode
    """

    # Compute eigenvalues and eigenvectors of longi CONCISE equations at trim
    eg_value_longi, eg_vector_longi = linalg.eig(A_longi)

    # TODO: maybe use as test
    # delta = a S^4 + bS^3 + cS^2 + dS  + e  , delta_longi  = [a,b,c,d,e]     from page 423 Cook
    # delta_longi = [1, \
    #                        -(m_q+x_u+z_w),\
    #                        (m_q*z_w - m_w*z_q) + (m_q*x_u - m_u*x_q) + (x_u*z_w - x_w*z_u) - m_theta,\
    #                        (m_theta*x_u-m_u*x_theta)+(m_theta*z_w-m_w*z_theta)+m_q*(x_w*z_u-x_u*z_w)+x_q*(m_u*z_w-m_w*z_u)+z_q*(m_w*x_u-m_u*x_w),\
    #                        m_theta*(x_w*z_u-x_u*z_w)+x_theta*(m_u*z_w-m_w*z_u)+z_theta*(m_w*x_u-m_u*x_w)]
    # roots_longi = np.roots(delta_longi)
    # print('\n Eigenvalues Longitudinal :')
    # print(eg_value_longi)
    # print('\n DEN TF roots Longitudinal :')
    # print(roots_longi)
    # print('\n Eigenvectors Longitudinal :')
    # print(eg_vector_longi)

    count = 0
    real_root = []
    complex_root = []
    for root in eg_value_longi:
        if isinstance(root, complex):
            count += 1
            complex_root.append(root)
        else:
            real_root.append(root)

    # count number of complex numbers
    if count == 2:  #  if phugoid not stable (real number):
        if real_root[0] <= real_root[0]:
            ph1 = real_root[0]
            ph2 = real_root[1]
        else:
            ph1 = real_root[1]
            ph2 = real_root[0]
        if np.imag(complex_root[0]) < np.imag(complex_root[1]):
            sp1 = complex_root[0]
            sp2 = complex_root[1]
        else:
            sp1 = complex_root[1]
            sp2 = complex_root[0]
    else:  #  if phugoid and short period both complex:
        root1 = eg_value_longi[0]
        root2 = eg_value_longi[1]
        root3 = eg_value_longi[2]
        root4 = eg_value_longi[3]
        if (np.imag(root1)) ** 2 == (np.imag(root2)) ** 2:
            couple1 = [root1, root2]
            couple2 = [root3, root4]
        elif (np.imag(root1)) ** 2 == (np.imag(root3)) ** 2:
            couple1 = [root1, root3]
            couple2 = [root2, root4]
        else:
            couple1 = [root1, root4]
            couple2 = [root2, root3]

        if abs(np.imag(root1)) > abs(np.imag(couple2[0])) ** 2:
            sp1 = root1
            sp2 = couple1[1]
            ph1 = couple2[0]
            ph2 = couple2[1]
        else:
            ph1 = root1
            ph2 = couple1[1]
            sp1 = couple2[0]
            sp2 = couple2[1]

    # If short period roots are not correctly identified all longi roots are not identified and roots are not physically possible, and programm has to stop
    if sp1 != np.conj(sp2) or ph1 != np.conj(ph2):
        return (None, eg_value_longi)
    else:
        # Calculate eigen vectors magnitude :
        eg_vector_longi_magnitude = []
        for row in eg_vector_longi:
            new_row = []
            for vector in row:
                vector_magnitude = abs(vector)  # Module of complex number
                new_row.append(format(vector_magnitude, ".3g"))
            eg_vector_longi_magnitude.append(new_row)
        return (sp1, sp2, ph1, ph2, eg_value_longi, eg_vector_longi, eg_vector_longi_magnitude)


def longi_mode_characteristic(sp1, sp2, ph1, ph2, load_factor):
    # Short Period mode characteristics
    sp_freq = (
        np.sqrt(sp1 * sp2)
    ).real  #  [rad/s] Undamped natural frequency omega, of concise equations, .real  for get ride of  "+0j"
    sp_damp = -np.real(sp1) / sp_freq  # [-] Damping of concise equations
    sp_cap = sp_freq ** 2 / load_factor  # [1/g 1/s^2]   g: g's (1g 2g 3g)

    # Phugoid mode characteristics
    if ph1.real < 0:  #  If Phugoid stable
        ph_freq = (
            np.sqrt(ph1 * ph2)
        ).real  #  [rad/s] Undamped natural frequency omega, of concise equations
        ph_damp = -np.real(ph1) / ph_freq  # [-] Damping of concise equations
        ph_t2 = None
    else:  # ph1.real > 0 # Phugoi unstable
        ph_freq = None
        ph_damp = None
        ph_t2 = ln(2) / np.real(ph1)  # [s] Time to double amplitude

    return (sp_freq, sp_damp, sp_cap, ph_freq, ph_damp, ph_t2)


def cap_rating(flight_phase, short_period_cap, short_period_damping):
    """Give a rating of the short period mode flight quality level: Level1 Level2 or Level3 and 4
          according to MIL-STD-1797A
    Args:
        flight_phase (string) : 'A',  'B' or 'C'
        short_period_cap (float): Control Anticipation Parameter [1/(g*s^2)]
        short_period_damping (float ):  short period damping [-]

    Returns:
        cap_rate (int) : 1, 2, 3 or 4 if the dmaping is out Level3 limit :  corresponding to the
                                 flight quality rating
    """

    if flight_phase == "A":
        if 0.35 <= short_period_damping <= 1.3:
            if 0.28 <= short_period_cap <= 3.6:
                cap_rate = 1
            elif 0.16 <= short_period_cap <= 310:
                cap_rate = 2
            else:
                cap_rate = 3

        elif 0.25 <= short_period_damping <= 2:
            if 0.16 <= short_period_cap <= 10:
                cap_rate = 2
            else:
                cap_rate = 3
        elif 0.15 <= short_period_damping:
            cap_rate = 3
        else:
            cap_rate = None

    elif flight_phase == "B":
        if 0.3 <= short_period_damping <= 2:
            if 0.085 <= short_period_cap <= 3.6:
                cap_rate = 1
            elif 0.038 <= short_period_cap <= 10:
                cap_rate = 2
            else:
                cap_rate = 3
        elif 0.2 <= short_period_damping <= 0.3:
            if 0.038 <= short_period_cap <= 10:
                cap_rate = 2
            else:
                cap_rate = 3
        else:
            cap_rate = 3

    else:  #   flight_phase == 'C'
        if 0.35 <= short_period_damping <= 1.3:
            if 0.16 <= short_period_cap <= 3.6:
                cap_rate = 1
            elif 0.05 <= short_period_cap <= 10:
                cap_rate = 2
            else:
                cap_rate = 3
        elif 0.25 <= short_period_damping <= 2:
            if 0.05 <= short_period_cap <= 10:
                cap_rate = 2
            else:
                cap_rate = 3
        elif 0.15 <= short_period_damping:
            cap_rate = 3
        else:
            cap_rate = None

    return cap_rate


def short_period_damping_rating(flight_phase, short_period_damping):
    """Give a rating of the short period damping Level1 Level2 or Level 3 according to MILF-8785C
    Args:
        flight_phase (str): Flight phase A, B or C
        short_period_damping (float): Short period damping ratio

    Returns:
        sp_damp_rate (int): 1 one 2 or 3 corresponding to the flight level

    """

    if flight_phase == "A" or flight_phase == "C":
        if 0.35 <= short_period_damping <= 1.3:
            sp_damp_rate = 1
        elif 0.25 <= short_period_damping <= 2:
            sp_damp_rate = 2
        elif 0.15 <= short_period_damping:
            sp_damp_rate = 3
        else:
            sp_damp_rate = None
    else:  # Aircraft class : B
        if 0.3 <= short_period_damping <= 2:
            sp_damp_rate = 1
        elif 0.2 <= short_period_damping <= 2:
            sp_damp_rate = 2
        elif 0.15 <= short_period_damping:
            sp_damp_rate = 3
        else:
            sp_damp_rate = None

    return sp_damp_rate


def short_period_frequency_rating(flight_phase, aircraft_class, sp_freq, load_factor):
    """Give a rating of the Roll mode : Level1 Level2 or Level 3 according to MILF-8785C
    Args:
        flight_phase (str): Flith phase 'A',  'B' or 'C' (Cooper-Harper)
        aircraft_class (int): Type of aircrft (1, 2, 3 or 4) (Cooper-Harper)
        sp_freq (float): Short perido frequency [rad/s]
        load_factor (float): Load factor [-]

    Returns:
        sp_freq_rate (int): 1 one 2 or 3 corresponding to the flight level

    """
    if flight_phase == "A":
        if 3.6 <= load_factor <= 100:
            if 0.28 * load_factor <= sp_freq ** 2 <= 3.5 * load_factor:
                sp_freq_rate = 1
            elif 0.28 * load_factor <= sp_freq ** 2 <= 10 * load_factor:
                sp_freq_rate = 2
            else:
                sp_freq_rate = 3
        elif 2.2 <= load_factor <= 3.6:
            if 1 <= sp_freq ** 2 <= 3.5 * load_factor:
                sp_freq_rate = 1
            elif 1 <= sp_freq ** 2 <= 10 * load_factor:
                sp_freq_rate = 2
            else:
                sp_freq_rate = 3
        elif 1 <= load_factor <= 2.2:
            if 1 <= sp_freq ** 2 <= 3.5 * load_factor:
                sp_freq_rate = 1
            elif 0.6 <= sp_freq ** 2 <= 10 * load_factor:
                sp_freq_rate = 2
            else:
                sp_freq_rate = 3
        else:
            sp_freq_rate = None

    elif flight_phase == "B":
        if 1 <= load_factor <= 100:
            if 0.085 * load_factor <= sp_freq ** 2 <= 3.6 * load_factor:
                sp_freq_rate = 1
            elif 0.085 * load_factor <= sp_freq ** 2 <= 10 * load_factor:
                sp_freq_rate = 2
            else:
                sp_freq_rate = 3
        else:
            sp_freq_rate = None

    else:  #  flight_phase == 'C' :
        if aircraft_class == 1 or aircraft_class == 4:
            if 4.2 <= load_factor <= 100:
                if 0.16 * load_factor <= sp_freq ** 2 <= 3.6 * load_factor:
                    sp_freq_rate = 1
                elif 0.096 * load_factor <= sp_freq ** 2 <= 10 * load_factor:
                    sp_freq_rate = 2
                else:
                    sp_freq_rate = 3
            elif 3.3 <= load_factor <= 4.2:
                if 0.86 <= sp_freq ** 2 <= 3.6 * load_factor:
                    sp_freq_rate = 1
                elif 0.86 <= sp_freq ** 2 <= 10 * load_factor:
                    sp_freq_rate = 2
                else:
                    sp_freq_rate = 3
            elif 2.7 <= load_factor <= 3.3:
                if 0.86 <= sp_freq ** 2 <= 3.6 * load_factor:
                    sp_freq_rate = 1
                elif 0.6 <= sp_freq ** 2 <= 10 * load_factor:
                    sp_freq_rate = 2
                else:
                    sp_freq_rate = 3
            elif 1.7 <= load_factor <= 2.7:
                if 0.6 <= sp_freq ** 2 <= 10 * load_factor:
                    sp_freq_rate = 2
                else:
                    sp_freq_rate = 3
            elif 1 <= load_factor <= 1.7:
                sp_freq_rate = 3
            else:
                sp_freq_rate = None

        else:  # aircraft_class == 2 or aircraft_class == 3:
            if 3 <= load_factor <= 100:
                if 0.16 * load_factor <= sp_freq ** 2 <= 3.6 * load_factor:
                    sp_freq_rate = 1
                elif 0.096 * load_factor <= sp_freq ** 2 <= 10 * load_factor:
                    sp_freq_rate = 2
                else:
                    sp_freq_rate = 3
            elif 2 <= load_factor <= 3:
                if 0.7 <= sp_freq ** 2 <= 3.6 * load_factor:
                    sp_freq_rate = 1
                elif 0.096 * load_factor <= sp_freq ** 2 <= 10 * load_factor:
                    sp_freq_rate = 2
                else:
                    sp_freq_rate = 3
            elif 1.6 <= load_factor <= 3:
                if 0.096 * load_factor <= sp_freq ** 2 <= 10 * load_factor:
                    sp_freq_rate = 2
                else:
                    sp_freq_rate = 3
            elif 1 <= load_factor <= 1.6:
                if 0.4 <= sp_freq ** 2 <= 10 * load_factor:
                    sp_freq_rate = 2
                else:
                    sp_freq_rate = 3
            else:
                sp_freq_rate = None

    return sp_freq_rate


def phugoid_rating(phugoid_damping, ph_t2):
    """Give a rating of the phugoid mode : Level1 Level2 or Level 3 according to MILF-8785C

    Args:
        phugoid_damping (float): Phugoid damping ratio[-]
        ph_t2 (float): Phugoid time to double amplitude [s]

    Returns:
        ph_rate (int): 1 one 2 or 3 corresponding to the flight level
    """

    if 0.04 < phugoid_damping:
        ph_rate = 1
    elif 0 < phugoid_damping < 0.04:
        ph_rate = 2
    elif 55 <= ph_t2:
        ph_rate = 3
    else:
        ph_rate = None

    return ph_rate


def direc_root_identification(A_direc):
    """identifies the root of the lateral charcateristic equation

    Args:
        roots_direc_list : a list of four roots

    Returns:
        If dutch roll roots are not complex conjugate, and spiral and roll not identified, the function returns:
            None
        If roots are well identified:
            roll : the root coresponding to the roll equation
            spiral : the root coresponding to the spiral equation
            dr1 : first complex root of the dutch roll mode
            dr1 : complex conjugate root of the dutch roll mode
    """

    # Compute eigenvalues and eigenvectors of lateral CONCISE equations at trim
    eg_value_direc, eg_vector_direc = linalg.eig(A_direc)

    # TODO: from book, maybe use as test
    # # In cincise form,   delta = aS^5 + bS^4 + cS^3+ dS^2 + eS + f ,  delta_direc =[a,b,c,d,e,f]
    # delta_direc = [1,\
    #                         -(l_p+n_r+y_v),
    #                         (l_p*n_r-l_r*n_p)+(n_r*y_v-n_v*y_r)+(l_p*y_v-l_v*y_p)-(l_phi+n_psi),\
    #                         (l_p*n_psi-l_psi*n_p)+(l_phi*n_r-l_r*n_phi)+l_v*(n_r*y_p-n_p*y_r-y_phi)+n_v*(l_p*y_r-l_r*y_p-y_psi)+y_v*(l_r*n_p-l_p*n_r+l_phi+n_psi),\
    #                         (l_phi*n_psi-l_psi*n_psi)+l_v*((n_r*y_phi-n_phi*y_r)+(n_psi*y_p-n_p*y_psi))+n_v*((l_phi*y_r-l_r*y_phi)+(l_p*y_psi-l_psi*y_p))+y_v*((l_r*n_phi-l_phi*n_r)+(l_psi*n_p-l_p*n_psi)),\
    #                         l_v*(n_psi*y_phi-n_phi*y_psi)+n_v*(l_phi*y_psi-l_psi*y_phi)+y_v*(l_psi*n_phi-l_phi*n_psi)]

    roll = None
    spiral = None
    dr1 = None
    dr2 = None
    reals = []

    for root in eg_value_direc:
        if root.imag != 0:  # if complex root
            if np.imag(root) > 0:  # If imaginary part >0
                dr1 = root  # Dutch Roll Root1
            else:
                dr2 = root  # Dutch Roll Root2
        else:  # If real root
            reals.append(root.real)

    absolute = [abs(value) for value in reals]
    absolute.sort(reverse=True)

    for elem in reals:
        if abs(elem) == absolute[0]:
            roll = elem
        elif abs(elem) == absolute[1]:
            spiral = elem
        else:
            pass

    if (
        dr1 == None or dr2 == None or roll == None or spiral == None
    ):  # Check that all variable have been assigned a value
        return (None, eg_value_direc)
    elif dr1 != np.conj(dr2):  # Check that dr roots are complex conjugate
        return (None, eg_value_direc)
    else:
        # Calculate eigen vectors magnitude :
        eg_vector_direc_magnitude = []
        for row in eg_vector_direc:
            new_row = []
            for vector in row:
                vector_magnitude = abs(vector)  # Module of complex number
                new_row.append(format(vector_magnitude, ".4g"))
            eg_vector_direc_magnitude.append(new_row)
        return (roll, spiral, dr1, dr2, eg_value_direc, eg_vector_direc, eg_vector_direc_magnitude)


def direc_mode_characteristic(roll, spiral, dr1, dr2):
    """TODO:

    roll,spiral,dr1,dr2 roots of characteristic equation

    Args:

    Returns:
        roll_timecst,
        spiral_timecst,
        spiral_t2: time to double amplitude
        dr_freq  [rad/s]
        dr_damp
        dr_damp_freq (): product of freq and damping ratio[rad/s]

    """

    # Roll
    roll_timecst = -1 / roll

    # Spiral
    spiral_timecst = -1 / spiral
    spiral_t2 = ln(2) / spiral

    # Dutch Roll
    dr_freq = (
        np.sqrt(dr1 * dr2)
    ).real  #  [rad/s] Undamped natural frequency omega, of concise equations
    dr_damp = -dr1.real / dr_freq  # [-] Damping of concise equations
    dr_damp_freq = dr_damp * dr_freq  # [rad/s] time constante  T = 1/(XiOmega)

    return (roll_timecst, spiral_timecst, spiral_t2, dr_freq, dr_damp, dr_damp_freq)


def roll_rating(flight_phase, aircraft_class, roll_timecst):
    """Give a rating of the Roll mode : Level1 Level2 or Level 3 according to MILF-8785C

    Args:
        flight_phase (str): 'A',  'B' or 'C'
        aircraft_class (int): 1, 2, 3 or 4
        roll_timecst (float): Roll Mode time constante [s]

    Returns:
        roll_rate (int): 1 one 2 or 3 corresponding to the flight level

    """

    if flight_phase == "A" or flight_phase == "C":
        if aircraft_class == 1 or aircraft_class == 4:
            if 0 <= roll_timecst <= 1:
                roll_rate = 1
            elif roll_timecst <= 1.4:
                roll_rate = 2
            elif roll_timecst <= 10:
                roll_rate = 3
            else:
                roll_rate = None
        else:  # aircraft_class == 2 or aircraft_class == 3:
            if 0 <= roll_timecst <= 1.4:
                roll_rate = 1
            elif roll_timecst <= 3:
                roll_rate = 2
            elif roll_timecst <= 10:
                roll_rate = 3
            else:
                roll_rate = None
    else:  #   flight_phase == 'B':
        if 0 <= roll_timecst <= 1.4:
            roll_rate = 1
        elif roll_timecst <= 3:
            roll_rate = 2
        elif roll_timecst <= 10:
            roll_rate = 3
        else:
            roll_rate = None

    return roll_rate


def spiral_rating(flight_phase, spiral_timecst, spiral_t2):
    """Give a rating of the Spiral mode : Level1 Level2 or Level 3 according to MILF-8785C

    Args:
        flight_phase (str): 'A',  'B' or 'C'
        spiral_timecst ():
        spiral_t2 (float): Spiral Mode time to double amplitude [s]

    Returns:
        spiral_rate (int): 1 one 2 or 3 corresponding to the flight Level
    """

    # if stable : Level 1
    if spiral_timecst > 0:
        spiral_rate = 1

    # If unstable depends on time to double amplitude.
    else:
        if flight_phase == "A" or flight_phase == "C":
            if 12 <= spiral_t2:
                spiral_rate = 1
            elif 8 <= spiral_t2:
                spiral_rate = 2
            elif 4 <= spiral_t2:
                spiral_rate = 3
            else:
                spiral_rate = None

        else:  # flight_phase == 'B':
            if 20 <= spiral_t2:
                spiral_rate = 1
            elif 8 <= spiral_t2:
                spiral_rate = 2
            elif 4 <= spiral_t2:
                spiral_rate = 3
            else:
                spiral_rate = None

    return spiral_rate


def dutch_roll_rating(
    flight_phase, aircraft_class, dr_damping, dr_frequency, dr_damping_frequency
):
    """Give a rating of the Dutch Roll mode : Level1 Level2 or Level3 according to MILF-8785C
    Args:
        flight_phase (str) : 'A',  'B' or 'C'
        aircraft_class (int) : 1, 2, 3 or 4
        dr_damping (float) : Dutch Roll mode damping [-]
        dr_frequency (float): Dutch Roll mode damping [rad/s]
        dr_damping_frequency (float): product of dr_damping*dr_frequency [rad/s]

    Returns:
        dr_rate (int): 1 one 2 or 3 corresponding to the flight Level

    """

    if flight_phase == "A":  # flight Phase A
        if aircraft_class == 1 or aircraft_class == 4:  # Classes I and IV
            if dr_damping >= 0.19 and dr_damping_frequency >= 0.35 and dr_frequency >= 1:
                dr_rate = 1
            elif dr_damping >= 0.02 and dr_damping_frequency >= 0.05 and dr_frequency >= 0.4:
                dr_rate = 2
            elif dr_damping >= 0 and dr_frequency >= 0.4:
                dr_rate = 3
            else:
                dr_rate = None
        else:  #  aircraft_class ==2 or aircraft_class ==3: # Classes II and III
            if dr_damping >= 0.19 and dr_damping_frequency >= 0.35 and dr_frequency >= 0.4:
                dr_rate = 1
            elif dr_damping >= 0.02 and dr_damping_frequency >= 0.05 and dr_frequency >= 0.4:
                dr_rate = 2
            elif dr_damping >= 0 and dr_frequency >= 0.4:
                dr_rate = 3
            else:
                dr_rate = None
    elif flight_phase == "B":  # flight Phase B, whatever the aircraft class
        if dr_damping >= 0.08 and dr_damping_frequency >= 0.15 and dr_frequency >= 0.4:
            dr_rate = 1
        elif dr_damping >= 0.02 and dr_damping_frequency >= 0.05 and dr_frequency >= 0.4:
            dr_rate = 2
        elif dr_damping >= 0 and dr_frequency >= 0.4:
            dr_rate = 3
        else:
            dr_rate = None
    else:  # flight_phase == 'C':
        if aircraft_class == 1 or aircraft_class == 4:  # Classes I and IV
            if dr_damping >= 0.08 and dr_damping_frequency >= 0.15 and dr_frequency >= 1:
                dr_rate = 1
            elif dr_damping >= 0.02 and dr_damping_frequency >= 0.05 and dr_frequency >= 0.4:
                dr_rate = 2
            elif dr_damping >= 0 and dr_frequency >= 0.4:
                dr_rate = 3
            else:
                dr_rate = None
        else:  # aircraft_class ==2 or aircraft_class ==3: # Classes II and III
            if dr_damping >= 0.08 and dr_damping_frequency >= 0.1 and dr_frequency >= 0.4:
                dr_rate = 1
            elif dr_damping >= 0.02 and dr_damping_frequency >= 0.05 and dr_frequency >= 0.4:
                dr_rate = 2
            elif dr_damping >= 0 and dr_frequency >= 0.4:
                dr_rate = 3
            else:
                dr_rate = None

    return dr_rate


# ==============================================================================
#    MAIN
# ==============================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
