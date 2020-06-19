"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

This module generates a surrogate model based on specified inputs and outputs.

Python version: >=3.6

| Author: Vivien Riolo
| Creation: 2020-06-09
| Last modifiction: 2020-06-09

TODO:
    * Write the module
    * Make this module standalone
    * Deal with the objective function, to recover in all cases

"""

# =============================================================================
#   IMPORTS
# =============================================================================

import os
import smt.surrogate_models as sms
import smt.sampling_methods as smp
import pandas as pd
import numpy as np
from re import split as splt
import matplotlib.pyplot as plt

import ceasiompy.utils.moduleinterfaces as mi
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.optimfunctions as opf
import ceasiompy.Optimisation.optimisation as opt
import ceasiompy.utils.workflowfunctions as wkf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.Optimisation.func.tools as tls

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
#   GLOBALS
# =============================================================================

CPACS_PREDICT_PATH = '../PredictiveTool/ToolInput.ToolInput.xml'
PREDICT_XPATH = '/cpacs/toolspecific/CEASIOMpy/Prediction/'

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

class SM_parameters():
    """Parameters for the surrogate model"""

    def __init__(self):
        """Define default main parameters."""

        # Main parameters
        self.objectives = ['']
        self.user_config = 'Variable_history.csv'

        # Only for the aeromap case
        self.aeromap_case = False
        self.doedriver = 'LatinHypercube'
        self.samplesnb = 3

    def get_user_inputs(self, cpacs_path):
        """Take user inputs from the GUI."""
        tixi = cpsf.open_tixi(CPACS_PREDICT_PATH)

        self.objectives = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'objective', ['cl'])
        self.user_config = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'Config/filepath', 'Variable_history.csv')

        self.aeromap_case = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'aeromap_case/IsCase', False)
        self.doedriver = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'aeromap_case/DoEdriver', 'LatinHypercube')
        self.samplesnb = cpsf.get_value_or_default(tixi, PREDICT_XPATH+'aeromap_case/sampleNB', 3)
# =============================================================================
#   FUNCTIONS
# =============================================================================

def extract_data_set(file):
    """
    Retrieve training dataset from a file or generates it automatically. The
    file format must be a CSV with each variable parameters and values are in
    a row. The file must also contain a 'Name' and a 'type' column which are
    needed to describe the variable.

    Parameters
    ----------
    file : str (optional)
        Path to user-specified file (CSV format)

    Returns
    -------
    x : DataFrame
        Set of points in the design space
    y : DataFrame
        Set of points in the result space

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

    df = df.set_index('Name')

    # Extract the iteration results only
    x = x[[i for i in x.columns if i.isdigit()]]
    df = df[[i for i in df.columns if i.isdigit()]]

    # Compute the objectives in the aeromap case, else they are already given
    if 'Variable_history' not in file:
        y = pd.DataFrame()
        for i, obj_expr in enumerate(objectives):
            for name in splt('[+*/-]', obj_expr):
                obj_expr = obj_expr.replace(name,'df.loc["{}"]'.format(name))
            exec('y["{}"] = {}'.format(objectives[i], obj_expr))
    else:
        y = y[[i for i in y.columns if i.isdigit()]].transpose()

    return x.transpose().to_numpy(), y.to_numpy()


def aeromap_case_gen(modules):
    """
    Generate a CSV file containing a dataset generated with aeromap parameters
    only.

    Parameters
    ----------
    modules : lst
        List of modules to execute.

    Returns
    -------
    file : str
        Path to CSV file.

    """
    file = MODULE_DIR+'/Aeromap_generated.csv'
    infile = mi.get_toolinput_file_path('PredictiveTool')
    outfile = mi.get_tooloutput_file_path('PredictiveTool')

    tixi = cpsf.open_tixi(infile)

    # Inputs
    alt = [0, 0]
    mach = [0.5, 0.5]
    aoa = [-10, 10]
    aos = [0,0]
    nt = 100
    bounds = np.array([alt, mach, aoa, aos])
    # Sort criterion : ‘center’, ‘maximin’, ‘centermaximin’, ‘correlation’
    crit = 'corr'

    # Generate sample points, LHS or FullFactorial
    sampling = smp.LHS(xlimits=bounds, criterion=crit)
    xd = sampling(nt)
    print(xd)
    xd = xd.transpose()
    print(xd)
    # Delete the other aeromaps... maybe conserve them ?
    for uid in apmf.get_aeromap_uid_list(tixi):
        apmf.delete_aeromap(tixi, uid)

    # Create new aeromap
    aeromap_uid = 'DoE_Aeromap'
    am_xpath = tls.get_aeromap_path(modules)
    apmf.create_empty_aeromap(tixi, aeromap_uid)
    cpsf.add_string_vector(tixi, am_xpath+'/aeroMapUID', [aeromap_uid])

    # Add parameters to aeromap
    Param = apmf.AeroCoefficient()
    for i in range(0, xd.shape[1]):
        Param.add_param_point(xd[0][i], xd[1][i], xd[2][i], xd[3][i])
    apmf.save_parameters(tixi, aeromap_uid, Param)
    cpsf.close_tixi(tixi, infile)

    wkf.run_subworkflow(modules, cpacs_path_in=infile, cpacs_path_out=outfile)

    # Get Aerocoefficient
    tixi = cpsf.open_tixi(outfile)
    am_xpath = tls.get_aeromap_path(modules)
    aeromap_uid = cpsf.get_value(tixi, am_xpath+'/aeroMapUID')
    AeroCoefficient = apmf.get_aeromap(tixi,aeromap_uid)
    cpsf.close_tixi(tixi, outfile)

    dct = AeroCoefficient.to_dict()

    # Write to CSV
    df = pd.DataFrame(dct)
    df = df.transpose()
    var_type = ['obj' if i in objectives
                else 'des' if i in ['alt','mach','aoa','aos']
                else 'const'
                for i in df.index]
    df.insert(0,'type',var_type)
    df.to_csv(file, index=True)
    return file


