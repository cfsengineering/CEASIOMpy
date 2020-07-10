"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This module can be called either to generate a surrogate model based on
specified inputs and outputs, or to make a prediction by using a trained model.

Python version: >=3.6

| Author: Vivien Riolo
| Creation: 2020-07-06
| Last modifiction: 2020-07-06

TODO:
    *

"""

# =============================================================================
#   IMPORTS
# =============================================================================

import os
import re
import pickle
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import smt.surrogate_models as sms

from re import split as splt

import ceasiompy.utils.moduleinterfaces as mif
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.ceasiompyfunctions as ceaf

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

from ceasiompy.SMUse.SMUse import Surrogate_model
# =============================================================================
#   GLOBALS
# =============================================================================

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PREDICT_XPATH = '/cpacs/toolspecific/CEASIOMpy/surrogateModel/'
OPTWKDIR_XPATH = '/cpacs/toolspecific/CEASIOMpy/filesPath/optimPath'
# Working surrogate models
model_dict = {'KRG':'KRG(theta0=[1e-2]*xd.shape[1])',
              'KPLSK':'KPLS(theta0=[1e-2])',
              'KPLS':'KPLS(theta0=[1e-2])',
              'LS':'LS()'
              }
# To be implemented
# sm = sms.RMTB(
#     xlimits=xlimits,
#     order=4,
#     num_ctrl_pts=20,
#     energy_weight=1e-15,
#     regularization_weight=0.0,)
# sm = sms.QP()
# sm = GEKPLS(theta0=[1e-2], xlimits=fun.xlimits, extra_points=1, print_prediction=False)
# sm = sms.GENN()

# These methods create a model which is not supported by pickle, so it cannot be saved for now
# 'RBF':'RBF(d0=5)'
# 'IDW':'IDW(p=2)'

# =============================================================================
#   ClASSES
# =============================================================================
class Prediction_tool():
    """Parameters for the surrogate model"""

    def __init__(self):
        """Define default main parameters."""

        # Main parameters
        self.user_file = ''
        self.wkdir = ''

        # Surrogate model settings
        self.type = 'KRG'
        self.objectives = ['cl']
        self.df = pd.DataFrame()

        # Only for the aeromap case
        self.aeromap_case = False

    def get_user_inputs(self):
        """Take user inputs from the GUI."""
        cpacs_path = mif.get_toolinput_file_path('SMTrain')
        tixi = cpsf.open_tixi(cpacs_path)

        # Search working directory
        self.wkdir = cpsf.get_value_or_default(tixi, OPTWKDIR_XPATH, '')
        if self.wkdir == '':
            self.wkdir = ceaf.get_wkdir_or_create_new(tixi)+'/SM'
        if not os.path.isdir(self.wkdir):
            os.mkdir(self.wkdir)

        obj = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'objective', 'cl')
        self.objectives = re.split('; |,',obj)
        self.user_file = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'trainFile', '')
        if self.user_file == '':
            path = cpsf.get_value_or_default(tixi, OPTWKDIR_XPATH, '')
            if path != '':
                self.user_file = path+ '/Variable_history.csv'
        self.aeromap_case = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'aeromap_case/IsCase', False)

        cpsf.close_tixi(tixi, cpacs_path)

# =============================================================================
#   FUNCTIONS
# =============================================================================

def extract_data_set(file, Tool):
    """Get training data from file.

    Retrieve training dataset from a file or generates it automatically. The
    file format must be a CSV with each variable parameters and values are in
    a row. The file must also contain a 'Name' and a 'type' column which are
    needed to describe the variable.

    Args:
        file (str) : Path to user-specified file (CSV format)
        Tool (Prediction_tool object):

    Returns:
        x (numpy array) : Set of points in the design space
        y (numpy array) : Set of points in the result space

    """
    df = pd.read_csv(file)
    df = df.rename(columns={'Unnamed: 0':'Name'})

    # Separate the input and output points
    x = df.loc[[i for i,v in enumerate(df['type']) if v == 'des']]
    y = df.loc[[i for i, v in enumerate(df['type']) if v == 'obj']]
    df = df.loc[[i for i, v in enumerate(df['type']) if v in ['obj','des']]]

    Tool.df = df[['Name','type','getcmd','setcmd']]

    df = df.set_index('Name')
    y = y.set_index('Name')

    # Extract the iteration results only
    x = x[[i for i in x.columns if i.isdigit()]]
    df = df[[i for i in df.columns if i.isdigit()]]

    # Add user-specified objectives
    for obj in Tool.objectives:
        if obj not in df.index:
            var_list = splt('[+*/-]', obj)
            for v in var_list:
                if not v.isdigit() and v != '' and v in df.index:
                    exec('{} = df.loc["{}"]'.format(v, v))
            Tool.df = Tool.df.append({'Name':obj,'type':'obj'},ignore_index=True)
            y.loc[obj]=eval(obj)
    Tool.objectives = y.index

    y = y[[i for i in y.columns if i.isdigit()]]

    return x.transpose().to_numpy(), y.transpose().to_numpy()


def separate_data(x, y):
    """Create two sets of different sizes.

    Create two sets of points for the training and validation of
    the surrogate model.

    Args:
        x (np array) : DoE inputs
        y (np array) : DoE outputs

    Returns:
        xt (np array) : Training inputs
        yt (np array) : Training outputs
        xv (np array) : Validation inputs
        yv (np array) : Validation outputs

    """
    # Sets length of each set
    div = 0.3
    l = len(x)
    sep = int(np.ceil(div*l))

    # Random repartition of the sample
    rng = np.random.default_rng()
    train_index = rng.choice(l, sep, replace=False)
    valid_index = np.delete(np.arange(l), train_index)

    xt = x[train_index]
    yt = y[train_index]
    xv = x[valid_index]
    yv = y[valid_index]

    return xt, yt, xv, yv


def validation_plots(sm, xt, yt, xv, yv):
    """Create validation plots.

    Plot the training and validation set of points and compare the outputs for
    validation.

    Args:
        sm (object): trained surrogate model
        xt,yt (numpy array): training set
        xv,yv (numpy array): validation set

    Returns:
        None.

    """
    yp = sm.predict_values(xv)

    for i in range(0,yv.shape[1]):

        rms = np.sqrt(np.mean((yp[:,i]-yv[:,i])**2))

        plt.figure()
        plt.plot(yv[:,i], yv[:,i], '-', label='$y_{true}$')
        plt.plot(yv[:,i], yp[:,i], 'r.', label='$\hat{y}$ :'+Tool.objectives[i])

        plt.xlabel('$y_{true}$')
        plt.ylabel('$\hat{y}$')

        plt.legend(loc='upper left')
        plt.title('Kriging model: validation of the prediction model\n {}'.format(rms))
        plt.savefig(Tool.wkdir+'/Krigin_validation{}.svg'.format(i))

        plt.figure()
        for j in range(0,xv.shape[1]):
            plt.subplot(1,xv.shape[1]+1,j+1)
            if j == 0:
                plt.ylabel(Tool.objectives[i])
            plt.plot(xt[:,j], yt[:,i], 'b.', label='$y_{training set}$')
            plt.plot(xv[:,j], yp[:,i], 'r.', label='$y_{prediction set}$')
            plt.title('$'+Tool.objectives[i]+'$')
            plt.legend(loc='upper left')
        plt.savefig(Tool.wkdir+'/Output_comparison{}.svg'.format(i))

    plt.show()
    plt.close('all')


def create_model(Tool, xd, yd):
    """Create a surrogate.

    Generate, train and validate a surrogate model with the provided data.

    Args:
        Tool (Prediction_tool object) : Path to CSV file.
        xd, yd (numpy array): Input and output data

    """
    xt, yt, xv, yv = separate_data(xd, yd)
    sm = eval('sms.{}'.format(model_dict[Tool.type]))

    sm.set_training_values(xt, yt)

    sm.train()

    validation_plots(sm, xt, yt, xv, yv)

    Tool.sm = sm


def get_data_file(Tool):
    """Search for the file containing the data set.

    The programm searches for a file given by the user through the GUI, else
    it will look for a file that was generated by a previous DoE by looking at
    the optimPath location in the CPACS file. If no file is found it will run
    a DoE either with Aeromap parameters only, which will be run in one
    subworkflow, or with other parameters which will result in a conventional
    DoE.

    Args:
        Tool (Prediction_tool object): Current predictor object.

    Returns:
        file (str): Path to the file containing the data.

    """
    if os.path.isfile(Tool.user_file):
        file = Tool.user_file
        log.info('User-specified file found')
    else:
        raise FileNotFoundError("""File not found, please enter the name of an
                                 existing CSV file containing the data set.""")

    return file


def save_surrogate(Tool):
    """Save trained surrogate model to a file.

    Create a file to which the class containing the surrogate model and its
    parameters will be saved in order to be re-used using the pickle module.
    The file is either saved in the Output folder of the PredictiveTool module
    or in the current working directory.

    Args:
        Tool (Prediction_tool object): Contains the model

    Returns:
        None.

    """
    date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    filename = Tool.wkdir+'/Surrogate_Model_'+date

    Tool.df.to_csv(Tool.wkdir+'/Data_setup.csv', index=False)

    Model = Surrogate_model()
    Model.df = Tool.df
    Model.sm = Tool.sm

    sm_file = open(filename, 'wb')

    pickle.dump(Model, sm_file)


def generate_model(Tool):
    """Start process of creating a model

    Reads or generates data to create a surrogate model.

    Args:
        Tool (Prediction_tool): Class containing the user specification

    Returns:
        None.

    """
    file = get_data_file(Tool)

    xd, yd = extract_data_set(file, Tool)

    create_model(Tool, xd, yd)

    save_surrogate(Tool)


if __name__ == "__main__":

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    Tool = Prediction_tool()

    Tool.get_user_inputs()

    generate_model(Tool)

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')

