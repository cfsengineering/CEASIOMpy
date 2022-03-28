<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_geometry.png">

# CPACS2SUMO

**Categories:** Geometry, Mesh

**State**: :heavy_check_mark:


`CPACS2SUMO` is a geometry converter to go from a [CPACS](https://www.cpacs.de) aircraft geometry to a [SUMO](https://www.larosterna.com/products/open-source) geometry. It will then be possible to run `SUMOAutoMesh` to generate a mesh with SUMO or to open SUMO to generate a mesh manually. 

## Inputs

`CPACS2SUMO` only takes as input a CPACS file.

## Analyses

`CPACS2SUMO` computes nothing, it only convert the geometry into another format.


## Outputs

`CPACS2SUMO` outputs a SUMO files (.smx), the path to this file is save in the CPACS file under this xpath: `/cpacs/toolspecific/CEASIOMpy/filesPath/sumoFilePath`.


## Installation or requirements

`CPACS2SUMO` is a native CEASIOMpy module, hence it is available and installed by default. To run it, you just have to be sure that are you are in the CEASIOMpy Conda environment.


## Limitations

`CPACS2SUMO` can convert fuselage, wings, engines and pylons. Other parts such as control surfaces, can not be converted. 

Other differences may appear:

:warning: Even if the definition of SUMO is close to CPACS, they differ in some points, thus for complex geometries, the SUMO geometry obtained may not be exact.  

:warning: The interpolation of surfaces between existing sections may differ. 

:warning: SUMO cannot have a airfoils with cut trainling edge.


## More information

* [CPACS official website](https://www.cpacs.de)

* [SUMO official website](https://www.larosterna.com/products/open-source)

