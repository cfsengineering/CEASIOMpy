"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This programm stors all function needed for stability analysis (dynamic and static)


| Works with Python 2.7
| Author : Verdier Loic
| Date of creation: 2019-12-30
| Last modifiction: 2019-12-30
"""
#=============================================================================
#   IMPORTS
#=============================================================================

import os
import sys
from math import sqrt
import numpy as np
import matplotlib.patheffects
import matplotlib.pyplot as plt
from matplotlib import rcParams, cycler
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

#=============================================================================
#   CLASSES
#=============================================================================


#=============================================================================
#   FUNCTIONS
#=============================================================================

def short_period(u0, qs, m, i_yy, mac, cm_alpha,  cd0, cl_alpha, cm_q ): # To add: Cm_alphaDot, & raise value error
    """Short Periode mode dampig and frequence

    Args:
        Speed u0 in m/s
        qs : the dynamic pressure time the wing surface
        i_yy : the moment inertia aroud y axis
        mac: the mean aero dynamic chord of the plane
        m_alpha : derivative of M moment coefficient (litterature) with repect to the angle of attack
        cd0 : the drag coefficient in trimm boundaryConditions
        cl0 : the lift coefficient at trimm conditions
        cl_alpha :  derivative of L moment coefficient (litterature)  with repect to the angle of attack
        cm_q : derivative of M moment coefficient (litterature) with repect to the pitch rate [rad/s]

    Returns:
        damp : short period dampig at trim conditions
        freq: short period frequence (omega) at trim conditions [rad/s]
    """
    m_alpha = qs*mac*cm_alpha/(i_yy*u0**2)
    z_alpha = qs*(-cd0-cl_alpha)/(m*u0)
    m_q = qs*(mac**2)*cm_q/(2*i_yy*u0)

    if (-m_alpha + (z_alpha*m_q/u0)) > 0 :
        freq = sqrt(-m_alpha + (z_alpha*m_q/u0)) # [rad/s]
        damp = -(m_alpha+z_alpha/u0)/(2*freq)
    else:
        log.error('Error in calculating Short Period mode frequenc, negtive value in sqrt.')
        # raise value error
    return (damp, freq)


def phugoid( u0, cd0, cl0, g) :
    """Return phugoid mode damping and frequence

    Args:
        u0 : the trimm Speed [m/s]
        cd0 : the dragg coeff at trimm conditions
        lc0 : the lift coefficent at trimm conditions
        g : the gravittional acceleration

    Returns:
        damp : phugoid damping at trim conditions
        freq: phugoid frequence (omega) at trim conditions [rad/s]
    """
    freq = sqrt(2)*g/u0 # [rad/s]
    damp = -cd0/(sqrt(2)*cl0)

    return (damp, freq)


def roll(u0, qs, i_xx, i_zz, b, cl_p, cn_p):
    """Return roll mode damping and frequence is set to zero.

    Args:
        u0 : trimm speed in m/s
        qs : the dynamic pressure time the wing surface
        i_xx: the moment inertia aroud x axis
        i_zz: the moment inertia aroud z axis
        b : the aricraft span
        cl_p : L moment coefficent (litterature) derivative with respect to angular velocity around x axis [rad/s]
        cn_p : N moment coefficent (litterature) derivative with respect to angular velocity around x axis [rad/s]

    Returns:
        damp : roll damping at trim conditions
        freq:  is set at zero in order to plot it. (no imganary part for this mode)
    """
    l_p = (qs*(b**2)/(i_xx*u0))*cl_p # Moment L coefficeit derivated with p (lateral moment derivative) dcmddpstar
    n_p = (qs*(b**2)/(i_zz*u0))*cn_p # Moment N coefficeit derivated with p (Sideslip moment derivative) dcmldpstar

    damp = (l_p + i_xx*n_p)/(1-i_xx*i_zz)

    return (damp, 0)


# Spiral mode:
def spiral(u0, qs, b, i_xx, i_zz, cn_r, cl_r, cl_beta, cn_beta):
    """Return spiral mode damping and set frequence to zero.

    Args:
        u0 : trimm speed  in m/s
        qs : the dynamic pressure time the wing surface
        b : the aricraft span
        i_xx : the moment inertia aroud x axis
        i_yy : the moment inertia aroud y axis
        cn_r : N moment coefficent (litterature) derivative with respect to angular velocity around z axis [rad/s]
        cl_r : L moment coefficent (litterature) derivative with respect to angular velocity around z axis [rad/s]
        cl_beta :  L moment coefficent (litterature) derivative with respect to sideslip angle at trimm
        cn_beta : N moment coefficent (litterature) derivative with respect to sideslip angle at trimm

    Returns:
        damp : spiral damping at trim conditions
        freq :  is set at zero in order to plot it. (no imganary part for this mode)
    """
    n_r = (qs*(b**2)/(2*i_zz*u0))*cn_r # Moment N
    l_r = (qs*(b**2)/(2*i_xx*u0))*cl_r # Moment L
    n_v = (qs*b/(i_zz*u0))*cn_beta # Moment N
    l_v = (qs*b/(i_xx*u0)) *cl_beta # Moment L

    damp = n_r - (l_r * n_v/l_v)

    return (damp, 0)


# Dutch roll monde
def dutch_roll(u0, qs, b,i_xx, i_zz, cl_p, cl_r, cl_beta , cn_p, cn_r, cn_beta ): # l_p, l_r, l_v , L moment derivatives
    """Return dutch roll mode damping and frequnce

    Args:
        u0 : trimm speed  in m/s
        qs : the dynamic pressure time the wing surface
        b : the aricraft span
        i_xx : the moment inertia aroud x axis
        i_zz : the moment inertia aroud z axis
        cl_p : L moment coefficent (litterature) derivative with respect to angular velocity around x axis [rad/s]
        cl_r : L moment coefficent (litterature) derivative with respect to angular velocity around z axis [rad/s]
        cl_beta :  L moment coefficent (litterature) derivative with respect to sideslip angle at trimm
        cn_p : N moment coefficent (litterature) derivative with respect to angular velocity around x axis [rad/s]
        cn_r : N moment coefficent (litterature) derivative with respect to angular velocity around z axis [rad/s]
        cn_beta : N moment coefficent (litterature) derivative with respect to sideslip angle at trimm

    Returns:
        damp : dutch roll damping at trim conditions
        freq:  dutch roll angular frequence in rad/s at trimm condition
    """
    l_p =  (qs*(b**2)/(i_xx*u0))*cl_p
    l_r =  (qs*(b**2)/(i_xx*u0))*cl_r
    l_v =  (qs*b/(i_xx*u0))*cl_beta

    n_p =  (qs*(b**2)/(i_zz*u0))*cn_p
    n_r =  (qs*(b**2)/(i_zz*u0))*cn_r
    n_v =  (qs*b/(i_zz*u0))*cn_beta

    freq = sqrt(u0*(l_p*n_v-l_v*n_p)/(l_p+n_r))
    damp = (1/(2*freq)) * ((-l_p*n_r-u0*n_v+l_r*n_p)/(l_p+n_r) - u0*(-l_v*n_p + l_p*n_v)/((l_p+n_r)**2))
    return (damp, freq)


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

def extract_subelements(vector):
    """ Transform multiple element list into a 1D vector

    Function 'extract_subelements' return [1,2,3,1] from an oririginal vector
    like [[1,2,3], [1]]

    Args:
        vector (list of list): Original list of list

    Returns:
        extracted (list): Return 1D list
    """

    extracted = []
    for elem in vector:
        for value in elem :
            extracted.append(value)

    return extracted


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
    value = list[idx1] + ratio * ( list[idx2] - list[idx1])
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


# Function derivative, or more trim condition function
def trim_derivative(alt, mach, list1, list2):
    """Find if a moments coefficeint cm cross the 0 line, once or more
        Find if a moment coefficeint cm. crosse the 0 line only once and return
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
    if len(np.argwhere(np.diff(np.sign(list1)))) == 0  :
        crossed = False
        # If all list1. values are 0:
        if list1.count(0) == len(list1):
            log.warning('Alt = {}, mach = {} moment coefficients list is composed of 0 only.'.format(alt, mach))
        # If cm curve does not cross the 0 line
        else:
            log.error('Alt = {}, mach = {} moment coefficients list does not cross the 0 line, aircraft not stable, trimm conditions not achieved.'.format(alt, mach))
    # If list1. Curve crosses the 0 line more than once no stability analysis can be performed
    elif len(np.argwhere(np.diff(np.sign(list1)))) > 2 or list1.count(0) > 1:
        log.error('Alt = {}, mach = {} moment coefficients list crosses more than once the 0 line, no stability analysis performed'.format(alt, mach))
        crossed  = False
    # If list1. Curve crosses the 0 line twice
    elif 0 not in np.sign(list1) and len(np.argwhere(np.diff(np.sign(list1)))) == 2:
        log.error('Alt = {}, mach = {} moment coefficients list crosses the 0 line twice, no stability analysis performed'.format(alt, mach))
        crossed = False
    # If   0 is in list1
    elif 0 in np.sign(list1) and list1.count(0) == 1 and crossed:
        idx_list1_0 = [i for i in range(len(list1)) if list1[i] == 0][0]
        # If 0 is the first element in list1
        if idx_list1_0 == 0 :
            idx_trim_before = idx_list1_0
            idx_trim_after = idx_list1_0+1

            # Angles and coeffs before and after crossing the 0 line
            value_before = list2[idx_trim_before ]
            value_after = list2[idx_trim_after ]
            list1_before = list1[idx_trim_before ]
            list1_after = list1[idx_trim_after ]

            trim_value = value_before
            trim_parameter = (list1_after-list1_before)/(value_after-value_before)
            ratio = trim_value/(value_after -value_before )

        # If 0 is the last element in list1
        elif idx_list1_0 == len(list1) - 1:
            idx_trim_before = idx_list1_0-1
            idx_trim_after = idx_list1_0

            # values and coeffs before and after crossing the 0 line
            value_before = list2[idx_trim_before]
            value_after = list2[idx_trim_after]
            list1_before = list1[idx_trim_before]
            list1_after = list1[idx_trim_after]

            trim_value = value_after
            trim_parameter = (list1_after-list1_before)/(value_after-value_before)
            ratio = trim_value/(value_after -value_before)

        # If  0 is nor the first nor the last element in list1
        elif 0 < idx_list1_0 < len(list1)-1:
            idx_trim_before = idx_list1_0-1
            idx_trim_after = idx_list1_0+1

            # Angles and coeffs before and after crossing the 0 line
            value_before = list2[idx_trim_before]
            value_after = list2[idx_trim_after]
            list1_before = list1[idx_trim_before]
            list1_after = list1[idx_trim_after]

            trim_value= list2[idx_list1_0]
            trim_parameter = (list1_after - list1_before)/(value_after - value_before)
            ratio = trim_value/(value_after - value_before )

    # If list1 crosse the 0 line and 0 is not in list1
    elif  len(np.argwhere(np.diff(np.sign(list1)))) == 1 and 0 not in np.sign(list1) and crossed:
        # Make the linear equation btween the 2 point before and after crossing the 0 ine y=ax+b
        idx_list1_0 = np.argwhere(np.diff(np.sign(list1)))[0][0]
        idx_trim_before = idx_list1_0
        idx_trim_after = idx_list1_0+1

        # Angles and coeffs before and after crossing the 0 line
        value_before = list2[idx_trim_before]
        value_after = list2[idx_trim_after]
        list1_before = list1[idx_trim_before]
        list1_after = list1[idx_trim_after]

        fit = np.polyfit([value_before, value_after], [list1_before, list1_after], 1)  # returns [a,b] of y=ax+b

        trim_value= -fit[1]/fit[0]    # list1. = 0 for y = 0  hence cruise agngle = -b/a
        trim_parameter = fit[0]
        ratio =  trim_value/(value_after - value_before )

    return (trim_value, trim_parameter, idx_trim_before, idx_trim_after, ratio)

