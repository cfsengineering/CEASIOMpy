# scope user manual

Scope displays meshes for computational fluid dynamics (CFD), structural 
analysis and is meant to support many common operations in the fields of
flight dynamics and aeroelasticity.


## Basic Concepts

Scope loads a variety of [mesh file formats](formats.md); all of these files 
contain discretized information, that is, data defined in terms of nodes 
(grid points) and elements; scope does not handle continuous geometry, such as,
for example, surfaces defined in CAD systems adn stored in IGES or STEP files.

[Meshes analysis](display.md#inspecting-meshes) functions allow to generate sectional views through volume meshes. Quality criteria can be evaluated in order to locate and highlight low-quality elements.

In many cases, scope will also import data fields associated with these meshes. [Scalar fields](display.md#scalar-fields) can be displayed as color contours; vector fields can be turned into [surface streamlines](display.md#streamlines). Sectioning tools permit to generate XY-plots of surface data. 

Originally, scope was implemented to support [research](http://urn.kb.se/resolve?urn=urn:nbn:se:kth:diva-584) in the field of aeroelasticity. It has since been used as a visualization and post-processing back-end for [another solver](http://dx.doi.org/10.2514/1.C031738) and to support work on [automatic mesh generation](http://dx.doi.org/10.1016/j.cad.2015.06.010).

## Examples

### Map mesh deformation

Aeroelastic analyses regularly require that deformations of a structural model are translated to the wetted surface of a dissimilar aerodynamic mesh. Scope implements [different algorithms](mapping.md) which can deal with many industrially relevant cases with complex geometry and discontinuous displacements.

### Generate flight loads

Different types of [structural loads](loads.md) can be generated from one or a collection of aerodynamic solutions. 

### Convert mesh formats

Scope can be use simply to convert between [mesh formats](formats.md) (say, from the format used for the DLR TAU solver to Stanford's SU2 solver format), without the need to go through a commercial tool.

## Scope is not Paraview

Scope does not attempt to replace [Paraview](http://www.paraview.org), which is far more flexible and most likely more suitable for many applications. Instead, Scope will often be able to convert your analysis results to a [file format](formats.md) readable by Paraview for further postprocessing.


## State of Documentation

This user manual makes no claim to completeness; with time, some sections may become outdated or inaccurate. [Contact](mailto:david@larosterna.com) the author if you would like to fund improved documentation.

## License

Scope is available in source code form under the terms of the [GNU Public License](http://www.gnu.org/licenses/gpl-3.0.en.html). Compiled versions are regularly updated for use on Mac OS X, Windows and some Linux distibutions. 
 
