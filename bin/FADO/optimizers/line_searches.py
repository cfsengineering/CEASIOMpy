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


def goldenSection(fun,maxiter,f0=None,lbd0=1,tol=1e-3):
    """1D minimization using the Golden Section method."""
    # look for an interval that contains the minimum
    # assuming we have a descent direction
    feval = 0
    x = [0.0, 0.0, lbd0]
    if f0 is None:
        f0 = fun(0.0)
        feval += 1
    y = [f0,  f0, fun(lbd0)]
    feval += 1

    # while the function decreases the step is doubled
    while y[2]<y[1]:
        x[1] = x[2]
        y[1] = y[2]
        lbd0 *= 2.0
        x[2] = x[1]+lbd0
        y[2] = fun(x[2])
        feval += 1
    #end

    # initial points
    L2 = 0.381966*x[2] # 2/(3+sqrt(5))*x2
    x = [0.0, L2, x[2]-L2, x[2]]
    y = [fun(x[1]), fun(x[2])]
    feval += 2

    # iterate
    while feval < maxiter:
        if y[0] < y[1]: # keep left interval
            x[3] = x[2]
            x[2] = x[1]
            # new test point
            x[1] = x[0]+(x[3]-x[2])
            y[1] = y[0]
            y[0] = fun(x[1])
            feval += 1
        else:           # keep right interval
            x[0] = x[1]
            x[1] = x[2]
            # new test point
            x[2] = x[3]-(x[1]-x[0])
            y[0] = y[1]
            y[1] = fun(x[2])
            feval += 1
        #end

        # check convergence
        if abs(x[2]-x[1])/L2 < tol:
            break
    #end

    # minimum value found
    if y[0] < y[1]:
        x_opt = x[1]
        y_min = y[0]
    else:
        x_opt = x[2]
        y_min = y[1]
    #end

    return (x_opt,y_min,feval)
#end


def quadraticInterp(fun,maxiter,f0=None,lbd0=1,tol=1e-3):
    """1D minimization using the Quadratic Interpolation method."""
    # initialize
    feval = 0
    x = [0.0, 0.0, 0.0]
    if f0 is None:
        f0 = fun(0.0)
        feval += 1
    y = [f0, 0.0, 0.0]

    # bracket the minimum
    # assuming we have a descent direction
    f1 = fun(lbd0)
    feval += 1

    if f1 > f0:
        x[2] = lbd0
        y[2] = f1
        x[1] = lbd0/2
        y[1] = fun(x[1])
        feval += 1
    while f1 <= f0:
        f2 = fun(2*lbd0)
        feval += 1
        if f2 > f1:
            x[1] = lbd0
            y[1] = f1
            x[2] = 2*lbd0
            y[2] = f2
            break
        else:
            f1 = f2
            lbd0 *= 2
        #end
    #end

    # iterate
    y_ref = max(max(y),-min(y),tol)

    while True:
        # compute x_opt'
        det = (x[0]-x[1])*(x[1]-x[2])*(x[2]-x[0])
        a = y[0]*x[1]*x[2]*(x[2]-x[1]) + y[1]*x[2]*x[0]*(x[0]-x[2]) + y[2]*x[0]*x[1]*(x[1]-x[0])
        a /= det
        b = y[0]*(x[1]**2-x[2]**2) + y[1]*(x[2]**2-x[0]**2) + y[2]*(x[0]**2-x[1]**2)
        b /= det
        c = -(y[0]*(x[1]-x[2]) + y[1]*(x[2]-x[0]) + y[2]*(x[0]-x[1]))/det

        x_opt = -0.5*b/c
        y_star = a+b*x_opt+c*x_opt**2
        y_min = fun(x_opt)
        feval += 1

        if y_min > max(y):
            print("The quadratic approximation is not convex.")
            x_opt = sorted(zip(y,x))[0][1]
            y_min = min(y)
            break
        #end

        # check convergence
        if abs(y_min-y_star)/y_ref < tol or feval >= maxiter:
            break

        # drop highest point
        x.append(x_opt)
        y.append(y_min)
        yx = sorted(zip(y,x))
        x = [z for _,z in yx][:-1]
        y = [z for z,_ in yx][:-1]
    #end

    return (x_opt,y_min,feval)
#end
