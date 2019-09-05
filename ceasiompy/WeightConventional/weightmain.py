"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Weight main module for preliminary design of conventional aircraft, it evaluates:

 * the maximum take-off mass;
 * the operating empty mass;
 * the zero fuel mass;
 * the maximum amount of fuel;
 * the maximum number of passengers;
 * the maximum amount of fuel with max passengers;
 * the number of crew members needed;
 * the number of lavatories;
 * the seating disposition.

Starting point:

A)

* Main geometrical data:
* wing_area;
* wing_span;
* fuse_length;
* fuse_width.

B)

* ToolInput.xml file in the ToolInput folder.

Output:

* The code saves a user_tooloutput.xml file if case A,
  and  tooloutput.xml file if case B in the ToolOutput folder.
* The code saves a copy of the tooloutput.xml file inside the
  ToolInput folder of the range and balance analysis.
* The system creates a folder with the aircraft name, and it saves inside
  three txt file and one figure:
* NAME_Aircraft_Geometry.out: that contains all the information
  regarding the aircraft geometry (only with case B)
* NAME_Seats_disposition.out: with an example of the seat disposition.
* NAME_Weight_module.out: with all information evaluated with this code.
* NAME_mtomPrediction.png: contains the result of the linear regression
  carried on for the maximum take-off mass evaluation.

.. warning::

    The code deletes the ToolOutput folder and recreates it at the start of each run.

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
import numpy as np
import time

from ceasiompy.utils.InputClasses.Conventional import weightconvclass

from ceasiompy.WeightConventional.func.Passengers.passengers import estimate_passengers
from ceasiompy.WeightConventional.func.Passengers.seatsconfig import seat_config
from ceasiompy.WeightConventional.func.Crew.crewmembers import estimate_crew
from ceasiompy.WeightConventional.func.Masses.oem import operating_empty_mass_estimation
from ceasiompy.WeightConventional.func.Masses import mtomestimation
from ceasiompy.WeightConventional.func.AoutFunc import outputweightgen
from ceasiompy.WeightConventional.func.AoutFunc import cpacsweightupdate
from ceasiompy.WeightConventional.func.AoutFunc import createtmpcpacs
from ceasiompy.WeightConventional.func.AinFunc import getinput

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import aircraft_name
from ceasiompy.utils.WB.ConvGeometry import geometry

log = get_logger(__file__.split('.')[0])

#=============================================================================
#   CLASSES
#=============================================================================

"""
    All classes are defined in the Classes and in the Input_classes folders.
"""


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
    log.info('############ AIRCRAFT WEIGHT ESTIMATION MODULE ############')
    log.info('###########################################################')

##=============================== PREPROCESSING ============================##

    start = time.time()
    # Removing and recreating the ToolOutput folder.
    if os.path.exists('ToolOutput'):
        shutil.rmtree('ToolOutput')
        os.makedirs('ToolOutput')
    else:
        os.makedirs('ToolOutput')

    # Class Definition from the ceasiompy.Input_classes/Conventional folder
    ui = weightconvclass.UserInputs()

    # Class Definition from the classes folder
    mw = weightconvclass.MassesWeights()
    out = weightconvclass.WeightOutput()

    # Set True for option B or False for option A
    cpacs = True

    if not cpacs:
    ### Option 1: GEOMETRY FROM INPUT
        name = str(input('Name of the aircraft: '))
        wing_area = float(input('Wing plantform area [m^2]: '))
        wing_span = float(input('Wing span [m]: '))
        fuse_length = float(input('Fuselage length [m]: '))
        fuse_width = float(input('Fuselage width [m]: '))
        wing_area_tot = wing_area
        start = time.time()
        ind = weightconvclass.InsideDimensions(fuse_length,\
                                                 fuse_width, cpacs)
        cpacs_out = 'ToolOutput/user_tooloutput.xml'
        out_xml = createtmpcpacs.create_xml(cpacs_out, name)
        newpath = 'ToolOutput/' + name
        if not os.path.exists(newpath):
            os.makedirs(newpath)
    else:
    ### Option 2: GEOMETRY FROM CPACS
        cpacs_in = 'ToolInput/ToolInput.xml'

        if not os.path.exists(cpacs_in):
            raise Exception ('Error, no ToolInput.xml'\
                             + ' file in the ToolInput folder.')

        name = aircraft_name(cpacs_in)

        out_xml = 'ToolOutput/ToolOutput.xml'
        shutil.copyfile(cpacs_in, './' + out_xml)
        newpath = 'ToolOutput/' + name
        if not os.path.exists(newpath):
            os.makedirs(newpath)
        ag = geometry.geometry_eval(cpacs_in, name)
        fuse_length = round(ag.fuse_length[0],3)
        fuse_width = round(np.amax(ag.fuse_sec_width[:,0]),3)
        ind = weightconvclass.InsideDimensions(fuse_length, fuse_width, cpacs)
        # Nose length [m].
        ind.nose_length = round(ag.fuse_nose_length[0],3)
        # Tail length [m].
        ind.tail_length = round(ag.fuse_tail_length[0],3)
        # Cabin length [m].
        ind.cabin_length = round(ag.fuse_cabin_length[0],3)
        # Main wing span and plantform area [m].
        wing_area = round(ag.wing_plt_area_main,3)
        wing_span = round(ag.wing_span[ag.main_wing_index-1],3)
        wing_area_tot = np.sum(ag.wing_plt_area)

