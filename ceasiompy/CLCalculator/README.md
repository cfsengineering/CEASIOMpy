<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_aero.png">

# CLCalculator

**Categories:** Aerodynamics, Flight

**State**: :heavy_check_mark:


`CLCalculator` determines the lift coefficient C<sub>L</sub> of an aircraft to sustain a cruise flight, for a given Mach number, altitude, and mass.


## Inputs

`CLCalculator` only takes as input a CPACS file. The flight conditions and mass must be specified in the CPACS file.


## Analyses

`CLCalculator` determines the Lift coefficient C<sub>L</sub> required to fly with the set of following conditions:

* Mass of the aircraft: M [kg]
* Mach number: Ma [-] 
* Load Factor: LF [-] 
* Reference surface area: S<sub>ref</sub> [m<sup>2</sup>] 
* Static pressure: P<sub>S</sub> [Pa] 
* Acceleration of gravity: g [m/s<sup>2</sup>]

Static pressure and acceleration of gravity can be obtained from the altitude (with the module [Ambiance](https://github.com/airinnova/ambiance) installed with CEASIOMpy). The reference surface area: S<sub>ref</sub> is calculated from the aircraft's geometry. 

The Lift force of an aircraft is given by:

![Lift](https://latex.codecogs.com/png.image?\dpi{110}\bg{white}L&space;=&space;\frac{1}{2}&space;\cdot&space;q&space;\cdot&space;S_{ref}&space;\cdot&space;C_L)

Dynamic pressure can be calculated as:

![Dynamic pressure](https://latex.codecogs.com/png.image?\dpi{110}\bg{white}q&space;=&space;\frac{1}{2}&space;\cdot&space;\gamma&space;\cdot&space;P_s&space;\cdot&space;M^2)

and we know the lift force must compensate for the weight of the aircraft (times the load factor), so L=M·g·LF and with the first equation, we obtain:

![CL](https://latex.codecogs.com/png.image?\dpi{110}\bg{white}C_L&space;=&space;\frac{M&space;\cdot&space;g&space;\cdot&space;LF}{q&space;\cdot&space;S_{ref}})


## Outputs

 The output of `CLCalculator` is the target C<sub>L</sub> value to achieve, SU2 can use this value as input to make a fixed C<sub>L</sub> calculation where the angle of attack will be varied to find the correct C<sub>L</sub>.


## Installation or requirements

`CLCalculator` is a native CEASIOMpy module, hence it is available and installed by default. To run it, you just have to be sure that you are in the CEASIOMpy Conda environment.


## Limitations

When you run `CLCalculator` you must choose which mass it will use. However, in reality, the mass of the aircraft will vary during the flight.


## More information

* https://en.wikipedia.org/wiki/Lift_coefficient

