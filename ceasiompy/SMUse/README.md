
<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_main.png">

# SMUse

**Categories:** Optimisation, Surrogate Modeling

**State**: :x: must be refactored to work with the new version of the code (see [Issue #147](https://github.com/cfsengineering/CEASIOMpy/issues/147))

`SMUse` is a module to use a surrogate model to "predict" new data that could be used in a CEASIOMpy workflow.

## Inputs

`SMUse` takes as input a CPACS file, it must contained a path to a trained surrogate model in it.

## Analyses

`SMUse` uses a trained surrogate model to replace a module in the CEASIOMpy workflow. The aim is to use train the surrogate model upstream and be able to get quick results from the surrogate model in a new workflow.

## Outputs

`SMUse` should output the same results as the original modules it replaces.

## Installation or requirements

`SMUse` is a native CEASIOMpy module, hence it is available and installed by default. It is base on the [SMT: Surrogate Modeling Toolbox](https://smt.readthedocs.io/en/latest/)

## Limitations

-

## More information

- [SMTrain module](../SMTrain/README.md)
- [SMT: Surrogate Modeling Toolbox](https://smt.readthedocs.io/en/latest/)
