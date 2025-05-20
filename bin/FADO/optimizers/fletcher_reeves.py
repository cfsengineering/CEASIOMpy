#  Copyright 2019-2025, FADO Contributors (cf. AUTHORS.md)
#
#  This file is part of FADO.
#
#  FADO is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  FADO is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with FADO.  If not, see <https://www.gnu.org/licenses/>.

from .line_searches import goldenSection
import numpy as np


def fletcherReeves(fun,x,grad,options,lineSearch=goldenSection):
    """
    Fletcher-Reeves method. The interface and options are similar to SciPy's L-BFGS-B.

    Parameters
    ----------
    fun         : Callable function, should take a numpy array and return a float.
    x           : The starting point of the optimization.
    grad        : Callable gradient method, takes and returns a numpy array.
    options     : Dictionary of options:
                  "ftol" function-based tolerance [no default];
                  "gtol" norm of gradient-based tolerance [no default];
                  "maxiter" maximum number of iterations [no default];
                  "disp" True to print messages [False];
                  "maxcor" restart period of the method [x.size+1];
                  "maxls" maximum number of line searches per iteration [20];
                  "tolls" stopping criteria for line searches [1e-3].
    lineSearch  : The line search method used.

    See also
    --------
    goldenSection and quadraticInterpolation line search methods.
    """
    # unpack options
    ftol = options["ftol"]
    gtol = options["gtol"]
    maxiter = options["maxiter"]
    verbose = False
    if "disp" in options.keys(): verbose = options["disp"]
    restart = x.size+1
    if "maxcor" in options.keys(): restart = options["maxcor"]
    maxls = 20
    if "maxls" in options.keys(): maxls = options["maxls"]
    tolls = 0.001
    if "tolls" in options.keys(): tolls = options["tolls"]

    if verbose:
        headerLine = ""
        for data in ["ITER","FUN EVAL","LS EVAL","STEP","FUN EPS","GRAD EPS","FUN VAL"]:
            headerLine += data.rjust(13)
        logFormat = "{:>13}"*3+"{:>13.6g}"*4
        print("\n"+"*"*33+" Fletcher-Reeves Method "+"*"*34+"\n")
        print("Number of variables: "+str(x.size)+"    Restart period: "+str(restart)+"\n")
        print(headerLine)
    #end

    # initialize
    feval = 1
    jeval = 1
    lbd = -1
    f = fun(x)
    G = grad(x)
    success = False

    # log
    logData = [0, 1, 0, 0.0, 0.0, 0.0, f]
    if verbose: print(logFormat.format(*logData))

    # start
    for i in range(maxiter):
        # periodic restart
        if i%restart==0 : S=-G

        if verbose and i%10==0 and i>0: print(headerLine)

        # line search
        lsfun = lambda step: fun(x+step*S)

        if lbd<=0: lbd = 1.0
        else: lbd *= max(abs(S))/max(abs(S_old))
        f_old = f
        (lbd,f,nls) = lineSearch(lsfun,maxls,f,lbd,tolls)
        feval += nls

        # detect bad direction and restart
        if f>f_old or lbd==0:
            if i%restart!=0: # otherwise we already have S=-G
                if verbose: print("Bad search direction, taking steepest descent.")
                f = f_old
                S = -G
                (lbd,f,nls2) = lineSearch(lsfun,maxls,f,1.0,tolls)
                nls += nls2
                feval += nls2
            #end
            if f>f_old or lbd==0:
                if verbose: print("Could not improve along steepest descent direction.")
                f = f_old
                S = 2*(1-np.random.rand(S.size))*max(abs(S))
                (lbd,f,nls2) = lineSearch(lsfun,maxls,f,1.0,tolls)
                nls += nls2
                feval += nls2
            #end
            if f>f_old or lbd==0:
                if verbose: print("Could not improve along random direction.")
                f = f_old
                break
            #end
        #end

        # update search direction
        x += lbd*S
        G_old = G
        S_old = S
        G = grad(x)
        jeval += 1
        S = -G+G.dot(G)/G_old.dot(G_old)*S_old

        # log
        logData = [i+1, feval, nls, lbd, f_old-f, max(abs(G)), f]
        if verbose: print(logFormat.format(*logData))

        # convergence criteria
        if f_old-f < ftol or max(abs(G)) < gtol:
            success = True
            break
    #end

    result = {"x" : x, "fun" : f, "jac" : G, "nit" : i+1,
              "nfev" : feval, "njev" : jeval, "success" : success}
    return result
#end
