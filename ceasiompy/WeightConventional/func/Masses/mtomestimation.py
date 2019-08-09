"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This script estimates the maximum take of mass from a database
of conventional aircraft using the linear regression method.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2019-02-20
"""


#==============================================================================
#   IMPORT
#==============================================================================

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#==============================================================================
#   CLASSES
#==============================================================================


"""
 InsideDimensions class, can be found on the InputClasses folder inside the
 weightconvclass.py script.
"""


#==============================================================================
#   FUNCTIONS
#==============================================================================
def estimate_limits(input_data, OBJ, fuse_length, wing_area):
    """
    The funtion adjusts the upper and lower limits used for the linear
    regression method.


    INPUT
    (float_array) input_data --Arg.: Array containing all the geometrical
                                     data of the aircraft in the database
                                     (fuse_length, fuse_width,
                                     wing_area, wing_span).
    (float_Array) OBJ        --Arg.: Array containing the geometrical
                                     data of the aircraft studied
                                     (fuse_length, fuse_width,
                                     wing_area, wing_span).
    (float)     fuse_length  --Arg.: Fuselage length [m].
    (float)     wing_area    --Arg.: Main wing area [m^2].

    OUTPUT
    (float) upper_limit_out   --Out.: Upper limit for the central section
                                      of the linear regression method.
    (float) lower_limit_out   --Out.: Lower limit for the central section
                                      of the linear regression method.
    """

    (L,) = np.shape(input_data)
    l = L - 1
    upper_limit = np.zeros(l,)
    lower_limit = np.zeros(l,)
    cnt_l = 0
    cnt_u = 0

    for i in range(0, l):
        if (input_data[i,] - OBJ) >= 0:
           delta_plus = round(input_data[i,] - OBJ,2)
           upper_limit[cnt_u] = delta_plus
           cnt_u += 1
        else:
           delta_minus = round(input_data[i,]-OBJ,2)
           lower_limit[cnt_l] = delta_minus
           cnt_l += 1

    lower_limit = sorted(lower_limit)
    upper_limit = sorted(upper_limit, reverse=True)
    if fuse_length < 25.00 and wing_area < 55.00:
        U = 1        # If cnt_u+1, the upper limit is taken
                     # as the smallest value in database
        L = cnt_l+1  # If cnt_l+1, the lower limit is taken
                     # as the smallest value in database
    elif fuse_length < 40.00 and wing_area < 100.00:
        U =4        # If cnt_u+1, the upper limit is taken
                     # as the smallest value in database
        L = cnt_l+1  # If cnt_l+1, the lower limit is taken
                     # as the smallest value in database
    elif fuse_length < 60.00 and wing_area > 200.00 and wing_area < 400.00:
        U = 3
        L = 6
    elif fuse_length >= 60.00 and wing_area > 200.00 and wing_area < 400.00:
        U = 4
        L = 5
    else:
        U = 4
        L = 4
    if (cnt_u - U) >= 0:
       upper_limit_out = upper_limit[cnt_u - U] + 0.01
    else:
        upper_limit_out = upper_limit[0] + 0.01
    if (cnt_l - L) >= 0:
        lower_limit_out = lower_limit[cnt_l - L] - 0.01
    else:
        lower_limit_out = lower_limit[0] - 0.01

    return (upper_limit_out, lower_limit_out)


#==============================================================================

def estimate_mtom(fuse_length, fuse_width, wing_area, wing_span, NAME):
    """ Function that estimates the Maximum Take-Off Mass
        from statistical regression based on geometric parameters.

    INPUT
    (float)     fuse_length --Arg.: Fuselage length [m].
    (float)     fuse_width  --Arg.: Fuselage width [m].
    (float)     wing_area   --Arg.: Main wing area [m^2].
    (float)     wing_span   --Arg.: Main wing span [m].
    (char)      NAME        --Arg.: Name of the aircraft studied.

    OUTPUT
    (float)     mtom     --Out.: Maximum Take-Off Mass [kg].

    """

    log.info('-------------- mtom regression --------------')

    aircraft_data_file_name = 'ToolInput/AircraftData2018_v1_ste.csv'
    log.info('Open ' + str(aircraft_data_file_name))
    aircraft_data = pd.read_csv(aircraft_data_file_name)
    aircraft_data_1 = aircraft_data.set_index('Manufacturer')
    aircraft_data_2 = aircraft_data_1.transpose()
    aircraft_data_3 = aircraft_data_2.reset_index()
    aircraft_data_3.set_index(['index','Type','Model'])
    input_data = aircraft_data_3.iloc[:,[12,13,15,16]].values.astype(float)

    output_data = aircraft_data_3['MTOM'].values.astype(float)
    # Input: 12=Fuselage Length, 13=Fuselage Width, 15=Wing area, 16=Wing span
    # Ouput: mtom --> Maximu Take Off Mass

    input_new_aircraft = np.array([[fuse_length, fuse_width,\
                                    wing_area, wing_span]])

    # Choose 0 for fuselarge_length, 1 for fuselarge_width,
    # 2 for wing_area (best), 3 for wing_span

    if fuse_length < 40.00:
        ID = 3
    else:
        ID = 2

    u_limit,l_limit = estimate_limits(input_data[:,ID],\
        input_new_aircraft[0,ID], fuse_length, wing_area)

    upper_limit = input_new_aircraft[0,ID] + u_limit
    lower_limit = input_new_aircraft[0,ID] + l_limit

    mask_under = input_data[:,ID] < lower_limit
    mask_middle = np.logical_and(input_data[:,ID] < upper_limit,\
                                 input_data[:,ID] > lower_limit)
    mask_over = input_data[:,ID] > upper_limit

    if np.all(mask_under == False ):
        upper_limit *= 2
        lower_limit = 0
        mask_under = input_data[:,ID] < lower_limit
        mask_middle = np.logical_and(input_data[:,ID] < upper_limit,\
                                     input_data[:,ID] > lower_limit)
        mask_over = input_data[:,ID] > upper_limit

    if np.all(mask_over == False ):
        lower_limit /= 2
        upper_limit = 9999
        mask_under = input_data[:,ID] < lower_limit
        mask_middle = np.logical_and(input_data[:,ID] < upper_limit,\
                                     input_data[:,ID] > lower_limit)
        mask_over = input_data[:,ID] > upper_limit

    log.info('------- Calculating linear regression: ------')
    c=0
    # UNDER ------------------------------------------------------------------
    if not np.all(mask_under == False):
       c += 1
       input_data_under = input_data[mask_under]
       output_data_under = output_data[mask_under]
       regr_under = LinearRegression()
       regr_under.fit(input_data_under, output_data_under)
       output_predicted_under = regr_under.predict(input_data_under)

    # MIDDLE -----------------------------------------------------------------
    if not np.all(mask_middle == False):
        c += 1
        input_data_middle = input_data[mask_middle]
        output_data_middle = output_data[mask_middle]
        regr_middle = LinearRegression()
        regr_middle.fit(input_data_middle, output_data_middle)
        output_predicted_middle = regr_middle.predict(input_data_middle)

    # OVER -------------------------------------------------------------------
    if not np.all(mask_over == False):
        c += 1
        input_data_over = input_data[mask_over]
        output_data_over = output_data[mask_over]
        regr_over = LinearRegression()
        regr_over.fit(input_data_over, output_data_over)
        output_predicted_over = regr_over.predict(input_data_over)

    if input_new_aircraft[0,ID] > upper_limit:
        output_new_aircraft = regr_under.predict(input_new_aircraft)
    elif input_new_aircraft[0,ID] < lower_limit:
        output_new_aircraft = regr_over.predict(input_new_aircraft)
    else:
        output_new_aircraft = regr_middle.predict(input_new_aircraft)

    fig, ((ax1,ax2),(ax3,ax4)) = plt.subplots(2, 2, sharey=True, figsize=(12,12))
    if not np.all(mask_under == False):
        ax1.plot(input_data_under[:,2], output_data_under,'xb', label='Data')
        ax1.plot(input_data_under[:,2], output_predicted_under,'oc',\
                 label='Predictions under limits')
    if not np.all(mask_over == False):
        ax1.plot(input_data_over[:,2], output_data_over, 'xb')
        ax1.plot(input_data_over[:,2], output_predicted_over, 'og',\
                 label='Predictions over limits')
    if not np.all(mask_middle == False):
        ax1.plot(input_data_middle[:,2], output_data_middle, 'xb')
        ax1.plot(input_data_middle[:,2], output_predicted_middle, 'or',\
                 label='Predictions inside limits')

    ax1.plot(input_new_aircraft[:,2], output_new_aircraft, 'oy',\
             label='New Aircraft')
    ax1.set(xlabel='Wing Area [m^2]', ylabel='MTOM [kg]')
    ax1.grid()
    mpl.rcParams.update({'font.size': 14})

    if not np.all(mask_under == False):
        ax2.plot(input_data_under[:,0], output_data_under,'xb', markersize=7)
        ax2.plot(input_data_under[:,0], output_predicted_under,'oc', markersize=7)
    if not np.all(mask_over == False):
        ax2.plot(input_data_over[:,0], output_data_over,'xb', markersize=7)
        ax2.plot(input_data_over[:,0], output_predicted_over,'og', markersize=7)
    if not np.all(mask_middle == False):
        ax2.plot(input_data_middle[:,0], output_data_middle,'xb', markersize=7)
        ax2.plot(input_data_middle[:,0], output_predicted_middle,'or', markersize=7)
    ax2.plot(input_new_aircraft[:,0], output_new_aircraft,'oy', markersize=7)
    ax2.set(xlabel='Fuselage length [m]', ylabel='MTOM [kg]')
    ax2.grid()

    if not np.all(mask_under == False):
        ax3.plot(input_data_under[:,1], output_data_under,'xb', markersize=7)
        ax3.plot(input_data_under[:,1], output_predicted_under,'oc', markersize=7)
    if not np.all(mask_over == False):
        ax3.plot(input_data_over[:,1], output_data_over,'xb', markersize=7)
        ax3.plot(input_data_over[:,1], output_predicted_over,'og', markersize=7)
    if not np.all(mask_middle == False):
        ax3.plot(input_data_middle[:,1], output_data_middle,'xb', markersize=7)
        ax3.plot(input_data_middle[:,1], output_predicted_middle,'or', markersize=7)
    ax3.plot(input_new_aircraft[:,1], output_new_aircraft,'oy', markersize=7)
    ax3.set(xlabel='Fuselage Width [m]', ylabel='MTOM [kg]')
    ax3.grid()

    if not np.all(mask_under == False):
        ax4.plot(input_data_under[:,3], output_data_under,'xb', markersize=7)
        ax4.plot(input_data_under[:,3], output_predicted_under,'oc', markersize=7)
    if not np.all(mask_over == False):
        ax4.plot(input_data_over[:,3], output_data_over,'xb', markersize=7)
        ax4.plot(input_data_over[:,3], output_predicted_over,'og', markersize=7)
    if not np.all(mask_middle == False):
        ax4.plot(input_data_middle[:,3], output_data_middle,'xb', markersize=7)
        ax4.plot(input_data_middle[:,3], output_predicted_middle,'or', markersize=7)
    ax4.plot(input_new_aircraft[:,3], output_new_aircraft,'oy', markersize=7)
    ax4.set(xlabel='Wing Span [m]', ylabel='MTOM [kg]')
    ax4.grid()

    #ax4.legend()
    if c == 3:
        ax1.legend(loc='upper center', bbox_to_anchor=(1.05, 1.22),\
	           fancybox=True, shadow=True, ncol=3, numpoints=1)
    elif c == 2:
        ax1.legend(loc='upper center', bbox_to_anchor=(1.05, 1.22),\
	           fancybox=True, shadow=True, ncol=4, numpoints=1)
    elif c == 1:
        ax1.legend(loc='upper center', bbox_to_anchor=(1.05, 1.22),\
                   fancybox=True, shadow=True, ncol=3, numpoints=1)

    namefig = NAME + '_mtomPrediction.png'
    fig.savefig('ToolOutput/' + NAME + '/' + namefig)

    # Return mtom of the aircraft given in input
    mtom = round(output_new_aircraft[0],3)

    return mtom


#=============================================================================
#   MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('###########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####')
    log.warning('###########################################################')


