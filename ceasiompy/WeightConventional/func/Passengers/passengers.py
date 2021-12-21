"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script evaluates the maximum number of passengers (maximum
number of people in economy class that can leave the aircraft in 90 sec).

Python version: >=3.6

| Author : Stefano Piccini
| Date of creation: 2018-09-27

"""


# =============================================================================
#   IMPORTS
# =============================================================================

import math

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])


# =============================================================================
#   CLASSES
# =============================================================================

"""
 InsideDimensions class, can be found on the InputClasses folder inside the
 weightconvclass.py script.
"""


# =============================================================================
#   FUNCTIONS
# =============================================================================


def estimate_passengers(PASS_PER_TOILET, cabin_length, fuse_width, ind):
    """ The function evaluates the maximum number of passengers that can sit in
    the airplane, taking into account also the necessity of common space for
    big airplanes and a number of toilets in relation with the number
    of passengers.

    Args:
        PASS_PER_TOILET(int): Number of passengers per toilet [-]
        cabin_length (float): Cabin length [m]
        fuse_width (float): Fuselage width [m]
        ind (class): InsideDimensions class [-]

    Returns:
        pass_nb (int): Number of passengers [-]
        row_nb   (int): Number of seat rows [-]
        abreast_nb (int): Number of seat abreasts [-]
        aisle_nb (int): Number of aisles [-]
        toilet_nb (int): Number of toilets [-]
        ind (class): InsideDimensions class updated [-]

    """
    cabin_width = fuse_width * (1 - (ind.fuse_thick / 100))

    if cabin_width < 4.89:
        aisle_nb = 1
        max_abreasts = 3
        max_ab2 = 3
    elif cabin_width < 7.6:
        aisle_nb = 2
        max_abreasts = 4
        max_ab2 = 5
    else:
        aisle_nb = 3
        max_abreasts = 4
        max_ab2 = 7

    abreast_nb = math.floor(
        (fuse_width / (1 + (ind.fuse_thick / 100)) - aisle_nb * ind.aisle_width) / ind.seat_width
    )

    if int(round(abreast_nb / 2.0, 0) - max_ab2) > 0:
        add = int(round(abreast_nb / 2.0, 0) - max_ab2)
        log.warning("Configuration with " + str(max_abreasts + add) + " consecutive seats")

        if (max_abreasts + add >= 3 and aisle_nb == 1) or (
            (max_abreasts + add >= 5 and aisle_nb > 1)
        ):
            log.warning("Reducing it to " + str(max_abreasts) + " increasing the seats width")

            while add != 0:
                ind.seat_width = ind.seat_width + 0.01 * (add)
                abreast_nb = math.floor(
                    (fuse_width / (1 + (ind.fuse_thick / 100)) - aisle_nb * ind.aisle_width)
                    / ind.seat_width
                )
                add = int(round(abreast_nb / 2.0, 0) - max_ab2)
        log.warning("Seats width increased to [m]:" + str(ind.seat_width))

    if ind.seat_width < 0.4:
        log.warning("Seats width less than 0.4 m, seats are too small")

    check_width = ind.aisle_width * aisle_nb + ind.seat_width * abreast_nb
    if round(abs(cabin_width - check_width), 1) > 0.01:
        if check_width > cabin_width:
            log.warning("Not enought lateral space")
        log.info(
            "It is possible to modify the sits width by: "
            + str(round((cabin_width - check_width) / (abreast_nb), 2) - 0.01)
            + " m"
        )
        log.info("or")
        log.info(
            "It is possible to modify the aisles width by: "
            + str(round((cabin_width - check_width) / (aisle_nb), 2) - 0.01)
            + " m"
        )
        log.info("or")
        log.info(
            "It is possible to modify both seats and"
            + "aisles width by: "
            + str(round((cabin_width - check_width) / (abreast_nb + aisle_nb), 2) - 0.01)
            + " m"
        )

    row_nb = round((cabin_length) / ind.seat_length, 0)
    pass_nb = abreast_nb * row_nb
    control = 0
    count = 0
    a = 0

    while control == 0:
        count += 1
        if a != 1:
            toilet_nb = round(pass_nb / PASS_PER_TOILET, 1)
            a = 0
            Tot_T_L = int(round((toilet_nb / 2.0), 0))
            row_nb = round((cabin_length - Tot_T_L * ind.toilet_length) / ind.seat_length, 0)
            pass_nb = abreast_nb * row_nb
        if abs(int(toilet_nb) - int(round(pass_nb / PASS_PER_TOILET, 0))) == 0:
            control = 1
        elif abs(int(toilet_nb) - int(round(pass_nb / PASS_PER_TOILET, 0))) <= 1:
            if int(toilet_nb) % 2 == 0 & int(toilet_nb) > int(round(pass_nb / PASS_PER_TOILET, 0)):
                control = 2
            elif (
                int(toilet_nb) % 2 != 0 & int(toilet_nb) < int(round(pass_nb / PASS_PER_TOILET, 0))
            ):
                toilet_nb = int(round(pass_nb / PASS_PER_TOILET, 0))
                control = 3
            elif count > 5:
                control = 4
            elif abs(int(toilet_nb) - int(round(pass_nb / PASS_PER_TOILET, 0))) % 2 == 0:
                toilet_nb = abs(int(toilet_nb) + int(round(pass_nb / PASS_PER_TOILET, 0))) / 2
                a = 1
        elif count > 10:
            control = 5

    check_length = row_nb * ind.seat_length + round((toilet_nb / 2), 0) * ind.toilet_length
    if round(abs((cabin_length) - (check_length)) / (row_nb), 2) > 0.01:
        if check_length > cabin_length:
            log.warning("------------------- Warning -----------------")
            log.warning(" Not enought longitudinal space -------------")
            log.warning(" Reduce seats length ------------------------")
        log.info(
            "It is possible to modify the sits length by: "
            + str(round((cabin_length - check_length) / (row_nb), 2) - 0.01)
            + " m"
        )

    log.info("------------ Seating estimation -------------")
    log.info("  Nb of abreasts: " + str(abreast_nb))
    log.info("  Nb of row: " + str(row_nb))
    log.info("  Nb of passengers: " + str(pass_nb))
    log.info("  Nb of Toilets: " + str(int(toilet_nb)))

    ind.cabin_width = cabin_width
    ind.cabin_area = cabin_length * cabin_width

    return (int(pass_nb), int(row_nb), int(abreast_nb), int(aisle_nb), int(toilet_nb), ind)


# ==============================================================================
#   MAIN
# ==============================================================================

if __name__ == "__main__":

    log.warning("###########################################################")
    log.warning("#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####")
    log.warning("###########################################################")
