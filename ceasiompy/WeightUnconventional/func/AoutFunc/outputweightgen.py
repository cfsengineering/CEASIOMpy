"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Output text and plot generation function for unconventional aircraft analysis.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================

""" No imports """


#=============================================================================
#   CLASSES
#=============================================================================

"""All classes are defined inside the classes folder and in the
   InputClasses/Unconventional folder."""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def output_fuse_txt(f_nb, FLOORS_NB, ed, out, mw, adui, awg, afg, NAME):
    """ The function generates the output text file for the
        Weight_unc_main program in case of geometry with
        fuselages.

        INPUT
        (integer) f_nb         --Arg.: Number of fuselages.
        (integer) FLOORS_NB    --Arg.: Floor numbre indicator.
        (class) ed             --Arg.: EngineData class.
        (class) out            --Arg.: Output class.
        (class) mw             --Arg.: Mass and weight class.
        (class) adui           --Arg.: AdvancedInputs class.
        (class) awg            --Arg.: AircraftWingGeometry class.
        (class) afg            --Arg.: AircraftFuselageGeometry class.
        ##======== Class is defined in the InputClasses folder =========##
        (char) NAME            --Arg.: Aircraft name.

        OUTPUT
        (file) Weight.out --Out.: Text file containing all the
                                  informations estimated from the
                                  code.
    """

    out_name = 'ToolOutput/' + NAME + '/' + NAME\
               + '_Weight_unc_module.out'
    OutputTextFile = open(out_name, 'w')
    OutputTextFile.write('###############################################')
    OutputTextFile.write('\n######      UNCONVENTIONAL AIRCRAFT      ######')
    OutputTextFile.write('\n#####  WEIGHT ESTIMATION MODULE OUTPUTS   #####')
    OutputTextFile.write('\n###############################################')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nAircraft: ' + NAME )
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\n')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nAircraft Geometry Values used------------------')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nNumber of fuselages [-]: ' + str(f_nb))
    OutputTextFile.write('\nFuselage Length [m]: '\
                         + str(afg.fuse_length))
    OutputTextFile.write('\nFuselage mean Width [m]: '\
                         + str(afg.fuse_mean_width))
    OutputTextFile.write('\nWing span [m]: '\
                         + str(round(max(awg.wing_span),3)))
    OutputTextFile.write('\nTotal main wings plantform area [m^2]: '\
                         + str(awg.wing_plt_area_main))
    if FLOORS_NB > 1:
        OutputTextFile.write('\nThe aircraft has: ' + str(FLOORS_NB)\
                             + 'floors')
    else:
        OutputTextFile.write('\nThe aircraft has 1 floor')
    OutputTextFile.write('\n')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nResults ---------------------------------------')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nSeating estimation ----------------------------')
    OutputTextFile.write('\nNumber of passengers: ' + str(out.pass_nb))
    OutputTextFile.write('\nNumber of toilet: ' + str(int(out.toilet_nb)))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nSuggested crew members ------------------------')
    OutputTextFile.write('\nTotal crew members: ' + str(out.crew_nb))
    OutputTextFile.write('\nNumber of cabin crew members: '
                         + str(out.cabin_crew_nb))
    OutputTextFile.write('\nNumber of pilots: ' + str(adui.PILOT_NB))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nEngine estimation -----------------------------')
    OutputTextFile.write('\nNumber of engines: ' + str(ed.NE))
    OutputTextFile.write('\nSingle engine mass [kg]: ' + str(int(ed.en_mass)))
    OutputTextFile.write('\nSingle engine maximum take off thrust [kN]: '
                         + str(int(round(ed.max_thrust,0))))
    OutputTextFile.write('\nThrust specific fuel consumption in cruise'\
                         + ' [1/hr]: ' + str(ed.TSFC_CRUISE))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nMasses estimation -----------------------------')
    OutputTextFile.write('\nSystems mass [kg]: '\
                         + str(int(round(mw.mass_systems))))
    OutputTextFile.write('\nStructure mass [kg]: '\
                         + str(int(round(mw.mass_structure))))
    OutputTextFile.write('\nEngines mass [kg]: '\
                         + str(int(round(mw.mass_engines))))
    OutputTextFile.write('\nMaximum payload mass [kg]: '\
                         + str(int(round(mw.mass_payload))))
    OutputTextFile.write('\nMaximum passengers mass [kg]: '\
                         + str(int(round(mw.mass_pass))))
    OutputTextFile.write('\nMaximum fuel mass with max passengers [kg]: '\
                         + str(int(round(mw.mass_fuel_maxpass))))
    OutputTextFile.write('\nMaximum fuel mass with no passengers [kg]: '\
                         + str(int(round(mw.mass_fuel_max))))
    OutputTextFile.write('\nMaximum fuel volume with no passengers [l]: '\
                         + str(int(round(mw.mass_fuel_max/0.8,3))))
    OutputTextFile.write('\nMaximum take off mass [kg]: '\
                         + str(int(round(mw.maximum_take_off_mass))))
    OutputTextFile.write('\nOperating empty mass [kg]: '\
                         + str(int(round(mw.operating_empty_mass))))
    OutputTextFile.write('\nZero fuel mass [kg]: '\
                         + str(int(round(mw.zero_fuel_mass))))
    OutputTextFile.write('\nWing loading [kg/m^2]: '\
                         + str(int(round(out.wing_loading))))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\n-----------------------------------------------')
    ### Closing Text File
    OutputTextFile.close()

    return()

