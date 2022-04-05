

<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_main.png">

# SMTrain

**Categories:** Optimisation, Surrogate Modeling

**State**: :x: must be refactored to work version of the code (see [Issue #147](https://github.com/cfsengineering/CEASIOMpy/issues/147))


`SMTrain` is a module to train a surrogate model, with data calculated with CEASIOMpy.


## Inputs

`SMTrain` takes as input a CPACS file, it must contained a path to a CSV file with the training dataset in it, or an aeromap can be chosen instead. However the aeromap must have the outputs (cl, cd, ...).


## Analyses

`SMTrain` module generates a surrogate model by using a dataset which contains a list of inputs with their corresponding outputs. Therefore any parameters can be given to create a surrogate.

## Outputs

`SMTrain` outputs a CPACS files with the new values set by the user. It will be ready to be used by the next module in the workflow.


## Installation or requirements

`SMTrain` is a native CEASIOMpy module, hence it is available and installed by default. It is base on the [SMT: Surrogate Modeling Toolbox](https://smt.readthedocs.io/en/latest/)


## Limitations

For now the specific training options for a model are not implemented in the GUI and must be modified within the code.


## More information

* [SMT: Surrogate Modeling Toolbox](https://smt.readthedocs.io/en/latest/)
