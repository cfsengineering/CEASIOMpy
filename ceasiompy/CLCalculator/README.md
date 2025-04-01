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

$L=\frac{1}{2}\cdot q\cdot S_{ref}\cdot C_L$

Dynamic pressure can be calculated as:

$q = \frac{1}{2} \cdot \gamma \cdot P_s \cdot M^2$

and we know the lift force must compensate for the weight of the aircraft (times the load factor), so L=M·g·LF and with the first equation, we obtain:

$C_L = \frac{M \cdot g \cdot LF}{q \cdot S_{ref}}$

## Outputs

 The output of `CLCalculator` is the target C<sub>L</sub> value to achieve, SU2 can use this value as input to make a fixed C<sub>L</sub> calculation where the angle of attack will be varied to find the correct C<sub>L</sub>.

## Installation or requirements

`CLCalculator` is a native CEASIOMpy module, hence it is available and installed by default. To run it, you just have to be sure that you are in the CEASIOMpy Conda environment.

## Limitations

When you run `CLCalculator` you must choose which mass it will use. However, in reality, the mass of the aircraft will vary during the flight.

## More information

* <https://en.wikipedia.org/wiki/Lift_coefficient>
