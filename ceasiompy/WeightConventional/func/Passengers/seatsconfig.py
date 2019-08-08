"""
    CEASIOMpy: Conceptual Aircraft Design Software

    Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

    The script defines a possible configuration for the seats
    inside the conventional aircraft.

    Works with Python 2.7
    Author : Stefano Piccini
    Date of creation: 2018-09-27
    Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

"""
 InsideDimensions class, can be found on the InputClasses folder inside the
 weightconvclass.py script.
"""


#=============================================================================
#   FUNCTIONS
#=============================================================================

def seat_config(pass_nb, row_nb, abreast_nb, aisle_nb,\
                IS_DOUBLE_FLOOR, toilet_nb, PASS_PER_TOILET,\
                fuse_length, ind, NAME):

    """ The function proposes a sit disposition.

    ARGUMENTS
    (integer) pass_nb           --Arg.: Number of passengers [-].
    (integer) row_nb            --Arg.: Nmber of seat rows [-].
    (integer) abreast_nb        --Arg.: Number of seat abreasts [-].
    (integer) aisle_nb          --Arg.: Number of aisles [-].
    (integer) toilet_nb            --Arg.: Number of toilets [-].
    (integer) IS_DOUBLE_FLOOR   --Arg.: Double floor option [-].
    (integer) PASS_PER_TOILET      --Arg.: Number of passengers per toilet [-].
    (float) fuse_length         --Arg.: Fuselage_length [m].
    (class) ind                 --Arg.: InsideDimensions class [-].
    ##======= Class is defined in the Inputlasses folder =======##

    (char) NAME                 --Arg.: Name of the aircraft.

    RETURNS
    (file) NAME_Seats_disposition.out  --Out.: Print of the possible sets
                                               disposition per each rows.
    """

    out_name = 'ToolOutput/' + NAME + '/' + NAME + '_Seats_disposition.out'
    OutputTextFile = open(out_name, 'w')
    OutputTextFile.write('---------------------------------------------')
    OutputTextFile.write('\nPossible seat configuration -----------------')
    OutputTextFile.write('\nSeat = 1 and Aisle = 0 ----------------------')
    OutputTextFile.write('\n---------------------------------------------')
    OutputTextFile.write('\nAbreast nb.: ' + str(abreast_nb))
    OutputTextFile.write('\nRow nb.: ' + str(row_nb))
    OutputTextFile.write('\nSeats_nb : ' +str(abreast_nb*row_nb))
    OutputTextFile.write('\n---------------------------------------------')

    log.info('-------- Possible seat configuration --------')
    log.info('----------- Seat = 1 and Aisle = 0 ----------')
    warn = 0
    snd = False
    if IS_DOUBLE_FLOOR != 0:
        OutputTextFile.write('\n---------------- First Floor ----------------')
        if toilet_nb >= 1:
            f = ind.toilet_length
            t = toilet_nb - 2
        else:
            f = 0
            t = 0
    seat = list(range(1,int(abreast_nb + aisle_nb) + 1))
    for r in range(1,int(row_nb)+1):
        if IS_DOUBLE_FLOOR != 0:
            f += ind.seat_length
            if t > 0:
                if (r*abreast_nb)%(PASS_PER_TOILET*2) == 0:
                    f += ind.toilet_length
                    t -= 2
            if not snd and round((fuse_length - f),1) <= 0.1:
                snd = True
                OutputTextFile.write('\n---------------- Second Floor'\
                                     + ' ---------------')
        for l in range(int(abreast_nb+aisle_nb)):
            seat[l] = 1
            if aisle_nb == 1:
                seat[int(abreast_nb // 2)] = 0
            elif aisle_nb == 2:
                if abreast_nb %3 == 0:
                    seat[abreast_nb // 3] = 0
                    seat[abreast_nb * 2//3 + 1] = 0
                else:
                    s = int(round(abreast_nb // 3,0))
                    seat[s] = 0
                    seat[-s-1] = 0
        OutputTextFile.write('\n'+str(seat))
        e = (int(round((abreast_nb+aisle_nb)//2.0,0)))
        a = seat[0:e+1]
        if (int(round((abreast_nb+aisle_nb)%2.0,0))) == 0:
            b = seat[e-1:abreast_nb+aisle_nb]
        else:
            b = seat[e:abreast_nb+aisle_nb]
        b = b[::-1]
        if a != b:
            warn += 1

    if warn >= 1:
        log.warning('Asymmetric passengers disposition in ' + str(warn)\
                    +' rows')
        OutputTextFile.write('\nAsymmetric passengers disposition in '\
                             + str(warn) +' rows')
    log.info(str(seat))
    OutputTextFile.close()

    return()


#==============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__':
    log.warning('###########################################################')
    log.warning('#### ERROR NOT A STANDALONE PROGRAM, RUN weightmain.py ####')
    log.warning('###########################################################')
