"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Output text and plot generation function for unconventional aircraft analysis.


| Author : Stefano Piccini
| Date of creation: 2018-11-21

"""

# =============================================================================
#   IMPORTS
# =============================================================================

from ceasiompy.WeightConventional.func.weightutils import PILOT_NB


# =============================================================================
#   FUNCTIONS
# =============================================================================


def output_fuse_txt(fus_nb, FLOORS_NB, ed, out, mw, adui, awg, afg, NAME):
    """The function generates the output text file for the
        Weight_unc_main program in case of geometry with
        fuselages.

    Args:
        fus_nb (integer): Number of fuselages.
        FLOORS_NB (integer): Floor numbre indicator.
        ed   (class): EngineData class.
        out  (class): Output class.
        mw   (class): Mass and weight class.
        adui (class): AdvancedInputs class.
        awg  (class): AircraftWingGeometry class.
        afg  (class): AircraftFuselageGeometry class.
        NAME (str): Aircraft name.

    Output:
        Weight.out (file): Text file containing all the informations estimated
                           from the code.

    """

    out_name = "ToolOutput/" + NAME + "/" + NAME + "_Weight_unc_module.out"
    out_txt_file = open(out_name, "w")
    out_txt_file.write("###############################################")
    out_txt_file.write("\n######      UNCONVENTIONAL AIRCRAFT      ######")
    out_txt_file.write("\n#####  WEIGHT ESTIMATION MODULE OUTPUTS   #####")
    out_txt_file.write("\n###############################################")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nAircraft: " + NAME)
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\n")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nAircraft Geometry Values used------------------")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nNumber of fuselages [-]: " + str(fus_nb))
    out_txt_file.write("\nFuselage Length [m]: " + str(afg.fuse_length))
    out_txt_file.write("\nFuselage mean Width [m]: " + str(afg.fuse_mean_width))
    out_txt_file.write("\nWing span [m]: " + str(round(max(awg.wing_span), 3)))
    out_txt_file.write("\nTotal main wings plantform area [m^2]: " + str(awg.wing_plt_area_main))
    out_txt_file.write("\nThe aircraft has: " + str(FLOORS_NB) + "floor(s)")
    out_txt_file.write("\n")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nResults ---------------------------------------")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nSeating estimation ----------------------------")
    out_txt_file.write("\nNumber of passengers: " + str(out.pass_nb))
    out_txt_file.write("\nNumber of toilet: " + str(int(out.toilet_nb)))
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nSuggested crew members ------------------------")
    out_txt_file.write("\nTotal crew members: " + str(out.crew_nb))
    out_txt_file.write("\nNumber of cabin crew members: " + str(out.cabin_crew_nb))
    out_txt_file.write("\nNumber of pilots: " + str(PILOT_NB))
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nEngine estimation -----------------------------")
    out_txt_file.write("\nNumber of engines: " + str(ed.NE))
    out_txt_file.write("\nSingle engine mass [kg]: " + str(int(ed.en_mass)))
    out_txt_file.write(
        "\nSingle engine maximum take off thrust [kN]: " + str(int(round(ed.max_thrust, 0)))
    )
    out_txt_file.write(
        "\nThrust specific fuel consumption in cruise [1/hr]:" + str(ed.TSFC_CRUISE)
    )
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nMasses estimation -----------------------------")
    out_txt_file.write("\nSystems mass [kg]: " + str(int(round(mw.mass_systems))))
    out_txt_file.write("\nStructure mass [kg]: " + str(int(round(mw.mass_structure))))
    out_txt_file.write("\nEngines mass [kg]: " + str(int(round(mw.mass_engines))))
    out_txt_file.write("\nMaximum payload mass [kg]: " + str(int(round(mw.mass_payload))))
    out_txt_file.write("\nMaximum passengers mass [kg]: " + str(int(round(mw.mass_pass))))
    out_txt_file.write(
        "\nMaximum fuel mass with max passengers [kg]: " + str(int(round(mw.mass_fuel_maxpass)))
    )
    out_txt_file.write(
        "\nMaximum fuel mass with no passengers [kg]: " + str(int(round(mw.mass_fuel_max)))
    )
    out_txt_file.write(
        "\nMaximum fuel volume with no passengers [l]: "
        + str(int(round(mw.mass_fuel_max / 0.8, 3)))
    )  # TODO: 0.8 shoud be a variable...
    out_txt_file.write(
        "\nMaximum take off mass [kg]: " + str(int(round(mw.maximum_take_off_mass)))
    )
    out_txt_file.write("\nOperating empty mass [kg]: " + str(int(round(mw.operating_empty_mass))))
    out_txt_file.write("\nZero fuel mass [kg]: " + str(int(round(mw.zero_fuel_mass))))
    out_txt_file.write("\nWing loading [kg/m^2]: " + str(int(round(out.wing_loading))))
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\n-----------------------------------------------")

    out_txt_file.close()

    return ()


def output_bwb_txt(FLOORS_NB, ed, out, mw, adui, awg, NAME):
    """The function generates the output text file for the
        Weight_unc_main program in case of geometry without
        fuselage.

    Args:
        FLOOR_NB (integer): Floor numbre indicator.
        ed   (class): EngineData class.
        out  (class): Output class.
        mw   (class): Mass and weight class.
        adui (class): AdvancedInputs class.
        awg  (class): AircraftWingGeometry Class.
        NAME (str): Aircraft name.

    Output:
        Weight.out (file): Text file containing all the informations estimated
                           from the code.
    """

    out_name = "ToolOutput/" + NAME + "/" + NAME + "_Weight_module.out"
    out_txt_file = open(out_name, "w")
    out_txt_file.write("###############################################")
    out_txt_file.write("\n###### AIRCRAFT WEIGHT ESTIMATION MODULE ######")
    out_txt_file.write("\n#####               OUTPUTS               #####")
    out_txt_file.write("\n###############################################")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nAircraft: " + NAME)
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\n")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nAircraft Geometry Values used------------------")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nWing Span [m]: " + str(round(max(awg.wing_span), 3)))
    out_txt_file.write("\nWing Area [m^2]: " + str(round(awg.wing_plt_area_main, 3)))
    out_txt_file.write("\nCabin Area [m^2]: " + str(round(awg.cabin_area, 3)))
    out_txt_file.write("\nThe aircraft has: " + str(FLOORS_NB) + "floor(s)")
    out_txt_file.write("\n")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nResults ---------------------------------------")
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nSeating estimation ----------------------------")
    out_txt_file.write("\nNumber of passengers: " + str(out.pass_nb))
    out_txt_file.write("\nNumber of toilet: " + str(int(out.toilet_nb)))
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nSuggested crew members ------------------------")
    out_txt_file.write("\nTotal crew members: " + str(out.crew_nb))
    out_txt_file.write("\nNumber of cabin crew members: " + str(out.cabin_crew_nb))
    out_txt_file.write("\nNumber of pilots: " + str(PILOT_NB))
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nEngine estimation -----------------------------")
    out_txt_file.write("\nNumber of engines: " + str(ed.NE))
    out_txt_file.write("\nSingle engine mass [kg]: " + str(int(ed.en_mass)))
    out_txt_file.write(
        "\nSingle engine maximum take off thrust [kN]: " + str(int(round(ed.max_thrust, 0)))
    )
    out_txt_file.write(
        "\nThrust specific fuel consumption in cruise [1/hr]:" + str(ed.TSFC_CRUISE)
    )
    out_txt_file.write("\n-----------------------------------------------")
    out_txt_file.write("\nMasses estimation -----------------------------")
    out_txt_file.write("\nSystems mass [kg]: " + str(int(round(mw.mass_systems))))
    out_txt_file.write("\nStructure mass [kg]: " + str(int(round(mw.mass_structure))))
    out_txt_file.write("\nEngines mass [kg]: " + str(int(round(mw.mass_engines))))
    out_txt_file.write("\nMaximum payload mass [kg]: " + str(int(round(mw.mass_payload))))
    out_txt_file.write("\nMaximum passengers mass [kg]: " + str(int(round(mw.mass_pass))))
    out_txt_file.write(
        "\nMaximum fuel mass with max passengers [kg]: " + str(int(round(mw.mass_fuel_maxpass)))
    )
    out_txt_file.write(
        "\nMaximum fuel mass with no passengers [kg]: " + str(int(round(mw.mass_fuel_max)))
    )
    out_txt_file.write(
        "\nMaximum fuel volume with no passengers [l]: "
        + str(int(round(mw.mass_fuel_max / 0.8, 3)))
    )
    out_txt_file.write(
        "\nMaximum take off mass [kg]: " + str(int(round(mw.maximum_take_off_mass)))
    )
    out_txt_file.write("\nOperating empty mass [kg]: " + str(int(round(mw.operating_empty_mass))))
    out_txt_file.write("\nZero fuel mass [kg]: " + str(int(round(mw.zero_fuel_mass))))
    out_txt_file.write("\nWing loading [kg/m^2]: " + str(int(round(out.wing_loading))))
    out_txt_file.write("\n-----------------------------------------------")

    out_txt_file.close()

    return ()


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":

    print("########################################################")
    print("# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #")
    print("########################################################")
