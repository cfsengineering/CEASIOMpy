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
| Author : Stefano Piccini
| Date of creation: 2018-09-27

"""

# =============================================================================
#   IMPORTS
# =============================================================================

from .fusecog import center_of_gravity_evaluation
from .bwbcog import center_of_gravity_evaluation_bwb

<<<<<<< HEAD
from ceasiompy import log

=======
from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()
>>>>>>> origin/main


# =============================================================================
#   CLASSES
# =============================================================================

"""All classes are defined inside the classes and into
   the InputClasses/Unconventional folder."""


# =============================================================================
#   FUNCTIONS
# =============================================================================
def unc_center_of_gravity(awg, afg, bout, ui, bi, mw, ed):
    """Unconventional aircraft center of gravity analysis main function.
    It dvides the cases defined and evaluates them calling the
    function in the with_fuse_geom subfolder.

    Source: An introduction to mechanics, 2nd ed., D. Kleppner
            and R. Kolenkow, Cambridge University Press.

    ARGUMENTS
    (class) awg  --Arg.: AircraftWingGeometry class.
    (class) afg  --Arg.: AircraftFuseGeometry class.
    (class) bout --Arg.: BalanceOutputs class.
    (class) ui    --Arg.: UserInputs class.
    (class) bi    --Arg.: BalanceInputs class.
    (class) mw    --Arg.: MassesWeights class.
    (class) ed    --Arg.: EngineData class.
    ##======= Classes are defined in the InputClasses folder =======##

    RETURN
    (float_array) airplane_centers_segs --Out.: point at the center of
                                                each segment of the
                                                aircraft.
    (class) bout  --Out.: Updated BalanceOutputs class.
    """

    # Fuel amount inside fuselage check
    for i in ui.F_FUEL:
        if i > 80:
            fn = ui.F_FUEL.index(i)
            ui.F_FUEL[fn] = 80
            log.warning(
                "Fuel amount inside the fuselage number "
                + str(fn)
                + "greater than 80%, automatically reduced to 80%."
            )
            log.warning("F_FUEL = " + str(ui.F_FUEL))

    F_PERC_MAXPASS = (mw.mass_fuel_maxpass / mw.mass_fuel_tot) * 100

    log.info("---- Center of Gravity coordinates ----")
    log.info("------ Max Payload configuration ------")
    (bout.center_of_gravity, mw.mass_seg_i, airplane_centers_segs) = center_of_gravity_evaluation(
        F_PERC_MAXPASS, 100, afg, awg, mw, ed, ui, bi
    )
    log.info("[x, y, z] = " + str(bout.center_of_gravity))

    log.info("------- Zero Fuel configuration -------")
    (bout.cg_zfm, mw.ms_zfm, airplane_centers_segs) = center_of_gravity_evaluation(
        0, 100, afg, awg, mw, ed, ui, bi
    )
    log.info("[x, y, z] = " + str(bout.cg_zfm))

    log.info("----- Zero Payload configuration ------")
    (bout.cg_zpm, mw.ms_zpm, airplane_centers_segs) = center_of_gravity_evaluation(
        100, 0, afg, awg, mw, ed, ui, bi
    )
    log.info("[x, y, z] = " + str(bout.cg_zpm))

    log.info("---------- OEM configuration ----------")
    (bout.cg_oem, mw.ms_oem, airplane_centers_segs) = center_of_gravity_evaluation(
        0, 0, afg, awg, mw, ed, ui, bi
    )
    log.info("[x, y, z] = " + str(bout.cg_oem))

    if bi.USER_CASE:
        if bi.P_PERC < 0 or bi.F_PERC < 0:
            raise Exception("Error, F_PERC and P_PERC can" + " not be negative.")
        if (
            mw.mass_fuel_maxpass * (bi.F_PERC / 100) + mw.mass_payload * (bi.P_PERC / 100)
        ) > mw.mass_fuel_maxpass + mw.mass_payload:
            log.warning(
                "Exceeding maximum fuel amount with the"
                + "chosen payload mass,"
                + "fuel mass automatically reduced"
            )
            bi.F_PERC = 1 + ((mw.mass_payload / mw.mass_fuel_maxpass) * (1 - (bi.P_PERC / 100)))
            log.warning("FUEL percentage: " + str(bi.F_PERC * 100))
        log.info("---------- User configuration ---------")
        (bout.cg_user, mw.ms_user, airplane_centers_segs) = center_of_gravity_evaluation(
            bi.F_PERC * 100, bi.P_PERC, afg, awg, mw, ed, ui, bi
        )
        log.info("[x, y, z] = " + str(bout.cg_user))

    return (bout, airplane_centers_segs)


# =============================================================================


def bwb_center_of_gravity(awg, bout, ui, bi, mw, ed):
    """Blended wing Body aircraft center of gravity analysis main function.
    It dvides the cases defined and evaluates them calling the
    function in the no_fuse_geom subfolder.

    Source: An introduction to mechanics, 2nd ed., D. Kleppner
            and R. Kolenkow, Cambridge University Press.

    ARGUMENTS
    (class) awg  --Arg.: AircraftWingGeometry class.
    (class) bout --Arg.: BalanceOutputs class.
    (class) bi       --Arg.: BalanceInputs class.
    (class) mw       --Arg.: MassesWeights class.
    (class) ed    --Arg.: EnfineData class.
    ##======= Classes are defined in the InputClasses folder =======##

    RETURN
    (float_array) airplane_centers_segs --Out.: point at the center of
                                                each segment of the
                                                aircraft.
    (class) bout  --Out.: Updated BalanceOutputs class.
    """
    F_PERC_MAXPASS = (mw.mass_fuel_maxpass / mw.mass_fuel_tot) * 100

    log.info("---- Center of Gravity coordinates ----")
    log.info("------ Max Payload configuration ------")
    (
        bout.center_of_gravity,
        mw.mass_seg_i,
        airplane_centers_segs,
    ) = center_of_gravity_evaluation_bwb(F_PERC_MAXPASS, 100, awg, mw, ed, ui, bi)
    log.info("[x, y, z] = " + str(bout.center_of_gravity))

    log.info("------- Zero Fuel configuration -------")
    (bout.cg_zfm, mw.ms_zfm, airplane_centers_segs) = center_of_gravity_evaluation_bwb(
        0, 100, awg, mw, ed, ui, bi
    )
    log.info("[x, y, z] = " + str(bout.cg_zfm))

    log.info("----- Zero Payload configuration ------")
    (bout.cg_zpm, mw.ms_zpm, airplane_centers_segs) = center_of_gravity_evaluation_bwb(
        100, 0, awg, mw, ed, ui, bi
    )
    log.info("[x, y, z] = " + str(bout.cg_zpm))

    log.info("---------- OEM configuration ----------")
    (bout.cg_oem, mw.ms_oem, airplane_centers_segs) = center_of_gravity_evaluation_bwb(
        0, 0, awg, mw, ed, ui, bi
    )
    log.info("[x, y, z] = " + str(bout.cg_oem))

    if bi.USER_CASE:
        if bi.P_PERC < 0 or bi.F_PERC < 0:
            raise Exception("Error, F_PERC and P_PERC can" + " not be negative.")
        if (
            mw.mass_fuel_maxpass * (bi.F_PERC / 100) + mw.mass_payload * (bi.P_PERC / 100)
        ) > mw.mass_fuel_maxpass + mw.mass_payload:
            log.warning(
                "Exceeding maximum fuel amount with the"
                + "chosen payload mass,"
                + "fuel mass automatically reduced"
            )
            bi.F_PERC = 1 + ((mw.mass_payload / mw.mass_fuel_maxpass) * (1 - bi.P_PERC / 100))
            log.warning("FUEL percentage: " + str(bi.F_PERC))
        log.info("---------- User configuration ---------")
        (bout.cg_user, mw.ms_user, airplane_centers_segs) = center_of_gravity_evaluation_bwb(
            bi.F_PERC, bi.P_PERC, awg, mw, ed, ui, bi
        )
        log.info("[x, y, z] = " + str(bout.cg_user))

    return (bout, airplane_centers_segs)


# =============================================================================
#   MAIN
# =============================================================================

if __name__ == "__main__":
    log.warning("###########################################################")
    log.warning("# ERROR NOT A STANDALONE PROGRAM, RUN balanceuncmain.py #")
    log.warning("###########################################################")