#=============================================================================
def output_bwb_txt(FLOORS_NB, ed, out, mw, adui, awg, NAME):
    """ The function generates the output text file for the
        Weight_unc_main program in case of geometry without
        fuselage.

        INPUT
        (integer) FLOOR_NB    --Arg.: Floor numbre indicator.
        (class) ed             --Arg.: EngineData class.
        (class) out           --Arg.: Output class.
        (class) mw            --Arg.: Mass and weight class.
        (class) adui          --Arg.: AdvancedInputs class.
        (class) awg           --Arg.: AircraftWingGeometry Class.
        ##======== Class is defined in the InputClasses folder =========##
        (char) NAME           --Arg.: Aircraft name.

        OUTPUT
        (file) Weight.out --Out.: Text file containing all the
                                  informations estimated from the
                                  code.
    """

    out_name = 'ToolOutput/' + NAME + '/' + NAME\
               + '_Weight_module.out'
    OutputTextFile = open(out_name, 'w')
    OutputTextFile.write('###############################################')
    OutputTextFile.write('\n###### AIRCRAFT WEIGHT ESTIMATION MODULE ######')
    OutputTextFile.write('\n#####               OUTPUTS               #####')
    OutputTextFile.write('\n###############################################')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nAircraft: ' + NAME )
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\n')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nAircraft Geometry Values used------------------')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nWing Span [m]: '\
                         + str(round(max(awg.wing_span),3)))
    OutputTextFile.write('\nWing Area [m^2]: '\
                         + str(round(awg.wing_plt_area_main,3)))
    OutputTextFile.write('\nCabin Area [m^2]: '\
                         + str(round(awg.cabin_area,3)))
    if FLOORS_NB > 1:
        OutputTextFile.write('\nThe aircraft has: ' + str(FLOORS_NB)\
                             + 'floors')
    else:
        OutputTextFile.write('\nThe aircraft has 1 floor')
    OutputTextFile.write('\n')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nResults ---------------------------------------')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nSeating estimation ----------------------------')
    OutputTextFile.write('\nNumber of passengers: ' + str(out.pass_nb))
    OutputTextFile.write('\nNumber of toilet: ' + str(int(out.toilet_nb)))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nSuggested crew members ------------------------')
    OutputTextFile.write('\nTotal crew members: ' + str(out.crew_nb))
    OutputTextFile.write('\nNumber of cabin crew members: '
                         + str(out.cabin_crew_nb))
    OutputTextFile.write('\nNumber of pilots: ' + str(adui.PILOT_NB))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nEngine estimation -----------------------------')
    OutputTextFile.write('\nNumber of engines: ' + str(ed.NE))
    OutputTextFile.write('\nSingle engine mass [kg]: ' + str(int(ed.en_mass)))
    OutputTextFile.write('\nSingle engine maximum take off thrust [kN]: '
                         + str(int(round(ed.max_thrust,0))))
    OutputTextFile.write('\nThrust specific fuel consumption in cruise'\
                         + ' [1/hr]: ' + str(ed.TSFC_CRUISE))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nMasses estimation -----------------------------')
    OutputTextFile.write('\nSystems mass [kg]: '\
                         + str(int(round(mw.mass_systems))))
    OutputTextFile.write('\nStructure mass [kg]: '\
                         + str(int(round(mw.mass_structure))))
    OutputTextFile.write('\nEngines mass [kg]: '\
                         + str(int(round(mw.mass_engines))))
    OutputTextFile.write('\nMaximum payload mass [kg]: '\
                         + str(int(round(mw.mass_payload))))
    OutputTextFile.write('\nMaximum passengers mass [kg]: '\
                         + str(int(round(mw.mass_pass))))
    OutputTextFile.write('\nMaximum fuel mass with max passengers [kg]: '\
                         + str(int(round(mw.mass_fuel_maxpass))))
    OutputTextFile.write('\nMaximum fuel mass with no passengers [kg]: '\
                         + str(int(round(mw.mass_fuel_max))))
    OutputTextFile.write('\nMaximum fuel volume with no passengers [l]: '\
                         + str(int(round(mw.mass_fuel_max/0.8,3))))
    OutputTextFile.write('\nMaximum take off mass [kg]: '\
                         + str(int(round(mw.maximum_take_off_mass))))
    OutputTextFile.write('\nOperating empty mass [kg]: '\
                         + str(int(round(mw.operating_empty_mass))))
    OutputTextFile.write('\nZero fuel mass [kg]: '\
                         + str(int(round(mw.zero_fuel_mass))))
    OutputTextFile.write('\nWing loading [kg/m^2]: '\
                         + str(int(round(out.wing_loading))))
    OutputTextFile.write('\n-----------------------------------------------')

    ### Closing Text File
    OutputTextFile.close()

    return()


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('########################################################')
    log.warning('# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #')
    log.warning('########################################################')
