"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Weight unconventional module for preliminary design of unconventional aircraft

Python version: >=3.6

| Author : Stefano Piccini
| Date of creation: 2018-12-07
| Last modifiction: 2020-01-16 (AJ)

TODO:
    * Simplify classes, use only one or use subclasses
    * Make tings compatible also with the oters W&B Modules

"""


#=============================================================================
#   IMPORTS
#=============================================================================
import os
import shutil
import numpy as np
import time

# Should be kept



# Should be changed or removed



# Classes
from ceasiompy.utils.InputClasses.Unconventional.weightuncclass import UserInputs, AdvancedInputs, MassesWeights, WeightOutput
from ceasiompy.utils.InputClasses.Unconventional.engineclass import EngineData

# Functions
from ceasiompy.WeightUnconventional.func.AinFunc import getinput
from ceasiompy.WeightUnconventional.func.AoutFunc import cpacs_out_path, cpacsweightupdate
from ceasiompy.WeightUnconventional.func.People.passengers import estimate_fuse_passengers, estimate_wing_passengers
from ceasiompy.WeightUnconventional.func.People.crewmembers import estimate_crew
from ceasiompy.WeightUnconventional.func.Systems.systemsmass import estimate_system_mass
from ceasiompy.WeightUnconventional.func.Engines.enginesanalysis import check_ed, engine_definition
from ceasiompy.WeightUnconventional.func.Fuel.fuelmass import estimate_fuse_fuel_mass, estimate_wing_fuel_mass


from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import aircraft_name
from ceasiompy.utils.WB.UncGeometry import uncgeomanalysis

log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes and into
   the InputClasses/Unconventional folder."""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def get_weight_unc_estimations(cpacs_path, cpacs_out_path):
    """Function to estimate the all weights for a unconventional aircraft.

    Function 'get_weight_unc_estimations' ...

    Source:
        * Reference paper or book, with author and date, see ...

    Args:
        cpacs_path (str): Path to CPACS file
        cpacs_out_path (str):Path to CPACS output file

    """

    # TODO: replace that by a general function??? (same for all modules)
    start = time.time()

    # Removing and recreating the ToolOutput folder.
    if os.path.exists('ToolOutput'):
        shutil.rmtree('ToolOutput')
        os.makedirs('ToolOutput')
    else:
        os.makedirs('ToolOutput')

    if not os.path.exists(cpacs_path):
        raise ValueError ('No "ToolInput.xml" file in the ToolInput folder.')

    name = aircraft_name(cpacs_path)

    shutil.copyfile(cpacs_path, cpacs_out_path) # TODO: shoud not be like that
    newpath = 'ToolOutput/' + name
    if not os.path.exists(newpath):
        os.makedirs(newpath)


##================================ USER INPUTS =============================##
    # All the input data must be defined into the unc_weight_user_input.py
    # file inside the ceasiompy.InputClasses/Unconventioanl folder.

    adui = AdvancedInputs()
    ui = UserInputs()
    mw = MassesWeights()
    out = WeightOutput()
    ed = EngineData()
    (ed, ui, adui) = getinput.get_user_inputs(ed, ui, adui, cpacs_out_path)
    if ui.USER_ENGINES:
        (ed) = getinput.get_engine_inputs(ui, ed, cpacs_out_path)

##============================= GEOMETRY ANALYSIS ==========================##

    (f_nb, w_nb) = uncgeomanalysis.get_number_of_parts(cpacs_path)
    h_min = ui.FLOORS_NB * ui.H_LIM_CABIN

    if not w_nb:
        log.warning('Aircraft does not have wings')
        raise Exception('Aircraft does not have wings')
    elif not f_nb:
        (awg, wing_nodes) =\
            uncgeomanalysis.no_fuse_geom_analysis(ui.FLOORS_NB, w_nb,\
                h_min, ui.FUEL_ON_CABIN, cpacs_out_path, name, ed.TURBOPROP)
    else:
        log.info('Fuselage detected')
        log.info('Number of fuselage: ' + str(int(f_nb)))
        # Minimum fuselage segment height to be a cabin segment.
        (afg, awg) =\
            uncgeomanalysis.with_fuse_geom_analysis(f_nb, w_nb, h_min, adui,\
                                                    ed.TURBOPROP, ui.F_FUEL,\
                                                    cpacs_out_path, name)

    ui = getinput.get_user_fuel(f_nb, ui, cpacs_out_path)