##======================= DEFAULT OR ADVANCE USER INPUT ====================##

    if cpacs:
        (ind, ui) = getinput.get_user_inputs(ind, ui, ag, out_xml, cpacs)
        if ui.MAX_FUEL_VOL>0 and ui.MAX_FUEL_VOL<ag.wing_fuel_vol:
            max_fuel_vol = ui.MAX_FUEL_VOL
        else:
            max_fuel_vol = ag.wing_fuel_vol
    else:
        (ind, ui) = getinput.get_user_inputs(ind, ui, 'nogeometry',\
                                              out_xml, cpacs)

    out.PILOT_NB = ui.PILOT_NB # Number of pilot [-].

    # Massimum payload allowed, set 0 if equal to max passenger mass.
    mw.MAX_PAYLOAD = ui.MAX_PAYLOAD

    # Adding extra length in case of aircraft with second floor [m].
    if ui.IS_DOUBLE_FLOOR == 1:
        cabin_length2 = ind.cabin_length*1.91
    elif ui.IS_DOUBLE_FLOOR == 2:
        cabin_length2 = ind.cabin_length*1.20
    elif ui.IS_DOUBLE_FLOOR == 0:
        cabin_length2 = ind.cabin_length
    else:
        log.warning('Warning, double floor index can be 0 (1 floor),\
                    2 (B747-2nd floor type) or 3 (A380-2nd floor type).\
                    Set Default value (0)')
        fuse_length2 = ind.fuse_length


##============================= WEIGHT ANALYSIS ============================##

    log.info('------- Starting the weight analysis --------')
    log.info('---------- Aircraft: ' + name + ' -----------')

### MAXIMUM TAKE OFF MASS EVALUATION -----------------------------------------
    mw.maximum_take_off_mass = mtomestimation.estimate_mtom(\
                             fuse_length, fuse_width,\
                             wing_area, wing_span, name)
    if mw.maximum_take_off_mass <= 0:
        raise Exception('Wrong mass estimation, unconventional aircraft '\
                        + 'studied using the conventional aircraft database.')

### WING LOADING -------------------------------------------------------------
    out.wing_loading = mw.maximum_take_off_mass/wing_area_tot

### OPERATIVE EMPTY MASS EVALUATION ------------------------------------------
    mw.operating_empty_mass = operating_empty_mass_estimation(\
                            mw.maximum_take_off_mass, fuse_length,
                            fuse_width, wing_area, wing_span,\
                            ui.TURBOPROP)

