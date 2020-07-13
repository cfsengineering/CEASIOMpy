"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Output text and plot generation functions.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================

import numpy as np
import matplotlib as mpl
from matplotlib import rcParams
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator


#=============================================================================
#   CLASSES
#=============================================================================


#=============================================================================
#   FUNCTIONS
#=============================================================================

def output_txt(LDloi, LDcru, mw, ri, out, NAME):
    """ The function that generats the output text file for the range analysis.

        INPUT
        (float) LDloi         --Att.: Lift over drag during loiter [-].
        (float) LDcru         --Att.: Lift over drag duing cruise [-].
        (class) mw            --Arg.: MassesWeights class.
        (class) ri            --Arg.: RangeInputs class.
        ##======= Classes are defined in the InputClasses folder =======##

        (class) out               --Arg.: RangeOutput class.
        ##========= Class is defined in the InputClasses folder ========##
        (char) NAME               --Arg.: Name of the aircraft

        OUTPUT
        (file) Range_module.out --Out.: Text file containing all the
                                              informations estimated from the
                                              code.
    """
    OUT_NAME = 'ToolOutput/' + NAME + '/' + NAME\
               + '_Range_module.out'
    OutputTextFile = open(OUT_NAME, 'w+')
    OutputTextFile.write('\n###############################################')
    OutputTextFile.write('\n####### AIRCRAFT RANGE ESTIMATION MODULE ######')
    OutputTextFile.write('\n#####               OUTPUTS               #####')
    OutputTextFile.write('\n###############################################')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nAircraft: ' + NAME)
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nAircraft Geometry Values used -----------------')
    OutputTextFile.write('\n-----------------------------------------------')
    if ri.WINGLET:
        OutputTextFile.write('\nWinglet type:' + str(ri.WINGLET))
    else:
        OutputTextFile.write('\nWinglet: no')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nEngine Inputs ---------------------------------')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nCruise Speed [m/s]: ' + str(ri.CRUISE_SPEED))
    OutputTextFile.write('\nCL/CD during cruise [-]: ' + str(LDcru))
    OutputTextFile.write('\nCL/CD during loiter[-]: ' + str(LDloi))
    OutputTextFile.write('\nCruise TSFC [1/hr]: ' + str(ri.TSFC_CRUISE))
    OutputTextFile.write('\nLoiter TSFC [1/hr]: ' + str(ri.TSFC_LOITER))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nResults ---------------------------------------')
    OutputTextFile.write('\n-----------------------------------------------')
    if ri.cabin_crew_nb:
        OutputTextFile.write('\nCrew suggested ----------------------------'\
                             + '----')
        OutputTextFile.write('\nTotal crew members: ' + str(out.crew_nb))
        OutputTextFile.write('\nNumber of cabin crew members: '
                             + str(out.cabin_crew_nb))
        OutputTextFile.write('\nNumber of pilots: ' + str(out.pilot_nb))
        OutputTextFile.write('\nTotal crew mass [kg]: '\
                             + str(int(round(out.mass_crew))))
        OutputTextFile.write('\nFlight time [min]: '\
                             + str(int(round(out.flight_time*60))))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nFuel Composition ------------------------------')
    OutputTextFile.write('\nTotal fuel with max passengers [kg]: '\
                         + str(int(round(mw.mass_fuel_maxpass))))
    OutputTextFile.write('\nFuel for take off [kg]: '\
                         + str(int(round(mw.mf_for_to))))
    OutputTextFile.write('\nFuel for climb [kg]: '\
                         + str(int(round(mw.mf_for_climb))))
    OutputTextFile.write('\nFuel for cruise [kg]: '\
                         + str(int(round(mw.mf_for_cruise))))
    OutputTextFile.write('\nFuel for a 30 min loiter [kg]: '\
                         + str(int(round(mw.mf_for_loiter))))
    OutputTextFile.write('\nFuel for landing [kg]: '\
                         + str(int(round(mw.mf_for_landing))))
    OutputTextFile.write('\nTotal fuel remaining after landing [kg]: '\
                         + str(int(round(mw.mf_after_land))))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nWeigth loss due to fuel usage (max passengers) ')
    OutputTextFile.write('\nTotal fuel storaged with max passengers [kg]: '\
                         + str(int(round(mw.mass_fuel_maxpass))))
    OutputTextFile.write('\nWeight after take off [N]: '\
                         + str(int(round(mw.w_after_to))))
    OutputTextFile.write('\nWeight after climb [N]: '\
                         + str(int(round(mw.w_after_climb))))
    OutputTextFile.write('\nWeight after cruise [N]: '\
                         + str(int(round(mw.w_after_cruise))))
    OutputTextFile.write('\nWeight after a 30 min loiter [N]: '\
                         + str(int(round(mw.w_after_loiter))))
    OutputTextFile.write('\nWeight after landing [N]: '\
                         + str(int(round(mw.w_after_land))))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nRange Analysis --------------------------------')
    OutputTextFile.write('\nTotal range -----------------------------------')
    OutputTextFile.write('\nRange with maximum payload [km]: '\
                         + str(int(round(out.ranges[1]))))
    OutputTextFile.write('\nRange with maximum fuel and some payload [km]: '\
                         + str(int(round(out.ranges[2]))))
    OutputTextFile.write('\nMaximum range [km]: '\
                         + str(int(round(out.ranges[-1]))))
    OutputTextFile.write('\nCruise range ----------------------------------')
    OutputTextFile.write('\nCruise range with maximum payload [km]: '\
                         + str(int(round(out.ranges_cru[1]))))
    OutputTextFile.write('\nCruise range with maximum fuel and some payload'\
                         + '[km]: ' + str(int(round(out.ranges_cru[2]))))
    OutputTextFile.write('\nMaximum cruise range [km]: '\
                         + str(int(round(out.ranges_cru[-1]))))
    ### Closing Text File
    OutputTextFile.close()

    return()

