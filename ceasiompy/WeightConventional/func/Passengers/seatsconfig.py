"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script defines a possible configuration for the seats
inside the conventional aircraft.

Python version: >=3.7

| Author : Stefano Piccini
| Date of creation: 2018-09-27

"""


# =============================================================================
#   IMPORTS
# =============================================================================

from pathlib import Path
from ceasiompy.WeightConventional.func.weight_utils import PASSENGER_PER_TOILET
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.ceasiompyutils import get_results_directory

log = get_logger()


# =============================================================================
#   CLASSES
# =============================================================================

#  InsideDimensions class, can be found on the InputClasses folder inside the
#  weightconvclass.py script.

# =============================================================================
#   FUNCTIONS
# =============================================================================


def get_seat_config(
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
        toilet_length (float): Toilet length [m]
        toilet_nb (int): Number of toilets [-]

    """

    result_dir = get_results_directory("WeightConventional")
    output_file = Path(result_dir, "Seats_disposition.out")

    lines = open(output_file, "w")
    lines.write("---------------------------------------------")
    lines.write("\nPossible seat configuration -----------------")
    lines.write("\nSeat = 1 and Aisle = 0 ----------------------")
    lines.write("\n---------------------------------------------")
    lines.write(f"\nAbreast nb.: {abreast_nb}")
    lines.write(f"\nRow nb.: {row_nb}")
    lines.write(f"\nSeats_nb : {abreast_nb * row_nb}")
    lines.write("\n---------------------------------------------")

    lines.write("\n-------- Possible seat configuration --------")
    lines.write("\n----------- Seat = 1 and Aisle = 0 ----------")
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

        lines.write("\n" + str(seat))
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


# ==============================================================================
#   MAIN
# ==============================================================================

if __name__ == "__main__":

    log.warning("###########################################################")
    log.warning("#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####")
    log.warning("###########################################################")
