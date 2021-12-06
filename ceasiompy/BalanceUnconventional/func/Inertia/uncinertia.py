"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script evaluates the Moments of Inertia (Ixx, Iyy, Izz) in case of:

* OEM = Operating empty mass;
* MTOM = Maximum take off mass, with Max Payload:
* ZFM = zero fuel mass;
* ZPM = zero Payload mass
* With a percentage of Fuel and Payload defined by the user.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2019-02-20
"""


# =============================================================================
#   IMPORTS
# =============================================================================

from . import lumpedmassesinertia

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])


# =============================================================================
#   CLASSES
# =============================================================================

"""All classes are defined inside the classes and into
   the InputClasses/Unconventional folder."""


# =============================================================================
#   FUNCTIONS
# =============================================================================
def check_rounding(I1, I2):
    """Evaluation of the rounding digit for the inertia evaluation

       ARGUMENTS
       (float) I1 --Arg.: Yaw moment of inertia with Max Payload.
       (float) I2 --Arg.: Ixy moment of inertia with Max Payload.

       RETURN
       (int) rd  --Out.: Number of rounded digits.
    """
    ex = False
    rd = 0
    rd2 = 0
    while not ex:
        if round(I1, rd) == 0:
            ex = True
        else:
            rd -= 1
        if round(I2, rd2) != 0:
            rd2 -= 1
    rd += 5
    if rd2 > rd:
        rd = rd2

    return rd


def unc_inertia_eval(awg, afg, bout, bi, mw, ed, out_xml):
    """ Unconventional aircraft Moment of Inertia analysis main function.
        It dvides the cases defined and evaluates them calling the
        function in the with_fuse_geom subfolder.

        Source: An introduction to mechanics, 2nd ed., D. Kleppner
                and R. Kolenkow, Cambridge University Press.

        ARGUMENTS
        (class) awg  --Arg.: AircraftWingGeometry class.
        (class) afg  --Arg.: AircraftFuseGeometry class.
        (class) bout --Arg.: BalanceOutputs class.
        (class) bi   --Arg.: BalanceInputs class.
        (class) mw   --Arg.: MassesWeights class.
        (class) ed   --Arg.: EngineData class.
        ##======= Classes are defined in the InputClasses folder =======##

        RETURN
        (float_array) fx      --Out.: Array containing the x-coordinates
                                      of the fuselage nodes.
        (float_array) fy      --Out.: Array containing the y-coordinates
                                      of the fuselage nodes.
        (float_array) fz      --Out.: Array containing the z-coordinates
                                      of the fuselage nodes.
        (float_array) wx      --Out.: Array containing the x-coordinates
                                      of the wing nodes.
        (float_array) wy      --Out.: Array containing the y-coordinates
                                      of the wing nodes.
        (float_array) wz      --Out.: Array containing the z-coordinates
                                      of the wing nodes.
        (class) bout  --Out.: Updated BalanceOutputs class.

    """

    log.info("---------- Inertia Evaluation ---------")
    if bi.USER_EN_PLACEMENT:
        (
            bout.Ixxen,
            bout.Iyyen,
            bout.Izzen,
            bout.Ixyen,
            bout.Iyzen,
            bout.Ixzen,
        ) = lumpedmassesinertia.engine_inertia(bout.center_of_gravity, ed)
    else:
        (bout.Ixxen, bout.Iyyen, bout.Izzen, bout.Ixyen, bout.Iyzen, bout.Ixzen) = (
            0,
            0,
            0,
            0,
            0,
            0,
        )

    # Max Payload Configuration
    log.info("------------ Lumped mass Inertia ------------")
    log.info("--------- Max Payload configuration ---------")
    (fx, fy, fz, Ixxf, Iyyf, Izzf, Ixyf, Iyzf, Ixzf) = lumpedmassesinertia.fuselage_inertia(
        bi.SPACING_FUSE, bout.center_of_gravity, mw.mass_seg_i, afg, out_xml
    )
    (wx, wy, wz, Ixxw, Iyyw, Izzw, Ixyw, Iyzw, Ixzw) = lumpedmassesinertia.wing_inertia(
        bi.WPP, bi.SPACING_WING, afg.fuse_nb, bout.center_of_gravity, mw.mass_seg_i, awg, out_xml
    )

    rd = check_rounding(Izzf + Izzw + bout.Izzen, Ixyf + Ixyw + bout.Ixyen)
    bout.Ixx_lump = round(Ixxf + Ixxw + bout.Ixxen, rd)
    bout.Iyy_lump = round(Iyyf + Iyyw + bout.Iyyen, rd)
    bout.Izz_lump = round(Izzf + Izzw + bout.Izzen, rd)
    bout.Ixy_lump = round(Ixyf + Ixyw + bout.Ixyen, rd)
    bout.Iyz_lump = round(Iyzf + Iyzw + bout.Iyzen, rd)
    bout.Ixz_lump = round(Ixzf + Ixzw + bout.Ixzen, rd)
    # Zero Fuel Configuration
    log.info("---------- Zero Fuel configuration ----------")
    (fx, fy, fz, Ixxf2, Iyyf2, Izzf2, Ixyf2, Iyzf2, Ixzf2) = lumpedmassesinertia.fuselage_inertia(
        bi.SPACING_FUSE, bout.cg_zfm, mw.ms_zfm, afg, out_xml
    )
    (wx, wy, wz, Ixxw2, Iyyw2, Izzw2, Ixyw2, Iyzw2, Ixzw2) = lumpedmassesinertia.wing_inertia(
        bi.WPP, bi.SPACING_WING, afg.fuse_nb, bout.cg_zfm, mw.ms_zfm, awg, out_xml
    )
    bout.Ixx_lump_zfm = round(Ixxf2 + Ixxw2 + bout.Ixxen, rd)
    bout.Iyy_lump_zfm = round(Iyyf2 + Iyyw2 + bout.Iyyen, rd)
    bout.Izz_lump_zfm = round(Izzf2 + Izzw2 + bout.Izzen, rd)
    bout.Ixy_lump_zfm = round(Ixyf2 + Ixyw2 + bout.Ixyen, rd)
    bout.Iyz_lump_zfm = round(Iyzf2 + Iyzw2 + bout.Iyzen, rd)
    bout.Ixz_lump_zfm = round(Ixzf2 + Ixzw2 + bout.Ixzen, rd)

    # Zero Payload Configuration
    log.info("--------- Zero Payload configuration --------")
    (fx, fy, fz, Ixxf3, Iyyf3, Izzf3, Ixyf3, Iyzf3, Ixzf3) = lumpedmassesinertia.fuselage_inertia(
        bi.SPACING_FUSE, bout.cg_zpm, mw.ms_zpm, afg, out_xml
    )
    (wx, wy, wz, Ixxw3, Iyyw3, Izzw3, Ixyw3, Iyzw3, Ixzw3) = lumpedmassesinertia.wing_inertia(
        bi.WPP, bi.SPACING_WING, afg.fuse_nb, bout.cg_zpm, mw.ms_zpm, awg, out_xml
    )

    bout.Ixx_lump_zpm = round(Ixxf3 + Ixxw3 + bout.Ixxen, rd)
    bout.Iyy_lump_zpm = round(Iyyf3 + Iyyw3 + bout.Iyyen, rd)
    bout.Izz_lump_zpm = round(Izzf3 + Izzw3 + bout.Izzen, rd)
    bout.Ixy_lump_zpm = round(Ixyf3 + Ixyw3 + bout.Ixyen, rd)
    bout.Iyz_lump_zpm = round(Iyzf3 + Iyzw3 + bout.Iyzen, rd)
    bout.Ixz_lump_zpm = round(Ixzf3 + Ixzw3 + bout.Ixzen, rd)

    # OEM Configuration
    log.info("------------- OEM configuration -------------")
    (fx, fy, fz, Ixxf4, Iyyf4, Izzf4, Ixyf4, Iyzf4, Ixzf4) = lumpedmassesinertia.fuselage_inertia(
        bi.SPACING_FUSE, bout.cg_oem, mw.ms_oem, afg, out_xml
    )
    (wx, wy, wz, Ixxw4, Iyyw4, Izzw4, Ixyw4, Iyzw4, Ixzw4) = lumpedmassesinertia.wing_inertia(
        bi.WPP, bi.SPACING_WING, afg.fuse_nb, bout.cg_oem, mw.ms_oem, awg, out_xml
    )

    bout.Ixx_lump_oem = round(Ixxf4 + Ixxw4 + bout.Ixxen, rd)
    bout.Iyy_lump_oem = round(Iyyf4 + Iyyw4 + bout.Iyyen, rd)
    bout.Izz_lump_oem = round(Izzf4 + Izzw4 + bout.Izzen, rd)
    bout.Ixy_lump_oem = round(Ixyf4 + Ixyw4 + bout.Ixyen, rd)
    bout.Iyz_lump_oem = round(Iyzf4 + Iyzw4 + bout.Iyzen, rd)
    bout.Ixz_lump_oem = round(Ixzf4 + Ixzw4 + bout.Ixzen, rd)

    # User Configuration
    if bi.USER_CASE:
        log.info("------------- User configuration ------------")
        (
            fx,
            fy,
            fz,
            Ixxfu,
            Iyyfu,
            Izzfu,
            Ixyfu,
            Iyzfu,
            Ixzfu,
        ) = lumpedmassesinertia.fuselage_inertia(
            bi.SPACING_FUSE, bout.cg_user, mw.ms_user, afg, out_xml
        )
        (wx, wy, wz, Ixxwu, Iyywu, Izzwu, Ixywu, Iyzwu, Ixzwu) = lumpedmassesinertia.wing_inertia(
            bi.WPP, bi.SPACING_WING, afg.fuse_nb, bout.cg_user, mw.ms_user, awg, out_xml
        )

        bout.Ixx_lump_user = round(Ixxfu + Ixxwu + bout.Ixxen, rd)
        bout.Iyy_lump_user = round(Iyyfu + Iyywu + bout.Iyyen, rd)
        bout.Izz_lump_user = round(Izzfu + Izzwu + bout.Izzen, rd)
        bout.Ixy_lump_user = round(Ixyfu + Ixywu + bout.Ixyen, rd)
        bout.Iyz_lump_user = round(Iyzfu + Iyzwu + bout.Iyzen, rd)
        bout.Ixz_lump_user = round(Ixzfu + Ixzwu + bout.Ixzen, rd)

    bout.Ixxen = round(bout.Ixxen, rd)
    bout.Iyyen = round(bout.Iyyen, rd)
    bout.Izzen = round(bout.Izzen, rd)
    bout.Ixyen = round(bout.Ixyen, rd)
    bout.Iyzen = round(bout.Iyzen, rd)
    bout.Ixzen = round(bout.Ixzen, rd)

    return (bout, fx, fy, fz, wx, wy, wz)


# =============================================================================


def bwb_inertia_eval(awg, bout, bi, mw, ed, out_xml):
    """ Blended wing Body aircraft Moment of Inertia analysis main function.
        It dvides the cases defined and evaluates them calling the
        function in the no_fuse_geom subfolder.

        Source: An introduction to mechanics, 2nd ed., D. Kleppner
                and R. Kolenkow, Cambridge University Press.

        ARGUMENTS
        (class) awg  --Arg.: AircraftWingGeometry class.
        (class) bout --Arg.: BalanceOutputs class.
        (class) bi   --Arg.: BalanceInputs class.
        (class) mw   --Arg.: MassesWeights class.
        (class) ed   --Arg.: EnfineData class.
        ##======= Classes are defined in the InputClasses folder =======##

        RETURN
        (float_array) wx  --Out.: Array containing the x-coordinates
                                  of the wing nodes.
        (float_array) wy  --Out.: Array containing the y-coordinates
                                  of the wing nodes.
        (float_array) wz  --Out.: Array containing the z-coordinates
                                  of the wing nodes.
        (class) bout  --Out.: Updated BalanceOutputs class.
    """

    log.info("---------- Inertia Evaluation ---------")
    if bi.USER_EN_PLACEMENT:
        (
            bout.Ixxen,
            bout.Iyyen,
            bout.Izzen,
            bout.Ixyen,
            bout.Iyzen,
            bout.Ixzen,
        ) = lumpedmassesinertia.engine_inertia(bout.center_of_gravity, ed)
    else:
        (bout.Ixxen, bout.Iyyen, bout.Izzen, bout.Ixyen, bout.Iyzen, bout.Ixzen) = (
            0,
            0,
            0,
            0,
            0,
            0,
        )

    # Max payload confiuration
    (wx, wy, wz, Ixxw, Iyyw, Izzw, Ixyw, Iyzw, Ixzw) = lumpedmassesinertia.wing_inertia(
        bi.WPP, bi.SPACING_WING, 0, bout.center_of_gravity, mw.mass_seg_i, awg, out_xml
    )

    rd = check_rounding(Izzw + bout.Izzen, Ixyw + bout.Ixyen)
    bout.Ixx_lump = round(Ixxw + bout.Ixxen, rd)
    bout.Iyy_lump = round(Iyyw + bout.Iyyen, rd)
    bout.Izz_lump = round(Izzw + bout.Izzen, rd)
    bout.Ixy_lump = round(Ixyw + bout.Ixyen, rd)
    bout.Iyz_lump = round(Iyzw + bout.Iyzen, rd)
    bout.Ixz_lump = round(Ixzw + bout.Ixzen, rd)

    # Zero Fuel Configuration
    (wx, wy, wz, Ixxw2, Iyyw2, Izzw2, Ixyw2, Iyzw2, Ixzw2) = lumpedmassesinertia.wing_inertia(
        bi.WPP, bi.SPACING_WING, 0, bout.cg_zfm, mw.ms_zfm, awg, out_xml
    )

    bout.Ixx_lump_zfm = round(Ixxw2 + bout.Ixxen, rd)
    bout.Iyy_lump_zfm = round(Iyyw2 + bout.Iyyen, rd)
    bout.Izz_lump_zfm = round(Izzw2 + bout.Izzen, rd)
    bout.Ixy_lump_zfm = round(Ixyw2 + bout.Ixyen, rd)
    bout.Iyz_lump_zfm = round(Iyzw2 + bout.Iyzen, rd)
    bout.Ixz_lump_zfm = round(Ixzw2 + bout.Ixzen, rd)

    # Zero Payload Configuration
    (wx, wy, wz, Ixxw3, Iyyw3, Izzw3, Ixyw3, Iyzw3, Ixzw3) = lumpedmassesinertia.wing_inertia(
        bi.WPP, bi.SPACING_WING, 0, bout.cg_zpm, mw.ms_zpm, awg, out_xml
    )

    bout.Ixx_lump_zpm = round(Ixxw3 + bout.Ixxen, rd)
    bout.Iyy_lump_zpm = round(Iyyw3 + bout.Iyyen, rd)
    bout.Izz_lump_zpm = round(Izzw3 + bout.Izzen, rd)
    bout.Ixy_lump_zpm = round(Ixyw3 + bout.Ixyen, rd)
    bout.Iyz_lump_zpm = round(Iyzw3 + bout.Iyzen, rd)
    bout.Ixz_lump_zpm = round(Ixzw3 + bout.Ixzen, rd)

    # OEM configuration
    (wx, wy, wz, Ixxw4, Iyyw4, Izzw4, Ixyw4, Iyzw4, Ixzw4) = lumpedmassesinertia.wing_inertia(
        bi.WPP, bi.SPACING_WING, 0, bout.cg_oem, mw.ms_oem, awg, out_xml
    )

    bout.Ixx_lump_oem = round(Ixxw4 + bout.Ixxen, rd)
    bout.Iyy_lump_oem = round(Iyyw4 + bout.Iyyen, rd)
    bout.Izz_lump_oem = round(Izzw4 + bout.Izzen, rd)
    bout.Ixy_lump_oem = round(Ixyw4 + bout.Ixyen, rd)
    bout.Iyz_lump_oem = round(Iyzw4 + bout.Iyzen, rd)
    bout.Ixz_lump_oem = round(Ixzw4 + bout.Ixzen, rd)

    # User configuration
    if bi.USER_CASE:
        (wx, wy, wz, Ixxwu, Iyywu, Izzwu, Ixywu, Iyzwu, Ixzwu) = lumpedmassesinertia.wing_inertia(
            bi.WPP, bi.SPACING_WING, 0, bout.cg_user, mw.ms_user, awg, out_xml
        )

        bout.Ixx_lump_user = round(Ixxwu + bout.Ixxen, rd)
        bout.Iyy_lump_user = round(Iyywu + bout.Iyyen, rd)
        bout.Izz_lump_user = round(Izzwu + bout.Izzen, rd)
        bout.Ixy_lump_user = round(Ixywu + bout.Ixyen, rd)
        bout.Iyz_lump_user = round(Iyzwu + bout.Iyzen, rd)
        bout.Ixz_lump_user = round(Ixzwu + bout.Ixzen, rd)

    bout.Ixxen = round(bout.Ixxen, rd)
    bout.Iyyen = round(bout.Iyyen, rd)
    bout.Izzen = round(bout.Izzen, rd)
    bout.Ixyen = round(bout.Ixyen, rd)
    bout.Iyzen = round(bout.Iyzen, rd)
    bout.Ixzen = round(bout.Ixzen, rd)

    return (bout, wx, wy, wz)


# =============================================================================
#   MAIN
# =============================================================================

if __name__ == "__main__":
    log.warning("#########################################################")
    log.warning("# ERROR NOT A STANDALONE PROGRAM, RUN balanceuncmain.py #")
    log.warning("#########################################################")