def adimensionalise(a,mach,rho,s,b,mac,m,I_xx,I_yy,I_zz,I_xz):
    u0 = a*mach # Trimm speed
    q = 0.5 * rho * u0**2 # Static pressure
    qs = q*s
    m_adim = m/(0.5*rho*u0*s)
    i_xx = I_xx/(0.5*rho*u0*s*b)
    i_yy = I_yy/(0.5*rho*u0*s*mac)
    i_zz = I_zz/(0.5*rho*u0*s*b)
    i_xz = I_xz/(0.5*rho*u0*s*b)
    return(u0, m_adim, i_xx, i_yy, i_zz, i_xz)



def speed_derivative_at_trim(parameter_list,mach,idx_alt,aoa_list,aos,aos_list,mach_unic_list,idx_trim_before, idx_trim_after, ratio):
                      # speed_derivative_at_trim(cs,aos,idx_alt,aoa_list,mach,mach_list,aos_unic,idx_trim_before, idx_trim_after, ratio)
    """ find the speed derivative of "paramter" at trim conditions
    Args:
        parameter_list : list of parameter's values : e.i. Cd (dragg coefficient)
        mach : the mach at trim conditions
        mach_unic_list : list of unic values of mach
        idx_trim_before : index
    Returns:
        paramter_speed_derivative: paramter speed derivaive at trim condtion ei cd@ aoa=4.22
    """
    idx_mach_left = []
    idx_mach_right = []
    # if Mach first value,of Mach unic hence make a right derivative
    if mach == mach_unic_list[0]:
    # if aos == aos_unic_list[0] :
        mach_left = mach
        mach_right = mach_unic_list[1]
        idx_mach_left = [j for j in range(len(mach_list)) if mach_list[j] == mach_left]
        idx_mach_right = [j for j in range(len(mach_list)) if mach_list[j] == mach_right ]
    # if Mach last value,of Mach_unic hence make a left derivative
    elif mach == mach_unic_list[-1]:
    # elif aos == aos_unic_list[-1] :
        mach_left =  mach_unic_list[-2]
        mach_right = mach
        idx_mach_left = [j for j in range(len(mach_list)) if mach_list[j] == mach_left ]
        idx_mach_right = [j for j in range(len(mach_list)) if mach_list[j] == mach_right ]
    # else,  Mach  value is nor the first nor the last value, of Mach_unic hence make middle derivative
    else:
        idx_mach_in_mach_unic = [j for j in range(len(mach_unic_list)) if mach_unic_list[j] == mach][0]
        mach_left = mach_unic_list[idx_mach_in_mach_unic-1]
        mach_right = mach_unic_list[idx_mach_in_mach_unic+1]
        idx_mach_left = [j for j in range(len(mach_list)) if mach_list[j] == mach_left ]
        idx_mach_right = [j for j in range(len(mach_list)) if mach_list[j] == mach_right ]
    idx_aoa_left = [j for j in range(len(aoa_list)) if aoa_list[j] == aoa_list[idx_trim_before]]
    idx_aoa_right = [j for j in range(len(aoa_list)) if aoa_list[j] == aoa_list[idx_trim_after]]
    idx_aos = [j for j in range(len(aos_list)) if aos_list[j] == aos]
    # Cd @ trim AOA @mach_left
    idx_parameter_left_left = get_index(get_index(idx_aoa_left, idx_mach_left, idx_aos),idx_alt,idx_alt)[0] # left value
    idx_parameter_left_right= get_index(get_index(idx_aoa_right, idx_mach_left, idx_aos),idx_alt,idx_alt)[0]  # right value
    parameter_left = parameter_list[idx_parameter_left_left]  + (parameter_list[idx_parameter_left_right] - parameter_list[idx_parameter_left_left])*ratio
    # Cd @ trim AOA @mach_right
    idx_parameter_right_left = get_index(get_index(idx_aoa_left, idx_mach_right, idx_aos),idx_alt,idx_alt)[0]  # left value
    idx_parameter_right_right= get_index(get_index(idx_aoa_right, idx_mach_right, idx_aos),idx_alt,idx_alt)[0]  # right value
    parameter_right = parameter_list[idx_parameter_right_left]  + (parameter_list[idx_parameter_right_right] - parameter_list[idx_parameter_right_left])*ratio
    # Cd  derivative @ trim AOA
    parameter_speed_derivative = (parameter_left-parameter_right)/(mach_left-mach_right)
    return parameter_speed_derivative

