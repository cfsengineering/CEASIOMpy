"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script evaluates the maximum number of passengers (maximum
number of people in economy class that can leave the aircraft in 90 sec).

Python version: >=3.7

| Author : Stefano Piccini
| Date of creation: 2018-09-27

"""


# =================================================================================================
#   IMPORTS
# =================================================================================================

import math
from pathlib import Path
from ceasiompy.WeightConventional.func.weightutils import PASSENGER_PER_TOILET

from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def get_aisle_and_max_abreast(cabin_width):
    """The function to evaluate the number of aisles and the maximum number of abreasts adn ...?

    Args:
        cabin_width (float): Cabin width [m]

    """

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

    return aisle_nb, max_abreasts, max_ab2


def get_abreast_nb(fuselage_width, fuselage_thickness, aisle_nb, aisle_width, seat_width):
    """
    The function to evaluate the number of abreasts.

    Args:
        fuselage_width (float): Fuselage width [m]
        fuselage_thickness (float): Fuselage thickness, ratio of the fuselage width [-]
        aisle_nb (int): Number of aisles [-]
        aisle_width (float): Aisle width [m]
        seat_width (float): Seat width [m]

    """

    return int((fuselage_width / (1 + fuselage_thickness) - aisle_nb * aisle_width) / seat_width)


# TODO: this function could be improved (simplify the algorithm)
def get_toilet_number(pass_nb, cabin_length, abreast_nb, seat_length, toilet_length):
    """The function to evaluate the number of toilets.

    Args:
        pass_nb (int): Number of passengers [-]
        cabin_length (float): Cabin length [m]
        abreast_nb (int): Number of abreasts [-]
        seat_length (float): Seat length [m]
        toilet_length (float): Toilet length [m]

    """

    control = 0
    count = 0
    a = 0

    while control == 0:
        count += 1
        if a != 1:
            toilet_nb = int(math.ceil(pass_nb / PASSENGER_PER_TOILET))
            a = 0
            all_toilet_length = round((toilet_nb / 2.0), 0) * toilet_length
            row_nb = round((cabin_length - all_toilet_length) / seat_length, 0)
            pass_nb = abreast_nb * row_nb
        if abs(toilet_nb - int(round(pass_nb / PASSENGER_PER_TOILET, 0))) == 0:
            control = 1
        elif abs(toilet_nb - int(round(pass_nb / PASSENGER_PER_TOILET, 0))) <= 1:
            if toilet_nb % 2 == 0 & toilet_nb > int(round(pass_nb / PASSENGER_PER_TOILET, 0)):
                control = 2
            elif toilet_nb % 2 != 0 & toilet_nb < int(round(pass_nb / PASSENGER_PER_TOILET, 0)):
                toilet_nb = int(round(pass_nb / PASSENGER_PER_TOILET, 0))
                control = 3
            elif count > 5:
                control = 4
            elif abs(toilet_nb - int(round(pass_nb / PASSENGER_PER_TOILET, 0))) % 2 == 0:
                toilet_nb = abs(toilet_nb + int(round(pass_nb / PASSENGER_PER_TOILET, 0))) / 2
                a = 1
        elif count > 10:
            control = 5

        return toilet_nb, pass_nb


def estimate_passengers(cabin_length, fuse_width, inside_dim):
    """The function evaluates the maximum number of passengers that can sit in
    the airplane, taking into account also the necessity of common space for
    big airplanes and a number of toilets in relation with the number
    of passengers.

    Args:
        cabin_length (float): Cabin length [m]
        fuse_width (float): Fuselage width [m]
        inside_dim (class): InsideDimensions class [-]

    Returns:
        pass_nb (int): Number of passengers [-]
        row_nb   (int): Number of seat rows [-]
        abreast_nb (int): Number of seat abreasts [-]
        aisle_nb (int): Number of aisles [-]
        toilet_nb (int): Number of toilets [-]
        ind (class): InsideDimensions class updated [-]

    """

    fuselage_thickness = inside_dim.fuse_thick / 100  # convert percentage to ratio

    cabin_width = fuse_width * (1 - fuselage_thickness)

    aisle_nb, max_abreasts, max_ab2 = get_aisle_and_max_abreast(cabin_width)

    abreast_nb = get_abreast_nb(
        fuselage_width=fuse_width,
        fuselage_thickness=fuselage_thickness,
        aisle_nb=aisle_nb,
        aisle_width=inside_dim.aisle_width,
        seat_width=inside_dim.seat_width,
    )

    add = int(round(abreast_nb / 2.0, 0) - max_ab2)
    if add > 0:

        log.warning(f"Configuration with {max_abreasts+add} consecutive seats")

        if (max_abreasts + add >= 3 and aisle_nb == 1) or (
            (max_abreasts + add >= 5 and aisle_nb > 1)
        ):
            log.warning(f"Reducing it to {max_abreasts} increasing the seats width")

            while add != 0:
                inside_dim.seat_width = inside_dim.seat_width + 0.01 * (add)
                abreast_nb = get_abreast_nb(
                    fuselage_width=fuse_width,
                    fuselage_thickness=fuselage_thickness,
                    aisle_nb=aisle_nb,
                    aisle_width=inside_dim.aisle_width,
                    seat_width=inside_dim.seat_width,
                )
                add = int(abreast_nb / 2.0 - max_ab2)
        log.warning(f"Seats width increased to [m]: {inside_dim.seat_width}")

    if inside_dim.seat_width < 0.4:
        log.warning("Seats width less than 0.4 m, seats are too small")

    check_width = inside_dim.aisle_width * aisle_nb + inside_dim.seat_width * abreast_nb
    if round(abs(cabin_width - check_width), 1) > 0.01:
        if check_width > cabin_width:
            log.warning("Not enough lateral space")

        diff = round((cabin_width - check_width) / (abreast_nb), 2) - 0.01
        log.info("It is possible to modify the sits width by: {diff} m")
        log.info("or")
        diff = round((cabin_width - check_width) / (aisle_nb), 2) - 0.01
        log.info(f"It is possible to modify the aisles width by: {diff} m")
        log.info("or")
        diff = round((cabin_width - check_width) / (abreast_nb + aisle_nb), 2) - 0.01
        log.info(f"It is possible to modify both seats and aisles width by: {diff} m")

    row_nb = round((cabin_length) / inside_dim.seat_length, 0)
    pass_nb = abreast_nb * row_nb

    toilet_nb, pass_nb = get_toilet_number(
        pass_nb, cabin_length, abreast_nb, inside_dim.seat_length, inside_dim.toilet_length
    )

    check_length = (
        row_nb * inside_dim.seat_length + round((toilet_nb / 2), 0) * inside_dim.toilet_length
    )
    if round(abs(cabin_length - check_length) / (row_nb), 2) > 0.01:
        if check_length > cabin_length:
            log.warning("------------------- Warning -----------------")
            log.warning(" Not enough longitudinal space -------------")
            log.warning(" Reduce seats length ------------------------")
        diff = round((cabin_length - check_length) / (row_nb), 2) - 0.01
        log.info(f"It is possible to modify the sits length by: {diff} m")

    log.info("------------ Seating estimation -------------")
    log.info(f"Nb of abreasts: {abreast_nb}")
    log.info(f"Nb of row: {row_nb}")
    log.info(f"Nb of passengers: {pass_nb}")
    log.info(f"Nb of Toilets: {int(toilet_nb)}")

    inside_dim.cabin_width = cabin_width
    inside_dim.cabin_area = cabin_length * cabin_width

    return (int(pass_nb), int(row_nb), int(abreast_nb), int(aisle_nb), int(toilet_nb), inside_dim)


def stringed_seat_row(seats):
    seat_str = ""
    for s in seats:
        if s == 1:
            seat_str += "X "
        elif s == 0:
            seat_str += "|| "
        else:
            raise ValueError("Seat value must be 0 or 1")
    return "\n" + seat_str


# TODO: Should use only value calculated in estimate_passengers (right now the total number of
# seats is wrong with this function)
def write_seat_config(
    fuse_length,
    row_nb,
    abreast_nb,
    aisle_nb,
    is_double_floor,
    seat_length,
    toilet_nb,
    toilet_length,
):

    """The function to proposes a sit disposition.

    Args:
        fuse_length (float): Fuselage_length [m]
        row_nb (int): Number of seat rows [-]
        abreast_nb (int): Number of seat abreasts [-]
        aisle_nb (int): Number of aisles [-]
        is_double_floor (int): Double floor option [-]
        seat_length (float): Seat length [m]
        toilet_nb (int): Number of toilets [-]
        toilet_length (float): Toilet length [m]

    """

    result_dir = get_results_directory("WeightConventional")
    output_file = Path(result_dir, "Seats_disposition.out")

    lines = open(output_file, "w")
    lines.write("---------------------------------------------")
    lines.write("\nPossible seat configuration -----------------")
    lines.write("\nSeat = X and Aisle = || ----------------------")
    lines.write("\n---------------------------------------------")
    lines.write(f"\nAbreast nb.: {abreast_nb}")
    lines.write(f"\nRow nb.: {row_nb}")
    lines.write(f"\nSeats_nb : {abreast_nb * row_nb}")
    lines.write("\n---------------------------------------------")

    warn = 0
    snd = False
    if is_double_floor != 0:
        lines.write("\n---------------- First Floor ----------------")
        if toilet_nb >= 1:
            f = toilet_length
            t = toilet_nb - 2
        else:
            f = 0
            t = 0
    seat = list(range(1, int(abreast_nb + aisle_nb) + 1))
    for r in range(1, int(row_nb) + 1):
        if is_double_floor != 0:
            f += seat_length
            if t > 0:
                if (r * abreast_nb) % (PASSENGER_PER_TOILET * 2) == 0:
                    f += toilet_length
                    t -= 2
            if not snd and round((fuse_length - f), 1) <= 0.1:
                snd = True
                lines.write("\n---------------- Second Floor" + " ---------------")
        for i in range(int(abreast_nb + aisle_nb)):
            seat[i] = 1
            if aisle_nb == 1:
                seat[int(abreast_nb // 2)] = 0
            elif aisle_nb == 2:
                if abreast_nb % 3 == 0:
                    seat[abreast_nb // 3] = 0
                    seat[abreast_nb * 2 // 3 + 1] = 0
                else:
                    s = int(round(abreast_nb // 3, 0))
                    seat[s] = 0
                    seat[-s - 1] = 0

        lines.write(stringed_seat_row(seat))
        e = int(round((abreast_nb + aisle_nb) // 2.0, 0))
        a = seat[0 : e + 1]

        if (int(round((abreast_nb + aisle_nb) % 2.0, 0))) == 0:
            b = seat[e - 1 : abreast_nb + aisle_nb]
        else:
            b = seat[e : abreast_nb + aisle_nb]
        b = b[::-1]

        if a != b:
            warn += 1

    if warn >= 1:
        log.warning(f"Asymmetric passengers disposition in {warn} rows")
        lines.write(f"\nAsymmetric passengers disposition in {warn} rows")

    lines.close()


# =================================================================================================
#   MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
