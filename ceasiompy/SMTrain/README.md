
<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_main.png">

# SMTrain

**Categories:** Optimisation, Surrogate Modeling

`SMTrain` is a module to train a surrogate model, with data computed using CEASIOMpy.

## Inputs

`SMTrain` takes as input a CPACS file.

## Analyses

`SMTrain` module generates:
    - data depending on the chosen fidelity level (1: AVL, 2: Euler_SU2). In the GUI of CEASIOMpy, you chan choose the range of these values.
    - a surrogate model with already fixed Hyper-parameters

## Outputs

`SMTrain` outputs a CPACS files with the new values set by the user in the aeromap lh_sampling_data.

## Installation or requirements

`SMTrain` is a native CEASIOMpy module, hence it is available and installed by default. It is base on the [SMT: Surrogate Modeling Toolbox](https://smt.readthedocs.io/en/latest/)

## Limitations

1. Can not choose the Hyper-parameters of the surrogate model

## More information
- [SMT: Surrogate Modeling Toolbox](https://smt.readthedocs.io/en/latest/)
