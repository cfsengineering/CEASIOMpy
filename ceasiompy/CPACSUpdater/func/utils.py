"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Utils for CPACSUpdater.

Python version: >=3.8

| Author: Leon Deligny
| Creation: 2025-Feb-26

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
import math
import matplotlib

import numpy as np
import matplotlib.pyplot as plt

from numpy import array

from numpy import ndarray
from typing import Optional
from tixi3.tixi3wrapper import Tixi3

from typing import (
    List,
    Tuple,
)

from ceasiompy import log

# =================================================================================================
#   BACKEND SETTING
# =================================================================================================

if os.environ.get('DISPLAY', '') == '':
    matplotlib.use('Agg')
else:
    matplotlib.use('TkAgg')

# ==============================================================================
#   FUNCTIONS
# ==============================================================================


def copy_children(tixi: Tixi3, source_xpath: str, target_xpath: str, copy_id: str) -> None:
    """
    Modifies tixi handle of CPACS file.
    Copies all childrens of attribute at source_xpath to target_xpath.
    Recursive call until there are no more childrens.

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.
        source_xpath (str): xPath of attribute to copy.
        target_xpath (str): xPath to copy's destination.
        copy_id (str): Copy identifier to modify the uIDs in the CPACS.

    """
    # Get the number of children at the source XPath
    num_children = tixi.getNumberOfChilds(source_xpath)

    for i in range(1, num_children + 1):
        # Get the XPath of the child
        child_name = tixi.getChildNodeName(source_xpath, i)
        child_xpath = f"{source_xpath}/{child_name}"

        # Check if there are multiple elements with the same name
        num_same_name_children = sum(1 for j in range(
            1, num_children + 1) if tixi.getChildNodeName(source_xpath, j) == child_name)
        if num_same_name_children > 1:
            child_xpath += f"[{i}]"

        if (child_name != "#text") and (child_name != "#comment"):
            # Create the child element at the target XPath
            new_child_xpath = f"{target_xpath}/{child_name}"
            if num_same_name_children > 1:
                new_child_xpath += f"[{i}]"

            tixi.createElement(target_xpath, child_name)

            # Check if the child element exists before copying attributes
            if tixi.checkElement(child_xpath):

                # Copy the attributes of the child element
                num_attributes = tixi.getNumberOfAttributes(child_xpath)
                for j in range(1, num_attributes + 1):
                    attr_name = tixi.getAttributeName(child_xpath, j)
                    attr_value = tixi.getTextAttribute(child_xpath, attr_name)
                    if attr_name == "uID":
                        attr_value += copy_id

                    tixi.addTextAttribute(new_child_xpath, attr_name, attr_value)

                # Recursively copy the children of the child element
                copy_children(tixi, child_xpath, new_child_xpath, copy_id)
        elif (child_name == "#text"):
            # Copy the text value if the child is a text node
            text_value = tixi.getTextElement(source_xpath)
            tixi.updateTextElement(target_xpath, text_value)


def array_to_str(x: ndarray, z: ndarray) -> Tuple[str, str, str]:
    l = len(x)
    y = np.zeros(l)

    # Convert back to strings
    x_str = ';'.join(map(str, x))
    y_str = ';'.join(map(str, y))
    z_str = ';'.join(map(str, z))

    return x_str, y_str, z_str


def copy(tixi: Tixi3, xpath: str, copy_name: str, ids: str, sym: bool = True) -> str:
    """
    Copies an element and its children from a given xpath
    to a new element with the specified copy_name.

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.
        xpath (str): xPath of the element to copy.
        copy_name (str): Name for the new copied element.

    Returns:
        (str): New xPath to copied element.

    """
    # Create the new element at the same level as the source element
    parent_xpath = xpath.rsplit('/', 1)[0]
    new_xpath = f"{parent_xpath}/{ids}"
    tixi.createElement(parent_xpath, ids)

    # Copy the children of the source element to the new element
    copy_children(tixi, xpath, new_xpath, '_' + ids)

    update_uids(tixi, new_xpath, '_' + ids)

    # Modify name and description
    modify_element(tixi, new_xpath + "/name", ids)
    modify_element(tixi, new_xpath + "/description", ids)

    if sym:
        modify_attribute(tixi, new_xpath, "symmetry", "x-z-plane")
    modify_attribute(tixi, new_xpath, "uID", ids)

    if copy_name == "wing":
        modify_attribute(tixi, new_xpath, "xsi:type", "wingType")

    parent_xpath = new_xpath.rsplit('/', 1)[0]

    tixi.renameElement(parent_xpath, ids, copy_name)

    ret_xpath = parent_xpath + f"/{copy_name}[@uID='{ids}']"

    return ret_xpath


