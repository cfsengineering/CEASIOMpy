"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Output text and plot generation functions.

Python version: >=3.6

| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2020-01-24 (AJ)

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

def output_txt(out, mw, ind, ui, NAME):
    """ The function generates the output text file for the Weight analysis.

    Args:
        out  (class): WeightOutput class.
        mw   (class): MassesWeights class.
        ind  (class): InsideDimensions class.
        ui   (class): UserInputs class.
        NAME (str): Aircraft name.

    Output:
        NAME_Weight_module.out (file) : Text file containing all the informations
                                        estimated from the code.
    """

    out_name = 'ToolOutput/' + NAME + '/' + NAME + '_Weight_module.out'

    out_txt_file = open(out_name, 'w')
    out_txt_file.write('\n###############################################')
    out_txt_file.write('\n###### AIRCRAFT WEIGHT ESTIMATION MODULE ######')
    out_txt_file.write('\n#####               OUTPUTS               #####')
    out_txt_file.write('\n###############################################')
    out_txt_file.write('\n-----------------------------------------------')
    out_txt_file.write('\nAircraft: ' + NAME )
    out_txt_file.write('\n-----------------------------------------------')
    out_txt_file.write('\n')
    out_txt_file.write('\n-----------------------------------------------')
    out_txt_file.write('\nAircraft Geometry Evaluated -------------------')
    out_txt_file.write('\n-----------------------------------------------')
    out_txt_file.write('\nNose length [m]: ' + str(round(ind.nose_length,3)))
    out_txt_file.write('\nTail length [m]: ' + str(round(ind.tail_length,3)))
    out_txt_file.write('\nCabin length [m]: ' + str(round(ind.cabin_length,3)))
    out_txt_file.write('\nCabin width [m]: ' + str(round(ind.cabin_width,3)))
    out_txt_file.write('\nCabin Area [m^2]: ' + str(round(ind.cabin_area,3)))
    if ui.IS_DOUBLE_FLOOR == 1:
        out_txt_file.write('\nThe aircraft has a full 2nd floor')
    elif ui.IS_DOUBLE_FLOOR == 2:
        out_txt_file.write('\nThe aircraft has a reduced 2nd floor')
    else:
        out_txt_file.write('\nThe aircraft has 1 floor')
    out_txt_file.write('\n-----------------------------------------------')
    out_txt_file.write('\nUser Input and Default Values -----------------')
    out_txt_file.write('\n-----------------------------------------------')
    out_txt_file.write('\nseat length [m]: ' + str(ind.seat_length))
    out_txt_file.write('\nseat width [m]: ' + str(ind.seat_width))
    out_txt_file.write('\naisle width [m]: ' + str(ind.aisle_width))
    if ui.MAX_PAYLOAD > 0:
        out_txt_file.write('\nMaximum payload allowed [kg]: ' + str(ui.MAX_PAYLOAD))
    if ui.MAX_FUEL_VOL > 0:
        out_txt_file.write('\nMaximum amount of fuel [kg]: '\
                             + str(ui.MAX_FUEL_VOL*ui.FUEL_DENSITY))
    out_txt_file.write('\n-----------------------------------------------')
    out_txt_file.write('\nResults ---------------------------------------')
    out_txt_file.write('\n-----------------------------------------------')
    out_txt_file.write('\nSeating estimation ----------------------------')
    out_txt_file.write('\nNumber of abreasts: ' + str(out.abreast_nb))
    out_txt_file.write('\nNumber of row: ' + str(out.row_nb))
    out_txt_file.write('\nNumber of passengers: ' + str(out.pass_nb))
    out_txt_file.write('\nNumber of lavatory: ' + str(int(out.toilet_nb)))
    out_txt_file.write('\n-----------------------------------------------')
    out_txt_file.write('\nCrew estimation -------------------------------')
    out_txt_file.write('\nTotal crew members: ' + str(out.crew_nb))
    out_txt_file.write('\nNumber of cabin crew members: ' + str(out.cabin_crew_nb))
    out_txt_file.write('\nNumber of pilots: ' + str(out.PILOT_NB))
    out_txt_file.write('\n-----------------------------------------------')
    out_txt_file.write('\nMasses estimation -----------------------------')
    out_txt_file.write('\nMaximum payload mass [kg]: '\
                         + str(int(round(mw.mass_payload,0))))
    out_txt_file.write('\nMaximum passengers mass [kg]: '\
                         + str(int(round(out.pass_nb * ui.MASS_PASS,0))))
    if mw.mass_cargo:
        out_txt_file.write('\nMaximum extra payload mass [kg]: '\
                             + str(int(round(mw.cargo,0))))
    out_txt_file.write('\nMaximum fuel mass with max passengers [kg]: '\
                         + str(int(round(mw.mass_fuel_maxpass,0))))
    out_txt_file.write('\nMaximum fuel mass with no passengers [kg]: '\
                         + str(int(round(mw.mass_fuel_max,))))
    out_txt_file.write('\nMaximum fuel volume with no passengers [l]: '\
                         + str(int(round(mw.mass_fuel_max/ui.FUEL_DENSITY*1000,0))))
    out_txt_file.write('\nMaximum take off mass [kg]: '\
                         + str(int(round(mw.maximum_take_off_mass,0))))
    out_txt_file.write('\nOperating empty mass [kg]: '\
                         + str(int(round(mw.operating_empty_mass,0))))
    out_txt_file.write('\nZero fuel mass [kg]: ' + str(int(round(mw.zero_fuel_mass,0))))
    out_txt_file.write('\nWing loading [kg/m^2]: ' + str(int(round(out.wing_loading))))

    out_txt_file.close()

    return()


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':

    log.warning('###########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####')
    log.warning('###########################################################')
