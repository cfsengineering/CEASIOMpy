"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions used to help the cration of SUMO file

Python version: >=3.8

| Author: Aidan Jungo
| Creation: 2021-02-25

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import json

from ceasiompy import log
from cpacspy.cpacsfunctions import copy_branch

from tixi3.tixi3wrapper import Tixi3


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def sumo_str_format(x: float, y: float, z: float) -> str:
    """
    Get coordinate x,y,z into the string format which is use by SUMO.

    Args:
        x (float): x coordinate.
        y (float): y coordinate.
        z (float): z coordinate.

    Returns:
         (str): String point format for SUMO.

    """

    return str(x) + " " + str(y) + " " + str(z)


def sumo_add_nacelle_lip(
    sumo: Tixi3,
    xpath: str,
    ax_offset: float = 1.2,
    rad_offset: float = 0.15,
    shape_coef: float = 0.3
) -> None:
    """
    Add nacelle lips option in SUMO.

    Args:
        sumo (obj): Tixi handle for SUMO.
        xpath (str): xpath.
        ax_offset (float): Axial offset of the nacelle lip.
        rad_offset (float): Radial offset of the nacelle lip.
        shape_coef (float): Shape coefficient of the nacelle lip.

    """

    sumo.createElementAtIndex(xpath, "NacelleInletLip", 1)
    sumo.addTextAttribute(xpath + "/NacelleInletLip", "axialOffset", str(ax_offset))
    sumo.addTextAttribute(xpath + "/NacelleInletLip", "radialOffset", str(rad_offset))
    sumo.addTextAttribute(xpath + "/NacelleInletLip", "shapeCoef", str(shape_coef))


def sumo_add_engine_bc(sumo: Tixi3, eng_name: str, part_uid: str) -> None:
    """
    Add engine boundary conditions in SUMO.

    Args:
        sumo (obj): Tixi handle for SUMO.
        eng_name (str): Name of this engine.
        part_uid (str): Part of the nacelle (fan/core).

    """

    sumo.createElementAtIndex("/Assembly", "JetEngineSpec", 1)
    eng_spec_xpath = "/Assembly/JetEngineSpec[" + str(1) + "]"

    sumo.addTextAttribute(eng_spec_xpath, "massflow", "0")
    sumo.addTextAttribute(eng_spec_xpath, "name", eng_name)

    sumo.createElement(eng_spec_xpath, "Turbofan")
    turbofan_xpath = eng_spec_xpath + "/Turbofan"

    # For now value not taken into account
    sumo.addTextAttribute(turbofan_xpath, "bypass_ratio", "3.5")
    sumo.addTextAttribute(turbofan_xpath, "fan_pr", "1.7")
    sumo.addTextAttribute(turbofan_xpath, "total_pr", "0")
    sumo.addTextAttribute(turbofan_xpath, "turbine_temp", "1400")

    sumo.createElement(eng_spec_xpath, "IntakeRegions")
    intake_xpath = eng_spec_xpath + "/IntakeRegions"

    sumo.createElement(intake_xpath, "JeRegion")
    jeregion_xpath = intake_xpath + "/JeRegion"

    sumo.addTextAttribute(jeregion_xpath, "surface", part_uid)
    sumo.addTextAttribute(jeregion_xpath, "type", "nose")

    sumo.createElement(eng_spec_xpath, "NozzleRegions")
    nozzle_xpath = eng_spec_xpath + "/NozzleRegions"

    sumo.createElement(nozzle_xpath, "JeRegion")
    jeregion_xpath = nozzle_xpath + "/JeRegion"

    sumo.addTextAttribute(jeregion_xpath, "surface", part_uid)
    sumo.addTextAttribute(jeregion_xpath, "type", "tail")


