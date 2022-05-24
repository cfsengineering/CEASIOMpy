"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Output text and plot generation functions.

Python version: >=3.7

| Author : Stefano Piccini
| Date of creation: 2018-11-21

"""


# =============================================================================
#   IMPORTS
# =============================================================================

# No imports needed


# =============================================================================
#   CLASSES
# =============================================================================

#  InsideDimensions class, can be found on the InputClasses folder inside the
#  weightconvclass.py script.


# =============================================================================
#   FUNCTIONS
# =============================================================================


from ceasiompy.WeightConventional.func.weight_utils import PASSENGER_MASS, PILOT_NB


def output_txt(out, mw, ind, ui, NAME):
    """The function generates the output text file for the Weight analysis.

    Args:
        out  (class): WeightOutput class.
        mw   (class): MassesWeights class.
        ind  (class): InsideDimensions class.
        ui   (class): UserInputs class.
        NAME (str): Aircraft name.

    Output:
        NAME_Weight_module.out (file) : Text file containing all the information
                                        estimated from the code.
    """

    out_name = "ToolOutput/" + NAME + "/" + NAME + "_Weight_module.out"

    out_txt_file = open(out_name, "w")
    out_txt_file.write("\n###############################################")
    out_txt_file.write("\n###### AIRCRAFT WEIGHT ESTIMATION MODULE ######")
    out_txt_file.write("\n#####               OUTPUTS               #####")
    out_txt_file.write("\n###############################################")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nAircraft: {NAME}")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\n")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nAircraft Geometry Evaluated -------------------")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write(f"\nNose length [m]: {round(ind.nose_length, 3)}")
    out_txt_file.write(f"\nTail length [m]: {round(ind.tail_length, 3)}")
    out_txt_file.write(f"\nCabin length [m]: {round(ind.cabin_length, 3)}")
    out_txt_file.write(f"\nCabin width [m]: {round(ind.cabin_width, 3)}")
    out_txt_file.write(f"\nCabin Area [m^2]: {round(ind.cabin_area, 3)}")
    if ui.IS_DOUBLE_FLOOR == 1:
        out_txt_file.write("\nThe aircraft has a full 2nd floor")
    elif ui.IS_DOUBLE_FLOOR == 2:
        out_txt_file.write("\nThe aircraft has a reduced 2nd floor")
    else:
        out_txt_file.write("\nThe aircraft has 1 floor")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nUser Input and Default Values -----------------")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write(f"\nseat length [m]: {ind.seat_length}")
    out_txt_file.write(f"\nseat width [m]: {ind.seat_width}")
    out_txt_file.write(f"\naisle width [m]: {ind.aisle_width}")
    if ui.MAX_PAYLOAD > 0:
        out_txt_file.write(f"\nMaximum payload allowed [kg]: {ui.MAX_PAYLOAD}")
    if ui.MAX_FUEL_VOL > 0:
        out_txt_file.write(f"\nMaximum amount of fuel [kg]: {ui.MAX_FUEL_VOL * ui.FUEL_DENSITY}")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nResults ---------------------------------------")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nSeating estimation ----------------------------")
    out_txt_file.write(f"\nNumber of abreasts: {out.abreast_nb}")
    out_txt_file.write(f"\nNumber of row: {out.row_nb}")
    out_txt_file.write(f"\nNumber of passengers: {out.pass_nb}")
    out_txt_file.write(f"\nNumber of lavatory: {int(out.toilet_nb)}")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nCrew estimation -------------------------------")
    out_txt_file.write(f"\nTotal crew members: {out.crew_nb}")
    out_txt_file.write(f"\nNumber of cabin crew members: {out.cabin_crew_nb}")
    out_txt_file.write(f"\nNumber of pilots: {PILOT_NB}")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nMasses estimation -----------------------------")
    out_txt_file.write(f"\nMaximum payload mass [kg]: {int(mw.mass_payload)}")
    out_txt_file.write(f"\nMaximum passengers mass [kg]: {int(out.pass_nb * PASSENGER_MASS)}")
    if mw.mass_cargo:
        out_txt_file.write("\nMaximum extra payload mass [kg]: " + str(int(mw.cargo)))
    out_txt_file.write(
        f"\nMaximum fuel mass with max passengers [kg]: {int(mw.mass_fuel_maxpass)}"
    )
    out_txt_file.write(f"\nMaximum fuel mass with no passengers [kg]: {int(mw.mass_fuel_max)}")
    out_txt_file.write(
        f"\nMaximum fuel volume with no passengers [l]: {int(mw.mass_fuel_max / ui.FUEL_DENSITY)}"
    )
    out_txt_file.write("\nMaximum take off mass [kg]: {int(mw.maximum_take_off_mass)}")
    out_txt_file.write(f"\nOperating empty mass [kg]: {int(mw.operating_empty_mass)}")
    out_txt_file.write(f"\nZero fuel mass [kg]: {int(mw.zero_fuel_mass)}")
    out_txt_file.write(f"\nWing loading [kg/m^2]: {int(out.wing_loading)}")

    out_txt_file.close()


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":

    print("###########################################################")
    print("#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####")
    print("###########################################################")
