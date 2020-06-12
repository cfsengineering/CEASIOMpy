"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

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
from smt.utils import compute_rms_error
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
#   FUNCTIONS
# =============================================================================

def extract_data_set(file):
    """
    Retrieve training dataset from a file or generates it automatically

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
    df = df.rename(columns={'Unnamed: 0':'name'})

    # Separate the input and output points
    x = df.loc[[i for i,v in enumerate(df['type']) if v == 'des']]
    y = pd.DataFrame()

    # Compute values of the objective function
    df = df.set_index('name')

    # Extract the iteration results only
    x = x[[i for i in x.columns if i.isdigit()]]
    df = df[[i for i in df.columns if i.isdigit()]]

    # Compute the objectives
    for i, obj_expr in enumerate(objective):
        for name in splt('[+*/-]', obj_expr):
            obj_expr = obj_expr.replace(name,'df.loc["{}"]'.format(name))
        exec('y["{}"] = {}'.format(objective[i], obj_expr))

    print(x)
    print(y)
    return x.transpose().to_numpy(), y.to_numpy()


def aeromap_case(modules):
    """
    Generate a CSV file containing a dataset generated with aeromap parameters only.

    Parameters
    ----------
    modules : lst
        List of modules to execute.

    Returns
    -------
    file : str
        Path to CSV file.

    """
    log.info('No file found, a DoE will be run and a CSV file will be generated')

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
    # Sort criterion : ‘center’, ‘maximin’, ‘centermaximin’, ‘correlation’
    crit = 'corr'

    # Generate sample points, LHS or FullFactorial
    sampling = smp.LHS(xlimits = np.array([alt, mach, aoa, aos]), criterion=crit)
    xd = sampling(nt)
    xd = xd.transpose()

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

    wkf.run_subworkflow(modules, cpacs_path_in = infile, cpacs_path_out = outfile)

    # Get Aerocoefficient
    tixi = cpsf.open_tixi(outfile)
    am_xpath = tls.get_aeromap_path(modules)
    aeromap_uid = cpsf.get_value(tixi, am_xpath + '/aeroMapUID')
    AeroCoefficient = apmf.get_aeromap(tixi,aeromap_uid)
    cpsf.close_tixi(tixi, outfile)

    dct = AeroCoefficient.to_dict()

    # Write to CSV
    df = pd.DataFrame(dct)
    df = df.transpose()
    var_type = ['obj' if i in objective else 'des' if i in ['alt','mach','aoa','aos'] else 'const' for i in df.index]
    df.insert(0,'type',var_type)
    df.to_csv(file, index=True)

    return file


def separate(x, y):
    """
    Create two sets of points for the training and validation of the surrogate
    model.

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
    # Sets length d
    l = len(x)
    sep = int(np.ceil(0.7*l))

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
    xt, yt, xv, yv = separate(xd, yd)

    sm = sms.KRG(theta0=[1e-2]*xd.shape[1])
    sm.set_training_values(xt, yt)
    sm.train()

    yp = sm.predict_values(xv)

    for i in range(0,yv.shape[1]):
        plt.figure()
        plt.plot(yv[:,i], yv[:,i], '-', label='$y_{true}$')
        plt.plot(yv[:,i], yp[:,i], 'r.', label='$\hat{y}$ :'+objective[i])

        plt.xlabel('$y_{true}$')
        plt.ylabel('$\hat{y}$')

        plt.legend(loc='upper left')
        plt.title('Kriging model: validation of the prediction model')

        plt.figure()
        for j in range(0,xv.shape[1]):
            plt.subplot(1,xv.shape[1]+1,j+1)
            if j == 0:
                plt.ylabel(objective[i])
            plt.plot(xv[:,j], yv[:,i], 'b.')
            plt.plot(xt[:,j], yt[:,i], 'b.')
            plt.plot(xv[:,j], yp[:,i], 'r.')
            plt.xlabel(['alt','mach','aoa','aos'][j])
            plt.title('$'+objective[i]+'$')
    plt.show()

    return sm


if __name__ == "__main__":

    log.info('Start of Predictive tool')

    # Variables declaration
    global objective
    objective = ['cl', 'cd', 'cl/cd', 'cd/cl']
    file = '_Aeromap_generated.csv'
    aeromap = True
    modules = ['SettingsGUI','WeightConventional', 'PyTornado']

    # Specific aeromap case
    if aeromap and not os.path.isfile(file):
        file = aeromap_case(modules)

    if os.path.isfile(file):
        log.info('File found, will be used to get training set')
    else:
        log.info('No file found, a DoE will be run and a default file will be generated')
        opt.routine_setup(modules, 'DoE')
        cpacs_path = mi.get_tooloutput_file_path('Optimisation')
        tixi = cpsf.open_tixi(cpacs_path)
        file = cpsf.get_value(tixi, opf.OPTWKDIR_XPATH)+'/Variable_history.csv'
        objective = cpsf.get_value(tixi, opf.OPTIM_XPATH+'/objective')

    xd, yd = extract_data_set(file)

    sm = create_model(xd, yd)

    log.info('End of Predictive tool')
