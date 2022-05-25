"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This file will connect the wing/fuse/output modules.

| Works with Python 2.7/3.4
| Author : Stefano Piccini
| Date of creation: 2018-09-27

"""

# =============================================================================
#   IMPORTS
# =============================================================================

import math
import numpy as np
from pathlib import Path
from ceasiompy.utils.WB.ConvGeometry.Fuselage.fusegeom import (
    fuselage_check_segment_connection,
    rel_dist,
)
from ceasiompy.utils.ceasiompyutils import get_results_directory
from ceasiompy.utils.commonxpath import FUSELAGES_XPATH, WINGS_XPATH

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()


# =============================================================================
#   CLASSES
# =============================================================================


class AircraftGeometry:
    """
    The class contains all the information about the geometry of
    the aircraft analyzed.

    """

    def __init__(self):

        # General
        self.tot_length = 0  # (float) Aircraft total length [m]

        # Fuselage
        self.fus_nb = 0  # (int) Number of fuselage [-]
        self.fuse_nb = 0  # (int)  Number of fuselage counting symmetry [-]
        self.fuse_sym = []  # (int_array) Fuselage symmetry plane [-]
        self.fuse_sec_nb = []  # (int_array) Number of fuselage sections [-]
        self.fuse_seg_nb = []  # (int_array) Number of fuselage sections [-]
        self.fuse_seg_index = 0  # (int_array) Number of fuselage sections [-]
        self.cabin_nb = 0  # (int_array) Number if cabins per fuselage
        self.cabin_seg = 0  # (int_array) Array that will contain 1 if the segment is a cabin
        # segment or 0 otherwise.
        self.fuse_length = []  # (float_array) Fuselage length [m].
        self.fuse_sec_circ = 0  # (float_array) Circumference of fuselage sections [m].
        self.fuse_sec_width = 0  # (float_array) Width of fuselage sections [m].
        self.fuse_sec_abs_dist = (
            0  # (float_array) Relative distance of each section to the start profile.
        )
        self.fuse_seg_length = 0  # (float_array) Length of each fuselage segments [m].
        self.fuse_nose_length = []  # (float_array) Length of each fuselage nose [m].
        self.fuse_cabin_length = []  # (float_array) Length of each fuselage cabin [m].
        self.fuse_tail_length = []  # (float_array) Length of each fuselage tail [m].
        self.fuse_mean_width = []  # (float_array) Mean fuselage width [m].
        self.fuse_width = 0  # (float) Fuselage width [m].
        self.fuse_center_seg_point = 0  # (float_array) 3D array containing the position of the
        # point at the center of each segment of the fuselage (x,y,z - coord.) [m,m,m].
        # Balance Analysis Only
        self.fuse_center_sec_point = 0  # (float_array) 3D array containing the position of the
        # point at the center of each section of th fuselage (x,y,z - coord.) [m,m,m].
        # Balance Analysis Only
        self.fuse_seg_vol = 0  # (float_array) Volume of fuselage segments [m^3]
        self.fuse_cabin_vol = []  # (float_array) Cabin volume of each fuselage [m^3]
        self.fuse_vol = []  # (float_array) Fuselage volume [m^3]
        self.f_seg_sec = 0  # (float_array) Reordered segments with respective start and end
        # sections for each fuselage.

        # Wing
        self.w_nb = 0  # (int) Number of wings [-]
        self.wing_nb = 0  # (int) Number of wings [-]
        self.main_wing_index = 0  # (int) Main wing index
        self.wing_sym = []  # (int_array) Wing symmetry plane [-]
        self.wing_sec_nb = []  # (int_array) Number of fuselage sections [-]
        self.wing_seg_nb = []  # (int_array) Number of fuselage segments [-]
        self.wing_span = []  # (float_array) Wing span [m]
        self.wing_seg_length = 0  # (floar_array) Wings sements length [m].
        self.wing_sec_thickness = 0  # (float) Wing sections thicknes [m]
        self.wing_sec_mean_thick = []  # (float) Wing sections mean thicknes [m]
        self.wing_max_chord = []  # (float_array) Wing chord in the connection with fuselage [m]
        self.wing_min_chord = []  # (float_array) Wing tip chord [m]
        self.wing_mac = 0  # (float_array) Wing m.a.c. length and position (x,y,z)[m,m,m,m]
        self.wing_center_seg_point = 0  # (floar_array) 3D array containing the position of the
        # point at the center of each segment of the wing (x,y,zcoord.) [m]. Balance Analysis Only
        self.wing_plt_area = []  # (float_array) Wings plantform area [m^2]
        self.wing_plt_area_main = 0  # (float) Main wing area [m^2]
        self.wing_seg_vol = 0  # (float_array) Wing segments volume [m^3]
        self.wing_vol = []  # (float_array) Volume of each wing [m^3]
        self.wing_tot_vol = 0  # (float) Total wing volume [m^3]
        self.wing_fuel_vol = 0  # (float_array) Wing volume available for fuel storage for each
        # wing or couple of wings if symmetry defined [m^3]
        self.wing_fuel_seg_vol = 0  # (float_array) Wing volume available for fuel storage for each
        # wing segment or couple of wing segments
        self.w_seg_sec = 0  # (float_array) Reordered segments with respective start and end
        # sections for each wing
        self.is_horiz = []  # (boolean_array) Define if a wing is horizontal [-]
        self.wing_area = 0  # (float) Wing area [m^2]

    def fuse_geom_eval(self, cpacs):
        """Get the full fuselage geometry from a CPACS file."""

        log.info("Analysing fuselage geometry")

        # Opening tixi and tigl
        tixi = cpacs.tixi
        tigl = cpacs.tigl

        #  Counting fuselage number ---------------------------------------------------
        fus_nb = tixi.getNamedChildrenCount(FUSELAGES_XPATH, "fuselage")
        self.fus_nb = fus_nb
        self.fuse_nb = fus_nb
        i = self.fus_nb

        #  Counting sections and segments----------------------------------------------
        double = 1
        self.fuse_sym.append(tigl.fuselageGetSymmetry(i))
        if self.fuse_sym[i - 1] != 0:
            self.fuse_nb += 1
            double = 2
        self.fuse_sec_nb.append(tigl.fuselageGetSectionCount(i))
        self.fuse_seg_nb.append(tigl.fuselageGetSegmentCount(i))
        self.fuse_vol.append(tigl.fuselageGetVolume(i) * double)

        #  Checking segment and section connection and reordering them
        self.fuse_sec_nb, start_index, seg_sec, fuse_sec_index = fuselage_check_segment_connection(
            fus_nb, self.fuse_seg_nb, self.fuse_sec_nb, tigl
        )

        #  INITIALIZATION 2 -----------------------------------------------------------
        max_sec_nb = np.amax(self.fuse_sec_nb)
        max_seg_nb = np.amax(self.fuse_seg_nb)
        self.fuse_sec_circ = np.zeros((max_sec_nb, fus_nb))
        self.fuse_sec_width = np.zeros((max_sec_nb, fus_nb))
        self.fuse_sec_rel_dist = np.zeros((max_sec_nb, fus_nb))
        self.fuse_seg_index = np.zeros((max_sec_nb, fus_nb))
        self.fuse_seg_length = np.zeros((max_seg_nb, fus_nb))
        fuse_center_section_point = np.zeros((max_sec_nb, fus_nb, 3))
        self.fuse_center_seg_point = np.zeros((max_seg_nb, self.fuse_nb, 3))
        self.fuse_center_sec_point = np.zeros((max_sec_nb, self.fuse_nb, 3))
        self.fuse_seg_vol = np.zeros((max_seg_nb, fus_nb))

        #  FUSELAGE ANALYSIS ----------------------------------------------------------

        #  Aircraft total length
        self.tot_length = tigl.configurationGetLength()

        #  Evaluating fuselage: sections circumference, segments volume and length ---
        (self.fuse_sec_rel_dist[:, i - 1], self.fuse_seg_index[:, i - 1]) = rel_dist(
            i,
            self.fuse_sec_nb[i - 1],
            self.fuse_seg_nb[i - 1],
            tigl,
            seg_sec[:, i - 1, :],
            start_index[i - 1],
        )
        self.fuse_length.append(self.fuse_sec_rel_dist[-1, i - 1])
        for j in range(1, self.fuse_seg_nb[i - 1] + 1):
            k = int(self.fuse_seg_index[j][i - 1])
            self.fuse_sec_circ[j][i - 1] = tigl.fuselageGetCircumference(i, k, 1.0)
            (fpx, fpy, fpz) = tigl.fuselageGetPoint(i, k, 1.0, 0.0)
            (fpx2, fpy2, fpz2) = tigl.fuselageGetPoint(i, k, 1.0, 0.5)
            self.fuse_seg_vol[j - 1][i - 1] = abs(tigl.fuselageGetSegmentVolume(i, k))
            fuse_center_section_point[j][i - 1][0] = (fpx + fpx2) / 2
            fuse_center_section_point[j][i - 1][1] = (fpy + fpy2) / 2
            fuse_center_section_point[j][i - 1][2] = (fpz + fpz2) / 2
            hw1 = 0
            hw2 = 0
            for zeta in np.arange(0.0, 1.0, 0.001):
                (fpx, fpy, fpz) = tigl.fuselageGetPoint(i, k, 1.0, zeta)
                if abs(fpz - fuse_center_section_point[j][i - 1][2]) < 0.01:
                    if fpy > fuse_center_section_point[j][i - 1][1] and hw1 == 0:
                        hw1 = abs(fpy - fuse_center_section_point[j][i - 1][1])
                    elif fpy < fuse_center_section_point[j][i - 1][1] and hw2 == 0:
                        hw2 = abs(fpy - fuse_center_section_point[j][i - 1][1])
                        break
            self.fuse_sec_width[j][i - 1] = hw1 + hw2
            fslpx, _, _ = tigl.fuselageGetPoint(1, k, 0.0, 0.0)
            fslpx2, _, _ = tigl.fuselageGetPoint(1, k, 1.0, 0.0)
            self.fuse_seg_length[j - 1][i - 1] = abs(fslpx2 - fslpx)
        k = int(self.fuse_seg_index[1][i - 1])
        self.fuse_sec_circ[0][i - 1] = tigl.fuselageGetCircumference(i, k, 0.0)
        fpx, fpy, fpz = tigl.fuselageGetPoint(i, k, 0.0, 0.0)
        fpx2, fpy2, fpz2 = tigl.fuselageGetPoint(i, k, 0.0, 0.5)
        fuse_center_section_point[0][i - 1][0] = (fpx + fpx2) / 2
        fuse_center_section_point[0][i - 1][1] = (fpy + fpy2) / 2
        fuse_center_section_point[0][i - 1][2] = (fpz + fpz2) / 2
        hw1 = 0
        hw2 = 0
        for zeta in np.arange(0.0, 1.0, 0.001):
            (fpx, fpy, fpz) = tigl.fuselageGetPoint(i, k, 0.0, zeta)
            if abs(fpz - fuse_center_section_point[0][i - 1][2]) < 0.01:
                if fpy > fuse_center_section_point[0][i - 1][1] and hw1 == 0:
                    hw1 = abs(fpy - fuse_center_section_point[0][i - 1][1])
                elif fpy < fuse_center_section_point[0][i - 1][1] and hw2 == 0:
                    hw2 = abs(fpy - fuse_center_section_point[0][i - 1][1])
                    break
        self.fuse_sec_width[0][i - 1] = hw1 + hw2
        self.fuse_mean_width.append(np.mean(self.fuse_sec_width[:, i - 1]))

        #  Evaluating the point at the center of each segment, symmetry is considered
        a = 0
        cs = False
        for i in range(int(self.fuse_nb)):
            if cs:
                cs = False
                continue
            for j in range(1, self.fuse_seg_nb[i - a - 1] + 1):
                self.fuse_center_seg_point[j - 1][i - 1][0] = (
                    fuse_center_section_point[j - 1][i - a - 1][0]
                    + fuse_center_section_point[j][i - a - 1][0]
                ) / 2
                self.fuse_center_seg_point[j - 1][i - 1][1] = (
                    fuse_center_section_point[j - 1][i - a - 1][1]
                    + fuse_center_section_point[j][i - a - 1][1]
                ) / 2
                self.fuse_center_seg_point[j - 1][i - 1][2] = (
                    fuse_center_section_point[j - 1][i - a - 1][2]
                    + fuse_center_section_point[j][i - a - 1][2]
                ) / 2
                self.fuse_center_sec_point[j - 1][i - 1][:] = fuse_center_section_point[j - 1][
                    i - a - 1
                ][:]
            if self.fuse_sym[i - 1 - a] != 0:
                if self.fuse_sym[i - 1 - a] == 1:
                    symy = 1
                    symx = 1
                    symz = -1
                if self.fuse_sym[i - 1 - a] == 2:
                    symy = -1
                    symx = 1
                    symz = 1
                if self.fuse_sym[i - 1 - a] == 3:
                    symy = 1
                    symx = -1
                    symz = 1
                self.fuse_center_seg_point[:, i, 0] = (
                    self.fuse_center_seg_point[:, i - 1, 0] * symx
                )
                self.fuse_center_seg_point[:, i, 1] = (
                    self.fuse_center_seg_point[:, i - 1, 1] * symy
                )
                self.fuse_center_seg_point[:, i, 2] = (
                    self.fuse_center_seg_point[:, i - 1, 2] * symz
                )
                self.fuse_center_sec_point[j - 1][i][:] = fuse_center_section_point[j - 1][
                    i - a - 1
                ][:]
                cs = True
                a += 1

        # Evaluating cabin length and volume, nose length and tail_length ------------
        ex = False
        corr = 1.25 + np.zeros((1, fus_nb))
        c = False
        cabin_nb = np.zeros((1, fus_nb))
        cabin_seg = np.zeros((max_seg_nb, fus_nb))
        cabin_length = 0
        cabin_volume = 0
        nose_length = 0
        tail_length = 0
        for j in range(1, self.fuse_seg_nb[i - 1] + 1):
            if round(self.fuse_sec_width[j][i - 1], 3) == round(
                np.amax(self.fuse_sec_width[:, i - 1]), 3
            ):
                cabin_length += self.fuse_seg_length[j - 1, i - 1]
                cabin_volume += self.fuse_seg_vol[j - 1, i - 1]
                cabin_seg[j - 1][i - 1] = 1
                c = True
            elif not c:
                nose_length += self.fuse_seg_length[j - 1, i - 1]
        if cabin_length >= 0.65 * self.fuse_length[i - 1]:
            # If the aircraft is designed with 1 or more sections with
            # maximum width and the sun of their length is greater the 65%
            # of the total length, the cabin will be considered only in those
            # sections
            tail_length = self.fuse_length[i - 1] - cabin_length - nose_length
            cabin_nb[i - 1] = 1
            ex = True
        while ex is False:
            c = False
            cabin_seg = np.zeros((max_seg_nb, fus_nb))
            nose_length = 0
            tail_length = 0
            cabin_length = 0
            cabin_volume = 0
            for j in range(1, self.fuse_seg_nb[i - 1] + 1):
                if self.fuse_sec_width[j][i - 1] >= (corr[i - 1] * self.fuse_mean_width[i - 1]):
                    cabin_length += self.fuse_seg_length[j - 1, i - 1]
                    cabin_volume += self.fuse_seg_vol[j - 1, i - 1]
                    cabin_seg[j - 1][i - 1] = 1
                    c = True
                elif c:
                    tail_length += self.fuse_seg_length[j - 1, i - 1]
                else:
                    nose_length += self.fuse_seg_length[j - 1, i - 1]
            if corr[i - 1] > 0.0 and cabin_length < (0.20 * self.fuse_length[i - 1]):
                corr[i - 1] -= 0.05
            else:
                ex = True

        self.fuse_nose_length.append(nose_length)
        self.fuse_tail_length.append(tail_length)
        self.fuse_cabin_length.append(cabin_length)
        self.fuse_cabin_vol.append(cabin_volume)
        self.f_seg_sec = seg_sec
        self.cabin_nb = cabin_nb
        self.cabin_seg = cabin_seg
        self.fuse_mean_width = self.fuse_mean_width[0]

        self.fuse_width = round(np.amax(self.fuse_sec_width[:, 0]), 3)

        # log info display ------------------------------------------------------------

        log.info("---------------------------------------------")
        log.info("---------- Geometry Evaluations -------------")
        log.info("---------- USEFUL INFO ----------------------")
        log.info("If fuselage or wing number is greater than 1 the ")
        log.info("information of each part is listed in an ")
        log.info("array ordered per column progressively")
        log.info("Symmetry output: 0 = no symmetry, 1 =  x-y, " + "2 = x-z, 3 = y-z planes")
        log.info("---------------------------------------------")
        log.info("---------- Fuselage Results -----------------")
        log.info(f"Number of fuselage [-]: {self.fuse_nb}")
        log.info(f"Fuselage symmetry plane [-]: {self.fuse_sym}")
        log.info(f"Number of fuselage sections (not counting symmetry) [-]: {self.fuse_sec_nb}")
        log.info(f"Number of fuselage segments (not counting symmetry) [-]: {self.fuse_seg_nb}")
        log.info(f"Fuse Length [m]: {self.fuse_length}")
        log.info(f"Fuse nose Length [m]: {self.fuse_nose_length}")
        log.info(f"Fuse cabin Length [m]: {self.fuse_cabin_length}")
        log.info(f"Fuse tail Length [m]: {self.fuse_tail_length}")
        log.info(f"Aircraft Length [m]: {self.tot_length}")
        log.info(f"Mean fuselage width [m]: {self.fuse_mean_width}")
        log.info(f"Volume of each cabin [m^3]: {self.fuse_cabin_vol}")
        log.info(f"Volume of each fuselage [m^3]: {self.fuse_vol}")
        log.info("---------------------------------------------")

    def wing_geom_eval(self, cpacs):
        """Get wing geometry information from cpacs file."""

        log.info("---------- Analysing wing geometry ----------")

        # Opening tixi and tigl
        tixi = cpacs.tixi
        tigl = cpacs.tigl

        #  Counting wing number without symmetry --------------------------------------
        w_nb = tixi.getNamedChildrenCount(WINGS_XPATH, "wing")

        #  INITIALIZATION 1 -----------------------------------------------------------
        self.w_nb = w_nb
        self.wing_nb = w_nb
        wing_plt_area_xz = []
        wing_plt_area_yz = []
        wingUID = []

        #  Counting sections and segments----------------------------------------------
        b = 0
        for i in range(1, w_nb + 1):
            double = 1
            self.wing_sym.append(tigl.wingGetSymmetry(i))
            if self.wing_sym[i - 1] != 0:
                double = 2  # To consider the real amount of wing
                # when they are defined using symmetry
                self.wing_nb += 1
            self.wing_sec_nb.append(tigl.wingGetSectionCount(i))
            self.wing_seg_nb.append(tigl.wingGetSegmentCount(i))
            self.wing_vol.append(tigl.wingGetVolume(i) * double)

            self.wing_plt_area.append(tigl.wingGetReferenceArea(i, 1) * double)  # x-y plane
            wing_plt_area_xz.append(tigl.wingGetReferenceArea(i, 2) * double)  # x-z plane
            wing_plt_area_yz.append(tigl.wingGetReferenceArea(i, 3) * double)  # y-z plane

            self.wing_tot_vol = self.wing_tot_vol + self.wing_vol[i - 1]
            wingUID.append(tigl.wingGetUID(i))
            self.wing_span.append(tigl.wingGetSpan(wingUID[i - 1]))
            a = np.amax(self.wing_span)
            # Evaluating the index that corresponds to the main wing
            if a > b:
                self.main_wing_index = i
                b = a

        #  Checking segment and section connection and reordering them
        (
            self.wing_sec_nb,
            start_index,
            seg_sec,
            wing_sec_index,
        ) = self.wing_check_segment_connection(wing_plt_area_xz, wing_plt_area_yz, tigl)

        #  INITIALIZATION 2 -----------------------------------------------------------

        max_wing_sec_nb = np.amax(self.wing_sec_nb)
        max_wing_seg_nb = np.amax(self.wing_seg_nb)
        wing_center_section_point = np.zeros((max_wing_sec_nb, w_nb, 3))
        self.wing_center_seg_point = np.zeros((max_wing_seg_nb, self.wing_nb, 3))
        self.wing_seg_vol = np.zeros((max_wing_seg_nb, w_nb))
        self.wing_fuel_seg_vol = np.zeros((max_wing_seg_nb, w_nb))
        self.wing_fuel_vol = 0
        self.wing_mac = np.zeros((4, w_nb))
        self.wing_sec_thickness = np.zeros((max_wing_sec_nb + 1, w_nb))

        #  WING ANALYSIS --------------------------------------------------------------

        # Main wing plantform area
        self.wing_plt_area_main = self.wing_plt_area[self.main_wing_index - 1]

        #  Wing: MAC,chords,thickness,span,plantform area ------------------------------

        for i in range(1, w_nb + 1):
            mac = tigl.wingGetMAC(wingUID[i - 1])
            wpx, wpy, wpz = tigl.wingGetChordPoint(i, 1, 0.0, 0.0)
            wpx2, wpy2, wpz2 = tigl.wingGetChordPoint(i, 1, 0.0, 1.0)
            self.wing_max_chord.append(
                np.sqrt((wpx2 - wpx) ** 2 + (wpy2 - wpy) ** 2 + (wpz2 - wpz) ** 2)
            )
            wpx, wpy, wpz = tigl.wingGetChordPoint(i, self.wing_seg_nb[i - 1], 1.0, 0.0)
            wpx2, wpy2, wpz2 = tigl.wingGetChordPoint(i, self.wing_seg_nb[i - 1], 1.0, 1.0)
            self.wing_min_chord.append(
                np.sqrt((wpx2 - wpx) ** 2 + (wpy2 - wpy) ** 2 + (wpz2 - wpz) ** 2)
            )
            for k in range(1, 5):
                self.wing_mac[k - 1][i - 1] = mac[k - 1]
            for jj in range(1, self.wing_seg_nb[i - 1] + 1):
                j = int(seg_sec[jj - 1, i - 1, 2])
                cle = tigl.wingGetChordPoint(i, j, 0.0, 0.0)
                self.wing_seg_vol[j - 1][i - 1] = tigl.wingGetSegmentVolume(i, j)
                lp = tigl.wingGetLowerPoint(i, j, 0.0, 0.0)
                up = tigl.wingGetUpperPoint(i, j, 0.0, 0.0)
                if np.all(cle == lp):
                    L = 0.25
                else:
                    L = 0.75
                if np.all(cle == up):
                    U = 0.25
                else:
                    U = 0.75
                wplx, wply, wplz = tigl.wingGetLowerPoint(i, j, 0.0, L)
                wpux, wpuy, wpuz = tigl.wingGetUpperPoint(i, j, 0.0, U)
                wing_center_section_point[j - 1][i - 1][0] = (wplx + wpux) / 2
                wing_center_section_point[j - 1][i - 1][1] = (wply + wpuy) / 2
                wing_center_section_point[j - 1][i - 1][2] = (wplz + wpuz) / 2
                self.wing_sec_thickness[j - 1][i - 1] = np.sqrt(
                    (wpux - wplx) ** 2 + (wpuy - wply) ** 2 + (wpuz - wplz) ** 2
                )
            j = int(seg_sec[self.wing_seg_nb[i - 1] - 1, i - 1, 2])
            wplx, wply, wplz = tigl.wingGetLowerPoint(i, self.wing_seg_nb[i - 1], 1.0, L)
            wpux, wpuy, wpuz = tigl.wingGetUpperPoint(i, self.wing_seg_nb[i - 1], 1.0, U)
            self.wing_sec_thickness[j][i - 1] = np.sqrt(
                (wpux - wplx) ** 2 + (wpuy - wply) ** 2 + (wpuz - wplz) ** 2
            )
            wing_center_section_point[self.wing_seg_nb[i - 1]][i - 1][0] = (wplx + wpux) / 2
            wing_center_section_point[self.wing_seg_nb[i - 1]][i - 1][1] = (wply + wpuy) / 2
            wing_center_section_point[self.wing_seg_nb[i - 1]][i - 1][2] = (wplz + wpuz) / 2
            self.wing_sec_mean_thick.append(
                np.mean(self.wing_sec_thickness[0 : self.wing_seg_nb[i - 1] + 1, i - 1])
            )
            # Evaluating wing fuel tank volume in the main wings
            if abs(round(self.wing_plt_area[i - 1], 3) - self.wing_plt_area_main) < 0.001:
                tp_ratio = self.wing_min_chord[i - 1] / self.wing_max_chord[i - 1]
                ratio = round(tp_ratio * self.wing_plt_area[i - 1] / 100, 1)
                if ratio >= 1.0:
                    self.wing_fuel_vol = round(self.wing_vol[i - 1] * 0.8, 2)
                elif ratio >= 0.5:
                    self.wing_fuel_vol = round(self.wing_vol[i - 1] * 0.72, 2)
                else:
                    self.wing_fuel_vol = round(self.wing_vol[i - 1] * 0.5, 2)
                for j in seg_sec[:, i - 1, 2]:
                    if j == 0.0:
                        break
                    self.wing_fuel_seg_vol[int(j) - 1][i - 1] = round(
                        (self.wing_seg_vol[int(j) - 1][i - 1] / (sum(self.wing_vol)))
                        * self.wing_fuel_vol,
                        2,
                    )
            if (
                self.wing_plt_area[i - 1] > wing_plt_area_xz[i - 1]
                and self.wing_plt_area[i - 1] > wing_plt_area_yz[i - 1]
            ):
                self.is_horiz.append(True)
                if self.wing_sym[i - 1] != 0:
                    self.is_horiz.append(True)
            else:
                self.is_horiz.append(False)
                if self.wing_sym[i - 1] != 0:
                    self.is_horiz.append(False)

        # Wing segment length evaluating function
        self.get_wing_segment_length(wing_center_section_point)

        # Evaluating the point at the center of each segment, the center
        # is placed at 1/4 of the chord, symmetry is considered.

        a = 0
        c = False
        for i in range(1, int(self.wing_nb) + 1):
            if c:
                c = False
                continue
            for jj in range(1, self.wing_seg_nb[i - a - 1] + 1):
                j = int(seg_sec[jj - 1, i - a - 1, 2])
                self.wing_center_seg_point[j - 1][i - 1][0] = (
                    wing_center_section_point[j - 1][i - a - 1][0]
                    + wing_center_section_point[j][i - a - 1][0]
                ) / 2
                self.wing_center_seg_point[j - 1][i - 1][1] = (
                    wing_center_section_point[j - 1][i - a - 1][1]
                    + wing_center_section_point[j][i - a - 1][1]
                ) / 2
                self.wing_center_seg_point[j - 1][i - 1][2] = (
                    wing_center_section_point[j - 1][i - a - 1][2]
                    + wing_center_section_point[j][i - a - 1][2]
                ) / 2
            if self.wing_sym[i - 1 - a] != 0:
                if self.wing_sym[i - 1 - a] == 1:
                    symy = 1
                    symx = 1
                    symz = -1
                if self.wing_sym[i - 1 - a] == 2:
                    symy = -1
                    symx = 1
                    symz = 1
                if self.wing_sym[i - 1 - a] == 3:
                    symy = 1
                    symx = -1
                    symz = 1
                self.wing_center_seg_point[:, i, 0] = (
                    self.wing_center_seg_point[:, i - 1, 0] * symx
                )
                self.wing_center_seg_point[:, i, 1] = (
                    self.wing_center_seg_point[:, i - 1, 1] * symy
                )
                self.wing_center_seg_point[:, i, 2] = (
                    self.wing_center_seg_point[:, i - 1, 2] * symz
                )
                c = True
                a += 1

        self.w_seg_sec = seg_sec

        self.wing_area = round(self.wing_plt_area_main, 3)

        log.info("---------------------------------------------")
        log.info("--------------- Wing Results ----------------")
        log.info(f"Number of Wings [-]: {self.wing_nb}")
        log.info(f"Wing symmetry plane [-]: {self.wing_sym}")
        log.info(f"Number of wing sections (not counting symmetry) [-]: {self.wing_sec_nb}")
        log.info(f"Number of wing segments (not counting symmetry) [-]: {self.wing_seg_nb}")
        log.info(f"Wing Span [m]: {self.wing_span}")
        log.info(f"Wing MAC length [m]: {self.wing_mac[0,]}")
        log.info(f"Wing max chord length [m]: {self.wing_max_chord}")
        log.info(f"Wing min chord length [m]: {self.wing_min_chord}")
        log.info(f"Main wing plantform area [m^2]: {self.wing_plt_area_main}")
        log.info(f"Wings plantform area [m^2]: {self.wing_plt_area}")
        log.info(f"Volume of each wing [m^3]: {self.wing_vol}")
        log.info(f"Total wing volume [m^3]: {self.wing_tot_vol}")
        log.info(f"Wing volume for fuel storage [m^3]: {self.wing_fuel_vol}")
        log.info("---------------------------------------------")

    # TODO: could probably be simplified
    def wing_check_segment_connection(self, wing_plt_area_xz, wing_plt_area_yz, tigl):
        """The function checks for each segment the start and end section index
            and to reorder them.

        ARGUMENTS
        (float) wing_plt_area_xz    --Arg.: Wing area on the xz plane [m^2].
        (float) wing_plt_area_yz    --Arg.: Wing area on the yz plane [m^2].
        (class) ag     --Arg.: AircraftGeometry class.
        # ======= Class are defined in the InputClasses folder =======##
        (char) tigl    --Arg.: Tigl handle.

        RETURN
        (int) sec_nb            --Out.: Number of sections for each wing.
        (int) start_index       --Out.: Start section index for each wing.
        (float-array) seg_sec_reordered -- Out.: Reordered segments with
                                                respective start and end section
                                                for each wing.
        (float_array) sec_index --Out.: List of section index reordered.
        """

        log.info("Checking wings segments connection")

        # Initializing arrays
        nbmax = np.amax(self.wing_seg_nb)
        seg_sec = np.zeros((nbmax, self.w_nb, 3))
        seg_sec_reordered = np.zeros(np.shape(seg_sec))
        sec_index = np.zeros((nbmax, self.w_nb))
        start_index = []
        sec_nb = []

        # First, for each segment the start and end sections are found. Then
        # they are reordered considering that the end section of a segment
        # is the start section of the next one.
        # The first section is the one that has the lowest y,
        # for horizontal wings, or z, for vertical wings position
        # The code works if a section is defined and not used and if the segments
        # are not define with a consequential order.
        # WARNING The code does not work if a segment is defined
        #         and then not used.
        #         The aircraft should be designed along the x-axis
        #         and on the x-y plane

        for i in range(1, self.w_nb + 1):
            wing_sec_index = []
            for j in range(1, self.wing_seg_nb[i - 1] + 1):
                (s0, e) = tigl.wingGetInnerSectionAndElementIndex(i, j)
                (s1, e) = tigl.wingGetOuterSectionAndElementIndex(i, j)
                seg_sec[j - 1, i - 1, 0] = s0
                seg_sec[j - 1, i - 1, 1] = s1
                seg_sec[j - 1, i - 1, 2] = j
            (slpx, slpy, slpz) = tigl.wingGetChordPoint(i, 1, 0.0, 0.0)
            seg_sec_reordered[0, i - 1, :] = seg_sec[0, i - 1, :]
            start_index.append(1)
            for j in range(2, self.wing_seg_nb[i - 1] + 1):
                (x, y, z) = tigl.wingGetChordPoint(i, j, 1.0, 0.0)
                if (
                    self.wing_plt_area[i - 1] > wing_plt_area_xz[i - 1]
                    and self.wing_plt_area[i - 1] > wing_plt_area_yz[i - 1]
                ):
                    if y < slpy:
                        (_, slpy, slpz) = (x, y, z)
                        start_index.append(j)
                        seg_sec_reordered[0, i - 1, :] = seg_sec[j - 1, i - 1, :]
                else:
                    if z < slpz:
                        (_, slpy, slpz) = (x, y, z)
                        start_index.append(j)
                        seg_sec_reordered[0, i - 1, :] = seg_sec[j - 1, i - 1, :]
            for j in range(2, self.wing_seg_nb[i - 1] + 1):
                end_sec = seg_sec_reordered[j - 2, i - 1, 1]
                start_next = np.where(seg_sec[:, i - 1, 0] == end_sec)
                seg_sec_reordered[j - 1, i - 1, :] = seg_sec[start_next[0], i - 1, :]
            wing_sec_index.append(seg_sec_reordered[0, 0, 0])
            for j in range(2, self.wing_seg_nb[i - 1] + 1):
                if seg_sec_reordered[j - 1, i - 1, 0] not in wing_sec_index:
                    wing_sec_index.append(seg_sec_reordered[j - 1, i - 1, 0])
            if seg_sec_reordered[j - 1, i - 1, 1] not in wing_sec_index:
                wing_sec_index.append(seg_sec_reordered[j - 1, i - 1, 1])
            nb = np.shape(wing_sec_index)
            if nb[0] > nbmax:
                nbmax = nb[0]
            sec_index.resize(nbmax, self.w_nb)
            sec_index[0 : nb[0], i - 1] = wing_sec_index[0 : nb[0]]
            sec_nb.append(nb[0])

        return sec_nb, start_index, seg_sec_reordered, sec_index

    def get_wing_segment_length(self, wing_center_section_point):
        """The function evaluates the length of each segment of each wing,
        also considering the ones defined using symmetry.
        The function will upload the aircraft geometry class.

        """

        log.info("----- Evaluating wings segments length ------")
        max_seg_nb = np.amax(self.wing_seg_nb)
        self.wing_seg_length = np.zeros((max_seg_nb, self.wing_nb))

        # To evaluate the length of each segment, the ditance of central point
        # of the start and end section of each segment is computed

        a = 0
        for i in range(1, self.w_nb + 1):
            for j in range(1, self.wing_seg_nb[i - 1] + 1):
                (x1, y1, z1) = wing_center_section_point[j - 1, i - 1, :]
                (x2, y2, z2) = wing_center_section_point[j, i - 1, :]
                self.wing_seg_length[j - 1][i + a - 1] = math.sqrt(
                    (x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2
                )
            if self.wing_sym[i - 1] != 0:
                self.wing_seg_length[:, i + a] = self.wing_seg_length[:, i + a - 1]
                a += 1

    def produce_output_txt(self):
        """Function to generate the output file with all the geometry data
        evaluated.
        """

        NAME = "TODO get name form cpacs object"

        result_dir = get_results_directory("WeightConventional")

        output_file = Path(result_dir, "Aircraft_Geometry.out")

        OutputTextFile = open(output_file, "w")

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
            "information of each obj are listed in an "
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
        OutputTextFile.write(f"\nNumber of fuselage sections [-]: {self.fuse_sec_nb}")
        OutputTextFile.write(f"\nNumber of fuselage segments [-]: {self.fuse_seg_nb}")
        OutputTextFile.write(f"\nCabin segments array [-]: {self.cabin_seg}")
        OutputTextFile.write(f"\nFuse Length [m]: {np.around(self.fuse_length, 5)}")
        OutputTextFile.write(f"\nFuse nose Length [m]: {np.around(self.fuse_nose_length, 5)}")
        OutputTextFile.write(f"\nFuse cabin Length [m]: {np.around(self.fuse_cabin_length, 5)}")
        OutputTextFile.write(f"\nFuse tail Length [m]: {np.around(self.fuse_tail_length, 5)}")
        OutputTextFile.write(f"\nAircraft Length [m]: {np.around(self.tot_length, 5)}")
        OutputTextFile.write(
            f"\nCircumference of each section of the fuselage [m]: \n{np.around(self.fuse_sec_circ, 5)}"
        )
        OutputTextFile.write(
            "\nRelative distance of each section of the"
            + "fuselage, respect to the first one [m]: \n"
            + str(np.around(self.fuse_sec_rel_dist, 5))
        )
        OutputTextFile.write(
            "\nLength of each segment of the fuselage [m]: \n"
            + str(np.around(self.fuse_seg_length, 5))
        )
        OutputTextFile.write(
            "\nMean fuselage width [m]: " + str(np.around(self.fuse_mean_width, 5))
        )
        OutputTextFile.write(
            "\nWidth of each section of the fuselage [m]: \n"
            + str(np.around(self.fuse_sec_width, 5))
        )
        OutputTextFile.write(
            "\nVolume of each segment of the fuselage "
            "[m^3]: \n" + str(np.around(self.fuse_seg_vol, 5))
        )
        OutputTextFile.write(
            "\nVolume of the cabin [m^3]: " + str(np.around(self.fuse_cabin_vol, 5))
        )
        OutputTextFile.write("\nVolume of the fuselage [m^3]: " + str(np.around(self.fuse_vol, 5)))
        OutputTextFile.write("\n")
        OutputTextFile.write("\n-------------------------------------------------")
        OutputTextFile.write("\nWINGS -------------------------------------------")
        OutputTextFile.write("\n-------------------------------------------------")
        OutputTextFile.write(f"\nNumber of Wings [-]: {self.wing_nb}")
        OutputTextFile.write(f"\nWing symmetry plane [-]: {self.wing_sym}")
        OutputTextFile.write(f"\nNumber of wing sections [-]: {self.wing_sec_nb}")
        OutputTextFile.write(f"\nNumber of wing segments [-]: {self.wing_seg_nb}")
        OutputTextFile.write(f"\nWing Span [m]: \n{np.around(self.wing_span, 5)}")
        OutputTextFile.write(
            "\nWing MAC length [m]: \n"
            + str(
                np.around(
                    self.wing_mac[
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
                    self.wing_mac[
                        1:4,
                    ],
                    5,
                )
            )
        )
        OutputTextFile.write(
            "\nWings sections thickness [m]: \n" + str(np.around(self.wing_sec_thickness, 5))
        )
        OutputTextFile.write(
            "\nWings sections mean thickness [m]: \n" + str(np.around(self.wing_sec_mean_thick, 5))
        )
        OutputTextFile.write(
            "\nWing segments length [m]: \n" + str(np.around(self.wing_seg_length, 5))
        )
        OutputTextFile.write(
            "\nWing max chord length [m]: \n" + str(np.around(self.wing_max_chord, 5))
        )
        OutputTextFile.write(
            "\nWing min chord length [m]: \n" + str(np.around(self.wing_min_chord, 5))
        )
        OutputTextFile.write(
            "\nWings planform area [m^2]: \n" + str(np.around(self.wing_plt_area, 5))
        )
        OutputTextFile.write(
            "\nMain wing planform area [m^2]: " + str(np.around(self.wing_plt_area_main, 5))
        )
        OutputTextFile.write("\nVolume of each wing [m^3]: \n" + str(np.around(self.wing_vol, 5)))
        OutputTextFile.write("\nTotal wing volume [m^3]: " + str(np.around(self.wing_tot_vol, 5)))
        OutputTextFile.write("\nWing volume for fuel storage [m^3]: " + str(self.wing_fuel_vol))

        # Close Text File
        OutputTextFile.close()


# =============================================================================
#   FUNCTIONS
# =============================================================================


# =============================================================================
#   MAIN
# ==============================================================================

if __name__ == "__main__":

    log.warning("##########################################################")
    log.warning("############# ERROR NOT A STANDALONE PROGRAM #############")
    log.warning("##########################################################")
