"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This file will generate the output.txt for the geometry analysis.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-09-27

"""


# =============================================================================
#   IMPORTS
# =============================================================================

import numpy as np


# =============================================================================
#   CLASSES
# =============================================================================

"""All classes are defined inside the InputClasses/Conventional"""


# =============================================================================
#   FUNCTIONS
# =============================================================================


def produce_output_txt(ag, NAME):
    """Function to generate the output file with all the geometry data
        evaluated.

    ARGUMENTS
    (class) ag            --Arg.: AircraftGeometry class.
    # ======= Class is defined in the InputClasses folder =======##
    (char) NAME           --Arg.: Name of the aircraft.
    RETURN
    (file) OutputTextFile --Out.: Output txt file
    """

    out_name = "ToolOutput/" + NAME + "/" + NAME + "_Aircraft_Geometry.out"
    OutputTextFile = open(out_name, "w")

    OutputTextFile.write("\n#################################################")
    OutputTextFile.write("\n###### AIRCRAFT GEOMETRY EVALUATION MODULE ######")
    OutputTextFile.write("\n######               OUTPUTS               ######")
    OutputTextFile.write("\n#################################################")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nAircraft: " + NAME)
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nGeometry Evaluations-----------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nUSEFUL INFO -------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write(
        "\nIf fuselage or wing number is greater than 1 the\n"
        "informations of each obj are listed in an "
        "array ordered\nprogressively"
    )
    OutputTextFile.write(
        "\nSymmetry output: 0 = no symmetry, 1 =  x-y,\n" + "2 = x-z, 3 = y-z planes"
    )
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nRESULTS -----------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nFUSELAGE ----------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nNumber of fuselage sections [-]: " + str(ag.fuse_sec_nb))
    OutputTextFile.write("\nNumber of fuselage segments [-]: " + str(ag.fuse_seg_nb))
    OutputTextFile.write("\nCabin segments array [-]: " + str(ag.cabin_seg))
    OutputTextFile.write("\nFuse Length [m]: " + str(np.around(ag.fuse_length, 5)))
    OutputTextFile.write("\nFuse nose Length [m]: " + str(np.around(ag.fuse_nose_length, 5)))
    OutputTextFile.write("\nFuse cabin Length [m]: " + str(np.around(ag.fuse_cabin_length, 5)))
    OutputTextFile.write("\nFuse tail Length [m]: " + str(np.around(ag.fuse_tail_length, 5)))
    OutputTextFile.write("\nAircraft Length [m]: " + str(np.around(ag.tot_length, 5)))
    OutputTextFile.write(
        "\nCircumference of each section of the fuselage "
        "[m]: \n" + str(np.around(ag.fuse_sec_circ, 5))
    )
    OutputTextFile.write(
        "\nRelative distance of each section of the"
        + "fuselage, respect to the first one [m]: \n"
        + str(np.around(ag.fuse_sec_rel_dist, 5))
    )
    OutputTextFile.write(
        "\nLength of each segment of the fuselage [m]: \n" + str(np.around(ag.fuse_seg_length, 5))
    )
    OutputTextFile.write("\nMean fuselage width [m]: " + str(np.around(ag.fuse_mean_width, 5)))
    OutputTextFile.write(
        "\nWidth of each section of the fuselage [m]: \n" + str(np.around(ag.fuse_sec_width, 5))
    )
    OutputTextFile.write(
        "\nVolume of each segment of the fuselage "
        "[m^3]: \n" + str(np.around(ag.fuse_seg_vol, 5))
    )
    OutputTextFile.write("\nVolume of the cabin [m^3]: " + str(np.around(ag.fuse_cabin_vol, 5)))
    OutputTextFile.write("\nVolume of the fuselage [m^3]: " + str(np.around(ag.fuse_vol, 5)))
    OutputTextFile.write("\n")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nWINGS -------------------------------------------")
    OutputTextFile.write("\n-------------------------------------------------")
    OutputTextFile.write("\nNumber of Wings [-]: " + str(ag.wing_nb))
    OutputTextFile.write("\nWing symmetry plane [-]: " + str(ag.wing_sym))
    OutputTextFile.write("\nNumber of wing sections [-]: " + str(ag.wing_sec_nb))
    OutputTextFile.write("\nNumber of wing segments [-]: " + str(ag.wing_seg_nb))
    OutputTextFile.write("\nWing Span [m]: \n" + str(np.around(ag.wing_span, 5)))
    OutputTextFile.write(
        "\nWing MAC length [m]: \n"
        + str(
            np.around(
                ag.wing_mac[
                    0,
                ],
                5,
            )
        )
    )
    OutputTextFile.write(
        "\nWing MAC x,y,z coordinate [m]: \n"
        + str(
            np.around(
                ag.wing_mac[
                    1:4,
                ],
                5,
            )
        )
    )
    OutputTextFile.write(
        "\nWings sections thicknes [m]: \n" + str(np.around(ag.wing_sec_thicknes, 5))
    )
    OutputTextFile.write(
        "\nWings sections mean thicknes [m]: \n" + str(np.around(ag.wing_sec_mean_thick, 5))
    )
    OutputTextFile.write("\nWing segments length [m]: \n" + str(np.around(ag.wing_seg_length, 5)))
    OutputTextFile.write("\nWing max chord length [m]: \n" + str(np.around(ag.wing_max_chord, 5)))
    OutputTextFile.write("\nWing min chord length [m]: \n" + str(np.around(ag.wing_min_chord, 5)))
    OutputTextFile.write("\nWings planform area [m^2]: \n" + str(np.around(ag.wing_plt_area, 5)))
    OutputTextFile.write(
        "\nMain wing planform area [m^2]: " + str(np.around(ag.wing_plt_area_main, 5))
    )
    OutputTextFile.write("\nVolume of each wing [m^3]: \n" + str(np.around(ag.wing_vol, 5)))
    OutputTextFile.write("\nTotal wing volume [m^3]: " + str(np.around(ag.wing_tot_vol, 5)))
    OutputTextFile.write("\nWing volume for fuel storage [m^3]: " + str(ag.wing_fuel_vol))

    # Close Text File
    OutputTextFile.close()

    return ()


# =============================================================================
#   MAIN
# ==============================================================================

if __name__ == "__main__":
    print("##########################################################")
    print("############# ERROR NOT A STANDALONE PROGRAM #############")
    print("##########################################################")
