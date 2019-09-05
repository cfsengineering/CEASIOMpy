"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Range main module for preliminary design on conventional aircraft, it evaluates:

* the range with max passengers;
* the range with max fuel and some passengers;
* the range with max fuel and no passengers;
* the fuel consumption fir each flight phase.

.. warning::

    The code deletes the ToolOutput folder and recreates
    it at the start of each run.
    The code also removes the ToolInput file from the
    ToolInput folder after copying it into the ToolOutput
    folder as ToolOutput.xml

Python version: >=3.6

| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2019-09-04 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================

import os
import shutil
import time

from ceasiompy.utils.InputClasses import rangeclass

from ceasiompy.Range.func.Crew.crewmembers import crew_check
from ceasiompy.Range.func.Fuel.fuelconsumption import fuel_consumption
from ceasiompy.Range.func.RangeEstimation.breguetrange import breguet_cruise_range
from ceasiompy.Range.func.AoutFunc import outputrangegen
from ceasiompy.Range.func.AoutFunc import cpacsrangeupdate
from ceasiompy.Range.func.AinFunc import getdatafromcpacs

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import aircraft_name

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes folder in the
   range_output_class script and into the Input_classes/Conventional
   folder inside the range_user_input.py script."""


#=============================================================================
#   FUNCTIONS
#=============================================================================

"""
    Each function is defined in a separate script inside the func folder.
