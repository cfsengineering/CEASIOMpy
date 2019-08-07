"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    Output text and plot generation functions.

    Works with Python 2.7
    Author : Stefano Piccini
    Date of creation: 2018-11-21
    Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================

""" No imports needed """


#=============================================================================
#   CLASSES
#=============================================================================

"""
 InsideDimensions class, can be found on the InputClasses folder inside the
 weightconvclass.py script.
"""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def output_txt(IS_DOUBLE_FLOOR, out, mw, ind, ui, NAME):
    """ The function generates the output text file for the Weight analysis.

        INPUT
        (integer) IS_DOUBLE_FLOOR --Arg.: Floor numbre indicator.
        (float) mass_pass         --Arg.: Mass of a single passenger.

        (class) out               --Arg.: WeightOutput class.
        (class) mw                --Arg.: MassesWeights class.
        ##========== Classes are defined in the classes folder ==========##

        (class) ind               --Arg.: InsideDimensions class.
        (class) ui                --Arg.: UserInputs class.
        ##======= Classes are defined in the Input_classes folder =======##

        (char) NAME               --Arg.: Aircraft name.

        OUTPUT
        (file) NAME_Weight_module.out --Out.: Text file containing all the
                                              informations estimated from the
                                              code.
    """
    out_name = 'ToolOutput/' + NAME + '/' + NAME\
               + '_Weight_module.out'
    OutputTextFile = open(out_name, 'w')
    OutputTextFile.write('\n###############################################')
    OutputTextFile.write('\n###### AIRCRAFT WEIGHT ESTIMATION MODULE ######')
    OutputTextFile.write('\n#####               OUTPUTS               #####')
    OutputTextFile.write('\n###############################################')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nAircraft: ' + NAME )
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\n')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nAircraft Geometry Evaluated -------------------')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nNose length [m]: '\
                         + str(round(ind.nose_length,3)))
    OutputTextFile.write('\nTail length [m]: '\
                         + str(round(ind.tail_length,3)))
    OutputTextFile.write('\nCabin length [m]: '\
                         + str(round(ind.cabin_length,3)))
    OutputTextFile.write('\nCabin width [m]: '\
                         + str(round(ind.cabin_width,3)))
    OutputTextFile.write('\nCabin Area [m^2]: '\
                         + str(round(ind.cabin_area,3)))
    if IS_DOUBLE_FLOOR == 1:
        OutputTextFile.write('\nThe aircraft has a full 2nd floor')
    elif IS_DOUBLE_FLOOR == 2:
        OutputTextFile.write('\nThe aircraft has a small 2nd floor')
    else:
        OutputTextFile.write('\nThe aircraft has 1 floor')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nUser Input and Default Values -----------------')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nseat length [m]: ' + str(ind.seat_length))
    OutputTextFile.write('\nseat width [m]: ' + str(ind.seat_width))
    OutputTextFile.write('\naisle width [m]: ' + str(ind.aisle_width))
    if ui.MAX_PAYLOAD > 0:
        OutputTextFile.write('\nMaximum payload allowed [kg]: '\
                             + str(ui.MAX_PAYLOAD))
    if ui.MAX_FUEL_VOL > 0:
        OutputTextFile.write('\nMaximum amount of fuel [kg]: '\
                             + str(ui.MAX_FUEL_VOL*ui.FUEL_DENSITY))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nResults ---------------------------------------')
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nSeating estimation ----------------------------')
    OutputTextFile.write('\nNumber of abreasts: ' + str(out.abreast_nb))
    OutputTextFile.write('\nNumber of row: ' + str(out.row_nb))
    OutputTextFile.write('\nNumber of passengers: ' + str(out.pass_nb))
    OutputTextFile.write('\nNumber of lavatory: ' + str(int(out.toilet_nb)))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nCrew estimation -------------------------------')
    OutputTextFile.write('\nTotal crew members: ' + str(out.crew_nb))
    OutputTextFile.write('\nNumber of cabin crew members: '
                         + str(out.cabin_crew_nb))
    OutputTextFile.write('\nNumber of pilots: ' + str(out.PILOT_NB))
    OutputTextFile.write('\n-----------------------------------------------')
    OutputTextFile.write('\nMasses estimation -----------------------------')
    OutputTextFile.write('\nMaximum payload mass [kg]: '\
                         + str(int(round(mw.mass_payload,0))))
    OutputTextFile.write('\nMaximum passengers mass [kg]: '\
                         + str(int(round(out.pass_nb * ui.MASS_PASS,0))))
    if mw.mass_cargo:
        OutputTextFile.write('\nMaximum extra payload mass [kg]: '\
                             + str(int(round(mw.cargo,0))))
    OutputTextFile.write('\nMaximum fuel mass with max passengers [kg]: '\
                         + str(int(round(mw.mass_fuel_maxpass,0))))
    OutputTextFile.write('\nMaximum fuel mass with no passengers [kg]: '\
                         + str(int(round(mw.mass_fuel_max,))))
    OutputTextFile.write('\nMaximum fuel volume with no passengers [l]: '\
                         + str(int(round(\
                         mw.mass_fuel_max/ui.FUEL_DENSITY*1000,0))))
    OutputTextFile.write('\nMaximum take off mass [kg]: '\
                         + str(int(round(mw.maximum_take_off_mass,0))))
    OutputTextFile.write('\nOperating empty mass [kg]: '\
                         + str(int(round(mw.operating_empty_mass,0))))
    OutputTextFile.write('\nZero fuel mass [kg]: '\
                         + str(int(round(mw.zero_fuel_mass,0))))
    OutputTextFile.write('\nWing loading [kg/m^2]: '\
                         + str(int(round(out.wing_loading))))

    ### Closing Text File
    OutputTextFile.close()

    return()


#=============================================================================
#   PLOTS
#=============================================================================

"""
    linear regression plot on the mtom_estimation module.
"""


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('###########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####')
    log.warning('###########################################################')