#=============================================================================
#   PLOTS
#=============================================================================

def payload_range_plot(ranges, ranges_cru, payloads, mw, NAME):
    """ The function that generate the plot of the payload vs range.

        INPUT
        (float_array) ranges      --Arg.: Array containing the ranges [km]
                                         evaluated in the
                                         breguet_cruise_range.py script.
        (float_array) ranges_cru  --Arg.: Array containing the cruise
                                          ranges [km] evaluated in the
                                          breguet_cruise_range.py script.
        (float_array) payloads    --Arg.: Array containing the payload [kg]
                                         corresponfing to the ranges in the
                                         ranges array.
        (class) mw                --Arg.: Mass and weight class.
        (char) NAME               --Arg.: Name of the aircraft.
        ##====== Class is defined in the InputClasses folder =======##

        OUTPUT
        (file)Payload_vs_Range.png --Out.: Png file containing all the
                                          range versus payload plot.
    """
    ### ----------------------------------------------------------------------
    fig,(ax) = plt.subplots(1, 1, sharey = True, figsize = (9,9))
    fig.patch.set_facecolor('w')
    mpl.rcParams.update({'font.size': 14})
    ax.plot(ranges[1], payloads[1],'ob', label = 'Range with max payload',\
            markersize = 10)
    ax.plot(ranges_cru[1], payloads[1],'ob', markersize = 10)
    if mw.m_pass_middle:
        ax.plot(ranges[2], payloads[2], 'sr',\
                label = 'Range with max fuel and some payload', markersize = 10)
        ax.plot(ranges_cru[2], payloads[2], 'sr', markersize = 10)
    ax.plot(ranges[3], payloads[3], '^g',\
            label = 'Range with max fuel and no payload', markersize = 10)
    ax.plot(ranges[3], payloads[3], '^g', markersize = 20)
    ax.plot(ranges_cru[3], payloads[3], '^g', markersize = 20)
    ax.plot(ranges, payloads, 'b-', label = 'Maximum range', markersize = 5)
    ax.plot(ranges_cru, payloads, 'b--', label = 'Cruise range', markersize = 5)
    ax.set(xlabel = 'Range [km]')
    ax.set(ylabel = 'Payload [kg]')
    ax.grid()

    n = -3
    ctr = False
    while not ctr:
        maxp_ax = round(np.amax(payloads)/10.0,n)
        minp_ax = maxp_ax/2.0
        maxr_ax = round(np.amax(ranges)/8.0,n)
        minr_ax = maxr_ax/2.0
        if not maxp_ax or not maxr_ax or not minp_ax or not minr_ax:
            n += 1
        else:
            ctr = True

    major_ticks_x = np.arange(0, (round(np.amax(ranges),0)\
                                  + round(np.amax(ranges),0)/4.0), maxr_ax)
    minor_ticks_x = np.arange(0, (round(np.amax(ranges),0)\
                                  + round(np.amax(ranges),0)/4.0), minr_ax)
    major_ticks_y = np.arange(0, (round(mw.mass_payload,0)\
                                  + round(mw.mass_payload,0)/4.0), maxp_ax)
    minor_ticks_y = np.arange(0, (round(mw.mass_payload,0)\
                                  + round(mw.mass_payload,0)/4.0), minp_ax)
    ax.set_axisbelow(True)
    ax.set_xticks(major_ticks_x)
    ax.set_xticks(minor_ticks_x, minor = True)
    ax.set_yticks(major_ticks_y)
    ax.set_yticks(minor_ticks_y, minor = True)
    ax.legend(loc='upper center', bbox_to_anchor = (0.5, 1.1),\
              fancybox = True, shadow = True, ncol = 1, numpoints = 1)
    ax.yaxis.set_minor_locator(MultipleLocator(minp_ax))
    ax.xaxis.set_minor_locator(MultipleLocator(minr_ax))
    ax.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
    ax.grid(which = 'both')
    FIG_NAME = 'ToolOutput/' + NAME + '/' + NAME + '_Payload_vs_Range.png'
    fig.savefig(FIG_NAME, dpi = 300)

    return()


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('##########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN rangemain.py ####')
    log.warning('##########################################################')