def symmetric_operation(tixi: Tixi3, xpath: str) -> None:
    """
    Replaces value x to -x at specified xPath.
    Symmetry operation centered at 0.
    """
    nb = float(tixi.getTextElement(xpath))
    nb = -nb
    tixi.updateTextElement(xpath, str(nb))


def symmetry(tixi: Tixi3, xpath: str) -> None:
    """
    Apply symmetry transformation to all children of the given xpath.
    Specifically, for any child element named "y", multiply its value by -1.

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.
        xpath (str): xPath to the parent element.

    """
    # Get the number of children at the given XPath
    num_children = tixi.getNumberOfChilds(xpath)

    for i in range(1, num_children + 1):
        # Get the name and XPath of the child
        child_name = tixi.getChildNodeName(xpath, i)
        child_xpath = f"{xpath}/{child_name}"

        # Check if there are multiple elements with the same name
        num_same_name_children = sum(1 for j in range(
            1, num_children + 1) if tixi.getChildNodeName(xpath, j) == child_name)
        if num_same_name_children > 1:
            child_xpath += f"[{i}]"

        if child_name == "y":
            # Apply symmetry transformation to the "y" element
            y_value_str = tixi.getTextElement(child_xpath)
            y_value = float(y_value_str)
            y_value = -y_value
            tixi.updateTextElement(child_xpath, str(y_value))

        if (child_name != "#text") and (child_name != "#comment"):
            # Recursively apply symmetry to the child's children
            symmetry(tixi, child_xpath)


def update_uid_element(tixi: Tixi3, xpath: str, element_name: str, uids_identifier: str) -> None:
    """
    Helper function to update a specific UID element if it exists.

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.
        xpath (str): xPath to the element.
        element_name (str): Name of the UID element to update.
        uids_identifier (str): uID identifier to add.

    """
    element_xpath = f"{xpath}/{element_name}"
    if tixi.checkElement(element_xpath):
        uid_value = tixi.getTextElement(element_xpath)
        if uid_value:
            modify_element(tixi, element_xpath, uid_value + uids_identifier)


def update_uids(tixi: Tixi3, xpath: str, uids_identifier: str) -> None:
    """
    Recursively update the specified elements with uids_identifier suffix.

    Args:
        tixi (Tixi3): Tixi handle of CPACS file.
        xpath (str): xPath to start the search.
        uids_identifier (str): uID identifier to add.

    """

    num_children = tixi.getNumberOfChilds(xpath)
    for i in range(1, num_children + 1):
        child_name = tixi.getChildNodeName(xpath, i)
        child_xpath = f"{xpath}/{child_name}"
        num_same_name_children = sum(1 for j in range(
            1, num_children + 1) if tixi.getChildNodeName(xpath, j) == child_name)

        if num_same_name_children > 1:
            child_xpath += f"[{i}]"

        if child_name not in ["#text", "#comment"]:
            if tixi.checkElement(child_xpath):
                uid_elements = [
                    "fromSectionUID", "toSectionUID", "fromElementUID",
                    "toElementUID", "parentUID", "referenceUID"
                ]
                for element in uid_elements:
                    update_uid_element(tixi, child_xpath, element, uids_identifier)

                update_uids(tixi, child_xpath, uids_identifier)


def remove(tixi: Tixi3, xpath: str, attr_name: Optional[str] = None) -> None:
    """
    Remove element/attribute and its childrens at specified xpath.
    """
    try:
        if tixi.checkElement(xpath):
            tixi.removeElement(xpath)
        elif attr_name is not None:
            if tixi.checkAttribute(xpath, attr_name):
                tixi.removeAttribute(xpath, attr_name)
            log.warning(f"Attribute {attr_name} not found at '{xpath}'.")
        else:
            log.warning(f"No elements found at '{xpath}'.")

    except Exception as e:
        log.warning(f"An error occurred while removing the element at '{xpath}': {e}.")


