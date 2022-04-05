<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_aero.png">

# PlotAeroCoefficients

**Categories:** Aerodynamics, Results, Plot

**State**: :heavy_check_mark:


`PlotAeroCoefficients` module allows to plot aerodynamic coefficients calculated by the different modules of CEASIOMpy.


## Inputs

`PlotAeroCoefficients` only takes as input a CPACS file. It must contain at least one aeromap to plot.


## Analyses

Nothing is calculated by this module, it just plots the aerodynamic coefficients with [Matplotlib](https://matplotlib.org/).


## Outputs

`PlotAeroCoefficients` only open a new window to show the coefficients, you can then save manually.


## Installation or requirements

`PlotAeroCoefficients` is a native CEASIOMpy module, hence it is available and installed by default. To run it, you just have to be sure that you are in the CEASIOMpy Conda environment.


## Limitations

For now `PlotAeroCoefficients` do not save the figures automatically, you must save them manually.
