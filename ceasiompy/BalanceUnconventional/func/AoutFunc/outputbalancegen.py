"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Output text and plot generation functions.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-11-21
| Last modifiction: 2019-02-20
"""


# =============================================================================
#   IMPORTS
# =============================================================================

import numpy as np
import math
import matplotlib as mpl
from matplotlib import rcParams
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt


# =============================================================================
#   CLASSES
# =============================================================================

"""All classes are defined inside the classes folder and into the
   InputClasses/Uconventional folder"""


# =============================================================================
#   FUNCTIONS
# =============================================================================


def output_txt(bout, mw, bi, ec, NAME):
    """ The function generates the output text file for the unconventional
        balance analysis.

        INPUT
        (class) bout     --Arg.: BalanceOutput class.
        (class) mw      --Arg.: MassesWeights class.
        (class) bi      --Arg.: BalanceInputs class.
        ##======= Classes are defined in the InputClasses folder =======##
        (char) NAME     --Arg.: Name of the Aircraft

        OUTPUT
        (file) Balance_module.out --Out.: Text file containing all the
                                          informations estimated from the
                                          code.
    """
    out_name = "ToolOutput/" + NAME + "/" + NAME + "_Balance_unc_module.out"

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
    OutputTextFile.write("\nEngine in the back: " + str(not ec.WING_MOUNTED))
    OutputTextFile.write("\n")
    OutputTextFile.write("\n-----------------------------------------------")
    OutputTextFile.write("\nMass data -------------------------------------")
    OutputTextFile.write("\n-----------------------------------------------")
    OutputTextFile.write("\nMaximum payload mass [kg]: " + str(int(mw.mass_payload)))
    OutputTextFile.write(
        "\nMaximum fuel mass with no passengers [kg]: " + str(int(mw.mass_fuel_tot))
    )
    OutputTextFile.write("\nMaximum take off mass [kg]: " + str(int(mw.maximum_take_off_mass)))
    OutputTextFile.write("\nOperating empty mass [kg]: " + str(int(mw.operating_empty_mass)))
    OutputTextFile.write(
        "\nMaximum fuel mass with max passengers [kg]: " + str(int(mw.mass_fuel_maxpass))
    )
    OutputTextFile.write("\n")
    OutputTextFile.write("\n-----------------------------------------------")
    OutputTextFile.write("\nResults ---------------------------------------")
    OutputTextFile.write("\n-----------------------------------------------")
    OutputTextFile.write("\n")
    OutputTextFile.write("\nCenter of Gravity coordinates -------------" + "----")
    OutputTextFile.write("\nMax Payload configuration -----------------" + "----")
    OutputTextFile.write("\n[x, y, z]: " + str(bout.center_of_gravity))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nZero Fuel configuration -------------------" + "----")
    OutputTextFile.write("\n[x, y, z]: " + str(bout.cg_zfm))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nZero Payload configuration ----------------" + "----")
    OutputTextFile.write("\n[x, y, z]: " + str(bout.cg_zpm))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nOEM configuration -------------------------" + "----")
    OutputTextFile.write("\n[x, y, z]: " + str(bout.cg_oem))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    if bi.USER_CASE:
        OutputTextFile.write("\nUser configuration --------------------" + "--------")
        OutputTextFile.write("\n[x, y, z]: " + str(bout.cg_user))
        OutputTextFile.write("\n---------------------------------------" + "--------")
    if bi.USER_EN_PLACEMENT:
        OutputTextFile.write("\n---------------- Engine Inertia ------------" + "---")
        OutputTextFile.write("\nRoll moment, Ixx [kgm^2]: " + str(int(round(bout.Ixxen))))
        OutputTextFile.write("\nPitch moment, Iyy [kgm^2]: " + str(int(round(bout.Iyyen))))
        OutputTextFile.write("\nYaw moment, Izz [kgm^2]: " + str(int(round(bout.Izzen))))
        OutputTextFile.write("\nIxy moment [kgm^2]: " + str(int(round(bout.Ixyen))))
        OutputTextFile.write("\nIyz moment [kgm^2]: " + str(int(round(bout.Iyzen))))
        OutputTextFile.write("\nIxz moment [kgm^2]: " + str(int(round(bout.Ixzen))))
        OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nMoment of Inertia -------------------------" + "----")
    OutputTextFile.write("\n-----------------------------------------------")
    OutputTextFile.write("\nLumped mass Inertia -----------------------" + "----")
    OutputTextFile.write("\nMax Payload configuration -----------------" + "----")
    OutputTextFile.write("\nRoll moment, Ixx [kgm^2]: " + str(int(round(bout.Ixx_lump))))
    OutputTextFile.write("\nPitch moment, Iyy [kgm^2]: " + str(int(round(bout.Iyy_lump))))
    OutputTextFile.write("\nYaw moment, Izz [kgm^2]: " + str(int(round(bout.Izz_lump))))
    OutputTextFile.write("\nIxy moment [kgm^2]: " + str(bout.Ixy_lump))
    OutputTextFile.write("\nIyz moment [kgm^2]: " + str(bout.Iyz_lump))
    OutputTextFile.write("\nIxz moment [kgm^2]: " + str(bout.Ixz_lump))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nZero Fuel configuration -------------------" + "----")
    OutputTextFile.write("\nRoll moment, Ixx [kgm^2]: " + str(int(round(bout.Ixx_lump_zfm))))
    OutputTextFile.write("\nPitch moment, Iyy [kgm^2]: " + str(int(round(bout.Iyy_lump_zfm))))
    OutputTextFile.write("\nYaw moment, Izz [kgm^2]: " + str(int(round(bout.Izz_lump_zfm))))
    OutputTextFile.write("\nIxy moment [kgm^2]: " + str(bout.Ixy_lump_zfm))
    OutputTextFile.write("\nIyz moment [kgm^2]: " + str(bout.Iyz_lump_zfm))
    OutputTextFile.write("\nIxz moment [kgm^2]: " + str(bout.Ixz_lump_zfm))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nZero Payload configuration ----------------" + "----")
    OutputTextFile.write("\nRoll moment, Ixx [kgm^2]: " + str(int(round(bout.Ixx_lump_zpm))))
    OutputTextFile.write("\nPitch moment, Iyy [kgm^2]: " + str(int(round(bout.Iyy_lump_zpm))))
    OutputTextFile.write("\nYaw moment, Izz [kgm^2]: " + str(int(round(bout.Izz_lump_zpm))))
    OutputTextFile.write("\nIxy moment [kgm^2]: " + str(bout.Ixy_lump_zpm))
    OutputTextFile.write("\nIyz moment [kgm^2]: " + str(bout.Iyz_lump_zpm))
    OutputTextFile.write("\nIxz moment [kgm^2]: " + str(bout.Ixz_lump_zpm))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    OutputTextFile.write("\nOEM configuration -------------------------" + "----")
    OutputTextFile.write("\nRoll moment, Ixx [kgm^2]: " + str(int(round(bout.Ixx_lump_oem))))
    OutputTextFile.write("\nPitch moment, Iyy [kgm^2]: " + str(int(round(bout.Iyy_lump_oem))))
    OutputTextFile.write("\nYaw moment, Izz [kgm^2]: " + str(int(round(bout.Izz_lump_oem))))
    OutputTextFile.write("\nIxy moment [kgm^2]: " + str(bout.Ixy_lump_oem))
    OutputTextFile.write("\nIyz moment [kgm^2]: " + str(bout.Iyz_lump_oem))
    OutputTextFile.write("\nIxz moment [kgm^2]: " + str(bout.Ixz_lump_oem))
    OutputTextFile.write("\n-------------------------------------------" + "----")
    if bi.USER_CASE:
        OutputTextFile.write("\nUser configuration --------------------" + "--------")
        OutputTextFile.write("\nRoll moment, Ixx [kgm^2]: " + str(int(round(bout.Ixx_lump_user))))
        OutputTextFile.write("\nPitch moment, Iyy [kgm^2]: " + str(int(round(bout.Iyy_lump_user))))
        OutputTextFile.write("\nYaw moment, Izz [kgm^2]: " + str(int(round(bout.Izz_lump_user))))
        OutputTextFile.write("\nIxy moment [kgm^2]: " + str(bout.Ixy_lump_oem))
        OutputTextFile.write("\nIyz moment [kgm^2]: " + str(bout.Iyz_lump_oem))
        OutputTextFile.write("\nIxz moment [kgm^2]: " + str(bout.Ixz_lump_oem))
        OutputTextFile.write("\n---------------------------------------" + "--------")

    ### Closing Text File
    OutputTextFile.close()
    return ()


# =============================================================================
#   PLOTS
# =============================================================================

### AIRCRAFT NODES PLOT ------------------------------------------------------
def aircraft_nodes_unc_plot(fx, fy, fz, wx, wy, wz, NAME):
    """The function generates the plot of the aircraft nodes.
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
       (file)Aircraft_Nodes.png --Out.: Png file containing all the
                                        aircraft nodes plot.
    """
    fig = plt.figure()
    mpl.rcParams.update({"font.size": 20})
    ax = fig.add_subplot(111, projection="3d")
    ax.plot([fx[0]], [fy[0]], [fz[0]], c="g", marker="o", label="Fuselage nodes", markersize=10)
    ax.plot([wx[0]], [wy[0]], [wz[0]], c="b", marker="o", label="Wing nodes", markersize=10)
    s1 = ax.scatter(fx, fy, fz, c="g", marker="o", s=100 * np.ones((np.max(np.shape(fx)))))
    s2 = ax.scatter(wx, wy, wz, c="b", marker="o", s=100 * np.ones((np.max(np.shape(wx)))))
    ax.set_ylim3d(np.min(wy) - 5, np.max(wy) + 5)
    ax.set_xlim3d(np.min(fx) - 10, np.max(fx) + 10)
    ax.set_zlim3d(np.min(wz) - 5, np.max(wz) + 5)
    ax.set_xlabel("X Label")
    ax.set_ylabel("Y Label")
    ax.set_zlabel("Z Label")
    ax.legend(numpoints=1, loc="upper right")
    FIG_NAME = "ToolOutput/" + NAME + "/" + NAME + "_Aircraft_Nodes.png"
    fig.savefig(FIG_NAME, dpi=500)

    return ()


def aircraft_nodes_bwb_plot(wx, wy, wz, NAME):
    """The function generates the plot of the aircraft nodes.
       INPUT
       (float_array) wx      --Arg.: Array containing the x-coordinates
                                     of the wing nodes.
       (float_array) wy      --Arg.: Array containing the y-coordinates
                                     of the wing nodes.
       (float_array) wz      --Arg.: Array containing the z-coordinates
                                     of the wing nodes.
       (char) NAME           --Arg.: Aircraft name.
       OUTPUT
       (file)Aircraft_Nodes.png --Out.: Png file containing all the
                                        aircraft nodes plot.
    """
    fig = plt.figure()
    mpl.rcParams.update({"font.size": 20})
    ax = fig.add_subplot(111, projection="3d")
    ax.plot([wx[0]], [wy[0]], [wz[0]], c="b", marker="o", label="Wing nodes", markersize=10)
    s = ax.scatter(wx, wy, wz, c="b", marker="o", s=100 * np.ones((np.max(np.shape(wx)))))
    ax.set_ylim3d(np.min(wy) - 5, np.max(wy) + 5)
    ax.set_xlim3d(np.min(wx) - 10, np.max(wx) + 10)
    ax.set_zlim3d(np.min(wz) - 5, np.max(wz) + 5)
    ax.set_xlabel("X Label")
    ax.set_ylabel("Y Label")
    ax.set_zlabel("Z Label")
    ax.legend(numpoints=1, loc="upper right")
    FIG_NAME = "ToolOutput/" + NAME + "/" + NAME + "_Aircraft_Nodes.png"
    fig.savefig(FIG_NAME, dpi=500)

    return ()


### AIRCRAFT CoG PLOT --------------------------------------------------------
def aircraft_cog_unc_plot(cg, bi, ed, afg, awg, NAME):
    """ The function generates the plot of the unconventional aircrafy
        center og gravity and the nodes used to evaluate it.

        INPUT
        (float_array) cg --Arg.: Center of gravity global coordinates [m].
        (class) bi       --Arg.: BalanceInputs class.
        (class) ed       --Arg.: EnineData class.
        ##======= Classes are defined in the Input_classes folder =======##
        (class) afg      --Arg.: AircraftFuseGeometry class.
        (class) awg      --Arg.: AircraftWingGeometry class.
        ##========== Classes are defined in the classes folder ==========##
        (char) NAME      --Arg.: Aircraft name.


        OUTPUT
        (file)Aircraft_Cog.png --Out.: Png file containing the center of gravity
                                       and the nodes used to evaluate it.
    """
    fig = plt.figure()
    fig.patch.set_facecolor("w")
    mpl.rcParams.update({"font.size": 12})
    cx = cg[0]
    cy = cg[1]
    cz = cg[2]
    ax = fig.add_subplot(111, projection="3d")
    wx = []
    wy = []
    wz = []
    fx = afg.fuse_center_seg_point[:, :, 0]
    fy = afg.fuse_center_seg_point[:, :, 1]
    fz = afg.fuse_center_seg_point[:, :, 2]
    for i in range(1, awg.wing_nb + 1):
        for j in range(1, np.max(awg.wing_seg_nb) + 1):
            if awg.wing_center_seg_point[j - 1, i - 1, 0] != 0.0:
                wx.append(awg.wing_center_seg_point[j - 1, i - 1, 0])
                wy.append(awg.wing_center_seg_point[j - 1, i - 1, 1])
                wz.append(awg.wing_center_seg_point[j - 1, i - 1, 2])
    wplot1 = wx[0]
    wplot2 = wy[0]
    wplot3 = wz[0]
    if bi.USER_EN_PLACEMENT:
        ax.plot(
            [ed.EN_PLACEMENT[0, 0]],
            [ed.EN_PLACEMENT[0, 1]],
            [ed.EN_PLACEMENT[0, 2]],
            "ok",
            label="Engine nodes",
            markersize=8,
        )
        ex = ed.EN_PLACEMENT[:, 0]
        ey = ed.EN_PLACEMENT[:, 1]
        ez = ed.EN_PLACEMENT[:, 2]
        ax.scatter([ex], [ey], [ez], c="k", marker="o", s=80 * np.ones((np.max(np.shape(ex)))))
    ax.plot(
        [afg.fuse_center_seg_point[0, 0, 0]],
        [afg.fuse_center_seg_point[0, 0, 1]],
        [afg.fuse_center_seg_point[0, 0, 2]],
        "og",
        label="Fuselage nodes",
        markersize=8,
    )
    ax.plot([wplot1], [wplot2], [wplot3], "ob", label="Wing nodes", markersize=8)
    ax.plot([cx], [cy], [cz], "xr", label="Center of Gravity", markersize=14)
    s1 = ax.scatter([fx], [fy], [fz], c="g", marker="o", s=80 * np.ones((np.max(np.shape(fx)))))
    ax.scatter([wx], [wy], [wz], c="b", marker="o", s=80 * np.ones((np.max(np.shape(wx)))))
    ax.scatter([cx], [cy], [cz], c="r", marker="x", s=80)
    ax.set_ylim(np.min(wy) - 5, np.max(wy) + 5)
    ax.set_xlim(np.min(fx) - 10, np.max(fx) + 10)
    ax.set_zlim3d(np.min(wz) - 5, np.max(wz) + 5)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.legend(
        loc="upper right",
        bbox_to_anchor=(0.5, 1.0),
        fancybox=True,
        shadow=True,
        ncol=1,
        numpoints=1,
    )
    FIG_NAME = "ToolOutput/" + NAME + "/" + NAME + "_Aircraft_Cog.png"
    fig.savefig(FIG_NAME, dpi=500)

    return ()


def aircraft_cog_bwb_plot(cg, bi, ed, awg, NAME):

    """ The function that generate the plot of the blended wing body
        center of gravity and the nodes used to evaluate it.

        INPUT
        (float_array) cg --Arg.: Center of gravity global coordinates [m].
        (class) bi       --Arg.: BalanceInputs class.
        (class) ed       --Arg.: EngineInputs class.
        (class) awg      --Arg.: AircraftWingGeometry class.
        ##======= Class is defined in the InputClasses folder =======##
        (char) NAME      --Arg.: Aircraft name.

        OUTPUT
        (file)Aircraft_Cog.png --Out.: Png file containing the center of gravity.
    """
    fig = plt.figure()
    fig.patch.set_facecolor("w")
    mpl.rcParams.update({"font.size": 12})
    cx = cg[0]
    cy = cg[1]
    cz = cg[2]
    ax = fig.add_subplot(111, projection="3d")
    wx = []
    wy = []
    wz = []
    for i in range(1, awg.wing_nb + 1):
        for j in range(1, np.max(awg.wing_seg_nb) + 1):
            if awg.wing_center_seg_point[j - 1, i - 1, 0] != 0.0:
                wx.append(awg.wing_center_seg_point[j - 1, i - 1, 0])
                wy.append(awg.wing_center_seg_point[j - 1, i - 1, 1])
                wz.append(awg.wing_center_seg_point[j - 1, i - 1, 2])
    wplot1 = wx[0]
    wplot2 = wy[0]
    wplot3 = wz[0]
    if bi.USER_EN_PLACEMENT:
        ax.plot(
            [ed.EN_PLACEMENT[0, 0]],
            [ed.EN_PLACEMENT[0, 1]],
            [ed.EN_PLACEMENT[0, 2]],
            "ok",
            label="Engine nodes",
            markersize=8,
        )
        ex = ed.EN_PLACEMENT[:, 0]
        ey = ed.EN_PLACEMENT[:, 1]
        ez = ed.EN_PLACEMENT[:, 2]
        ax.scatter([ex], [ey], [ez], c="k", marker="o", s=80 * np.ones((np.max(np.shape(ex)))))
    ax.plot([wplot1], [wplot2], [wplot3], "ob", label="Wing nodes", markersize=10)
    ax.plot([cx], [cy], [cz], "xr", label="Center of Gravity", markersize=10)
    ax.scatter([wx], [wy], [wz], c="b", marker="o", s=80 * np.ones((np.max(np.shape(wx)))))
    ax.scatter([cx], [cy], [cz], c="r", marker="x", s=80)
    ax.set_ylim3d(np.min(wy) - 5, np.max(wy) + 5)
    ax.set_xlim3d(np.min(wx) - 10, np.max(wx) + 10)
    ax.set_zlim3d(np.min(wz) - 5, np.max(wz) + 5)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
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

    return ()


# =============================================================================
#    MAIN
# =============================================================================
if __name__ == "__main__":
    print("###########################################################")
    print("# ERROR NOT A STANDALONE PROGRAM, RUN Balance_unc_main.py #")
    print("###########################################################")
