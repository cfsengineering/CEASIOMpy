"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This module can be called to make a prediction by using a trained model.
One particular feature is the Aeromap option which enables you to evaluate all
points of an aeromap in one run, as they can be stored as vectors into the
CPACS file.

Python version: >=3.7

| Author: Vivien Riolo
| Creation: 2020-07-06

TODO:
    *

"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import smt.surrogate_models as sms  # Use after loading the model
from ceasiompy.utils.ceasiomlogger import get_logger
from ceasiompy.utils.moduleinterfaces import get_toolinput_file_path, get_tooloutput_file_path
from ceasiompy.utils.xpath import SMTRAIN_XPATH, SMUSE_XPATH
from cpacspy.cpacsfunctions import create_branch, get_value_or_default
from cpacspy.cpacspy import CPACS
from cpacspy.utils import PARAMS_COEFS

log = get_logger(__file__.split(".")[0])

MODULE_DIR = Path(__file__).parent
MODULE_NAME = MODULE_DIR.name


# =================================================================================================
#   ClASSES
# =================================================================================================


class Surrogate_model:
    """Class to be dumped for later use of a model"""

    def __init__(self):
        """Creates main components"""
        # The dataframe that contains the ordered list of variables to be given
        # to this model, as well as their respective XPATH.
        self.data = pd.DataFrame()

        # The trained surrogate model object
        self.sm = sms.surrogate_model.SurrogateModel()


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def load_surrogate(tixi):
    """Load a surrogate model object from file

    Using the pickle module, a surrogate model object is retrieved from a file
    provided by the user.

    Args:
        tixi (Tixi handle): Handle of the current CPACS.

    Returns:
        sm (object): The surrogate model.

    """

    file = get_value_or_default(tixi, SMUSE_XPATH + "/modelFile", "")

    log.info("Trying to open file" + file)
    with open(file, "rb") as f:
        Model = pickle.load(f)

    return Model


def get_inputs(cpacs, x):
    """Get input for the surrogate model.

    Retrieve the inputs from the cpacs and return them as a numpy array.

    Args:
        cpacs (obj): CPACS instance form cpacspy
        x (DataFrame): Contains the inputs locations.

    Returns:
        inputs (np.array): Array of floats.

    """

    # These variable will be used in eval
    aircraft = cpacs.aircraft.configuration
    wings = aircraft.get_wings()
    fuselage = aircraft.get_fuselages().get_fuselage(1)

    inputs = []

    aeromap_uid = cpacs.tixi.getTextElement(SMUSE_XPATH + "/aeroMapUID")
    xpath = cpacs.tixi.uIDGetXPath(aeromap_uid) + "/aeroPerformanceMap/"

    x.set_index("Name", inplace=True)
    for name in x.index:
        if x.loc[name, "setcmd"] != "-":
            inputs.append(eval(x.loc[name, "getcmd"]))
        else:
            if name in PARAMS_COEFS:
                x.loc[name, "getcmd"] = xpath + name
            inputs.append(cpacs.tixi.getDoubleElement(x.loc[name, "getcmd"]))

    # cpacs.save_cpacs(cpacs_path, overwrite=True)

    return np.array([inputs])


def write_inouts(v, inout, tixi):
    """Write inputs or outputs to cpacs.

    Write the specified input or the predicted output of the model to the
    CPACS file.

    Args:
        v (DataFrame): Contains the inout, locations.
        inout (np.array): Values of the inout.

    Returns:
        None.

    """

    v.fillna("-", inplace=True)
    for i, name in enumerate(v.index):
        if v.loc[name, "setcmd"] != "-":
            exec("{} = {}".format(name, inout[0][i]))
            eval(v.loc[name, "setcmd"])
        elif v.loc[name, "getcmd"] != "-":
            xpath = v.loc[name, "getcmd"]
            create_branch(tixi, xpath)
            tixi.updateDoubleElement(xpath, inout[0][i], "%g")


def aeromap_calculation(sm, cpacs):
    """Make a prediction using only the aeromap entries.

    By using only the aeromap functions this module is way faster to execute. Only
    works  with the aeromap as the other values of the CPACs are not vectors and
    have to be evaluated with a different CPACS every time.

    Args:
        sm (Surrogate model object): Surrogate used to predict the function output.
        cpacs (object): CPACS object from cpacspy

    Returns:
        None.

    """

    aeromap_uid = cpacs.tixi.getTextElement(SMUSE_XPATH + "/aeroMapUID")
    log.info("Using aeromap :" + aeromap_uid)
    aeromap = cpacs.get_aeromap_by_uid(aeromap_uid)

    alt_list = aeromap.get("altitude").tolist()
    mach_list = aeromap.get("machNumber").tolist()
    aoa_list = aeromap.get("angleOfAttack").tolist()
    aos_list = aeromap.get("angleOfSideslip").tolist()

    inputs = np.array([alt_list, mach_list, aoa_list, aos_list]).T
    outputs = sm.predict_values(inputs)

    i = 0
    for alt, mach, aos, aoa in zip(alt_list, mach_list, aos_list, aoa_list):
        aeromap.add_coefficients(
            alt,
            mach,
            aos,
            aoa,
            cl=outputs[i, 0],
            cd=outputs[i, 1],
            cs=outputs[i, 2],
            cml=outputs[i, 3],
            cmd=outputs[i, 4],
            cms=outputs[i, 5],
        )
        i += 1

    print(aeromap)
    aeromap.save()


def predict_output(Model, cpacs):
    """Make a prediction.

    Args:
        Model (Class): Object containing the surrogate model and its parameters

    Returns:
        None.

    """

    sm = Model.sm
    df = Model.df

    x = df.loc[[i for i, v in enumerate(df["type"]) if v == "des"]]
    y = df.loc[[i for i, v in enumerate(df["type"]) if v == "obj"]]
    df = df.set_index("Name")

    inputs = get_inputs(cpacs, x)
    outputs = sm.predict_values(inputs)
    y.set_index("Name", inplace=True)

    write_inouts(y, outputs, cpacs.tixi)


def check_aeromap(tixi):
    """Check if aeromap is not used to train the model.

    To avoid re-writting results on the aeromap that was used to train the
    model, the uid of the training aeromap is compared to the one that is
    given by the user to be computed. Stops the program if they match.

    Args:
        tixi (Tixi handle): Handle of the current CPACS.

    Returns:
        None.

    """

    am_uid_use = get_value_or_default(tixi, SMUSE_XPATH + "/aeroMapUID", "")
    am_uid_train = get_value_or_default(tixi, SMTRAIN_XPATH + "/aeroMapUID", "")

    if am_uid_train == am_uid_use:
        sys.exit("Same aeromap that was used to create the model")


# ==================================================================================================
#    MAIN
# ==================================================================================================


def main(cpacs_path, cpacs_out_path):

    log.info("----- Start of " + MODULE_NAME + " -----")

    # Load the model
    cpacs = CPACS(cpacs_path)
    Model = load_surrogate(cpacs.tixi)

    check_aeromap(cpacs.tixi)

    if get_value_or_default(cpacs.tixi, SMUSE_XPATH + "/AeroMapOnly", False):
        aeromap_calculation(Model.sm, cpacs)
    else:
        predict_output(Model, cpacs)

    cpacs.save_cpacs(cpacs_out_path, overwrite=True)

    log.info("----- End of " + MODULE_NAME + " -----")


if __name__ == "__main__":

    cpacs_path = get_toolinput_file_path("SMUse")
    cpacs_out_path = get_tooloutput_file_path("SMUse")

    main(cpacs_path, cpacs_out_path)
