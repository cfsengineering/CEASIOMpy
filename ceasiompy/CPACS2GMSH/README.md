<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_geometry.png">

# CPACS2GMSH

**Categories:** Geometry, Mesh

**State**: :heavy_check_mark:


`CPACS2GMSH` is an automatic mesh generator module for a [CPACS](https://www.cpacs.de) aircraft geometry [[1]](#Alder20) using [GMSH](https://gmsh.info/) ,a finite element mesh generator. An unstructured mesh is automatically generated in a spherical domain surrounding the aircraft. The resulting mesh can be used for a CFD calculation by connecting the `SU2Run` module after `CPACS2GMSH` module.

## Inputs

`CPACS2GMSH` takes as input a CPACS file. This is done automatically when it is run in workflow

Multiple options are available with `CPACS2GMSH`
They are tunable with the `SettingsGUI` module:

General options:

* `Display mesh with GMSHl : False`
Open the gmsh GUI after the generation of the surface mesh (2D) and the domain mesh (3D). This option is usefully to control the quality of the automated generated mesh or make extra operation with gmsh GUI.

Domain:

* `Use Symmetry : False`
Apply a symmetry operation to the model with a xz symmetry plane in the center of the aircraft. The resulting mesh will only be generated in the y positive domain.

* `Farfield size factor : 6.0`
Enable to control the spherical domain size. The fluid domain surrounding the aircraft is defined with a radius equivalent to the largest xyz aircraft dimension times the `Farfield size factor`

Mesh size:

* `Farfield mesh size : 25.0` Mesh size of the farfield surface
* `Fuselage mesh size : 0.4` Mesh size of the fuselage surface
* `Wings mesh size : 0.23` Mesh size of the wings surface

:warning: The mesh size values are unitless. They are consistent with the aircraft dimensions units

Advanced mesh parameters :

* `Le/Te refinement factor : 7.0`
Apply a refinement on the leading and trailing edge of the aircraft wings. the element size at the le/te will be set to the wing mesh size divided by the refinement factor. This refinement decay according to a power law from the edge to 30% of the wing section cord length, where the mesh size is the wing's one.`

:warning: It is recommended to check the mesh convergence to know which value gives the best trade-off between the results accuracy and computation time, for your application case.

## Analyses

`CPACS2GMSH` Generate .brep files with TiGL for each part of the aircraft configuration. Then all the parts are imported into GMSH to generates a SU2 mesh file.

## Outputs

`CPACS2GMSH` outputs a SU2 mesh files (.su2), the path to this file is saved in the CPACS file under this xpath: /cpacs/toolspecific/CEASIOMpy/filesPath/su2Mesh.

## Installation or requirements

`CPACS2GMSH` is a native CEASIOMpy module, hence it is available and installed by default. To run it, you just have to be sure that you are in the CEASIOMpy Conda environment.

## Limitations

At the time of writing, this module is not able to handle aircraft with control surfaces (they will not be modelled and thus appear in the final mesh).

## More information

* [CPACS official website](https://www.cpacs.de)

* [GMSH official website](https://gmsh.info/)
