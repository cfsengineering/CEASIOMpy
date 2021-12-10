"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to simplify some file and data handling in CEASIOMpy

Python version: >=3.6

| Author : Aidan Jungo
| Creation: 2021-12-10
| Last modifiction: 2021-12-10

TODO:

    *

"""

# ==============================================================================
#   IMPORTS
# ==============================================================================

import os
from collections import OrderedDict

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split(".")[0])


# ==============================================================================
#   CLASSES
# ==============================================================================

class ConfigFile:
    
    def __init__(self, filename):
        self.filename = filename
        
        self.data = OrderedDict()
        self.comment_idx = 1
        
        self.read_file(filename)
        
    def read_file(self, file):
        
        if not os.path.isfile(file):
            raise FileNotFoundError(f"File {file} not found")
        
        with open(file, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                
                elif line.startswith("%"):
                    key = f"comment_{self.comment_idx}"
                    self.data[key] = line.strip()
                    self.comment_idx += 1
                
                elif "=" in line:

                    key, value = line.split("=")
                    
                    if "(" in value and ")" in value:
                        value = value.replace('(','').replace(')','')
                        value_list = value.split(",")
                        value_list = [ val.strip() for val in value_list ]
                        
                        # Check if the list could be a list of floats
                        try:
                            value_list = [ float(val) for val in value_list ]
                        except ValueError:
                            pass
                        
                        self.data[key.strip()] = value_list
                        
                    else:                    

                        self.data[key.strip()] = value.strip()
                
                else:
                    raise ValueError(f"Invalid line in file {file}: {line}")
                
 
    
    def write_file(self, file, overwrite=False):
        
        if os.path.isfile(file) and overwrite:
            os.remove(file)
        else:
            raise FileExistsError(f"File {file} already exists. Use overwrite=True to overwrite")
        
        with open(file, "w") as f:
            for key, value in self.data.items():
                if "comment_" in key:
                    f.write(value + "\n")
                elif isinstance(value, list):
                    f.write(f"{key} = ( {' , '.join(map(str,value))} )\n")
                else:
                    f.write(f"{key} = {value}\n")
        
        
    def __setitem__(self, key, value):
        self.data[key] = value
        
    def __getitem__(self, key):
        return self.data[key]
    
    def __str__(self) -> str:
        for key, value in self.data.items():
            if "comment_" in key:
                print(value)
            elif isinstance(value, list):
                print(f"{key} = ( {' , '.join(map(str,value))} )\n")
            else:
                print(f"{key} = {value}")
        return ""


# ==============================================================================
#   FUNCTIONS
# ==============================================================================


if __name__ == "__main__":
    
    # print("Nothing to execute")
    
    # Test ConfigFile class
    
    A = ConfigFile("test.cfg")
    
    A['test1'] = 1
    A['test2'] = 2

    print(A)
    
    A.write_file("test_output.cfg",overwrite=True)