def separate_data(x, y):
    """
    Create two sets of points for the training and validation of
    the surrogate model.

    Parameters
    ----------
    x : numpy array
        DoE inputs
    y : numpy array
        DoE outputs

    Returns
    -------
    xt : numpy array
        Training inputs
    yt : numpy array
        Training outputs
    xv : numpy array
        Validation inputs
    yv : numpy array
        Validation outputs

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


def create_model(xd, yd):
    """
    Generate, train and validate a surrogate model with the provided data.

    Parameters
    ----------
    file : str
        Path to CSV file.

    Returns
    -------
    sm : surrogate model class
        Trained surrogate model.

    """
    model = 'KRG'
    xt, yt, xv, yv = separate_data(xd, yd)
    sm = eval('sms.{}'.format(model_dict[model]))
    # In case the options get user defined as string
    # sm = eval('sms.{}({})'.format(model_dict[model]), options))

    sm.set_training_values(xt, yt)

    sm.train()

    yp = sm.predict_values(xv)

    for i in range(0,yv.shape[1]):

        rms = np.sqrt(np.mean((yp[:,i]-yv[:,i])**2))#/yv.shape[0])
        log.info(rms)
        plt.figure()
        plt.plot(yv[:,i], yv[:,i], '-', label='$y_{true}$')
        plt.plot(yv[:,i], yp[:,i], 'r.', label='$\hat{y}$ :'+objectives[i])

        plt.xlabel('$y_{true}$')
        plt.ylabel('$\hat{y}$')

        plt.legend(loc='upper left')
        plt.title('Kriging model: validation of the prediction model\n {}'.format(rms))

        plt.figure()
        for j in range(0,xv.shape[1]):
            plt.subplot(1,xv.shape[1]+1,j+1)
            if j == 0:
                plt.ylabel(objectives[i])
            plt.plot(xt[:,j], yt[:,i], 'b.', label='$y_{training set}$')
            plt.plot(xv[:,j], yp[:,i], 'r.', label='$y_{prediction set}$')
            plt.title('$'+objectives[i]+'$')
            plt.legend(loc='upper left')
    plt.show()

    return sm


if __name__ == "__main__":

    log.info('Start of Predictive tool')

    # Variable declarations
    global objectives
    objectives = ['cl/cd','cms']
    # file = 'Aeromap_generated100_points.csv'
    file = '_Variable_history.csv'
    aeromap = True
    modules = ['WeightConventional', 'PyTornado']

    if os.path.isfile(file):
        log.info('File found, will be used to generate the model')
    elif aeromap and not os.path.isfile(file):
        log.info('Specific aeromap case')
        file = aeromap_case_gen(modules.insert(0,'SettingsGUI'))
    else:
        log.info('No file found, running DoE')

        wkf.copy_module_to_module('PredictiveTool', 'in', 'Optimisation', 'in')
        opt.routine_setup(modules, 'DoE')
        wkf.copy_module_to_module('Optimisation', 'out', 'PredictiveTool', 'in')

        cpacs_path = mi.get_tooloutput_file_path('Optimisation')
        tixi = cpsf.open_tixi(cpacs_path)
        file = cpsf.get_value(tixi, opf.OPTWKDIR_XPATH)+'/Variable_history.csv'
        objectives = cpsf.get_value(tixi, opf.OPTIM_XPATH+'/objectives')

    xd, yd = extract_data_set(file)

    sm = create_model(xd, yd)

    log.info('End of Predictive tool')
