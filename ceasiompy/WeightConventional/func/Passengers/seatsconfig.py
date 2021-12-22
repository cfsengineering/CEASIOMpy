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


def get_seat_config(
    pass_nb,
    row_nb,
    abreast_nb,
    aisle_nb,
    IS_DOUBLE_FLOOR,
    toilet_nb,
    PASS_PER_TOILET,
    fuse_length,
    ind,
    NAME,
):

    """ The function to proposes a sit disposition.

    Args:
        pass_nb (int): Number of passengers [-]
        row_nb (int): Nmber of seat rows [-]
        abreast_nb (int): Number of seat abreasts [-]
        aisle_nb (int): Number of aisles [-]
        toilet_nb (int): Number of toilets [-]
        IS_DOUBLE_FLOOR (int): Double floor option [-]
        PASS_PER_TOILET (int): Number of passengers per toilet [-]
        fuse_length (float): Fuselage_length [m]
        ind (class): InsideDimensions class [-]
        NAME  (str): Name of the aircraft

    Returns:
        NAME_Seats_disposition.out (file) : Print of the possible sets
                                               disposition per each rows.
    """

    out_name = "ToolOutput/" + NAME + "/" + NAME + "_Seats_disposition.out"
    out_txt_file = open(out_name, "w")
    out_txt_file.write("---------------------------------------------")
    out_txt_file.write("\nPossible seat configuration -----------------")
    out_txt_file.write("\nSeat = 1 and Aisle = 0 ----------------------")
    out_txt_file.write("\n---------------------------------------------")
    out_txt_file.write("\nAbreast nb.: " + str(abreast_nb))
    out_txt_file.write("\nRow nb.: " + str(row_nb))
    out_txt_file.write("\nSeats_nb : " + str(abreast_nb * row_nb))
    out_txt_file.write("\n---------------------------------------------")

    log.info("-------- Possible seat configuration --------")
    log.info("----------- Seat = 1 and Aisle = 0 ----------")
    warn = 0
    snd = False
    if IS_DOUBLE_FLOOR != 0:
        out_txt_file.write("\n---------------- First Floor ----------------")
        if toilet_nb >= 1:
            f = ind.toilet_length
            t = toilet_nb - 2
        else:
            f = 0
            t = 0
    seat = list(range(1, int(abreast_nb + aisle_nb) + 1))
    for r in range(1, int(row_nb) + 1):
        if IS_DOUBLE_FLOOR != 0:
            f += ind.seat_length
            if t > 0:
                if (r * abreast_nb) % (PASS_PER_TOILET * 2) == 0:
                    f += ind.toilet_length
                    t -= 2
            if not snd and round((fuse_length - f), 1) <= 0.1:
                snd = True
                out_txt_file.write("\n---------------- Second Floor" + " ---------------")
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

        out_txt_file.write("\n" + str(seat))
        e = int(round((abreast_nb + aisle_nb) // 2.0, 0))
        a = seat[0:e + 1]

        if (int(round((abreast_nb + aisle_nb) % 2.0, 0))) == 0:
            b = seat[e - 1:abreast_nb + aisle_nb]
        else:
            b = seat[e:abreast_nb + aisle_nb]
        b = b[::-1]

        if a != b:
            warn += 1

    if warn >= 1:
        log.warning("Asymmetric passengers disposition in " + str(warn) + " rows")
        out_txt_file.write("\nAsymmetric passengers disposition in " + str(warn) + " rows")

    out_txt_file.close()

    return ()


# ==============================================================================
#   MAIN
# ==============================================================================

if __name__ == "__main__":

    log.warning("###########################################################")
    log.warning("#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####")
    log.warning("###########################################################")