def speed_derivative_at_trim_lat(parameter_list,aos,idx_alt,mach_list,mach,aos_list,aos_unic_list,idx_trim_before, idx_trim_after, ratio):
                      # speed_derivative_at_trim(cs,aos,idx_alt,aoa_list,mach,mach_list,aos_unic,idx_trim_before, idx_trim_after, ratio)
    """ find the speed derivative of "paramter" at trim conditions
    Args:
        parameter_list : list of parameter's values : e.i. Cd (dragg coefficient)
        aos : the aos at trim conditions
        aos_unic_list : list of unic values of aos
        idx_trim_before : index
    Returns:
        paramter_speed_derivative: paramter speed derivaive at trim condtion ei cd@ aoa=4.22
    """
    idx_aos_left = []
    idx_aos_right = []
    # if aos first value,of aos unic hence make a right derivative
    if aos == aos_unic_list[0] :
        aos_left = aos
        aos_right = aos_unic_list[1]
        idx_aos_left = [j for j in range(len(aos_list)) if aos_list[j] == aos_left]
        idx_aos_right = [j for j in range(len(aos_list)) if aos_list[j] == aos_right ]
    # if aos last value,of aos_unic hence make a left derivative
    elif aos == aos_unic_list[-1] :
        aos_left =  aos_unic_list[-2]
        aos_right = aos
        idx_aos_left = [j for j in range(len(aos_list)) if aos_list[j] == aos_left ]
        idx_aos_right = [j for j in range(len(aos_list)) if aos_list[j] == aos_right ]
    # else,  aos  value is nor the first nor the last value, of aos_unic hence make middle derivative
    else:
        idx_aos_in_aos_unic = [j for j in range(len(aos_unic_list)) if aos_unic_list[j] == aos][0]
        aos_left = aos_unic_list[idx_aos_in_aos_unic-1]
        aos_right = aos_unic_list[idx_aos_in_aos_unic+1]
        idx_aos_left = [j for j in range(len(aos_list)) if aos_list[j] == aos_left ]
        idx_aos_right = [j for j in range(len(aos_list)) if aos_list[j] == aos_right ]
    idx_aoa_left = [j for j in range(len(aoa_list)) if aoa_list[j] == aoa_list[idx_trim_before]]
    idx_aoa_right = [j for j in range(len(aoa_list)) if aoa_list[j] == aoa_list[idx_trim_after]]
    idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]
    # Cs @ trim AOA @aos_left

    alt_list      = [0,0,0,0,0,0,  0,0,0,0,0,0,  1,1,1,1,1,1,  1,1,1,1,1,1]
    mach_list = [0,0,1,1,2,2,  0,0,1,1,2,2,  0,0,1,1,2,2,  0,0,1,1,2,2]
    aoa_list    = [1,2,1,2,1,2,  1,2,1,2,1,2,  1,2,1,2,1,2,  1,2,1,2,1,2]
    aos_list    = [0,0,0,0,0,0,  1,1,1,1,1,1,  0,0,0,0,0,0,  1,1,1,1,1,1]
    cs_list      = [1,2,2,3,3,4,  2,3,2,3,2,3,  1,2,1,2,1,2,  2,3,2,3,2,3]

    idx_parameter_left_left = get_index(get_index(idx_aoa_left, idx_aos_left, idx_mach),idx_alt,idx_alt) # left value
    idx_parameter_left_right= get_index(get_index(idx_aoa_right, idx_aos_left, idx_mach),idx_alt,idx_alt)  # right value
    # if no value found for the left parameters, the function returns: None
    if idx_parameter_left_left == [] or idx_parameter_left_right == []:
        return
    else:
        idx_parameter_left_left = idx_parameter_left_left[0]# left value
        idx_parameter_left_right = idx_parameter_left_right[0]  # right value
    parameter_left = parameter_list[idx_parameter_left_left]  + (parameter_list[idx_parameter_left_right] - parameter_list[idx_parameter_left_left])*ratio
    # Cd @ trim AOA @aos_right
    idx_parameter_right_left = get_index(get_index(idx_aoa_left, idx_aos_right, idx_mach),idx_alt,idx_alt)  # left value
    idx_parameter_right_right= get_index(get_index(idx_aoa_right, idx_aos_right, idx_mach),idx_alt,idx_alt) # right value
    # if no value found for the left parameters, the function returns: None
    if idx_parameter_right_left == [] or idx_parameter_right_right == []:
        return
    else:
        idx_parameter_right_left = idx_parameter_right_left[0] # left value
        idx_parameter_right_right = idx_parameter_right_right[0] # right value
    parameter_right = parameter_list[idx_parameter_right_left]  + (parameter_list[idx_parameter_right_right] - parameter_list[idx_parameter_right_left])*ratio
    # Cd  derivative @ trim AOA
    parameter_speed_derivative = (parameter_left-parameter_right)/(aos_left-aos_right)
    return parameter_speed_derivative

