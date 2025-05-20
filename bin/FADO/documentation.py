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

import inspect


def printDocumentation(obj=None):
    """
    Prints the documentation strings of an object (class or function).
    For classes print the documentation for all "public" and documented methods.
    """
    if obj is None:
        printDocumentation(printDocumentation)
        return
    #end

    # Documentation for a function
    if str(obj).startswith("<function"):
        if not obj.__doc__: return
        sig = str(inspect.signature(obj))
        sig = sig.replace("(self, ","(")
        sig = sig.replace("(self,","(")
        sig = sig.replace("(self","(")
        name = str(obj).split()[1] + sig
        print("")
        print(name)
        print("-"*len(name))
        print(inspect.getdoc(obj))
        print("\n"+"*"*80)
        return
    #end

    # Documentation for classes
    className = str(obj).split(".")[-1].split("'")[0]
    name = className + str(inspect.signature(obj))
    print("")
    print(name)
    print("-"*len(name))
    print(inspect.getdoc(obj))
    print("\n"+"*"*80+"\n")

    for methodName in dir(obj):
        if methodName.startswith("_"): continue
        method = getattr(obj,methodName)
        printDocumentation(method)
    #end
#end
