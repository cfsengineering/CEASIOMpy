"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Weight conventional module for preliminary design of conventional aircraft

Python version: >=3.6

| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2020-07-09 (AJ)

TODO:
    * Simplify classes, use only one or use subclasses
    * Make tings compatible also with the others W&B Modules

"""

#=============================================================================
#   IMPORTS
#=============================================================================

import os
import shutil
import numpy as np

# Should be kept
from ceasiompy.WeightConventional.func.Passengers.passengers import estimate_passengers
from ceasiompy.WeightConventional.func.Passengers.seatsconfig import get_seat_config
from ceasiompy.WeightConventional.func.Crew.crewmembers import estimate_crew
from ceasiompy.WeightConventional.func.Masses.oem import estimate_operating_empty_mass
from ceasiompy.WeightConventional.func.Masses.mtom import estimate_limits, estimate_mtom
from ceasiompy.utils.cpacsfunctions import aircraft_name

# Should be changed or removed
from ceasiompy.utils.InputClasses.Conventional import weightconvclass
from ceasiompy.WeightConventional.func.AoutFunc import outputweightgen, cpacsweightupdate
from ceasiompy.utils.WB.ConvGeometry import geometry
import ceasiompy.utils.moduleinterfaces as mi

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

#=============================================================================
#   CLASSES
#=============================================================================

"""
    All classes are defined in the Classes and in the Input_classes folders.