def speed_derivative_at_trim_lat(parameter_list,aos,idx_alt,aoa_list,mach_list,mach,aos_list,aos_unic_list,idx_trim_before, idx_trim_after, ratio):
                      # speed_derivative_at_trim(cs,aos,idx_alt,aoa_list,mach,mach_list,aos_unic,idx_trim_before, idx_trim_after, ratio)
    """ find the speed derivative of "paramter" at trim conditions
    Args:
        parameter_list : list of parameter's values : e.i. Cd (dragg coefficient)
        aos : the aos at trim conditions
        aos_unic_list : list of unic values of aos
        idx_trim_before : index
    Returns:
        paramter_speed_derivative: paramter speed derivaive at trim condtion ei cd@ aoa=4.22
    """
    idx_aos_left = []
    idx_aos_right = []
    # if aos first value,of aos unic hence make a right derivative
    if aos == aos_unic_list[0] :
        aos_left = aos
        aos_right = aos_unic_list[1]
        idx_aos_left = [j for j in range(len(aos_list)) if aos_list[j] == aos_left]
        idx_aos_right = [j for j in range(len(aos_list)) if aos_list[j] == aos_right ]
    # if aos last value,of aos_unic hence make a left derivative
    elif aos == aos_unic_list[-1] :
        aos_left =  aos_unic_list[-2]
        aos_right = aos
        idx_aos_left = [j for j in range(len(aos_list)) if aos_list[j] == aos_left ]
        idx_aos_right = [j for j in range(len(aos_list)) if aos_list[j] == aos_right ]
    # else,  aos  value is nor the first nor the last value, of aos_unic hence make middle derivative
    else:
        idx_aos_in_aos_unic = [j for j in range(len(aos_unic_list)) if aos_unic_list[j] == aos][0]
        aos_left = aos_unic_list[idx_aos_in_aos_unic-1]
        aos_right = aos_unic_list[idx_aos_in_aos_unic+1]
        idx_aos_left = [j for j in range(len(aos_list)) if aos_list[j] == aos_left ]
        idx_aos_right = [j for j in range(len(aos_list)) if aos_list[j] == aos_right ]
    idx_aoa_left = [j for j in range(len(aoa_list)) if aoa_list[j] == aoa_list[idx_trim_before]]
    idx_aoa_right = [j for j in range(len(aoa_list)) if aoa_list[j] == aoa_list[idx_trim_after]]
    idx_mach = [j for j in range(len(mach_list)) if mach_list[j] == mach]
    # Cs @ trim AOA @aos_left
    idx_parameter_left_left = get_index(get_index(idx_aoa_left, idx_aos_left, idx_mach),idx_alt,idx_alt) # left value list containing only one value or empty
    idx_parameter_left_right= get_index(get_index(idx_aoa_right, idx_aos_left, idx_mach),idx_alt,idx_alt)  # right value list containing only one value or empty
    # if no value found for the left parameters, the function returns: None
    if idx_parameter_left_left == [] or idx_parameter_left_right == []:
        return
    else:
        idx_parameter_left_left = idx_parameter_left_left[0]# left value
        idx_parameter_left_right = idx_parameter_left_right[0]  # right value
    parameter_left = parameter_list[idx_parameter_left_left]  + (parameter_list[idx_parameter_left_right] - parameter_list[idx_parameter_left_left])*ratio
    # Cs @ trim AOA @aos_right
    idx_parameter_right_left = get_index(get_index(idx_aoa_left, idx_aos_right, idx_mach),idx_alt,idx_alt) # left value, list containing only one value or empty
    idx_parameter_right_right= get_index(get_index(idx_aoa_right, idx_aos_right, idx_mach),idx_alt,idx_alt)  # right value list containing only one value or empty
    # if no value found for the left parameters, the function returns: None
    if idx_parameter_right_left == [] or idx_parameter_right_right == []:
        return
    else:
        idx_parameter_right_left = idx_parameter_right_left[0] # left value
        idx_parameter_right_right = idx_parameter_right_right[0] # right value
    parameter_right = parameter_list[idx_parameter_right_left]  + (parameter_list[idx_parameter_right_right] - parameter_list[idx_parameter_right_left])*ratio
    # Cs derivative @ trim AOA
    parameter_speed_derivative = (parameter_left-parameter_right)/(aos_left-aos_right)
    return parameter_speed_derivative