"""


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.info('###########################################################')
    log.info('############ AIRCRAFT RANGE ESTIMATION MODULE #############')
    log.info('###########################################################')


##=============================== PREPROCESSING ============================##

    start = time.time()
    PATH1 = 'ToolInput/user_toolinput.xml'
    PATH2 = 'ToolInput/ToolInput.xml'

    if os.path.exists('ToolOutput'):
        shutil.rmtree('ToolOutput')
        os.makedirs('ToolOutput')
    else:
        os.makedirs('ToolOutput')

    if os.path.exists(PATH1):
        out_xml = 'ToolOutput/user_tooloutput.xml'
        shutil.copyfile(PATH1, './' + out_xml)
        #os.remove(PATH1)
    elif os.path.exists(PATH2):
        out_xml = 'ToolOutput/ToolOutput.xml'
        shutil.copyfile(PATH2, './' + out_xml)
        #os.remove(PATH2)
    else:
        raise Exception ('Error no ToolInput.xml  or user_toolinput file'\
                         + ' in the ToolInput folder ')

    name = aircraft_name(out_xml)

    newpath = 'ToolOutput/' + name
    if not os.path.exists(newpath):
        os.makedirs(newpath)


 ##========================= RANGE ANALYSIS IMPUTS =========================##

    ri = rangeclass.RangeInputs()
    out = rangeclass.RangeOutput()
    mw = rangeclass.MassesWeights()

    (mw, ri) = getdatafromcpacs.get_data(mw, ri, out_xml)

    if ri.TURBOPROP:
       LDcru = ri.LD
       LDloi = ri.LD * 0.866
    else:
       LDcru = ri.LD * 0.866
       LDloi = ri.LD

    if ri.WINGLET >= 0:
        ri.TSFC_CRUISE = ri.TSFC_CRUISE - 0.05*ri.WINGLET
    elif ri.WINGLET > 2:
        log.warning('Warning, winglet type index is 1 (medium efficiency),'\
                    + ' 2 (high efficiency). Set no winglet (0)')


##============================= RANGE ANALYSIS =============================##

    log.info('-------- Starting the range analysis --------')
    log.info('---------- Aircraft: ' + name + ' -----------')

### RANGE AND FUEL CONSUMPTION -----------------------------------------------
    mw = fuel_consumption(LDloi, mw, ri, ri.RES_FUEL_PERC/100.0)

    (out.ranges, out.ranges_cru, mw.m_pass_middle)\
        = breguet_cruise_range(LDcru, ri, mw, ri.RES_FUEL_PERC/100.0)

    if mw.m_pass_middle:
        out.payloads=[round(mw.mass_payload,0), round(mw.mass_payload,0),\
                      round(mw.m_pass_middle,0), 0]
    else:
        out.payloads=[round(mw.mass_payload,0), round(mw.mass_payload,0),\
                      round(mw.mass_payload,0), 0]

### CREW MEMBERS CHECK -------------------------------------------------------
    if ri.cabin_crew_nb:
        (out.pilot_nb, out.cabin_crew_nb, out.crew_nb,\
         out.mass_crew, out.flight_time)= crew_check(out.ranges[1], ri)


#=============================================================================
#    OUTPUT WRITING
#=============================================================================

    log.info('-------- Generating output text file --------')
    outputrangegen.output_txt(LDloi, LDcru, mw, ri, out, name)


#=============================================================================
#    CPACS WRITING
#=============================================================================

    cpacsrangeupdate.cpacs_update(ri.MASS_PASS, out, mw, out_xml)

    if os.path.exists('ToolInput/conv.temp'):
        B = 'BalanceConventional/ToolInput'
    elif os.path.exists('ToolInput/unconv.temp'):
        B = 'BalanceUnconventional/ToolInput'
    elif os.path.exists('ToolInput/nocpacs.temp'):
        log.warning('No Balance analysis without cpacs geometry file')
        B = False
    else:
        raise Exception('Error no conv.temp, unconv.temp '\
                        + 'or nocpacs.temp inside ToolInput folder')

    if os.path.exists('ToolOutput/ToolOutput.xml') and B:
        if os.path.exists('../' + B):
            shutil.rmtree('../' + B)
            os.makedirs('../' + B)
        PATH_BALANCE_OUT = '../' + B + '/ToolInput.xml'
        shutil.copyfile('ToolOutput/ToolOutput.xml', PATH_BALANCE_OUT)


#=============================================================================
#   PLOTS
#=============================================================================
### Payload vs Range ---------------------------------------------------------
    log.info('---- Generating payload versus range plot ---')
    outputrangegen.payload_range_plot(out.ranges, out.ranges_cru,\
                                      out.payloads, mw, name)

### Show plots
    #plt.show()


#=============================================================================
#    LOG WRITING
#=============================================================================

    log.info('------ Mass evaluation completed ------')
    log.info('-------------- Masses -----------------')
    log.info('Payload mass [kg]: ' + str(int(round(mw.mass_payload))))
    log.info('Total fuel mass [kg]: '\
             + str(int(round(mw.mass_fuel_max))))
    log.info('Mass of fuel with maximum passengers [kg]:'\
             + str(int(round(mw.mass_fuel_maxpass))))
    log.info('---------------------------------------')
    log.info('Maximum Take Off Mass [kg]: '\
             + str(int(round(mw.maximum_take_off_mass))))
    if ri.cabin_crew_nb:
        log.info('------- Suggested crew members --------')
        log.info('Pilots: ' + str(out.pilot_nb))
        log.info('Cabin crew members: ' + str(out.cabin_crew_nb))
        log.info('Flight time [min]: ' + str(int(round(out.flight_time*60))))
    log.info('--------------- Ranges ----------------')
    log.info('Range with maximum payload [km]: '\
             + str(int(round(out.ranges[1]))))
    log.info('Range with maximum fuel and some payload [km]: '\
             + str(int(round(out.ranges[2]))))
    log.info('Maximum range [km]: ' + str(int(round(out.ranges[-1]))))
    log.info('------------- Cruise Ranges --------------')
    log.info('Cruise range with maximum payload [km]: '\
             + str(int(round(out.ranges_cru[1]))))
    log.info('Cruise range with maximum fuel and some payload [km]: '\
             + str(int(round(out.ranges_cru[2]))))
    log.info('Maximum cruise range [km]: '\
             + str(int(round(out.ranges_cru[-1]))))
    log.info('--- Fuel Consumption  (max passengers) ---')
    log.info('Fuel for take off [kg]: ' + str(int(round(mw.mf_for_to))))
    log.info('Fuel for climb [kg]: ' + str(int(round(mw.mf_for_climb))))
    log.info('Fuel for cruise [kg]: ' + str(int(round(mw.mf_for_cruise))))
    log.info('Fuel for a 30 min loiter [kg]: '\
             + str(int(round(mw.mf_for_loiter))))
    log.info('Fuel for landing [kg]: '\
             + str(int(round(mw.mf_for_landing))))
    log.info('Total fuel remaining after landing [kg]: '\
             + str(int(round(mw.mf_after_land))))
    log.info('------ Weigth loss (max passengers) ------')
    log.info('Weight after take off [N]: ' + str(int(round(mw.w_after_to))))
    log.info('Weight after climb [N]: ' + str(int(round(mw.w_after_climb))))
    log.info('Weight after cruise [N]: ' + str(int(round(mw.w_after_cruise))))
    log.info('Weight after a 30 min loiter [N]: '\
             + str(int(round(mw.w_after_loiter))))
    log.info('Weight after landing [N]: ' + str(int(round(mw.w_after_land))))
    end = time.time()
    log.info('---------------------------------------')
    log.info('Elapsed time [s]: ' + str(round((end-start),3)))
    log.info('---------------------------------------')

    log.info('##########################################################')
    log.info('############### Range estimation completed ###############')
    log.info('##########################################################')
