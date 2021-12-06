"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script generates the output txt file from the geometry analysis
of an unconventional aircraft.

Python version: >=3.6

| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2020-01-21 (AJ)

"""

# =============================================================================
#   IMPORTS
# =============================================================================

""" No imports """


# =============================================================================
#   CLASSES
# =============================================================================

"""All classes are defined inside the classes and into
   the InputClasses/Unconventional folder."""


# =============================================================================
#   FUNCTIONS
# =============================================================================


def produce_wing_output_txt(awg, NAME):
    """ Function to generate the output file with all the geometry data
        evaluated for the aircraft built without fuselage.

    Args:
        awg (class): AircraftWingGeometry class
                     (look at aircraft_geometry_class.py in the classes folder for explanation)
        NAME (str): Name of the aircraft.

    Returns:
        OutputTextFile (file) : Output txt file
    """

    out_name = "ToolOutput/" + NAME + "/" + NAME + "_Aircraft_Geometry.out"
    OutputTextFile = open(out_name, "w")

    OutputTextFile.write("\n#################################################")
    OutputTextFile.write("\n######  UNCONVENTIONAL AIRCRAFT GEOMETRY   ######")
    OutputTextFile.write("\n######      ESTIMATION MODULE OUTPUTS      ######")
    OutputTextFile.write("\n#################################################")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nAircraft: " + NAME)
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nGeometry Evaluations---- ------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nUSEFUL INFO -------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write(
        "\nIf the wing number is greater than 1, the\n"
        + "informations of each object are listed in an "
        + "array ordered\nprogressively"
    )
    OutputTextFile.write(
        "\nSymmetry output: 0 = no symmetry, 1 =  x-y,\n" + "2 = x-z, 3 = y-z planes"
    )
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nRESULTS -----------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nWINGS -------------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nNumber of Wings [-]: " + str(awg.wing_nb))
    OutputTextFile.write("\nWing symmetry plane [-]: " + str(awg.wing_sym))
    OutputTextFile.write("\nNumber of wing sections [-]: " + str(awg.wing_sec_nb))
    OutputTextFile.write("\nNumber of wing segments [-]: " + str(awg.wing_seg_nb))
    OutputTextFile.write("\nWingd Span [m]: " + str(awg.wing_span))
    OutputTextFile.write("\nWing MAC length [m]: " + str(awg.wing_mac[0, ]))
    OutputTextFile.write("\nWing MAC x,y,z coordinate [m]: \n" + str(awg.wing_mac[1:4, ]))
    OutputTextFile.write("\nWings sections thickness [m]:\n" + str(awg.wing_sec_thicknes))
    OutputTextFile.write("\nWings sections mean thickness [m]:\n" + str(awg.wing_sec_mean_thick))
    OutputTextFile.write("\nWing segments length [m]:\n " + str(awg.wing_seg_length))
    OutputTextFile.write("\nWing max chord length [m]: " + str(awg.wing_max_chord))
    OutputTextFile.write("\nWing min chord length [m]: " + str(awg.wing_min_chord))
    OutputTextFile.write("\nWings planform area [m^2]: " + str(awg.wing_plt_area))
    OutputTextFile.write("\nMain wing wetted surface [m^2]: " + str(awg.main_wing_surface))
    OutputTextFile.write("\nTail wings wetted surface [m^2]: " + str(awg.tail_wings_surface))
    OutputTextFile.write("\nMain wing planform area [m^2]: " + str(awg.wing_plt_area_main))
    OutputTextFile.write("\nCabin area [m^2]: " + str(awg.cabin_area))
    OutputTextFile.write("\nVolume of each wing [m^3]: " + str(awg.wing_vol))
    OutputTextFile.write("\nTotal wing volume [m^3]: " + str(awg.wing_tot_vol))
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nWINGS VOLUMES -----------------------------------")
    OutputTextFile.write("\nCabin volume [m^3]: " + str(awg.cabin_vol))
    OutputTextFile.write("\nVolume of the wing as fuselage [m^3]: " + str(awg.fuse_vol))
    OutputTextFile.write(
        "\nVolume of the remaining portion of the wing [m^3]: " + str(awg.wing_vol)
    )
    OutputTextFile.write("\nFuel volume in the fuselage wing [m^3]: " + str(awg.fuse_fuel_vol))
    OutputTextFile.write("\nFuel volume in the wing [m^3]: " + str(awg.wing_fuel_vol))
    OutputTextFile.write("\nTotal fuel Volume [m^3]: " + str(awg.fuel_vol_tot))
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")

    # Close Text File
    OutputTextFile.close()

    return ()


def produce_geom_output_txt(afg, awg, NAME):
    """ Function to generate the output file with all the geometry data
        evaluated  for the aircraft built with 1 or more fuselage.

    Args:
        afg (class): Aircraft_geometry class or 0 otherwise.
        awg (class): AircraftWingGeometry class
                     (look at aircraft_geometry_class.py in the classes folder for explanation)
        NAME (str): Name of the aircraft.

    Returns:
        OutputTextFile (file) : Output txt file

    """

    out_name = "ToolOutput/" + NAME + "/" + NAME + "_Aircraft_Geometry.out"
    OutputTextFile = open(out_name, "w")

    OutputTextFile.write("#################################################")
    OutputTextFile.write("\n######  UNCONVENTIONAL AIRCRAFT GEOMETRY   ######")
    OutputTextFile.write("\n######      ESTIMATION MODULE OUTPUTS      ######")
    OutputTextFile.write("\n#################################################")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nAircraft: " + NAME)
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nGeometry Evaluations---- ------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nUSEFUL INFO -------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write(
        "\nIf fuselage or wing number is greater than 1,"
        " the\n"
        "informations of each object are listed in an\n"
        "array ordered progressively"
    )
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nRESULTS -----------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nFUSELAGES ---------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nNumber of fuselages [-]: " + str(afg.fuse_nb))
    OutputTextFile.write("\nNumber of fuselage sections [-]: " + str(afg.fuse_sec_nb))
    OutputTextFile.write("\nNumber of fuselage segments [-]: " + str(afg.fuse_seg_nb))
    OutputTextFile.write("\nCabin segments array [-]:\n" + str(afg.cabin_seg))
    OutputTextFile.write("\nFuse Length [m]: " + str(afg.fuse_length))
    OutputTextFile.write("\nFuse nose Length [m]: " + str(afg.fuse_nose_length))
    OutputTextFile.write("\nFuse cabin Length [m]: " + str(afg.fuse_cabin_length))
    OutputTextFile.write("\nFuse tail Length [m]: " + str(afg.fuse_tail_length))
    OutputTextFile.write("\nAircraft Length [m]: " + str(afg.tot_length))
    OutputTextFile.write(
        "\nPerimeter of each section of each fuselage [m]: \n" + str(afg.fuse_sec_per)
    )
    OutputTextFile.write(
        "\nRelative distance of each section of the fuselage, \
                          respect to the first one [m]: \n"
        + str(afg.fuse_sec_rel_dist)
    )
    OutputTextFile.write(
        "\nLength of each section of each fuselage [m]: \n" + str(afg.fuse_seg_length)
    )
    OutputTextFile.write("\nMean fuselage width [m]: " + str(afg.fuse_mean_width))
    OutputTextFile.write(
        "\nWidth of each section of each fuselage [m]: \n" + str(afg.fuse_sec_width)
    )
    OutputTextFile.write(
        "\nHeight of each section of each fuselage [m]: \n" + str(afg.fuse_sec_height)
    )
    OutputTextFile.write("\nCabin area [m^2]: " + str(afg.cabin_area))
    OutputTextFile.write("\nFuselages wetted surface [m^2]: " + str(afg.fuse_surface))
    OutputTextFile.write(
        "\nVolume of all the segmetns of each fuselage " + "[m^3]: \n" + str(afg.fuse_seg_vol)
    )
    OutputTextFile.write("\nVolume of each cabin [m^3]: " + str(afg.fuse_cabin_vol))
    OutputTextFile.write("\nVolume of each fuselage [m^3]: " + str(afg.fuse_vol))
    OutputTextFile.write("\nFuel Volume in each fuselage [m^3]: " + str(afg.fuse_fuel_vol))
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nWINGS -------------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nNumber of Wings [-]: " + str(awg.wing_nb))
    OutputTextFile.write("\nWing symmetry plane [-]: " + str(awg.wing_sym))
    OutputTextFile.write(
        "\nNumber of wing sections (not counting symmetry) [-]: " + str(awg.wing_sec_nb)
    )
    OutputTextFile.write(
        "\nNumber of wing segments (not counting symmetry) [-]: " + str(awg.wing_seg_nb)
    )
    OutputTextFile.write("\nWingd Span [m]: " + str(awg.wing_span))
    OutputTextFile.write("\nWing MAC length [m]: " + str(awg.wing_mac[0, ]))
    OutputTextFile.write("\nWing MAC x,y,z coordinate [m]: \n" + str(awg.wing_mac[1:4, ]))
    OutputTextFile.write("\nWings sections thickness [m]:\n" + str(awg.wing_sec_thicknes))
    OutputTextFile.write("\nWings sections mean thickness [m]:\n" + str(awg.wing_sec_mean_thick))
    OutputTextFile.write("\nWing segments length [m]:\n " + str(awg.wing_seg_length))
    OutputTextFile.write("\nWing max chord length [m]: " + str(awg.wing_max_chord))
    OutputTextFile.write("\nWing min chord length [m]: " + str(awg.wing_min_chord))
    OutputTextFile.write("\nWings planform area [m^2]: " + str(awg.wing_plt_area))
    OutputTextFile.write("\nMain wing wetted surface [m^2]: " + str(awg.main_wing_surface))
    OutputTextFile.write("\nTail wings wetted surface [m^2]: " + str(awg.tail_wings_surface))
    OutputTextFile.write("\nMain wing planform area [m^2]: " + str(awg.wing_plt_area_main))
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nWINGS VOLUMES -----------------------------------")
    OutputTextFile.write("\nVolume of each wing [m^3]: " + str(awg.wing_vol))
    OutputTextFile.write("\nTotal wing volume [m^3]: " + str(awg.wing_tot_vol))
    OutputTextFile.write("\nWing volume for fuel storage [m^3]: " + str(awg.wing_fuel_vol))
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")

    # Close Text File
    OutputTextFile.close()
    return ()


# =============================================================================
#   MAIN
# ==============================================================================

if __name__ == "__main__":

    print("#######################################################")
    print("#ERROR NOT A STANDALONE PROGRAM, RUN balanceuncmain.py#")
    print("#######################################################")