def find_max_min(list1,list2): # fin values max and mi in list of lists
    """find the max and the min of 2 lists of lists
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
    for n in range(min([len(list1), len(list2)])): # take the minimum length even if the vectors are supposed to have the same length
        # Find x and y axis limits
        if n==0 :
            x_max = max(list1[0])
            x_min = min(list1[0])
            y_max = max(list2[0])
            y_min = min(list2[0])
        if n > 0  and max(list2[n]) > y_max :
            y_max = max(list2[n])
        if n > 0  and min(list2[n]) < y_min :
            y_min  = min(list2[n])
        if n > 0  and max(list1[n]) > x_max :
            x_max = max(list1[n])
        if n > 0  and min(list1[n]) < x_min :
            x_min = min(list1[n])
    return (x_max, x_min, y_max, y_min)


def plot_multicurve(analyses, y_axis, x_axis, plot_legend, plot_title, xlabel, ylabel, show_plots, save_plots):
    """Function to plot graph with different curves for a varying parameter

    Function 'plot_multicurve' can plot few curves

    Args:
        analyse (list) : list of 5 boolean to select curves to plot
            1st value : for plotting Short Periode mode
            2nd value : for plottin phugoid
            3rd value : for plotting roll mode
            4th value : for plotting
        x_axis (list) : List of vector of each curve's X coordinates
        y axis (list) : List of vector of each curve's Y coordinates
        plot_legend (list) : List of the leggends of all the different curves
        plot_title (str) : Tile of the plot
        xlabel (str) : Label of the x axis
        ylabel (str) : Label of the y axis
        show_plot (boolean) : To show plots on screen or not
        save_plot (boolean) : To save plots in the /ToolOutput dir or not

    Returns:
        A plot with different curves if asked.
    """
    # Avoid to do the rest of the function if nothing to plot or save
    if not show_plots and not save_plots:
        return None
    # Create figure
    fig, ax = plt.subplots()

    # To plot:
    short_period = analyses[0]
    phugoid = analyses[1]
    roll = analyses[2]
    spiral = analyses[3]
    dutch_roll = analyses[4]

    # Plots
    N = len(x_axis)
    cmap = plt.cm.viridis
    rcParams['axes.prop_cycle'] = cycler(color=cmap(np.linspace(0, 1, N)))
    legend = []

    if len(x_axis[0]) == 2 and (short_period or phugoid): # Plot longi
        if short_period :
            legend.append(Line2D([0], [0], marker='+', color='k', lw=0, label='Short Period', markersize=7))
        if phugoid :
            legend.append(Line2D([0], [0], marker='*', color='k', lw=0, label='Phugoid', markersize=7))

        for n in range(N):
            the_color = cmap(np.linspace(0, 1, N))[n]
            legend.append(Patch(facecolor = the_color ,label=plot_legend[n]))
            if short_period:
                plt.plot(x_axis[n][0], y_axis[n][0], marker='+', color=the_color,  markersize=7)
            if phugoid :
                plt.plot(x_axis[n][1], y_axis[n][1], marker='*', color=the_color, markersize=7)

    else: # Plot dir-lat
        if roll:
            legend.append(Line2D([0], [0], marker='+', color='k', lw=0, label='Roll Mode', markersize=7))
        if spiral:
            legend.append(Line2D([0], [0], marker='*', color='k', lw=0, label='Spiral Mode', markersize=7))
        if dutch_roll :
            legend.append(Line2D([0], [0], marker='o', color='k', lw=0, label='Dutch Roll Mode', markersize=7))

        for n in range(len(x_axis)):
            the_color = cmap(np.linspace(0, 1, N))[n]
            legend.append(Patch(facecolor = the_color ,label=plot_legend[n]))
            if roll:
                plt.plot(x_axis[n][0], y_axis[n][0], marker='+', color=the_color, markersize=4)
            if spiral :
                plt.plot(x_axis[n][1], y_axis[n][1], marker='*',color=the_color, markersize=4)
            if dutch_roll :
                plt.plot(x_axis[n][2], y_axis[n][2], marker='o', color=the_color, markersize=4)

    # Title
    plt.title(plot_title, fontdict=None, loc='center')
    # Legend
    ax.legend(handles=legend, loc='upper right')

    # Axes position
    axes = plt.gca()
    # Remove Top and right axes
    axes.spines['right'].set_color('none')
    axes.spines['top'].set_color('none')
    #Locate correctly axes:
    (x_max, x_min, y_max, y_min) = find_max_min(x_axis,y_axis)
    # Y axes
    if y_max < 0 :
        axes.spines['bottom'].set_position(('axes',1))
    elif y_min > 0 :
        axes.spines['bottom'].set_position(('axes',0))
    elif len(np.argwhere(np.diff(np.sign([y_min, y_max])))) != 0 :
        axes.spines['bottom'].set_position(('data',0))
    # X axes
    if x_max < 0 :
        axes.spines['left'].set_position(('axes',1))
    elif x_min > 0 :
        axes.spines['left'].set_position(('axes',0))
    elif len(np.argwhere(np.diff(np.sign([x_min, x_max])))) != 0 :
        axes.spines['left'].set_position(('data',0))

    # Axes labels
    axes.annotate('$Im$', xy=(0.05*x_max, y_max+0.05*(y_max-y_min)),  ha='left', va='top',  fontsize=12)
    axes.annotate('$Re$', xy=(x_max, 0.1*y_max),  ha='left', va='top', fontsize=12)

    if save_plots:
        fig_title = plot_title.replace(' ','_')
        fig_path = os.path.join(MODULE_DIR,'ToolOutput',fig_title) + '.svg'
        plt.savefig(fig_path)

    if show_plots:
        plt.show()

    log.info('Graph "{}" has been created'.format(plot_title))

def plot_freq_phaseA(x_coordinates,y_coordinates,plot_title,legend,show_plots,save_plots):
    ###    --------------------  'MILF-8785C ShortPeriod natual frequency requirements for flight phase A'   ---------
    show_plots = True
    # Create figure
    fig, ax = plt.subplots()

    # To plot:
    x_axis = [5,15]
    y_axis= [2,20]

    plt.plot(x_coordinates, y_coordinates,  marker='o', markersize=4, linestyle = 'None')

    # Graphic Sttelement
    # Title
    plt.title(plot_title, fontdict=None, loc='center')
    # Legend
    ax.legend(legend, loc='upper right')
    # Axes labels
    plt.xlabel(r'n/$\alpha  \backsim$ gs/rad')
    plt.ylabel(r'$\omega_{Nsp}  \backsim$ rad/s')
    # Axes format and Limit:
    ax.loglog() # Loglog axes
    for axis in [ax.xaxis, ax.yaxis]: # Ful number and not scientific notaion on axes
        formatter = ScalarFormatter()
        formatter.set_scientific(False)
        axis.set_major_formatter(formatter)
    axes = plt.gca()
    ( x_min,x_max, y_min, y_max ) = (1,100, 0.1,100)
    axes.set_xlim([x_min , x_max])
    axes.set_ylim([y_min,y_max])
    # grid
    plt.grid(True,which="both",ls="-")

    # Stability Levels
    #Level 1 sup.
    x_level_one_sup = [1,100]
    y_level_one_sup = [1.9,20]
    plt.plot(x_level_one_sup, y_level_one_sup, color='green', linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l1_sup = np.array((11, 5.2)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_sup.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l1_sup[0], l1_sup[1], 'Level 1', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    #Level 2 sup.
    x_level_two_sup = [1,100]
    y_level_two_sup = [3.2,33]
    plt.plot(x_level_two_sup, y_level_two_sup, color='orange', linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l2_sup = np.array((11, 8.7)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_sup.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l2_sup[0], l2_sup[1], 'Level 2', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    #Level 1 inf.
    x_level_one_inf1 = [1,3.7]
    y_level_one_inf1 = [1,1]
    plt.plot(x_level_one_inf1, y_level_one_inf1, color='green', linewidth=1.5)
    x_level_one_inf2 = [3.7,100]
    y_level_one_inf2 = [1,5.6]
    plt.plot(x_level_one_inf2, y_level_one_inf2, color='green', linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l1_inf= np.array((11, 1.9)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_inf.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l1_inf[0], l1_inf[1], 'Level 1', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    #Level 2 inf.
    x_level_two_inf1 = [1,2.4]
    y_level_two_inf1 = [0.6,0.6]
    plt.plot(x_level_two_inf1, y_level_two_inf1, color='orange', linewidth=1.5)
    #  Plot text : "Level2" on garpah
    l2_inf1 = np.array((1.1, 0.62)) #Location
    angle = 0 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_inf1.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l2_inf1[0], l2_inf1[1], 'Level 2', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    x_level_two_inf2 = [2.4,100]
    y_level_two_inf2 = [0.6,4.1]
    plt.plot(x_level_two_inf2, y_level_two_inf2, color='orange', linewidth=1.5)
    #  Plot text : "Level2 & 3" on garpah
    l2_inf = np.array((11, 1.35)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_inf.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l2_inf[0], l2_inf[1], 'Level 2 & 3', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    #Level 3 inf.
    x_level_three_inf1 = [1,2.4]
    y_level_three_inf1 = [0.39,0.6]
    plt.plot(x_level_three_inf1, y_level_three_inf1, color='red', linewidth=1.5)
    #  Plot text : "Level 3" on garpah
    l3_inf = np.array((1.1, 0.33)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_inf.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l3_inf[0], l3_inf[1], 'Level 3', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    if show_plots:
        plt.show()

    # log.info('Graph "{}" has been created'.format(plot_title))

def plot_freq_phaseB(x_coordinates,y_coordinates,plot_title,legend,show_plots,save_plots):
    ###    --------------------  'MILF-8785C ShortPeriod natual frequency requirements for flight phase B'   ---------
    # Create figure
    fig, ax = plt.subplots()

    # To plot:
    x_axis = [5,15]
    y_axis= [2,20]

    plt.plot(x_coordinates, y_coordinates, marker='o', markersize=4, linestyle = 'None')

    # Graphic Sttelement
    # Title
    plt.title(plot_title, fontdict=None, loc='center')
    # Legend
    ax.legend(legend, loc='upper right')
    # Axes labels
    plt.xlabel(r'n/$\alpha  \backsim$ gs/rad')
    plt.ylabel(r'$\omega_{Nsp}  \backsim$ rad/s')
    # Axes format and Limit:
    ax.loglog() # Loglog axes
    for axis in [ax.xaxis, ax.yaxis]: # Ful number and not scientific notaion on axes
        formatter = ScalarFormatter()
        formatter.set_scientific(False)
        axis.set_major_formatter(formatter)
    axes = plt.gca()
    ( x_min,x_max, y_min, y_max ) = (1,100, 0.1,100)
    axes.set_xlim([x_min , x_max])
    axes.set_ylim([y_min,y_max])
    # grid
    plt.grid(True,which="both",ls="-")

    # Stability Levels
    #Level 1 sup.
    x_level_one_sup = [1,100]
    y_level_one_sup = [1.9,18]
    plt.plot(x_level_one_sup, y_level_one_sup, color='green', linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l1_sup = np.array((11, 5.1)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_sup.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l1_sup[0], l1_sup[1], 'Level 1', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    #Level 2 sup.
    x_level_two_sup = [1,100]
    y_level_two_sup = [3.1,28]
    plt.plot(x_level_two_sup, y_level_two_sup, color='orange', linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l2_sup = np.array((11, 8.4)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_sup.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l2_sup[0], l2_sup[1], 'Level 2', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    #Level 1 inf.
    x_level_one_inf1 = [1,100]
    y_level_one_inf1 = [0.3,2.8]
    plt.plot(x_level_one_inf1, y_level_one_inf1, color='green', linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l1_inf= np.array((11, 1)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_inf.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l1_inf[0], l1_inf[1], 'Level 1', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    #Level 2 inf.
    x_level_two_inf1 = [1,100]
    y_level_two_inf1 = [0.2,01.9]
    plt.plot(x_level_two_inf1, y_level_two_inf1, color='orange', linewidth=1.5)
    #  Plot text : "Level2 & 3" on garpah
    l2_inf = np.array((11, 0.68)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_inf.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l2_inf[0], l2_inf[1], 'Level 2 & 3', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    # Show Plots
    if show_plots:
        plt.show()

    #log.info('Graph "{}" has been created'.format(plot_title))

def plot_freq_phaseC(x_coordinates,y_coordinates,plot_title,legend,show_plots,save_plots):
    ###    --------------------  'MILF-8785C ShortPeriod natual frequency requirements for flight phase C   ---------
    # Create figure
    fig, ax = plt.subplots()

    # To plot:
    plt.plot(x_coordinates, y_coordinates, marker='o', markersize=4, linestyle = 'None')

    # Graphic Sttelement
    # Title
    plt.title(plot_title, fontdict=None, loc='center')
    # Legend
    ax.legend(legend, loc='upper right')
    # Axes labels
    plt.xlabel(r'n/$\alpha  \backsim$ gs/rad')
    plt.ylabel(r'$\omega_{Nsp}  \backsim$ rad/s')
    # Axes format and Limit:
    ax.loglog() # Loglog axes
    for axis in [ax.xaxis, ax.yaxis]: # Ful number and not scientific notaion on axes
        formatter = ScalarFormatter()
        formatter.set_scientific(False)
        axis.set_major_formatter(formatter)
    axes = plt.gca()
    ( x_min,x_max, y_min, y_max ) = (1,100, 0.1,100)
    axes.set_xlim([x_min , x_max])
    axes.set_ylim([y_min,y_max])
    # grid
    plt.grid(True,which="both",ls="-")

    # Stability Levels
    #Level 1 sup.
    x_level_one_sup = [2,100]
    y_level_one_sup = [2.7,18]
    plt.plot(x_level_one_sup, y_level_one_sup, color='green', linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l1_sup = np.array((11, 5.3)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_sup.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l1_sup[0], l1_sup[1], 'Level 1', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    #Level 2 sup.
    x_level_two_sup = [1,100]
    y_level_two_sup = [3.1,32]
    plt.plot(x_level_two_sup, y_level_two_sup, color='orange', linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l2_sup = np.array((11, 8.8)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_sup.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l2_sup[0], l2_sup[1], 'Level 2', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    #Level 1 inf.
    x_level_one_inf1 = [2.9,100]
    y_level_one_inf1 = [0.7,3.9]
    plt.plot(x_level_one_inf1, y_level_one_inf1, color='green', linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l1_inf= np.array((11, 1.4)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_inf.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l1_inf[0], l1_inf[1], 'Level 1', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text
    #Level 1 inf2
    x_level_one_inf2 = [2.6,4.5]
    y_level_one_inf2 = [0.88,0.88]
    plt.plot(x_level_one_inf2, y_level_one_inf2, color='green', linewidth=1.5)
    #Level 1 inf3
    x_level_one_inf3 = [2,2.9]
    y_level_one_inf3 = [0.7,0.7]
    plt.plot(x_level_one_inf3, y_level_one_inf3, color='green', linewidth=1.5)
    #Level 1 Vertical 1
    x_level_one_vert1 = [2.6,2.6]
    y_level_one_vert1 = [0.88,3]
    plt.plot(x_level_one_vert1, y_level_one_vert1, color='green', linewidth=1.5)
    #  Plot text : "Classes I & IV" on garpah
    l1_vert1 = np.array((3, 0.93)) #Location
    angle = 90 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_vert1.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l1_vert1[0], l1_vert1[1], 'Classes I & IV', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text
    #Level 1 Vertical 2
    x_level_one_vert2 = [2,2]
    y_level_one_vert2 = [0.7,2.7]
    plt.plot(x_level_one_vert2, y_level_one_vert2, color='green', linewidth=1.5)
    #  Plot text : "Classes II & III" on garpah
    l1_vert2 = np.array((2.2, 0.8)) #Location
    angle = 90 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l1_vert1.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l1_vert2[0], l1_vert2[1], 'Classes II & III', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    #Level 2 inf.
    x_level_two_inf1 = [1.4,100]
    y_level_two_inf1 = [0.39,3]
    plt.plot(x_level_two_inf1, y_level_two_inf1, color='orange', linewidth=1.5)
    #  Plot text : "Level2 & 3" on garpah
    l2_inf = np.array((11, 1.08)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_inf.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l2_inf[0], l2_inf[1], 'Level 2 & 3', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    #Level2 inf 2
    x_level_two_inf2 = [1.7,3.5]
    y_level_two_inf2 = [0.6,0.6]
    plt.plot(x_level_two_inf2, y_level_two_inf2, color='orange', linewidth=1.5)
    #Level2 Vert1
    x_level_two_vert1 = [1.7,1.7]
    y_level_two_vert1 = [0.6,4]
    plt.plot(x_level_two_vert1, y_level_two_vert1, color='orange', linewidth=1.5)
    #  Plot text : "Classes I & IV" on garpah
    l2_vert1 = np.array((1.64, 0.63)) #Location
    angle = 90 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_vert1.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l2_vert1[0], l2_vert1[1], 'Level2, Classes I & IV', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text
    #Level2 Vert2
    x_level_two_vert2 = [1.01,1.01]
    y_level_two_vert2 = [0.39,3]
    plt.plot(x_level_two_vert2, y_level_two_vert2, color='orange', linewidth=1.5)
    #  Plot text : "Classes I & IV" on garpah
    l2_vert2 = np.array((1.09, 0.48)) #Location
    angle = 90 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l2_vert2.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l2_vert2[0], l2_vert2[1], 'Level2, Classes II & III', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    #Level2 inf 3
    x_level_two_inf3 = [1,1.4]
    y_level_two_inf3 = [0.39,0.39]
    plt.plot(x_level_two_inf3, y_level_two_inf3, color='orange', linewidth=1.5)

    #Level 3 inf.
    x_level_three_inf = [1,1.4]
    y_level_three_inf = [0.33,0.39]
    plt.plot(x_level_three_inf, y_level_three_inf, color='red', linewidth=1.5)
    #  Plot text : "Level1" on garpah
    l3_inf= np.array((1.04, 0.27)) #Location
    angle = 18 # Rotate angle
    plt.gca().transData.transform_angles(np.array((45,)), l3_inf.reshape((1, 2)))[0] # Position+ Rotation
    plt.text(l3_inf[0], l3_inf[1], 'Level 3', fontsize=6, rotation=angle, rotation_mode='anchor') # Plot text

    if show_plots:
        plt.show()

    #log.info('Graph "{}" has been created'.format(plot_title))


# def plot_results_longi(analysis, longi_data, list1_unic, list2_unic, list3_unic, leg_var, title_var1, title_var2, show_plots, save_plots):
#     for x in list1_unic :
#         plot_damp_longi = []
#         plot_freq_longi = []
#         legend_longi = []
#         for y in list2_unic :
#             for z in list3_unic :
#                 for data in longi_data :
#                     if data[0] == x and data[1] == z and data[2] == y :
#                         # Get the data to plot in the element of longi_data at (x, z, y)
#                         trim_aoa= data[3]
#                         short_damp = data[4]
#                         short_freq = data[5]
#                         phugoid_damp = data[6]
#                         phugoid_freq = data[7]
#                         # Prepare for plotting
#                         plot_damp_longi.append([short_damp, phug_damp])
#                         plot_freq_longi.append([short_freq, phug_freq])
#                         legend_longi.append(leg_var + ' = ' + str(z) + r', $\alpha_{trim}$ = ' + str(trim_aoa) + '°')
#         title_longi = title_var1 + ' = ' + str(x) + ' , ' + title_var2 + str(y) + ' °, and different ' + leg_var
#         plot_multicurve(analysis, plot_damp_longi, plot_freq_longi,  legend_longi, title_longi, 'Re', 'Im', show_plots, save_plots)
#
#
# def plot_results_dir(analysis, lat_dir_data, list1_unic, list2_unic, list3_unic, leg_var, title_var1, title_var2, show_plots, save_plots):
#     for x in list1_unic :
#         plot_damp_dir = []
#         plot_freq_dir = []
#         legend_dir = []
#         for y in list2_unic :
#             for z in list3_unic :
#                 for data in longi_data :
#                     if data[0] == x and data[1] == z and data[2] == y :
#                         # Get the data to plot in the element of lat_dir_data at (alt, mach, aos)
#                         trim_aos = data[3]
#                         roll_damp = data[4]
#                         roll_freq = data[5]
#                         spiral_damp = data[6]
#                         spiral_freq = data[7]
#                         dutchl_damp = data[8]
#                         dutch_freq = data[9]
#                         # Prepare for plotting
#                         plot_damp_dir.append([roll_damp, spiral_damp, dutch_damp])
#                         plot_freq_dir.append([roll_freq, spiral_freq, dutch_freq])
#                         legend_longi.append(leg_var + ' = ' + str(z) + r', $\beta_{trim}$ = ' + str(trim_aos) + '°')
#         title_longi = title_var1 + ' = ' + str(x) + ' , ' + title_var2 + str(y) + ' °, and different ' + leg_var
#         plot_multicurve(analysis, plot_damp_longi, plot_freq_longi,  legend_longi, title_longi, 'Re', 'Im', show_plots, save_plots)
