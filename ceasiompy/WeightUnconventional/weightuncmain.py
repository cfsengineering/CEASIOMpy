"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Main module for the unconvenentional aircraft class I design, it evaluates:

* the structure mass;
* the systems mass,
* the engine mass;
* the maximum take-off mass;
* the operating empty mass;
* the zero fuel mass;
* the maximum amount of fuel;
* the maximum number of passengers;
* the maximum amount of fuel with max passengers;
* the number of crew members needed;
* the number of toilet.

Starting point:

* CPACS.xml file in the ToolInput folder.

Aircraft types:

* No Fuselage
* Multiple fuselage (Es.: 2 for payload and 1 for fuel etc..)

Output:

* The code saves a ToolOutput.xml file in the ToolOutput folder.
* The code saves a copy of the ToolOutput.xml file inside the
  ToolInput folder of the range and balance analysis.
* The system creates a folder with the aircraft name, and saves inside it
  two txt file and one figure:

    * NAME_Aircraft_Geometry.out: that contains all the information
      regarding the aircraft geometry (only with case B)
    * NAME_Weight_unc_module.out: with all information
                                  evaluated with this code.
    * NAME_mtomPrediction.png: contains the result of the linear regression
      carried on for the maximum take-off mass evaluation.

.. warning::

    The code deletes the ToolOutput folder and recreates
    it at the start of each run.

Python version: >=3.6


| Author : Stefano Piccini
| Date of creation: 2018-12-07
| Last modifiction: 2019-08-08 (AJ)
"""


#=============================================================================
#   IMPORTS
#=============================================================================
import os
import shutil

import numpy as np
import time

# Classes
from ceasiompy.utils.InputClasses.Unconventional.weightuncclass import UserInputs
from ceasiompy.utils.InputClasses.Unconventional.weightuncclass import AdvancedInputs
from ceasiompy.utils.InputClasses.Unconventional.engineclass import EngineData
from ceasiompy.utils.InputClasses.Unconventional.weightuncclass import MassesWeights
from ceasiompy.utils.InputClasses.Unconventional.weightuncclass import WeightOutput

# Functions
from ceasiompy.WeightUnconventional.func.AinFunc import getinput
from ceasiompy.WeightUnconventional.func.AoutFunc import outputweightgen
from ceasiompy.WeightUnconventional.func.AoutFunc import cpacsweightupdate
from ceasiompy.WeightUnconventional.func.People.passengers import estimate_fuse_passengers
from ceasiompy.WeightUnconventional.func.People.passengers import estimate_wing_passengers
from ceasiompy.WeightUnconventional.func.People.crewmembers import estimate_crew
from ceasiompy.WeightUnconventional.func.Systems.systemsmass import estimate_system_mass
from ceasiompy.WeightUnconventional.func.Engines.enginesanalysis import check_ed
from ceasiompy.WeightUnconventional.func.Engines.enginesanalysis import engine_definition
from ceasiompy.WeightUnconventional.func.Fuel.fuelmass import estimate_fuse_fuel_mass
from ceasiompy.WeightUnconventional.func.Fuel.fuelmass import estimate_wing_fuel_mass


from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.cpacsfunctions import aircraft_name
from ceasiompy.utils.WB.UncGeometry import uncgeomanalysis

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes and into
   the InputClasses/Unconventional folder."""


#=============================================================================
#   FUNCTIONS
#=============================================================================

"""
    Each function are defined in a separate script inside the func folder.
"""


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.info('##########################################################')
    log.info('#### UNCONVENTIONAL AIRCRAFT WEIGHT ESTIMATION MODULE ####')
    log.info('##########################################################')

##=============================== PREPROCESSING ============================##
    start = time.time()

    if os.path.exists('ToolOutput'):
        shutil.rmtree('ToolOutput')
        os.makedirs('ToolOutput')
    else:
        os.makedirs('ToolOutput')

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


