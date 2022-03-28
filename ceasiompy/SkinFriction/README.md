<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_aero.png">

# SkinFriction

**Categories:** Aerodynamics, Drag, Empirical

**State**: :heavy_check_mark:


`SkinFriction` module adds skin friction drag to an Aeromap calculated without it. The aerodynamic coefficients calculated with pyTornado or Euler methods (SU2) do not depend on atmospheric parameters and do not include the skin friction drag. It means that for different altitudes as input you will get the same aerodynamic coefficients. Furthermore, the drag calculated with these methods is generally underestimated. You can use this module to estimate the skin friction drag from empirical formula and add it to the selected aeroMap.


## Inputs

`SkinFriction` only takes as input a CPACS file. It needs the wetted surface area of the aircraft to get get it you must have run `SU2Run` before this modules, the it will be saved in the CPACS file.


## Analyses


The formula used to estimate the skin friction drag is from the paper by Gerard W. H. van Es [[1]](#Gerard12)

With the Wetted aera S<sub>wet</sub> the span b, the aircraft velocity 
V and kinematic viscosity ν we can calculate the Reynolds number Re:

![Re](https://latex.codecogs.com/png.image?\dpi{110}\bg{white}Re&space;=&space;(S_{wet}/b)&space;\cdot&space;V&space;/&space;\nu)

<!-- If one day Github accept Latex equation in Markdown... -->
<!-- Re = (S_{wet}/b) \cdot V / \nu -->

We can now compute the skin friction coefficient from the linear regression found in the paper:

![Cfe](https://latex.codecogs.com/png.image?\inline&space;\small&space;\dpi{100}\bg{white}C_{fe}&space;=&space;0.00258&space;&plus;&space;0.00102&space;\cdot&space;exp(-6.28\cdot10^{-9}&space;\cdot&space;Re)&space;&plus;&space;0.00295&space;\cdot&space;exp(-2.01&space;\cdot&space;10^{-8}&space;\cdot&space;Re)&space;)

<!-- C_{fe} = 0.00258 + 0.00102 \cdot exp(-6.28\cdot10^{-9} \cdot Re) + 0.00295 \cdot exp(-2.01 \cdot 10^{-8} \cdot Re) -->

And finally, we can calculate the zero-lift drag coefficient with the following formula:

![CD0](https://latex.codecogs.com/png.image?\inline&space;\small&space;\dpi{100}\bg{white}C_{D0}&space;=&space;C_{fe}&space;\cdot&space;S_{wet}&space;/&space;S&space;)

<!-- C_{D0} = C_{fe} \cdot S_{wet} / S -->

Then, this coefficient is added to the drag coefficient C<sub>D</sub> in the already calculated aeromap.


## Outputs

 The output of `SkinFriction` outputs a CPACS files with a new or updated aeromap.


## Installation or requirements

`SkinFriction` is a native CEASIOMpy module, hence it is available and installed by default. To run it, you just have to be sure that are you are in the CEASIOMpy Conda environment.


## Limitations

`SkinFriction` module only uses empirical formula to approximate the skin friction drag, it does not take into account the exact form of the aircraft or the surface roughness.

The equation used above should be valid in the following ranges of values:

* Re (based on S<sub>wet</sub>):  35-390·10<sup>6</sup> [-]
* S<sub>wet</sub>: 120-3400 [m<sup>2</sup>]
* S<sub>ref</sub>: 20-580 [m<sup>2</sup>]
* b: 10–68 [m]


## More information

* https://en.wikipedia.org/wiki/Skin_friction_drag


## References

<a id="Gerard12">[1]</a> Gerard W. H. van Es, Rapid Estimation of the Zero-Lift Drag Coefficient of Transport Aircraft, Journal of Aircraft, Volume 39, Number 4,  https://arc.aiaa.org/doi/10.2514/2.2997

