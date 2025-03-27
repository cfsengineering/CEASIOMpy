
<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_aero.png">

# PyAVL

**Categories:** Aerodynamics, vortex lattice method, low-fidelity.

**State**: :heavy_check_mark:

<img align="right" height="120" src="files/avl_logo.png">

`PyAVL` module is a launcher for the [Athena Vortex Lattice (AVL)](https://web.mit.edu/drela/Public/web/avl/) solver, developed by M. Drela and H. Youngren at MIT. It is a vortex lattice method (VLM) solver for low-fidelity aerodynamic computations. 

## Inputs

`PyAVL` takes as input a CPACS file, the aircraft geometry is read to create the VLM model for the wings and fuselage. The flight conditions have to be defined within an aeromap, as well as the number of vortex panels to use.

<p align="center">
<img height="340" src="files/avl_example.png">
</p>
<p align="center">
Example of AVL geometry model.
</p>

## Analyses

`PyAVL` computes the aerodynamic coefficients of an aircraft for a given aeromap and writes the results in a CPACS file. It calculates the total forces on the aircraft, the forces on individual surfaces, the forces on wing strips, and the forces on each panel. The stability derivatives can also be computed.

## Outputs

`PyAVL` outputs a CPACS file with the aerodynamic coefficients added in the aeromap. The settings of the simulation (number of chordwise/spanwise vortices, vortex distribution) are saved. The following force files are saved:
- `ft.txt`: Total Forces. 
- `fn.txt`: Surface Forces.
- `fs.txt`: Strip Forces.
- `fe.txt`: Element Forces (vortex strength).

The following plots are generated:
- `plot.pdf`: it contains a plot of the initial AVL geometry model, and a plot with the aerodynamic loads on the aircraft.
- `lift_distribution.png`: plot of the lift distribution along the span.

<p align="center">
<img height="340" src="files/avl_example_loads.png">
</p>
<p align="center">
Example of aerodynamic loads computed by AVL.
</p>


## Installation or requirements

Following the automatic installation procedure on the [CEASIOMpy installation page](../../installation/INSTALLATION.md) should install `PyAVL` automatically along with the other tools.

## Limitations

`PyAVL` uses a Vortex Lattice Method solver:
- The flow is quasi-steady and ideal: incompressible, irrotational, and inviscid.
- The flow is low-subsonic: [Prandlt-Glauert transformation](https://en.wikipedia.org/wiki/Prandtl%E2%80%93Glauert_transformation) is used to adapt the equations up to Mach 0.6.
- Lifting surfaces are assumed to be thin, the thickness is not taken into account.
- The angle of attack and sideslip must be small.
- Viscous effects, turbulence or boundary layer phenomena are not solved at all.

## More information

- [AVL documentation.](https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf)
- [AVL website.](https://web.mit.edu/drela/Public/web/avl/)
- [Flight Vehicule Aerodynamics](https://mitpress.mit.edu/9780262526449/flight-vehicle-aerodynamics/) by M. Drela.
- [Low-Speed Aerodynamics](https://www.cambridge.org/core/books/lowspeed-aerodynamics/077FAF851C4582F1B7593809752C44AE) by J. Katz and A. Plotkin.
- [Aerodynamics for Engineers](https://www.cambridge.org/highereducation/books/aerodynamics-for-engineers/C8AAC9F38F0781CA38AB65FA85E61CCF#overview) by J. Bertin.