##================================ USER INPUTS =============================##
    # All the input data must be defined into the unc_weight_user_input.py
    # file inside the ceasiompy.InputClasses/Unconventioanl folder.

    adui = AdvancedInputs()
    ui = UserInputs()
    mw = MassesWeights()
    out = WeightOutput()
    ed = EngineData()
    (ed, ui, adui) = getinput.get_user_inputs(ed, ui, adui, out_xml)
    if ui.USER_ENGINES:
        (ed) = getinput.get_engine_inputs(ui, ed, out_xml)

##============================= GEOMETRY ANALYSIS ==========================##

    (f_nb, w_nb) = uncgeomanalysis.get_number_of_parts(cpacs_in)
    h_min = ui.FLOORS_NB * ui.H_LIM_CABIN

    if not w_nb:
        log.warning('Aircraft does not have wings')
        raise Exception('Aircraft does not have wings')
    elif not f_nb:
        (awg, wing_nodes) =\
            uncgeomanalysis.no_fuse_geom_analysis(ui.FLOORS_NB, w_nb,\
                h_min, ui.FUEL_ON_CABIN, out_xml, name, ed.TURBOPROP)
    else:
        log.info('Fuselage detected')
        log.info('Number of fuselage: ' + str(int(f_nb)))
        # Minimum fuselage segment height to be a cabin segment.
        (afg, awg) =\
            uncgeomanalysis.with_fuse_geom_analysis(f_nb, w_nb, h_min, adui,\
                                                    ed.TURBOPROP, ui.F_FUEL,\
                                                    out_xml, name)

    ui = getinput.get_user_fuel(f_nb, ui, out_xml)

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
    mw.mass_fuel_unusable = mw.mass_fuel_max * (adui.RES_FUEL_PERC/100.0)

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
        mw.mass_systems\
                = round(estimate_system_mass(out.pass_nb, awg.main_wing_surface,\
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


#=============================================================================
#    OUTPUT WRITING
#=============================================================================

    log.info('----- Generating output text file -----')
    cpacsweightupdate.cpacs_weight_update(out, mw, ui, out_xml)
    cpacsweightupdate.toolspecific_update(f_nb, awg, mw, out, out_xml)
    cpacsweightupdate.cpacs_engine_update(ui, ed, mw, out_xml)

    if not f_nb:
        outputweightgen.output_bwb_txt(ui.FLOORS_NB, ed, out,\
                                       mw, adui, awg, name)
    else:
        outputweightgen.output_fuse_txt(f_nb, ui.FLOORS_NB, ed,\
                                        out, mw, adui, awg, afg, name)


#=============================================================================
#    CPACS WRITING
#=============================================================================

# Copying ToolOutput.xml as ToolInput.xml in the ToolInput folder in
# 2RangeModule and 6BalanceUncModule.

    # PATH = 'ToolOutput/ToolOutput.xml'
    # PATH_RANGE_OUT = '../Range/ToolInput/toolinput.xml'
    # PATH_BALANCE_OUT = '../BalanceUnconventional/ToolInput/ToolInput.xml'
    # TEMP = '/unconv.temp'
    # TEXT = 'Unconventional Aircraft'
    #
    # if os.path.exists('../Range/ToolInput'):
    #     shutil.rmtree('../Range/ToolInput')
    #     os.makedirs('../Range/ToolInput')
    # shutil.copyfile(PATH, PATH_RANGE_OUT)
    # OutputTextFile = open('../Range/ToolInput' + TEMP, 'w')
    # OutputTextFile.write(TEXT)
    # OutputTextFile.close()
    #
    # if os.path.exists('../BalanceUnconventional/ToolInput'):
    #     shutil.rmtree('../BalanceUnconventional/ToolInput')
    #     os.makedirs('../BalanceUnconventional/ToolInput')
    # shutil.copyfile(PATH, PATH_BALANCE_OUT)


#=============================================================================
#    LOG WRITING
#=============================================================================

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


    log.info('##########################################################')
    log.info('### Uconventional Weight analysis succesfuly completed ###')
    log.info('##########################################################')
