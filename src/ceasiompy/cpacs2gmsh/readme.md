<img align="right" height="70" src="../../../documents/logos/CEASIOMpy_banner_geometry.png">

# CPACS2GMSH

**Categories:** Geometry, Mesh

**State**: :heavy_check_mark:

<img align="right" height="150" src="https://gitlab.onelab.info/gmsh/gmsh/-/raw/a8662def403b8e0327a0f0e6ecf1d8aca1a1f63d/utils/icons/gmsh.png">

<br />

`CPACS2GMSH` is an automatic mesh generator module for a [CPACS](https://www.cpacs.de) aircraft geometry [[1]](#Alder20) using [GMSH](https://gmsh.info/) ,a finite element mesh generator.

It's currently possible to choose between two options for 3D meshing of the external domain.
Selecting the 'Euler' an unstructured mesh is automatically generated in a spherical domain surrounding the aircraft.
Instead, selecting the 'RANS' option Gmsh will generate only the 2D mesh of the entire aircraft, which will then be processed by the program Pentagrow to generate the structured part that wraps the geometry, then [Tetgen](https://wias-berlin.de/software/tetgen/1.5/doc/manual/manual.pdf) package provides for meshing of the unstructured part. The hybrid mesh obtained will constitute the 3D domain.


The resulting mesh can be used for a CFD calculation by connecting the `SU2Run` module after `CPACS2GMSH` module.

## Analyses

`CPACS2GMSH` Generate .brep files with TiGL for each part of the aircraft configuration. Then all the parts are imported into GMSH to generates a SU2 mesh file
for the euler case, instead a .stl file is generated to be read by pentagrow

## Outputs

`CPACS2GMSH` outputs a SU2 mesh files (.su2), the path to this file is saved in the CPACS file under this xpath: /cpacs/toolspecific/CEASIOMpy/filesPath/su2Mesh.

With RANS also a configuration file is created in the same directory containing the setup used to generate the hybrid mesh.

## Installation or requirements

`CPACS2GMSH` is a native CEASIOMpy module, hence it is available and installed by default. To run it, you just have to be sure that you are in the CEASIOMpy Conda environment.

## Limitations

At the time of writing, this module is not able to handle aircraft with control surfaces (they will not be modelled and thus appear in the final mesh).

For the RANS part, it is only possible to process aircraft consisting of .brep files of category 'fuselage', 'wing', 'engine', 'rotor' and 'propellers'.

## More information

* [CPACS official website](https://www.cpacs.de)

* [GMSH official website](https://gmsh.info/)
