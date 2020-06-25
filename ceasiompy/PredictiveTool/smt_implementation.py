"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Python version: >=3.6

| Author: Vivien Riolo
| Creation: 2020-06-09
| Last modifiction: 2020-06-09

TODO:
    *

"""

from __future__ import print_function, division
import numpy as np
from scipy import linalg
from smt.utils import compute_rms_error

from smt.problems import Sphere, NdimRobotArm, Rosenbrock
from smt.sampling_methods import LHS
from smt.surrogate_models import LS, QP, KPLS, KRG, KPLSK, GEKPLS
try:
    from smt.surrogate_models import IDW, RBF, RMTC, RMTB
    compiled_available = True
except:
    compiled_available = False

try:
    import matplotlib.pyplot as plt
    plot_status = True
except:
    plot_status = False

import scipy.interpolate

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm

########### Initialization of the problem, construction of the training and validation points

ndim = 2
ndoe = 20 #int(10*ndim)
# Define the function
fun = Rosenbrock(ndim=ndim)

# Construction of the DOE
sampling = LHS(xlimits=fun.xlimits, criterion='m')
xt = sampling(ndoe)
# Compute the outputs
yt = fun(xt)

# Construction of the validation points
ntest = 200 #500
sampling = LHS(xlimits=fun.xlimits)
xtest = sampling(ntest)
ytest = fun(xtest)



# To plot the Rosenbrock function
x = np.linspace(-2,2,50)
res = []
for x0 in x:
    for x1 in x:
        res.append(fun(np.array([[x0,x1]])))
res = np.array(res)
res = res.reshape((50,50)).T
X,Y = np.meshgrid(x,x)
fig = plt.figure(figsize=(15, 10))
ax = fig.gca(projection='3d')
surf = ax.plot_surface(X, Y, res, cmap=cm.viridis,
                       linewidth=0, antialiased=False,alpha=0.5)

ax.scatter(xt[:,0],xt[:,1],yt,zdir='z',marker = 'x',c='b',s=200,label='Training point')
ax.scatter(xtest[:,0],xtest[:,1],ytest,zdir='z',marker = '.',c='k',s=200,label='Validation point')

plt.title('Rosenbrock function')
plt.xlabel('x1')
plt.ylabel('x2')
plt.legend()
plt.show()

# The variable 'theta0' is a list of length ndim.
t = KRG(theta0=[1e-2]*ndim,print_prediction = False)
t.set_training_values(xt,yt[:,0])

t.train()

# Prediction of the validation points
y = t.predict_values(xtest)
print('Kriging,  err: '+ str(compute_rms_error(t,xtest,ytest)))
if plot_status:

# Plot the function, the prediction and the 95% confidence interval based on
# the MSE
    fig = plt.figure()
    plt.plot(ytest, ytest, '-', label='$y_{true}$')
    plt.plot(ytest, y, 'r.', label='$\hat{y}$')

    plt.xlabel('$y_{true}$')
    plt.ylabel('$\hat{y}$')

    plt.legend(loc='upper left')
    plt.title('Kriging model: validation of the prediction model')

if plot_status:
    plt.show()

# Value of theta
print("theta values",  t.optimal_theta)