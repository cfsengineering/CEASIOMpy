"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script evaluates the centre of gravity coordinates in case of:

* OEM = Operating empty mass;
* MTOM = Maximum take off mass, with Max Payload:
* ZFM = zero fuel mass;
* ZPM = zero Payload mass
* With a percentage of Fuel and Payload defined by the user.

| Works with Python 2.7
| Author: Stefano Piccini
| Date of creation: 2018-10-12

"""

# =============================================================================
#   IMPORTS
# =============================================================================

import numpy as np


from ceasiompy import log


# =============================================================================
#   CLASSES
# =============================================================================

# All classes are defined inside the InputClasses/Conventional


# =============================================================================
#   FUNCTIONS
# =============================================================================


def center_of_gravity_evaluation(F_PERC, P_PERC, cabin_seg, ag, mw, WING_MOUNTED=True):
    """The function evaluates the center of gravity of airplanes given the
    geometry from cpacs file (tigl_func.py) and masses from
    weight_main.py.

    Source: An introduction to mechanics, 2nd ed., D. Kleppner
            and R. Kolenkow, Cambridge University Press.

    ARGUMENTS
    (int) FPERC --Arg.: Percentage of the maximum amount of fuel used
    (int_array) cabin_seg --Arg.: Array that will contain 1 if the
                                  segment is a cabin segment or
                                  0 otherwise.
    (class) ag  --Arg.: AircraftGeometry class look at
                        aircraft_geometry_class.py in the
                        classes folder for explanation.
    (class) mw  --Arg.: MassesWeights class.
    ##======= Class is defined in the InputClasses folder =======##

    (boolean) WING_MOUNTED --Att.: True if the engines are
                                   mounted on the front main wing.
    RETURN
    (float_array) center_of_gravity --Out.: x,y,z coordinates of the CoG.
    (float_array) mass_seg_i        --Out.: Mass of each segment of each
                                            component of the aircraft.
    (float_array) airplane_centers_segs --Out.: Point at the center of
                                                each segment of the
                                                aircraft.
    """

    max_seg_n = np.max([np.amax(ag.fuse_seg_nb), np.amax(ag.wing_seg_nb)])
    t_nb = ag.fus_nb + ag.w_nb  # Number of parts not counting symmetry
    tot_nb = ag.fuse_nb + ag.wing_nb  # Number of parts counting symmetry
    segments_nb = []

    for i in range(1, ag.fus_nb + 1):
        segments_nb.append(ag.fuse_seg_nb[i - 1])
        if ag.fuse_sym[i - 1] != 0:
            segments_nb.append(ag.fuse_seg_nb[i - 1])

    htw = 0
    x0 = 0
    s = 0
    for i in range(1, ag.w_nb + 1):
        segments_nb.append(ag.wing_seg_nb[i - 1])
        if ag.wing_sym[i - 1] != 0:
            segments_nb.append(ag.wing_seg_nb[i - 1])
            s += 1
        if ag.is_horiz[i - 1 + s]:
            if i != ag.main_wing_index:
                htw = i
        else:
            x = np.amax(ag.wing_center_seg_point[:, i + s - 1, 0])
            if x > x0:
                tw = i
                x0 = x

    mass_seg_i = np.zeros((max_seg_n, tot_nb))
    v_tot = (ag.wing_tot_vol - ag.wing_fuel_vol) + np.sum(ag.fuse_vol)

    # Evaluating eom density, fuel density, passenger density
    oem_par = mw.operating_empty_mass / v_tot
    mpass_par = (mw.mass_payload * (P_PERC / 100)) / np.sum(ag.fuse_cabin_vol)
    mfuel_par = (mw.mass_fuel_max * (F_PERC / 100)) / ag.wing_fuel_vol

    mtom = (
        mw.operating_empty_mass
        + (mw.mass_payload * (P_PERC / 100))
        + (mw.mass_fuel_max * (F_PERC / 100))
    )
    # Definition of the mass of each segment
    ex = False
    fs = []
    wg = []
    f = 0
    i = ag.fus_nb
    for j in range(1, ag.fuse_seg_nb[i - 1] + 1):
        if cabin_seg[j - 1][i - 1 + f] == 1:
            mass_seg_i[j - 1][i - 1 + f] = (oem_par + mpass_par) * ag.fuse_seg_vol[j - 1][i - 1]
        else:
            mass_seg_i[j - 1][i - 1 + f] = oem_par * ag.fuse_seg_vol[j - 1][i - 1]
    fs.append(i)
    if ag.fuse_sym[i - 1 - ag.fus_nb] != 0:
        f += 1
        mass_seg_i[:, i - 1 + f] = mass_seg_i[:, i - 2 + f]
        fs.append(i)

    w = 0
    for i in range(ag.fus_nb + 1, t_nb + 1):
        for j in range(1, ag.wing_seg_nb[i - 1 - ag.fus_nb] + 1):
            if i == ag.main_wing_index:
                mass_seg_i[j - 1][i - 1 + w] = oem_par * (
                    ag.wing_seg_vol[j - 1][i - 1 - ag.fus_nb]
                    - ag.wing_fuel_seg_vol[j - 1][i - 1 - ag.fus_nb]
                ) + mfuel_par * (ag.wing_fuel_seg_vol[j - 1][i - 1 - ag.fus_nb])
            else:
                mass_seg_i[j - 1][i - 1 + w] = oem_par * ag.wing_seg_vol[j - 1][i - 1 - ag.fus_nb]
        wg.append(i - ag.fus_nb)
        if ag.wing_sym[i - 1 - ag.fus_nb] != 0:
            w += 1
            mass_seg_i[:, i - 1 + w] = mass_seg_i[:, i - 2 + w]
            wg.append(i - ag.fus_nb)
            if i + w + f == tot_nb:
                break

    # Mass check
    while not ex:
        if abs(round(mtom, 3) - round(np.sum(mass_seg_i), 3)) < 0.0001:
            ex = True
        else:

            mass = (round(mtom, 3) - round(np.sum(mass_seg_i), 3)) / 2
            if not WING_MOUNTED:
                if htw != 0:
                    a = wg.index(htw)
                else:
                    tw = 0
                    a = wg.index(tw)
            else:
                a = wg.index(ag.main_wing_index)
            mass_seg_i[0][ag.fuse_nb + a] = mass_seg_i[0][ag.fuse_nb + a] + mass
            if ag.is_horiz[a]:
                mass_seg_i[0][ag.fuse_nb + a + 1] = mass_seg_i[0][ag.fuse_nb + a + 1] + mass
            else:
                mass_seg_i[0][ag.fuse_nb + a] = mass_seg_i[0][ag.fuse_nb + a] + mass

    ag.wing_center_seg_point = np.resize(ag.wing_center_seg_point, (max_seg_n, ag.wing_nb, 3))
    ag.fuse_center_seg_point = np.resize(ag.fuse_center_seg_point, (max_seg_n, ag.fuse_nb, 3))

    airplane_centers_segs = np.concatenate((ag.fuse_center_seg_point, ag.wing_center_seg_point), 1)

    # CoG evalution
    center_of_gravity = []

    center_of_gravity.append(round(np.sum(airplane_centers_segs[:, :, 0] * mass_seg_i) / mtom, 3))
    center_of_gravity.append(round(np.sum(airplane_centers_segs[:, :, 1] * mass_seg_i) / mtom, 3))
    center_of_gravity.append(round(np.sum(airplane_centers_segs[:, :, 2] * mass_seg_i) / mtom, 3))
    for i in range(1, 4):
        if abs(center_of_gravity[i - 1]) < 10 ** (-5):
            center_of_gravity[i - 1] = 0.0

    return (center_of_gravity, mass_seg_i, airplane_centers_segs)


# =============================================================================
#   MAIN
# =============================================================================

if __name__ == "__main__":
    log.warning("##########################################################")
    log.warning("### ERROR NOT A STANDALONE PROGRAM, RUN balancemain.py ###")
    log.warning("##########################################################")