##============================= WEIGHT ANALYSIS ============================##
    ## Engine evaluation
    if ui.USER_ENGINES:
        check_ed(ed)
        mw.mass_engines = ed.en_mass * ed.NE

    if f_nb:
        # Passengers mass
        (out.pass_nb, out.toilet_nb, mw.mass_pass)\
                = estimate_fuse_passengers(f_nb, ui.FLOORS_NB,\
                    adui.PASS_PER_TOILET, afg.cabin_area, adui.MASS_PASS,\
                    ui.PASS_BASE_DENSITY)
        cabin_area = np.sum(afg.cabin_area)
        # Structure mass
        mw.mass_structure = adui.VRT_STR_DENSITY * adui.VRT_THICK\
            *(np.sum(afg.fuse_surface)\
            + np.sum(awg.total_wings_surface))**adui.VRT_EXP
    else:
        # Passengers mass
        (out.pass_nb, out.toilet_nb, mw.mass_pass)\
                = estimate_wing_passengers(ui.FLOORS_NB,\
                    adui.PASS_PER_TOILET, awg.cabin_area, adui.MASS_PASS,\
                    ui.PASS_BASE_DENSITY)
        cabin_area = awg.cabin_area
        # Structure mass
        mw.mass_structure = adui.VRT_STR_DENSITY * adui.VRT_THICK\
            *np.sum(awg.total_wings_surface)**adui.VRT_EXP

    pass_limit = False
    if ui.MAX_PASS > 0 and out.pass_nb > ui.MAX_PASS:
        out.pass_nb = ui.MAX_PASS
        pass_limit = True
        pass_density = round(out.pass_nb/cabin_area,2)
        mw.mass_pass = adui.MASS_PASS * out.pass_nb
        log.warning('With the defined maximum number of passengers,')
        log.warning('the number of passengers is reduced to : '\
                    + str(out.pass_nb))
        log.warning('and the passenger density is: ' + str(pass_density))

    #Payload masses
    mw.mass_payload = round(ui.MASS_CARGO + mw.mass_pass,0)

    if ui.MAX_PAYLOAD > 0 and mw.mass_payload > ui.MAX_PAYLOAD:
        mw.mass_payload = ui.MAX_PAYLOAD
        if ui.MASS_CARGO > ui.MAX_PAYLOAD:
            log.warning('Mass cargo defined exceeds the chosen'\
                        + ' maximum payload, the code do not consider the'\
                        + ' user cargo mass')
            ui.MASS_CARGO = 0.0
        if pass_limit and mw.mass_pass < ui.MAX_PAYLOAD:
            ui.MASS_CARGO = round(ui.MAX_PAYLOAD - mw.mass_pass,0)
        elif pass_limit and mw.mass_pass > ui.MAX_PAYLOAD:
            log.warning('Pass number defined exceeds the chosen'\
                        + ' maximum payload, the code do not consider the'\
                        + ' user passenger number.')
            mw.mass_pass = ui.MAX_PAYLOAD - ui.MASS_CARGO
            out.pass_nb = int(round(mw.mass_pass/adui.MASS_PASS,0))
        else:
            mw.mass_pass = ui.MAX_PAYLOAD - ui.MASS_CARGO
            out.pass_nb = int(round(mw.mass_pass/adui.MASS_PASS,0))
        pass_density = round(out.pass_nb/cabin_area,2)
        log.warning('With the defined maximum payload and cargo masses,')
        log.warning('the number of passengers is: ' + str(out.pass_nb))
        log.warning('and the passenger density is: ' + str(pass_density))

    ## Fuel mass
    if f_nb:
        mw.mass_fuse_fuel = estimate_fuse_fuel_mass(afg.fuse_fuel_vol,\
                                                    adui.FUEL_DENSITY)
        mw.mass_wing_fuel = estimate_wing_fuel_mass(awg.wing_fuel_vol,\
                                                    adui.FUEL_DENSITY)
        mw.mass_fuel_max = mw.mass_wing_fuel + mw.mass_fuse_fuel
    else:
        mw.mass_fuel_max = estimate_wing_fuel_mass(awg.fuel_vol_tot,\
                                                   adui.FUEL_DENSITY)

    if ui.MAX_FUEL_VOL > 0\
        and (mw.mass_fuel_max/adui.FUEL_DENSITY)*1000.0 > ui.MAX_FUEL_VOL:
        mw.mass_fuel_max = (ui.MAX_FUEL_VOL*adui.FUEL_DENSITY)/1000.0

    # Mass Reserve and Unusable Fuel
    mw.mass_fuel_unusable = mw.mass_fuel_max * (adui.RES_FUEL_PERC)

    # Mass Fuel Maxpass
    if not out.pass_nb:
        mw.mass_fuel_maxpass = mw.mass_fuel_max
    elif ed.TURBOPROP:
        mw.mass_fuel_maxpass = mw.mass_fuel_max * (adui.FPM_TP/100.0)
    else:
        mw.mass_fuel_maxpass = mw.mass_fuel_max * (adui.FPM/100.0)

    wing_area = np.sum(awg.wing_plt_area)
    mw.maximum_take_off_mass = wing_area * ui.wing_loading
    new_mtom = mw.maximum_take_off_mass
    old_mtom = 0
    it = 0
    mw.zero_fuel_mass = mw.maximum_take_off_mass\
                        - mw.mass_fuel_maxpass
    if  mw.zero_fuel_mass < 0:
        mw.maximum_take_off_mass = mw.mass_fuel_maxpass*2
        mw.zero_fuel_mass = mw.maximum_take_off_mass\
                            - mw.mass_fuel_maxpass
        ui.wing_loading = mw.maximum_take_off_mass/wing_area
        log.warning('Wing loading defined too low,'\
                    + ' starting value modified to [kg/m^2]: '\
                    + str(ui.wing_loading))

    while (abs(old_mtom - new_mtom)/max(old_mtom,new_mtom)) > 0.001:
        old_mtom = new_mtom
        mw.maximum_take_off_mass = new_mtom

        if not ui.USER_ENGINES:
            (mw.mass_engines, ed) = engine_definition(mw, ui, ed)

        # Crew mass
        (out.crew_nb, out.cabin_crew_nb, mw.mass_crew)\
                = estimate_crew(out.pass_nb, adui.MASS_PILOT,\
                                adui.MASS_CABIN_CREW,\
                                mw.maximum_take_off_mass, adui.PILOT_NB)

        # Total people and payload mass on the aircraft
        mw.mass_people = round(mw.mass_crew + mw.mass_pass,0)

        ## System mass
        mw.mass_systems= round(estimate_system_mass(out.pass_nb, awg.main_wing_surface,\
                               awg.tail_wings_surface, adui.SINGLE_HYDRAULICS, mw, ed),0)

        ## MTOM, OEM, ZFM re-evaluation
        mw.operating_empty_mass = round(mw.mass_systems + mw.mass_crew\
                                        + mw.mass_engines + mw.mass_structure\
                                        + mw.mass_fuel_unusable,0)

        new_mtom = round(mw.operating_empty_mass + mw.mass_payload\
                         + mw.mass_fuel_maxpass)
        mw.zero_fuel_mass = mw.operating_empty_mass + mw.mass_payload

        it += 1
    # End of the iterative process.

    mw.maximum_take_off_mass = new_mtom
    out.wing_loading = new_mtom/wing_area


    # Log writting  (TODO: maybe create a separate function)
    log.info('--------- Masses evaluated: -----------')
    log.info('System mass [kg]: ' + str(int(round(mw.mass_systems))))
    log.info('People mass [kg]: ' + str(int(round(mw.mass_people))))
    log.info('Payload mass [kg]: ' + str(int(round(mw.mass_payload))))
    log.info('Structure mass [kg]: '\
             + str(int(round(mw.mass_structure))))
    log.info('Total fuel mass [kg]: '\
             + str(int(round(mw.mass_fuel_max))))
    log.info('Total fuel volume [l]: '\
             + str(int(round(mw.mass_fuel_max/adui.FUEL_DENSITY*1000.0))))
    log.info('Mass of fuel with maximum passengers [kg]: '\
             + str(int(round(mw.mass_fuel_maxpass))))
    log.info('Volume of fuel with maximum passengers [l]: '\
             + str(int(round(mw.mass_fuel_maxpass/adui.FUEL_DENSITY*1000.0))))
    log.info('Engines mass [kg]: ' + str(int(round(mw.mass_engines))))
    log.info('---------------------------------------')
    log.info('Maximum Take Off Mass [kg]: '\
             + str(int(round(mw.maximum_take_off_mass))))
    log.info('Operating Empty Mass [kg]: '\
             + str(int(round(mw.operating_empty_mass))))
    log.info('Zero Fuel Mass [kg]: '\
             + str(int(round(mw.zero_fuel_mass))))
    log.info('Wing loading [kg/m^2]: '\
             + str(int(round(out.wing_loading))))
    log.info('--------- Passegers evaluated: ---------')
    log.info('Passengers: ' + str(out.pass_nb))
    log.info('Toilet: ' + str(int(out.toilet_nb)))
    log.info('------- Crew members evaluated: --------')
    log.info('Pilots: ' + str(adui.PILOT_NB))
    log.info('Cabin crew members: ' + str(out.cabin_crew_nb))
    end = time.time()
    log.info('---------------------------------------')
    log.info('Elapsed time [s]: ' + str(round((end-start),3)))
    log.info('Number of iterations: ' + str(it))
    log.info('---------------------------------------')
    log.info('### Uconventional Weight analysis succesfuly completed ###')

    # Outptu writting
    log.info('----- Generating output text file -----')
    cpacsweightupdate.cpacs_weight_update(out, mw, ui, cpacs_out_path)
    cpacsweightupdate.toolspecific_update(f_nb, awg, mw, out, cpacs_out_path)
    cpacsweightupdate.cpacs_engine_update(ui, ed, mw, cpacs_out_path)

    if not f_nb:
        cpacs_out_path.output_bwb_txt(ui.FLOORS_NB, ed, out,mw, adui, awg, name)
    else:
        cpacs_out_path.output_fuse_txt(f_nb, ui.FLOORS_NB, ed,out, mw, adui, awg, afg, name)


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    cpacs_path = os.path.join(MODULE_DIR,'ToolInput','ToolInput.xml')
    cpacs_out_path = os.path.join(MODULE_DIR,'ToolOutput','ToolOutput.xml')

    get_weight_unc_estimations(cpacs_path,cpacs_out_path)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