### PASSENGERS AND CREW MASS EVALUATION --------------------------------------
    if ((fuse_width / (1+(ind.fuse_thick/100)))\
            > (ind.seat_width + ind.aisle_width)):
        (out.pass_nb, out.row_nb, out.abreast_nb, out.aisle_nb,\
         out.toilet_nb, ind) = estimate_passengers(ui.PASS_PER_TOILET,\
                                                cabin_length2, fuse_width,\
                                                ind)
        seat_config(out.pass_nb, out.row_nb, out.abreast_nb,\
                    out.aisle_nb, ui.IS_DOUBLE_FLOOR, out.toilet_nb,\
                    ui.PASS_PER_TOILET, fuse_length, ind, name)
    else:
        out.pass_nb = 0
        raise Exception('The aircraft can not transport passengers, increase'\
                        + ' fuselage width.' + '\nCabin Width [m] = '\
                        + str((fuse_width/(1 + ind.fuse_thick)))\
                        + ' is less than seat width [m]'\
                        + ' + aisle width [m] = '\
                        + str(ind.seat_width + ind.aisle_width))

    (out.crew_nb, out.cabin_crew_nb, mw.mass_crew)\
        = estimate_crew(out.pass_nb, ui.MASS_PILOT, ui.MASS_CABIN_CREW,\
                        mw.maximum_take_off_mass, out.PILOT_NB)

    mw.mass_payload = out.pass_nb * ui.MASS_PASS + ui.MASS_CARGO

    mw.mass_people = mw.mass_crew + out.pass_nb * ui.MASS_PASS

    maxp = False
    if (mw.MAX_PAYLOAD > 0 and mw.mass_payload > mw.MAX_PAYLOAD):
      mw.mass_payload = mw.MAX_PAYLOAD
      maxp = True
      log.info('With the fixed payload, passenger nb reduced to: '\
               + str(round(mw.MAX_PAYLOAD / (ui.MASS_PASS),0)))

### FUEL MASS EVALUATION -----------------------------------------------------
    # Maximum fuel that can be storaged with maximum nuber of passengers.

    if (not cpacs and not ui.MAX_FUEL_VOL): # TODO while retesting, redo fitting
        if ui.TURBOPROP:
            if wing_area > 55.00:
                mw.mass_fuel_max = round(mw.maximum_take_off_mass/4.6,3)
            else:
                mw.mass_fuel_max = round(mw.maximum_take_off_mass/3.6,3)
        elif wing_area < 90.00:
            if fuse_length < 60.00:
                mw.mass_fuel_max = round(mw.maximum_take_off_mass/4.3,3)
            else:
                mw.mass_fuel_max = round(mw.maximum_take_off_mass/4.0,3)
        elif wing_area < 300.00:
            if fuse_length < 35.00:
                mw.mass_fuel_max = round(mw.maximum_take_off_mass/3.6,3)
            else:
                mw.mass_fuel_max = round(mw.maximum_take_off_mass/3.8,3)
        elif wing_area < 400.00:
            mw.mass_fuel_max = round(mw.maximum_take_off_mass/2.2,3)
        elif wing_area < 600.00:
            mw.mass_fuel_max = round(mw.maximum_take_off_mass/2.35,3)
        else:
            mw.mass_fuel_max = round(mw.maximum_take_off_mass/2.8,3)
    else:
        mw.mass_fuel_max = round(max_fuel_vol*ui.FUEL_DENSITY,3)

    mw.mass_fuel_maxpass = round(mw.maximum_take_off_mass\
                           - mw.operating_empty_mass - mw.mass_payload,3)

    if (mw.MAX_FUEL_MASS > 0 and mw.mass_fuel_maxpass > mw.MAX_FUEL_MASS):
        mw.mass_fuel_maxpass = mw.MAX_FUEL_MASS
        log.info('Maximum fuel ammount allowed reached [kg]: '\
                 + str(mw.mass_fuel_maxpass))
        if (mw.maximum_take_off_mass > (mw.mass_fuel_maxpass\
                + mw.operating_empty_mass + mw.mass_payload)):
            mw.mass_cargo = mw.maximum_take_off_mass - (mw.mass_fuel_maxpass\
                          + mw.operating_empty_mass + mw.mass_payload)
            if not maxp:
                log.info('Adding extra payload mass [kg]: '\
                         + str(mw.mass_cargo))
                mw.mass_payload = mw.mass_payload + mw.mass_cargo
            else:
                maximum_take_off_mass = maximum_take_off_mass - mw.mass_cargo
                log.info('With all the constrains on the fuel and payload, '\
                         + 'the maximum take off mass is not reached.'\
                         + '\n Maximum take off mass [kg]: '\
                         + str(maximum_take_off_mass))
    else:
        log.info('Fuel mass with maximum passengers [kg]: '\
                 + str(mw.mass_fuel_maxpass))

    if (mw.MAX_FUEL_MASS > 0 and mw.mass_fuel_max > mw.MAX_FUEL_MASS):
        mw.mass_fuel_max = mw.MAX_FUEL_MASS