def modify_element(tixi: Tixi3, xpath: str, new_value: str) -> None:
    try:
        if tixi.checkElement(xpath):
            tixi.updateTextElement(xpath, new_value)
        else:
            raise ValueError(f"Element at xpath '{xpath}' not found.")
    except Exception as e:
        log.warning(f"An error occurred while modifying an element in the CPACS file: {e}")


def modify_attribute(tixi: Tixi3, xpath: str, attribute: str, new_value: str) -> None:
    try:
        if tixi.checkElement(xpath):
            tixi.addTextAttribute(xpath, attribute, new_value)
        else:
            raise ValueError(f"Element at xpath '{xpath}' not found.")
    except Exception as e:
        log.warning(f"An error occurred while modifying an attribute in the CPACS file: {e}")


def interpolate(
    x1: float,
    z1: float,
    x2: float,
    z2: float,
    max_dist: float
) -> List[Tuple[float, float]]:

    distance = math.sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2)
    if distance > max_dist:
        mid_x = (x1 + x2) / 2
        mid_z = (z1 + z2) / 2
        return interpolate(x1, z1, mid_x, mid_z, max_dist) + \
            [(mid_x, mid_z)] + interpolate(mid_x, mid_z, x2, z2, max_dist)
    else:
        return [(x2, z2)]


def interpolate_points(
    x: ndarray,
    z: ndarray,
    max_dist: float,
) -> Tuple[ndarray, ndarray]:
    """
    Interpolate points through

    """
    new_x = [x[0]]
    new_z = [z[0]]

    for (x1, z1), (x2, z2) in zip(zip(x[:-1], z[:-1]), zip(x[1:], z[1:])):
        interpolated_points = interpolate(x1, z1, x2, z2, max_dist)
        for x_, z_ in interpolated_points:
            new_x.append(x_)
            new_z.append(z_)

    return array(new_x), array(new_z)


def find_max_x(x: ndarray, z: ndarray) -> Tuple[float, float, float, float]:
    """
    Finds the biggest x_value such that z is positive/negative.
    """
    pos_mask = z > 0
    neg_mask = z < 0

    if np.any(pos_mask):
        max_x_pos = np.max(x[pos_mask])
        z_pos = z[pos_mask][np.argmax(x[pos_mask])]
    else:
        max_x_pos, z_pos = None, None

    if np.any(neg_mask):
        max_x_neg = np.max(x[neg_mask])
        z_neg = z[neg_mask][np.argmax(x[neg_mask])]
    else:
        max_x_neg, z_neg = None, None

    return max_x_pos, z_pos, max_x_neg, z_neg


def find_min_x(x: ndarray, z: ndarray) -> Tuple[float, float, float, float]:
    """
    Finds the smallest x_value such that z is positive/negative.
    """
    pos_mask = z > 0
    neg_mask = z < 0

    if np.any(pos_mask):
        min_x_pos = np.min(x[pos_mask])
        z_pos = z[pos_mask][np.argmin(x[pos_mask])]
    else:
        min_x_pos, z_pos = None, None

    if np.any(neg_mask):
        min_x_neg = np.min(x[neg_mask])
        z_neg = z[neg_mask][np.argmin(x[neg_mask])]
    else:
        min_x_neg, z_neg = None, None

    return min_x_pos, z_pos, min_x_neg, z_neg


def plot_values(
    x: ndarray,
    z: ndarray,
    x_flap: ndarray = None,
    z_flap: ndarray = None,
) -> None:
    plt.plot(x, z, marker='o', label='X vs Z values')

    if x_flap is not None and z_flap is not None:
        plt.plot(
            x_flap,
            z_flap,
            marker='x',
            label='X Flap vs Z Flap values'
        )

    plt.xlabel('X values')
    plt.ylabel('Z values')
    plt.title('Plot of X vs Z values')
    plt.legend()
    plt.grid(True)
    plt.show()


# ==============================================================================
#    MAIN
# ==============================================================================
if __name__ == "__main__":
    log.info("Nothing to execute!")