def add_wing_cap(sumo: Tixi3, wg_sk_xpath: str) -> None:
    """
    Add Wing caps.

    Args:
        sumo (Tixi3): Tixi handle for SUMO.
        wg_sk_xpath (_type_): Wing skeleton xpath.

    """

    sumo.createElementAtIndex(wg_sk_xpath, "Cap", 1)
    sumo.addTextAttribute(wg_sk_xpath + "/Cap[1]", "height", "0")
    sumo.addTextAttribute(wg_sk_xpath + "/Cap[1]", "shape", "LongCap")
    sumo.addTextAttribute(wg_sk_xpath + "/Cap[1]", "side", "south")

    sumo.createElementAtIndex(wg_sk_xpath, "Cap", 2)
    sumo.addTextAttribute(wg_sk_xpath + "/Cap[2]", "height", "0")
    sumo.addTextAttribute(wg_sk_xpath + "/Cap[2]", "shape", "LongCap")
    sumo.addTextAttribute(wg_sk_xpath + "/Cap[2]", "side", "north")


def sumo_mirror_copy(sumo: Tixi3, xpath: str, uid: str, is_wing: bool = True) -> None:
    """
    If problem is symmetric in x-z-plane, copy attributes.

    Args:
        sumo (Tixi3): Tixi handle for SUMO.
        xpath (str): xPath to element to copy.
        uid (str): uid of element to copy.
        is_wing (bool = True): True if wing.

    """

    skeleton = "BodySkeleton"
    if is_wing:
        skeleton = "WingSkeleton"

    # Copy the element
    cnt = sumo.getNamedChildrenCount("/Assembly", skeleton)
    sumo.createElementAtIndex("/Assembly", skeleton, cnt + 1)
    xpath_sym = "/Assembly/" + skeleton + "[" + str(cnt + 1) + "]"
    copy_branch(sumo, xpath, xpath_sym)

    # Rename the element
    sumo.removeAttribute(xpath_sym, "name")
    sumo.addTextAttribute(xpath_sym, "name", uid + "_sym")

    # Inverse sign of y origin value
    ori_str = sumo.getTextAttribute(xpath_sym, "origin")
    x, y, z = [float(axis) for axis in ori_str.split(" ")]
    sumo.removeAttribute(xpath_sym, "origin")
    sumo.addTextAttribute(xpath_sym, "origin", sumo_str_format(x, -y, z))

    # Inverse things that must be invert for a mirror copy
    if is_wing:

        sec_cnt = sumo.getNamedChildrenCount(xpath_sym, "WingSection")

        for i_sec in range(sec_cnt):
            xpath_sec = xpath_sym + "/WingSection" + "[" + str(i_sec + 1) + "]"

            # Inverse section center in y
            center_str = sumo.getTextAttribute(xpath_sec, "center")
            x, y, z = [float(axis) for axis in center_str.split(" ")]
            sumo.removeAttribute(xpath_sec, "center")
            sumo.addTextAttribute(xpath_sec, "center", sumo_str_format(x, -y, z))

            # Inverse section dihedral rotation
            dih = sumo.getDoubleAttribute(xpath_sec, "dihedral")
            sumo.removeAttribute(xpath_sec, "dihedral")
            sumo.addTextAttribute(xpath_sec, "dihedral", str(-dih))

            # Inverse section yaw rotation
            yaw = sumo.getDoubleAttribute(xpath_sec, "yaw")
            sumo.removeAttribute(xpath_sec, "yaw")
            sumo.addTextAttribute(xpath_sec, "yaw", str(-yaw))

            # Inverse wing section order with "reversed" attribute
            rev_attr = sumo.getTextAttribute(xpath_sec, "reversed")
            rev_attr = json.loads(rev_attr)
            sumo.removeAttribute(xpath_sec, "reversed")
            sumo.addTextAttribute(xpath_sec, "reversed", str(not rev_attr).lower())

        add_wing_cap(sumo, xpath_sym)

# =================================================================================================
#    MAIN
# =================================================================================================


if __name__ == "__main__":
    log.info("Nothing to execute!")

if __name__ == "__main__":

    print("Nothing to execute!")