### ZERO FUEL MASS EVALUATION ------------------------------------------------
    mw.zero_fuel_mass = mw.maximum_take_off_mass - mw.mass_fuel_maxpass\
                        + (ui.RES_FUEL_PERC/100)*mw.mass_fuel_max

#=============================================================================
#    OUTPUT WRITING
#=============================================================================

    log.info('-------- Generating output text file --------')

    outputweightgen.output_txt(ui.IS_DOUBLE_FLOOR, out, mw, ind, ui, name)


#=============================================================================
#    CPACS WRITING
#=============================================================================

    cpacsweightupdate.cpacs_weight_update(out, mw, out_xml)
    cpacsweightupdate.toolspecific_update(mw, out, out_xml)

# Copying tooloutput.xml as toolinput.xml in the ToolInput folder in
# Range and BalanceConventional modules.
    # if not cpacs:
    #     PATH_IN = '/user_tooloutput.xml'
    #     PATH_OUT = '/user_toolinput.xml'
    #     TEMP = '/nocpacs.temp'
    #     TEXT = 'Conventional Aircraft from user_toolinput'
    # else:
    #     PATH_IN = '/ToolOutput.xml'
    #     PATH_OUT = '/ToolInput.xml'
    #     TEMP = '/conv.temp'
    #     TEXT = 'Conventional Aircraft'
    #
    # PATH = 'ToolOutput' + PATH_IN
    # PATH_RANGE_OUT = '../Range/ToolInput' + PATH_OUT
    # PATH_BALANCE_OUT = '../BalanceConventional/ToolInput' + PATH_OUT
    #
    # if os.path.exists('../Range/ToolInput'):
    #     shutil.rmtree('../Range/ToolInput')
    #     os.makedirs('../Range/ToolInput')
    # shutil.copyfile(PATH, PATH_RANGE_OUT)
    # OutputTextFile = open('../Range/ToolInput' + TEMP, 'w')
    # OutputTextFile.write(TEXT)
    # OutputTextFile.close()
    #
    # if os.path.exists('../BalanceConventional/ToolInput'):
    #     shutil.rmtree('../BalanceConventional/ToolInput')
    #     os.makedirs('../BalanceConventional/ToolInput')
    # shutil.copyfile(PATH, PATH_BALANCE_OUT)


#=============================================================================
#    LOG WRITING
#=============================================================================

    if cpacs:
        log.info('---- Geometry evaluation from CPACS file ----')
        log.info('Fuselage length [m]: ' + str(round(fuse_length,3)))
        log.info('Fuselage width [m]: ' + str(round(fuse_width,3)))
        log.info('Fuselage mean width [m]: '\
                 + str(round(ag.fuse_mean_width,3)) )
        log.info('Wing Span [m]: ' + str(round(wing_span,3)))

    log.info('--------- Masses evaluated: -----------')
    log.info('Maximum Take Off Mass [kg]: '\
             + str(int(round(mw.maximum_take_off_mass))))
    log.info('Operating Empty Mass [kg]: '\
             + str(int(round(mw.operating_empty_mass))))
    log.info('Zero Fuel Mass [kg]: '\
             + str(int(round(mw.zero_fuel_mass))))
    log.info('Wing loading [kg/m^2]: '\
             + str(int(round(out.wing_loading))))
    log.info('Maximum ammount of fuel allowed with no passengers [kg]: '\
             + str(int(round(mw.mass_fuel_max))))
    log.info('Maximum ammount of fuel allowed with no passengers [l]: '\
             + str(int(round(mw.mass_fuel_max/ui.FUEL_DENSITY*1000))))
    log.info('--------- Passegers evaluated: ---------')
    log.info('Passengers: ' + str(out.pass_nb))
    log.info('Lavatory: ' + str(out.toilet_nb))
    log.info('Payload mass [kg]: ' + str(mw.mass_payload))
    log.info('------- Crew members evaluated: --------')
    log.info('Pilots: ' + str(out.PILOT_NB))
    log.info('Cabin crew members: ' + str(out.cabin_crew_nb))

    end = time.time()
    log.info('---------------------------------------')
    log.info('Elapsed time [s]: ' + str(round((end-start),3)))
    log.info('---------------------------------------')

    log.info('###########################################################')
    log.info('############### Weight estimation completed ###############')
    log.info('###########################################################')
