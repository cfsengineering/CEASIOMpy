<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_main.png">

# ThermoData

**Categories:** Engine Boundary conditions

**State**: :heavy_check_mark:

<br />

`ThermoData` is a module to provide the outlet conditions of a given engine. It can calculate different operating conditions and save the results in a text file. This module is derived starting from the OpenSource code [pyCycle](https://github.com/OpenMDAO/pycycle) developed by Eric S. Hendricks and Justin S. Gray. It can perform calculations on both turbojet and turbofan engines, with the possibility to customize the parameters. The main parameters that can be modified are: the rotational speed of the shaft/s, the temperature at the inlet of the turbine/s, the efficiency of compressor/s and turbine/s (HP and LP) and the compressor/s pressure ratio. The results are automatically written inside the configuration file of the module `SU2Run` to be able to perform the CFD calculations if needed.

## Inputs
`ThermoData` can be run on is own by giving an Aeromap that contains Altitude and Mach number with the addition of the Net force that needs to be chosen. Otherwise it can take as an input the values from `CPACS2GMSH` module.

## Analyses
`ThermoData` compute the values obtained at the engine outlet giving a "EngineBC.dat" file as an output. If the workflow continues with the `SU2Run` run module the results are added to the config file of SU2 to perform the simulation.

## Outputs
`ThermoData` output is the "EngineBC.dat" file with stored inside for the turbojet engine:
* T_tot_out= Nozzle total temperature outlet[K],
* T_stat_out= Nozzle static temperature outlet[K],
* P_tot_out= Nozzle total pressure outlet [Pa],
* P_stat_out= Nozzle static pressure outlet [Pa].
* V_stat_out= Nozzle static velocity outlet[m/s],
* MN_out= Nozzle Mach number outlet [adim],
* massflow_stat_out= Nozzle massflow outlet [Kg/s]\\

For the turbofan engine are added also the values at the exit of the bypass nozzle.



## Installation or requirements
`ThermoData` needs the installation of the openMDAO and pycycle suite that are included in the python environment of CEASIOMpy.

## Limitations

To be able to change the engine parameters other than those given as input (altitude, mach, net force) the turbojet and turbofan functions in the module must be modified by coding.

## More information

* [pyCycle Github repository](https://github.com/OpenMDAO/pycycle)

* [OpenMDAO documentation ](https://openmdao.org/newdocs/versions/latest/main.html)

* [SU2 website](https://su2code.github.io/)

* [SU2 Github repository](https://github.com/su2code/SU2)


