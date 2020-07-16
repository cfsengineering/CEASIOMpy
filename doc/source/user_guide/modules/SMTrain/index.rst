SMTrain
=======

:Categories: Optimisation module

This module is used to create surrogate models


Installation
------------

The SMTrain module is a native |name| module, hence it is available and installed by default.

Analyses
--------

The SMTrain module generates a surrogate model by using a dataset which contains a list of inputs with their corresponding outputs. Therefore any parameters can be given to create a surrogate.

Output
------

SMTrain module outputs a binary file that contains an object whose attributes are one surrogate model from the Surrogate_model() class and a dataframe containing the informations about the inputs to give to the model and which outputs it will compute.

Required CPACS input and settings
---------------------------------

The CPACS must have a path to a CSV file with the training dataset in it, or an aeromap can be chosen instead. However the aeromap must have the outputs (cl, cl, ...) computed as well, else the model will not be created.

Limitations
-----------

* For now the specific training options for a model are not implemented in the GUI and must be modified within the code.

...

More information
----------------

* SMT: Surrogate Modeling Toolbox  https://smt.readthedocs.io/en/latest/
