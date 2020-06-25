#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 07:26:31 2020

Small programm that follows all the steps to create a surrogate
model based on the Krigin or Response surface method, using the openmdao libraries.

@author: Vivien Riolo
"""
from mpl_toolkits import mplot3d
import numpy as np
import openmdao.api as om
import matplotlib.pyplot as plt

def function(x,y):
    # Rosenbrock function
    result = (1-x)**2+100*(y-x**2)**2
    
    # 2nd order polynomial function
    # result = x**2+y**2+20
    
    # Non-linear function
    # result = np.exp(x)-y
    # result = x*np.sin(y**2)-np.sin(x*y)+5

    # Highly non-linear function
    # /!\ Too much of an exponential frequency growth, no true representation 
    # available after Shanon limit
    # result = x**1-15*np.sin(y**2*x)+y**1 +10
    
    return result


def create_model(name):
    # Setup training domain
    l = 1
    nb_sp = 25
    d1 = np.linspace(-l, l, nb_sp)
    d2 = d1
    X, Y = np.meshgrid(d1,d2)
    Z = function(X,Y)

    # Setup prediction domain
    a = np.linspace(-l,l,100)
    pd1 = a*np.sin(a**2)
    pd2 = a*np.cos(a**2)
    po = []
    err = []    

    # Computing the surface
    coord = []
    res = []
    for i in d1:
        for j in d2:
            res.append(function(i,j))
            coord.append([i,j])
    
    # Create the training dataset
    xi = np.array(coord)
    yi = np.transpose(np.atleast_2d(res))
    
    # Create and train the model
    if name == 'Kg':
        k = om.KrigingSurrogate()
    elif name == 'RS':
        k = om.ResponseSurface()
        
    print('train start')
    k.train(xi,yi)
    print('train stop')
    
    # Make a prediction
    for i in range(0,len(a)):
        pres = k.predict(np.array([pd1[i],pd2[i]]))
        if name == 'Kg':
            po.append(pres[-1][-1])
            err.append(po[-1]-function(pd1[i], pd2[i]))
        elif name == 'RS':
            po.append(pres[-1])
            err.append(po[-1]-function(pd1[i], pd2[i]))
    rms = np.sqrt(np.mean(np.array(err)**2))
    print('Root mean-square error {} : {}'.format(name,rms))
    
    # Plot the training set
    plt.figure()
    ax = plt.axes(projection='3d')
    # ax.plot_surface(X, Y, Z)
    ax.plot_wireframe(X, Y, Z)
    
    #Plot the predicted set
    ax.scatter(pd1,pd2,po,color='red')
    ax.plot(pd1,pd2,err,color='gray')
    
    
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')
    
    # plt.show()
    return rms


if __name__ == '__main__':
    
    plt.close('all')
    rmsk = create_model('Kg')
    rmsr = create_model('RS')
    