"""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def get_weight_estimations(cpacs_path, cpacs_out_path):
    """Function to estimate the all weights for a conventional aircraft.

    Function 'get_weight_estimations' ...

    Source:
        * Reference paper or book, with author and date, see ...

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file

    """

    # Removing and recreating the ToolOutput folder.
    if os.path.exists('ToolOutput'):
        shutil.rmtree('ToolOutput')
    os.makedirs('ToolOutput')


    # Classes
    # TODO: Use only one class or subclasses
    ui = weightconvclass.UserInputs()
    mw = weightconvclass.MassesWeights()
    out = weightconvclass.WeightOutput()

    if not os.path.exists(cpacs_path):
        raise ValueError ('No "ToolInput.xml" file in the ToolInput folder.')

    name = aircraft_name(cpacs_path)

    shutil.copyfile(cpacs_path, cpacs_out_path) # TODO: shoud not be like that
    newpath = 'ToolOutput/' + name
    if not os.path.exists(newpath):
        os.makedirs(newpath)

    ag = geometry.geometry_eval(cpacs_path, name)
    fuse_length = round(ag.fuse_length[0],3)
    fuse_width = round(np.amax(ag.fuse_sec_width[:,0]),3)
    ind = weightconvclass.InsideDimensions(fuse_length, fuse_width)
    ind.nose_length = round(ag.fuse_nose_length[0],3)
    ind.tail_length = round(ag.fuse_tail_length[0],3)
    ind.cabin_length = round(ag.fuse_cabin_length[0],3)
    wing_area = round(ag.wing_plt_area_main,3)
    wing_span = round(ag.wing_span[ag.main_wing_index-1],3)
    wing_area_tot = np.sum(ag.wing_plt_area)

    #Has been replace by classes function
    # (ind, ui) = getinput.get_user_inputs(ind, ui, ag, cpacs_out_path)
    ui.get_user_inputs(cpacs_out_path)
    ind.get_inside_dim(cpacs_out_path)

    if ui.MAX_FUEL_VOL>0 and ui.MAX_FUEL_VOL<ag.wing_fuel_vol:
        max_fuel_vol = ui.MAX_FUEL_VOL
    else:
        max_fuel_vol = ag.wing_fuel_vol

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
        log.warning('Warning, double floor index can be only 0 (1 floor),\
                    2 (B747-2nd floor type) or 3 (A380-2nd floor type).\
                    Set Default value (0)')
        cabin_length2 = ind.cabin_length


    # Maximum Take Off Mass Evaluation
    mw.maximum_take_off_mass = estimate_mtom(fuse_length,fuse_width,wing_area,
                                             wing_span,name)

    # Wing loading
    out.wing_loading = mw.maximum_take_off_mass/wing_area_tot

    # Operating Empty Mass evaluation
    mw.operating_empty_mass = estimate_operating_empty_mass(
                                 mw.maximum_take_off_mass, fuse_length,
                                 fuse_width, wing_area, wing_span,
                                 ui.TURBOPROP)

    # Passengers and Crew mass evaluation
    if ((fuse_width / (1+(ind.fuse_thick/100))) > (ind.seat_width + ind.aisle_width)):
        (out.pass_nb, out.row_nb, out.abreast_nb, out.aisle_nb,\
         out.toilet_nb, ind) = estimate_passengers(ui.PASS_PER_TOILET,\
                                                cabin_length2, fuse_width, ind)

        get_seat_config(out.pass_nb, out.row_nb, out.abreast_nb,
                    out.aisle_nb, ui.IS_DOUBLE_FLOOR, out.toilet_nb,
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

    # Fuel Mass evaluation
    # Maximum fuel that can be stored with maximum number of passengers.

    if not ui.MAX_FUEL_VOL: # TODO while retesting, redo fitting
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

    mw.mass_fuel_maxpass = round(mw.maximum_take_off_mass  \
                                 - mw.operating_empty_mass \
                                 - mw.mass_payload, 3)

    if (mw.MAX_FUEL_MASS > 0 and mw.mass_fuel_maxpass > mw.MAX_FUEL_MASS):
        mw.mass_fuel_maxpass = mw.MAX_FUEL_MASS
        log.info('Maximum fuel ammount allowed reached [kg]: ' + str(mw.mass_fuel_maxpass))
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

    # Zero Fuel Mass evaluation
    mw.zero_fuel_mass = mw.maximum_take_off_mass - mw.mass_fuel_maxpass\
                        + (ui.RES_FUEL_PERC)*mw.mass_fuel_max

    # Log writting  (TODO: maybe create a separate function)
    log.info('---- Geometry evaluation from CPACS file ----')
    log.info('Fuselage length [m]: ' + str(round(fuse_length,3)))
    log.info('Fuselage width [m]: ' + str(round(fuse_width,3)))
    log.info('Fuselage mean width [m]: ' + str(round(ag.fuse_mean_width,3)))
    log.info('Wing Span [m]: ' + str(round(wing_span,3)))

    log.info('--------- Masses evaluated: -----------')
    log.info('Maximum Take Off Mass [kg]: ' + str(int(round(mw.maximum_take_off_mass))))
    log.info('Operating Empty Mass [kg]: ' + str(int(round(mw.operating_empty_mass))))
    log.info('Zero Fuel Mass [kg]: '  + str(int(round(mw.zero_fuel_mass))))
    log.info('Wing loading [kg/m^2]: ' + str(int(round(out.wing_loading))))
    log.info('Maximum ammount of fuel allowed with no passengers [kg]: ' + str(int(round(mw.mass_fuel_max))))
    log.info('Maximum ammount of fuel allowed with no passengers [l]: ' + str(int(round(mw.mass_fuel_max/ui.FUEL_DENSITY))))
    log.info('--------- Passegers evaluated: ---------')
    log.info('Passengers: ' + str(out.pass_nb))
    log.info('Lavatory: ' + str(out.toilet_nb))
    log.info('Payload mass [kg]: ' + str(mw.mass_payload))
    log.info('------- Crew members evaluated: --------')
    log.info('Pilots: ' + str(out.PILOT_NB))
    log.info('Cabin crew members: ' + str(out.cabin_crew_nb))
    log.info('############### Weight estimation completed ###############')

    # Outptu writting
    log.info('-------- Generating output text file --------')
    outputweightgen.output_txt(out, mw, ind, ui, name)

    # CPACS writting
    cpacsweightupdate.cpacs_update(mw, out, cpacs_path, cpacs_out_path)


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    mi.check_cpacs_input_requirements(cpacs_path)

    get_weight_estimations(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
