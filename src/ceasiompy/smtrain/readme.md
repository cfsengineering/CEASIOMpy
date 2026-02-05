
<img align="right" height="70" src="../../../documents/logos/CEASIOMpy_banner_main.png">

# SMTrain

**Categories:** Optimisation, Surrogate Modeling

`SMTrain` is a module to train a surrogate model,
with data computed using CEASIOMpy's Modules.

Notion of fidelity in CFD:
    - 1st-level: potential flow
    - 2nd-level: euler flow
    - 3d-level: rans flow

The computed forces and moments are getting more and more accurate through each levels (in practice).

In CEASIOMpy currently you can use:
    - AVL for the 1st-level
    - SU2 Euler for the 2nd-level
    - Nothing for the 3rd-level (but there is going to be an update soon with CPACS2GMSH)

## Inputs

`SMTrain` takes as input a CPACS file.

## Workflow

`SMTrain`'s workflow in a nutshell:

1. DATA for training:
    - uniform sampling (n_samples parameter)
    - ceasiompy.db data [optional]

2. Training:
    - Trains on 1st-level
      - generates data using PyAVL module with the uniform-sampled parameters
      - augments the dataset with data from ceasiompy.db
      - trains solely on AVL results
    - Trains on 2nd-level:
      - using SU2Run module
      - trains on data with high-variance points from the 1st-level in a loop until the rmse error is small enough
    - Trains on 3rd-level (Not yet implemented due to CPACS2GMSH status)

3. Saves model and all results in an aeromap

## Installation or requirements

`SMTrain` is a native CEASIOMpy module, hence it is available and installed by default. It is base on the [SMT: Surrogate Modeling Toolbox](https://smt.readthedocs.io/en/latest/)

## Limitations

1. Can not choose the range for the Hyper-parameters of the surrogate model

## More information
- [SMT: Surrogate Modeling Toolbox](https://smt.readthedocs.io/en/latest/)
