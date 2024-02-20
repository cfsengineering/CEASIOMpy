<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_main.png">

# ThermoData

**Categories:** Engine Boundary conditions

**State**: :heavy_check_mark:



<br />

`ThermoData` is a module to provide the outlet conditions of a given engine. It can calculate different operating conditions and save the results in a text file. This module is derived starting from the OpenSource code [pyCycle](https://github.com/OpenMDAO/pycycle) developed by Eric S. Hendricks and Justin S. Gray. It can perform calculations on both turbojet and turbofan engines, with the possibility to customize the parameters. The results are automatically written inside the config file of the module `SU2Run` to be able to perform the calculations.

## Inputs
`ThermoData` can be run on is own by giving the altitude the Mach number and the Net force. Otherwise it can take as an input the values from `CPACS2GMSH` module. 

## Analyses
`ThermoData` compute the values obtained at the engine outlet giving a "EngineBC.dat" file as an output. if the workflow continues with the `SU2Run` run module the results are added to the config file to perform the simulation. 

## Outputs
`ThermoData` output is the "EngineBC.dat" file with stored inside: T_tot_out, V_stat_out, MN_out, P_tot_out, massflow_stat_out, T_stat_out, P_stat_out for the chosen engine configuration. 

## Installation or requirements
`ThermoData` needs the installation of the openmdao and pycycle suite that are included in the python environment of CEASIOMpy. 

## Limitations

To be able to change the engine parameters other than those given as input (altitude, mach, net force) the turbojet and turbofan functions in the module must be modified by coding.

## More information

* [pyCycle Github repository](https://github.com/OpenMDAO/pycycle)

* [OpenMDAO documentation ](https://openmdao.org/newdocs/versions/latest/main.html)

