"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This module can be called either to generate a surrogate model based on
specified inputs and outputs, or to make a prediction by using a trained model.

Python version: >=3.6

| Author: Vivien Riolo
| Creation: 2020-06-09
| Last modifiction: 2020-06-09

TODO:
    *

"""

# =============================================================================
#   IMPORTS
# =============================================================================

import os
import pickle
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import smt.surrogate_models as sms
import smt.sampling_methods as smp

from re import split as splt

import ceasiompy.utils.moduleinterfaces as mif
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.optimfunctions as opf
import ceasiompy.utils.workflowfunctions as wkf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.Optimisation.func.tools as tls

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])


# =============================================================================
#   GLOBALS
# =============================================================================

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PREDICT_XPATH = '/cpacs/toolspecific/CEASIOMpy/surrogateModel/'

# Working surrogate models
model_dict = {'KRG':'KRG(theta0=[1e-2]*xd.shape[1])',
              'KPLSK':'KPLS(theta0=[1e-2])',
              'KPLS':'KPLS(theta0=[1e-2])',
              'RBF':'RBF(d0=5)',
              'IDW':'IDW(p=2)',
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

# =============================================================================
#   ClASSES
# =============================================================================


class Prediction_tool():
    """Parameters for the surrogate model"""

    def __init__(self):
        """Define default main parameters."""

        # Main parameters
        self.use_model = False
        self.user_file = ''
        self.result_file = ''

        # Surrogate model settings
        self.type = 'KRG'
        self.objectives = ['cl']
        self.df = pd.DataFrame()

        # Only for the aeromap case
        self.aeromap_case = False
        self.aeromap_name = ''
        self.doedriver = 'LatinHypercube'
        self.samplesnb = 3

    def get_user_inputs(self, cpacs_path):
        """Take user inputs from the GUI."""
        cpacs_path = mif.get_toolinput_file_path('PredictiveTool')
        tixi = cpsf.open_tixi(cpacs_path)

        self.aeromap_case = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'useModel', False)
        obj = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'objective', ['cl'])
        if type(obj) == list:
            self.objectives = obj
        else:
            self.objectives = obj.split(';')
        self.user_file = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'Config/filepath', '')
        self.result_file = cpsf.get_value_or_default(tixi, opf.OPTWKDIR_XPATH, '')+'/Variable_history.csv'

        self.aeromap_case = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'aeromap_case/IsCase', False)
        self.doedriver = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'aeromap_case/uID', '')
        self.doedriver = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'aeromap_case/DoEdriver', 'LatinHypercube')
        self.samplesnb = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'aeromap_case/sampleNB', 3)

        cpsf.close_tixi(tixi, cpacs_path)

# =============================================================================
#   FUNCTIONS
# =============================================================================

def extract_data_set(file, Model):
    """Get training data from file.

    Retrieve training dataset from a file or generates it automatically. The
    file format must be a CSV with each variable parameters and values are in
    a row. The file must also contain a 'Name' and a 'type' column which are
    needed to describe the variable.

    Args:
        file (str) : Path to user-specified file (CSV format)

    Returns:
        x (DataFrame) : Set of points in the design space
        y (DataFrame) : Set of points in the result space

    TODO:
        * Maybe better deal with the dataframe, case of multiple objective functions ?

    """
    df = pd.read_csv(file)
    df = df.rename(columns={'Unnamed: 0':'Name'})

    # Drop duplicate (first and second columns are the same)
    df = df.drop('0',1)

    # Separate the input and output points
    x = df.loc[[i for i,v in enumerate(df['type']) if v == 'des']]
    y = df.loc[[i for i, v in enumerate(df['type']) if v == 'obj']]

    Model.df = df[['Name','type']]

    df = df.set_index('Name')

    # Extract the iteration results only
    x = x[[i for i in x.columns if i.isdigit()]]
    df = df[[i for i in df.columns if i.isdigit()]]

    # Compute the objectives in the aeromap case, else they are already given
    if 'Variable_history' not in file:
        y = pd.DataFrame()
        for i, obj_expr in enumerate(Model.objectives):
            for name in splt('[+*/-]', obj_expr):
                obj_expr = obj_expr.replace(name,'df.loc["{}"]'.format(name))
            exec('y["{}"] = {}'.format(Model.objectives[i], obj_expr))
    else:
        y = y[[i for i in y.columns if i.isdigit()]].transpose()

    return x.transpose().to_numpy(), y.to_numpy()


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


def create_model(Model, xd, yd):
    """Create a surrogate.

    Generate, train and validate a surrogate model with the provided data.

    Args:
        file (str) : Path to CSV file.

    """
    xt, yt, xv, yv = separate_data(xd, yd)
    sm = eval('sms.{}'.format(model_dict[Model.type]))

    sm.set_training_values(xt, yt)

    sm.train()

    yp = sm.predict_values(xv)

    for i in range(0,yv.shape[1]):

        rms = np.sqrt(np.mean((yp[:,i]-yv[:,i])**2))#/yv.shape[0])
        log.info(rms)
        plt.figure()
        plt.plot(yv[:,i], yv[:,i], '-', label='$y_{true}$')
        plt.plot(yv[:,i], yp[:,i], 'r.', label='$\hat{y}$ :'+Model.objectives[i])

        plt.xlabel('$y_{true}$')
        plt.ylabel('$\hat{y}$')

        plt.legend(loc='upper left')
        plt.title('Kriging model: validation of the prediction model\n {}'.format(rms))

        plt.figure()
        for j in range(0,xv.shape[1]):
            plt.subplot(1,xv.shape[1]+1,j+1)
            if j == 0:
                plt.ylabel(Model.objectives[i])
            plt.plot(xt[:,j], yt[:,i], 'b.', label='$y_{training set}$')
            plt.plot(xv[:,j], yp[:,i], 'r.', label='$y_{prediction set}$')
            plt.title('$'+Model.objectives[i]+'$')
            plt.legend(loc='upper left')
    plt.show()

    Model.sm = sm


def get_data_file(Model):
    """Search for the file containing the data set.

    The programm searches for a file given by the user through the GUI, else
    it will look for a file that was generated by a previous DoE by looking at
    the optimPath location in the CPACS file. If no file is found it will run
    a DoE either with Aeromap parameters only, which will be run in one
    subworkflow, or with other parameters which will result in a conventional
    DoE.

    Args:
        Model (Prediction_tool object): Current predictor object.

    Returns:
        file (str): Path to the file containing the data.

    """
    if os.path.isfile(Model.user_file):
        file = Model.user_file
        log.info('User-specified file found')
    elif os.path.isfile(Model.result_file):
        file = Model.result_file
        log.info('File found from a previous workflow')
    else:
        raise FileNotFoundError("""File not found, please enter the name of an
                                 existing CSV file containing the data set.""")

    return file


def save_surrogate(Model):
    """Save trained surrogate model to a file.

    Create a file to which the class containing the surrogate model and its
    parameters will be saved in order to be re-used using the pickle module.
    The file is either saved in the Output folder of the PredictiveTool module
    or in the current working directory.

    Args:
        sm (surrogate model object): Trained surrogate model.

    Returns:
        None.

    """
    date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    cpacs_path = mif.get_toolinput_file_path('PredictiveTool')
    tixi = cpsf.open_tixi(cpacs_path)
    filepath = cpsf.get_value_or_default(tixi, opf.OPTWKDIR_XPATH, '-')
    if os.path.isdir(filepath):
        filename = filepath+'/Surrogate_Model'
    else:
        filename = MODULE_DIR+'/ToolOutput/SM_'+ date

    Model.user_file = filename

    sm_file = open(filename, 'wb')

    pickle.dump(Model, sm_file)


def load_surrogate(file):
    """Load a surrogate model object from file

    Using the pickle module, a surrogate model object is retrieved from a file.

    Args:
        file (str): Path to file.

    Returns:
        sm (object): The surrogate model.

    """
    try:
        f = open(file, 'rb')
    except:
        raise IOError('File could not be opened')

    Model = pickle.load(f)

    return Model


def generate_model(Model):
    """Start process of creating a model

    Reads or generates data to create a surrogate model.

    Args:
        data (): data to use to create the model

    Returns:
        sm (object): The surrogate model.

    """
    file = get_data_file(Model)

    xd, yd = extract_data_set(file, Model)

    create_model(Model, xd, yd)

    save_surrogate(Model)


def initiate_module():
    """Check how to use the module.

    Takes the user input to see wether to create a model or just use an
    existing one to make a prediction.

    Args:
        None.

    Returns:
        None.

    """

    # Variable declarations
    global Model
    Model = Prediction_tool()
    cpacs_path = mif.get_toolinput_file_path('PredictiveTool')

    Model.get_user_inputs(cpacs_path)

    if Model.use_model:
        # Take the parameters from the loaded model structure (all of them ?)
        Model = load_surrogate(Model.user_file)
    else:
        generate_model(Model)


if __name__ == "__main__":

    log.info('----- Start of ' + os.path.basename(__file__) + ' -----')

    initiate_module()

    log.info('----- End of ' + os.path.basename(__file__) + ' -----')

