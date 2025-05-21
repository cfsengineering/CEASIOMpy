"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Evaluation of the mass of the aircraft engines.

| Author : Stefano Piccini
| Date of creation: 2018-12-19

"""


# =============================================================================
#   IMPORTS
# =============================================================================

import numpy as np

from ceasiompy import log


# =============================================================================
#   FUNCTIONS
# =============================================================================


def engine_definition(mw, ui, ed):
    """
    The function evaluates the engine characteristics, the user must define
    on the engine class the following quantities:
    - turboprop True or False;
    - WING_MOUNTED True  or False;
    - EN_PLACEMENT;
    - NE.

    Args:
        mw (class): MassesWeights class.
        ui (class): UserInputs class.
        ed (class): EngineData class.

    OUTPUT
        ed (class) : Updated EngineData class.
        en_mass*ed.NE ...?

    """

    if not ed.turboprop:
        LD_CRU = 0.866 * ui.LD
        # [kN] Cruise Thrust for 1 engine
        thrust = ((mw.maximum_take_off_mass * 9.81) / LD_CRU) / (1000.0 * ed.NE)
        # [kN] Max Take off Thrust for 1 engine
        ed.max_thrust = thrust / 0.25
        en_mass = round((16.948 * ed.max_thrust + 447.985), 0)
    else:
        LD_CRU = ui.LD
        # [kN] Cruise Thrust for 1 engine
        thrust = ((mw.maximum_take_off_mass * 9.81) / LD_CRU) / (1000.0 * ed.NE)
        # [kW] Max Take off Power for 1 engine
        ed.max_thrust = thrust / 0.5
        power = ed.max_thrust * ui.CRUISE_SPEED / 0.85
        en_mass = round((0.221 * power + 80.986), 0)

    ed.en_mass = en_mass

    return (round(en_mass * ed.NE, 0), ed)


# =============================================================================


def check_ed(ed):
    """
    The function checks if all the engine data are defined correctly in
    case they are defined directly by the user.

    Args:
        ed (class): EngineData class.

    """
    s = np.shape(ed.EN_PLACEMENT)
    if not ed.NE:
        raise Exception("No engine defined for the aircraft")
    elif not ed.en_mass:
        raise Exception("Engine weight equal to zero")
    elif not ed.max_thrust:
        raise Exception("Engine max thrust equal to zero")
    elif s[0] < ed.NE or s[1] < 3:
        raise Exception("Incorrect engine placement")
    else:
        log.info("EngineData class defined correctly.")


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":

    log.warning("########################################################")
    log.warning("# ERROR NOT A STANDALONE PROGRAM, RUN weightuncmain.py #")
    log.warning("########################################################")
