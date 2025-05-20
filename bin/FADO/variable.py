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

import copy
import numpy as np


class InputVariable:
    """
    Class to define design variables.

    Parameters
    ----------
    x0 is the initial value.
    parser specifies how the variable is written to file.
    size >= 1 defines a vector variable whose x0, lb, and ub values are broadcast.
    size == 0 means auto, i.e. size determined from x0, scale/lb/ub must be either compatible or scalar.
    scale, an optimizer will see x/lb/ub * scale
    lb/ub, the lower and upper bounds for the variable.

    See also
    --------
    Parameter, a variable-like object that is not exposed to optimizers.
    """
    def __init__(self, x0, parser, size=0, scale=1.0, lb=-1E20, ub=1E20):
        self._parser = parser

        if size == 0 and isinstance(x0,float): size=1
        if size >= 1:
            try:
                assert(isinstance(x0,float))
                assert(isinstance(lb,float))
                assert(isinstance(ub,float))
                assert(isinstance(scale,float))
            except:
                raise ValueError("If size is specified, x0, scale, lb, and ub must be scalars.")
            #end
            self._x0 = np.ones((size,))*x0
            self._lb = np.ones((size,))*lb
            self._ub = np.ones((size,))*ub
            self._scale = np.ones((size,))*scale
        else:
            try:
                size = x0.size
                assert(size>=1)
                self._x0 = x0
                if not isinstance(lb,float):
                    assert(lb.size == size)
                    self._lb = lb
                else:
                    self._lb = np.ones((size,))*lb
                #end
                if not isinstance(ub,float):
                    assert(ub.size == size)
                    self._ub = ub
                else:
                    self._ub = np.ones((size,))*ub
                #end
                if not isinstance(scale,float):
                    assert(scale.size == size)
                    self._scale = scale
                else:
                    self._scale = np.ones((size,))*scale
                #end
            except:
                raise ValueError("Incompatible sizes of x0, scale, lb, and ub.")
            #end
        #end

        self._size = size
        self._x = copy.deepcopy(self._x0)
    #end

    def getSize(self):
        return self._size

    def getInitial(self):
        return self._x0

    def getCurrent(self):
        return self._x

    def getLowerBound(self):
        return self._lb

    def getUpperBound(self):
        return self._ub

    def getScale(self):
        return self._scale

    def get(self,name):
        if name == "Initial":
            return self.getInitial()
        elif name == "Current":
            return self.getCurrent()
        elif name == "LowerBound":
            return self.getLowerBound()
        elif name == "UpperBound":
            return self.getUpperBound()
        elif name == "Scale":
            return self.getScale()
        else:
            raise KeyError("Variable does not have field: `"+name+"`")
        #end
    #end

    def setCurrent(self,x):
        self._x[()] = x

    def writeToFile(self,file):
        self._parser.write(file,self._x)
#end


class Parameter:
    """
    Class for optimization parameters, usually some value that is not an optimization
    variable but needs to be ramped over its course, e.g. a penalty factor.

    Parameters
    ----------
    values   : An indexable structure (e.g. range, list).
    parser   : How the values are written to file.
    start    : Initial index into values.
    function : Can be used to further convert the current value.
    """
    def __init__(self,values,parser,start=0,function=None):
        self._values = values
        self._parser = parser
        self._function = function
        # make sure starting possition is valid
        self._upper = len(values)-1
        self._index = max(0,min(self._upper,start))

    def increment(self):
        """Move to the next value, return True if the last value was reached."""
        self._index = max(0,min(self._upper,self._index+1))
        return self.isAtTop()

    def decrement(self):
        """Move to the previous value, return True if the first value was reached."""
        self._index = max(0,min(self._upper,self._index-1))
        return self.isAtBottom()

    def writeToFile(self,file):
        value = self._values[self._index]
        if self._function != None:
            value = self._function(value)
        self._parser.write(file,value)

    def isAtTop(self):
        """Return True if the current value is the last."""
        return (self._index == self._upper)

    def isAtBottom(self):
        """Return True if the current value is the first."""
        return (self._index == 0)
#end
