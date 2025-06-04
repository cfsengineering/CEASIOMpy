"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Output text and plot generation function.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-11-21

"""

# =============================================================================
#   IMPORTS
# =============================================================================

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt


# =============================================================================
#   FUNCTIONS
# =============================================================================


def output_txt(out, mw, bi, NAME):
    """Function that generate the output text file for the Weight_and_Balance
    program.

    INPUT
    (class) out     --Arg.: BalanceOutput class.
    (class) mw      --Arg.: MassesWeights class.
    (class) bi      --Arg.: BalanceInputs class.
    ##======= Classes are defined in the Input_classes folder =======##
    (char) NAME     --Arg.: Name of the Aircraft


    OUTPUT
    (file) Balance_module.out --Out.: Text file containing all the
                                      informations estimated from the
                                      code.
    """
    out_name = "ToolOutput/" + NAME + "/" + NAME + "_Balance_module.out"

    OutputTextFile = open(out_name, "w")
    OutputTextFile.write("###############################################")
    OutputTextFile.write("\n###### AIRCRAFT BALANCE ESTIMATION MODULE #####")
    OutputTextFile.write("\n#####               OUTPUTS               #####")
    OutputTextFile.write("\n###############################################")
    OutputTextFile.write("\n-----------------------------------------------")
    OutputTextFile.write("\nInput data used -------------------------------")
    OutputTextFile.write("\n-----------------------------------------------")
    if bi.USER_CASE:
        OutputTextFile.write("\nUser case option: True")
        OutputTextFile.write("\nChosen Fuel Percentage: " + str(bi.F_PERC))
        OutputTextFile.write("\nChosen Payload Percentage: " + str(bi.P_PERC))
    else:
        OutputTextFile.write("\nUser case option: False")
    OutputTextFile.write("\nEngine in the back: " + str(not bi.WING_MOUNTED))
    OutputTextFile.write("\n")
    OutputTextFile.write("\n-----------------------------------------------")
    OutputTextFile.write("\nMass data -------------------------------------")
    OutputTextFile.write("\n-----------------------------------------------")
    OutputTextFile.write("\nMaximum payload mass [kg]: " + str(int(round(mw.mass_payload))))
    OutputTextFile.write(
        "\nMaximum fuel mass with no passengers [kg]: " + str(int(round(mw.mass_fuel_max)))
    )
    OutputTextFile.write(
        "\nMaximum take off mass [kg]: " + str(int(round(mw.maximum_take_off_mass)))
    )
    OutputTextFile.write(
        "\nOperating empty mass [kg]: " + str(int(round(mw.operating_empty_mass)))
    )
    OutputTextFile.write(
        "\nMaximum fuel mass with max passengers [kg]: " + str(int(round(mw.mass_fuel_maxpass)))
    )
    OutputTextFile.write("\n")
    OutputTextFile.write("\n-----------------------------------------------")
    OutputTextFile.write("\nResults ---------------------------------------")
    OutputTextFile.write("\n-----------------------------------------------")
    OutputTextFile.write("\n")
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nCenter of Gravity coordinates -------------" + "----")
    OutputTextFile.write("\nMax Payload configuration -----------------" + "----")
    OutputTextFile.write("\n[x, y, z]: " + str(out.center_of_gravity))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nZero Fuel configuration -------------------" + "----")
    OutputTextFile.write("\n[x, y, z]: " + str(out.cg_zfm))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nZero Payload configuration ----------------" + "----")
    OutputTextFile.write("\n[x, y, z]: " + str(out.cg_zpm))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nOEM configuration -------------------------" + "----")
    OutputTextFile.write("\n[x, y, z]: " + str(out.cg_oem))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    if bi.USER_CASE:
        OutputTextFile.write("\nUser configuration --------------------" + "--------")
        OutputTextFile.write("\n[x, y, z]: " + str(out.cg_user))
        OutputTextFile.write("\n---------------------------------------" + "--------")
    OutputTextFile.write("\n")
    OutputTextFile.write("\nMoment of Inertia ---------------------------" + "----")
    OutputTextFile.write("\nLumped mass Inertia -----------------------" + "----")
    OutputTextFile.write("\nMax Payload configuration -----------------" + "----")
    OutputTextFile.write("\nRoll moment, Ixx [kgm^2]: " + str(int(round(out.Ixx_lump))))
    OutputTextFile.write("\nPitch moment, Iyy [kgm^2]: " + str(int(round(out.Iyy_lump))))
    OutputTextFile.write("\nYaw moment, Izz [kgm^2]: " + str(int(round(out.Izz_lump))))
    OutputTextFile.write("\nIxy moment [kgm^2]: " + str(int(round(out.Ixy_lump))))
    OutputTextFile.write("\nIyz moment [kgm^2]: " + str(int(round(out.Iyz_lump))))
    OutputTextFile.write("\nIxz moment [kgm^2]: " + str(int(round(out.Ixz_lump))))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nZero Fuel configuration -------------------" + "----")
    OutputTextFile.write("\nRoll moment, Ixx [kgm^2]: " + str(int(round(out.Ixx_lump_zfm))))
    OutputTextFile.write("\nPitch moment, Iyy [kgm^2]: " + str(int(round(out.Iyy_lump_zfm))))
    OutputTextFile.write("\nYaw moment, Izz [kgm^2]: " + str(int(round(out.Izz_lump_zfm))))
    OutputTextFile.write("\nIxy moment [kgm^2]: " + str(int(round(out.Ixy_lump_zfm))))
    OutputTextFile.write("\nIyz moment [kgm^2]: " + str(int(round(out.Iyz_lump_zfm))))
    OutputTextFile.write("\nIxz moment [kgm^2]: " + str(int(round(out.Ixz_lump_zfm))))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nZero Payload configuration ----------------" + "----")
    OutputTextFile.write("\nRoll moment, Ixx [kgm^2]: " + str(int(round(out.Ixx_lump_zpm))))
    OutputTextFile.write("\nPitch moment, Iyy [kgm^2]: " + str(int(round(out.Iyy_lump_zpm))))
    OutputTextFile.write("\nYaw moment, Izz [kgm^2]: " + str(int(round(out.Izz_lump_zpm))))
    OutputTextFile.write("\nIxy moment [kgm^2]: " + str(int(round(out.Ixy_lump_zpm))))
    OutputTextFile.write("\nIyz moment [kgm^2]: " + str(int(round(out.Iyz_lump_zpm))))
    OutputTextFile.write("\nIxz moment [kgm^2]: " + str(int(round(out.Ixz_lump_zpm))))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nOEM configuration -------------------------" + "----")
    OutputTextFile.write("\nRoll moment, Ixx [kgm^2]: " + str(int(round(out.Ixx_lump_oem))))
    OutputTextFile.write("\nPitch moment, Iyy [kgm^2]: " + str(int(round(out.Iyy_lump_oem))))
    OutputTextFile.write("\nYaw moment, Izz [kgm^2]: " + str(int(round(out.Izz_lump_oem))))
    OutputTextFile.write("\nIxy moment [kgm^2]: " + str(int(round(out.Ixy_lump_oem))))
    OutputTextFile.write("\nIyz moment [kgm^2]: " + str(int(round(out.Iyz_lump_oem))))
    OutputTextFile.write("\nIxz moment [kgm^2]: " + str(int(round(out.Ixz_lump_oem))))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    if bi.USER_CASE:
        OutputTextFile.write("\nUser configuration --------------------" + "--------")
        OutputTextFile.write("\nRoll moment, Ixx [kgm^2]: " + str(int(round(out.Ixx_lump_user))))
        OutputTextFile.write("\nPitch moment, Iyy [kgm^2]: " + str(int(round(out.Iyy_lump_user))))
        OutputTextFile.write("\nYaw moment, Izz [kgm^2]: " + str(int(round(out.Izz_lump_user))))
        OutputTextFile.write("\nIxy moment [kgm^2]: " + str(int(round(out.Ixy_lump_user))))
        OutputTextFile.write("\nIyz moment [kgm^2]: " + str(int(round(out.Iyz_lump_user))))
        OutputTextFile.write("\nIxz moment [kgm^2]: " + str(int(round(out.Ixz_lump_user))))
        OutputTextFile.write("\n---------------------------------------" + "--------")
    # Closing Text File
    OutputTextFile.close()


# =============================================================================
#   PLOTS
# =============================================================================


def aircraft_nodes_plot(fx, fy, fz, wx, wy, wz, NAME):
    """The function unction generates the plot of the aircraft nodes.
    INPUT
    (float_array) fx      --Arg.: Array containing the x-coordinates
                                  of the fuselage nodes.
    (float_array) fy      --Arg.: Array containing the y-coordinates
                                  of the fuselage nodes.
    (float_array) fz      --Arg.: Array containing the z-coordinates
                                  of the fuselage nodes.
    (float_array) wx      --Arg.: Array containing the x-coordinates
                                  of the wing nodes.
    (float_array) wy      --Arg.: Array containing the y-coordinates
                                  of the wing nodes.
    (float_array) wz      --Arg.: Array containing the z-coordinates
                                  of the wing nodes.
    (char) NAME           --Arg.: Aircraft name.
    OUTPUT
    (file)NAME_Aircraft_Nodes.png --Out.: Png file containing all the
                                          aircraft nodes plot.
    """
    fig = plt.figure()
    mpl.rcParams.update({"font.size": 20})
    ax = fig.add_subplot(111, projection="3d")
    ax.plot(
        [fx[0]],
        [fy[0]],
        [fz[0]],
        c="g",
        marker="o",
        label="Fuselage nodes",
        markersize=10,
    )
    ax.plot([wx[0]], [wy[0]], [wz[0]], c="b", marker="o", label="Wing nodes", markersize=10)
    # s1 = ax.scatter(fx, fy, fz, c="g", marker="o", s=100 * np.ones((np.max(np.shape(fx)))))
    # s2 = ax.scatter(wx, wy, wz, c="b", marker="o", s=100 * np.ones((np.max(np.shape(wx)))))
    ax.set_ylim3d(np.min(wy) - 5, np.max(wy) + 5)
    ax.set_xlim3d(np.min(fx) - 10, np.max(fx) + 10)
    ax.set_zlim3d(np.min(wz) - 5, np.max(wz) + 5)
    ax.set_xlabel("X Label")
    ax.set_ylabel("Y Label")
    ax.set_zlabel("Z Label")
    ax.legend(numpoints=1, loc="upper right")
    FIG_NAME = "ToolOutput/" + NAME + "/" + NAME + "_Aircraft_Nodes.png"
    fig.savefig(FIG_NAME, dpi=300)


# AIRCRAFT CoG PLOT --------------------------------------------------------


def aircraft_cog_plot(cg, ag, NAME):
    """The function generates the plot of the aircraf center of gravity and
    the nodes used to evaluate it.

    INPUT
    (float_array) cg --Arg.: Center of gravity global coordinates [m].
    (class) ag       --Arg.: Aircraft geometry class.
    (char) NAME      --Arg.: Aircraft name.

    ##======= Class are defined in the InputClasses folder =======##

    OUTPUT
    (file)NAME_Aircraft_Cog.png --Out.: Png file containing the center
                                        of gravity and the nodes used
                                        to evaluate it.
    """
    fig = plt.figure()
    fig.patch.set_facecolor("w")
    mpl.rcParams.update({"font.size": 16})
    cx = cg[0]
    cy = cg[1]
    cz = cg[2]
    ax = fig.add_subplot(111, projection="3d")
    wx = []
    wy = []
    wz = []
    fx = ag.fuse_center_seg_point[:, :, 0]
    # fy = ag.fuse_center_seg_point[:, :, 1]
    # fz = ag.fuse_center_seg_point[:, :, 2]
    for i in range(1, ag.wing_nb + 1):
        for j in range(1, np.max(ag.wing_seg_nb) + 1):
            if ag.wing_center_seg_point[j - 1, i - 1, 0] != 0.0:
                wx.append(ag.wing_center_seg_point[j - 1, i - 1, 0])
                wy.append(ag.wing_center_seg_point[j - 1, i - 1, 1])
                wz.append(ag.wing_center_seg_point[j - 1, i - 1, 2])
    wplot1 = wx[0]
    wplot2 = wy[0]
    wplot3 = wz[0]
    ax.plot(
        [ag.fuse_center_seg_point[0, 0, 0]],
        [ag.fuse_center_seg_point[0, 0, 1]],
        [ag.fuse_center_seg_point[0, 0, 2]],
        "og",
        label="Fuselage nodes",
        markersize=10,
    )
    ax.plot([wplot1], [wplot2], [wplot3], "ob", label="Wing nodes", markersize=10)
    ax.plot([cx], [cy], [cz], "xr", label="Center of Gravity", markersize=10)
    # s1 = ax.scatter([fx], [fy], [fz], c="g", marker="o", s=100 * np.ones((np.max(np.shape(fx)))))
    ax.scatter([wx], [wy], [wz], c="b", marker="o", s=100 * np.ones((np.max(np.shape(wx)))))
    ax.scatter([cx], [cy], [cz], c="r", marker="x", s=100)
    ax.set_ylim3d(np.min(wy) - 5, np.max(wy) + 5)
    ax.set_xlim3d(np.min(fx) - 10, np.max(fx) + 10)
    ax.set_zlim3d(np.min(wz) - 5, np.max(wz) + 5)
    ax.set_xlabel("X Label")
    ax.set_ylabel("Y Label")
    ax.set_zlabel("Z Label")
    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.1, 1.1),
        fancybox=True,
        shadow=True,
        ncol=1,
        numpoints=1,
    )
    FIG_NAME = "ToolOutput/" + NAME + "/" + NAME + "_Aircraft_Cog.png"
    fig.savefig(FIG_NAME, dpi=500)
