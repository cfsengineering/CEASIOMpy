"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This module can be called to make a prediction by using a trained model.
One particular feature is the Aeromap option which enables you to evaluate all
points of an aeromap in one run, as they can be stored as vectors into the
CPACS file.

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
import sys
import pickle
import numpy as np
import pandas as pd
import smt.surrogate_models as sms # Use after loading the model

import ceasiompy.utils.apmfunctions as apmf
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
SMTRAIN_XPATH = '/cpacs/toolspecific/CEASIOMpy/surrogateModel/'

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


def load_surrogate(tixi):
    """Load a surrogate model object from file

    Using the pickle module, a surrogate model object is retrieved from a file
    provided by the user.

    Args:
        tixi (Tixi handle): Handle of the current CPACS.

    Returns:
        sm (object): The surrogate model.

    """

    file = cpsf.get_value_or_default(tixi, SMUSE_XPATH+'modelFile', '')

    log.info('Trying to open file'+file)
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
    am_uid = apmf.get_current_aeromap_uid(tixi, 'SMUse')
    am_index = apmf.get_aeromap_index(tixi, am_uid)
    xpath = apmf.AEROPERFORMANCE_XPATH + '/aeroMap' + am_index + '/aeroPerformanceMap/'

    x.set_index('Name', inplace=True)
    for name in x.index:
        if x.loc[name, 'setcmd'] != '-':
            inputs.append(eval(x.loc[name, 'getcmd']))
        else:
            if name in apmf.COEF_LIST+apmf.XSTATES:
                x.loc[name, 'getcmd'] = xpath + name
            inputs.append(tixi.getDoubleElement(x.loc[name, 'getcmd']))

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
        if y.loc[name, 'setcmd'] != '-':
            exec('{} = {}'.format(name, outputs[0][i]))
            eval(y.loc[name, 'setcmd'])
        elif y.loc[name, 'getcmd'] != '-':
            xpath = y.loc[name, 'getcmd']
            cpsf.create_branch(tixi, xpath)
            tixi.updateDoubleElement(xpath, outputs[0][i], '%g')

    tigl.close()
    cpsf.close_tixi(tixi, cpacs_path_out)


def aeromap_calculation(sm, tixi):
    """Make a prediction using only the aeromap entries.

    By using only the aeromap functions this module is way faster to execute. Only
    works  with the aeromap as the other values of the CPACs are not vectors and
    have to be evaluated with a different CPACS every time.

    Args:
        sm (Surrogate model object): Surrogate used to predict the function output.
        tixi (Tixi handle): Handle of the current CPACS.

    Returns:
        None.

    """

    tigl = cpsf.open_tigl(tixi)
    aircraft = cpud.get_aircraft(tigl)
    wings = aircraft.get_wings()
    fuselage = aircraft.get_fuselages().get_fuselage(1)

    aeromap_uid = apmf.get_current_aeromap_uid(tixi, 'SMUse')
    log.info('Using aeromap :'+aeromap_uid)
    Coef = apmf.get_aeromap(tixi, aeromap_uid)

    inputs = np.array([Coef.alt, Coef.mach, Coef.aoa, Coef.aos]).T

    outputs = sm.predict_values(inputs)

    # Re-initiates the values of the results to write the new ones
    Coef.cl = []
    Coef.cd = []
    Coef.cs = []
    Coef.cml = []
    Coef.cmd = []
    Coef.cms = []
    for i in range(outputs.shape[0]):
        Coef.add_coefficients(outputs[i, 0], outputs[i, 1], outputs[i, 2],
                              outputs[i, 3], outputs[i, 4], outputs[i, 5])
    Coef.print_coef_list()
    apmf.save_coefficients(tixi, aeromap_uid, Coef)

    tigl.close()


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
    am_uid_use = cpsf.get_value_or_default(tixi, SMUSE_XPATH+'aeroMapUID', '')
    am_uid_train = cpsf.get_value_or_default(tixi, SMTRAIN_XPATH+'aeroMapUID', '')

    if am_uid_train == am_uid_use:
        sys.exit('Same aeromap that was used to create the model')


if __name__ == "__main__":

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    # Load the model
    tixi = cpsf.open_tixi(cpacs_path)
    Model = load_surrogate(tixi)

    check_aeromap(tixi)

    if cpsf.get_value_or_default(tixi, SMUSE_XPATH+'AeroMapOnly', False):
        aeromap_calculation(Model.sm, tixi)
    else:
        predict_output(Model)

    cpsf.close_tixi(tixi, cpacs_path_out)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')
