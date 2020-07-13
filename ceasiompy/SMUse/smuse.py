"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This module can be called either to generate a surrogate model based on
specified inputs and outputs, or to make a prediction by using a trained model.

Python version: >=3.6

| Author: Vivien Riolo
| Creation: 2020-07-06
| Last modification: 2020-07-06

TODO:
    *

"""


# =============================================================================
#   IMPORTS
# =============================================================================

import os
import pickle
import numpy as np
import pandas as pd
import smt.surrogate_models as sms # Use after loading the model

import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.moduleinterfaces as mif
import ceasiompy.CPACSUpdater.cpacsupdater as cpud

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])


# =============================================================================
#   GLOBALS
# =============================================================================

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_NAME = os.path.basename(os.getcwd())
SMUSE_XPATH = '/cpacs/toolspecific/CEASIOMpy/surrogateModelUse/'

cpacs_path = mif.get_toolinput_file_path('SMUse')
cpacs_path_out = mif.get_tooloutput_file_path('SMUse')

# =============================================================================
#   ClASSES
# =============================================================================
class Surrogate_model():
    """Class to be dumped for later use of a model"""

    def __init__(self):
        """Creates main components"""
        # The dataframe that contains the ordered list of variables to be given
        # to this model, as well as their respective XPATH.
        self.data = pd.DataFrame()

        # The trained surrogate model object
        self.sm = sms.surrogate_model.SurrogateModel()

# =============================================================================
#   FUNCTIONS
# =============================================================================


def load_surrogate():
    """Load a surrogate model object from file

    Using the pickle module, a surrogate model object is retrieved from a file
    provided by the user.

    Args:
        None.

    Returns:
        sm (object): The surrogate model.

    """
    tixi = cpsf.open_tixi(cpacs_path)
    file = cpsf.get_value_or_default(tixi, SMUSE_XPATH+'modelFile', '')
    cpsf.close_tixi(tixi, cpacs_path)

    try:
        f = open(file, 'rb')
    except:
        raise IOError('File could not be opened')

    Model = pickle.load(f)

    return Model


def get_inputs(x):
    """Get input for the surrogate model.

    Retrieve the inputs from the cpacs and return them as a numpy array.

    Args:
        x (DataFrame): Contains the inputs locations.

    Returns:
        inputs (np.array): Array of floats.

    """
    tixi = cpsf.open_tixi(cpacs_path)
    tigl = cpsf.open_tigl(tixi)
    aircraft = cpud.get_aircraft(tigl)
    wings = aircraft.get_wings()
    fuselage = aircraft.get_fuselages().get_fuselage(1)

    inputs = []

    x.set_index('Name', inplace=True)
    for name in x.index:
        if x.loc[name,'setcmd'] != '-':
            inputs.append(eval(x.loc[name,'setcmd']))
        else:
            inputs.append(tixi.getDoubleElement(x.loc[name,'getcmd']))

    tigl.close()
    cpsf.close_tixi(tixi, cpacs_path)

    inputs = np.array([inputs])
    return inputs


def write_outputs(y, outputs):
    """Write outputs to cpacs.

    Write the predicted output of the model to the CPACS file.

    Args:
        y (DataFrame): Contains the outputs, locations.
        outputs (np.array): Values of the outputs.

    Returns:
        None.

    """
    tixi = cpsf.open_tixi(cpacs_path)
    tigl = cpsf.open_tigl(tixi)
    aircraft = cpud.get_aircraft(tigl)
    wings = aircraft.get_wings()
    fuselage = aircraft.get_fuselages().get_fuselage(1)

    y.fillna('-', inplace=True)
    for i, name in enumerate(y.index):
        if y.loc[name,'setcmd'] != '-':
            exec('{} = {}'.format(name, outputs[0][i]))
            eval(y.loc[name,'setcmd'])
        elif y.loc[name,'getcmd'] != '-':
            xpath = y.loc[name,'getcmd']
            if not tixi.checkElement(xpath):
                elem_name = xpath.split('/')[-1]
                xpath = xpath.replace('/'+elem_name,'')
                tixi.addDoubleElement(xpath, elem_name, outputs[0][i], '%g')
            else:
                tixi.updateDoubleElement(y.loc[name,'getcmd'], outputs[0][i],'%g')

    tigl.close()
    cpsf.close_tixi(tixi, cpacs_path_out)


def predict_output(Model):
    """Make a prediction.

    Args:
        Model (Class): Object containing the surrogate model and its parameters

    Returns:
        None.

    """
    sm = Model.sm
    df = Model.df
    x = df.loc[[i for i,v in enumerate(df['type']) if v == 'des']]
    y = df.loc[[i for i, v in enumerate(df['type']) if v == 'obj']]
    df = df.set_index('Name')

    inputs = get_inputs(x)
    outputs = sm.predict_values(inputs)
    y.set_index('Name', inplace=True)
    write_outputs(y, outputs)


if __name__ == "__main__":

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    # Load the model
    Model = load_surrogate()
    predict_output(Model)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')


