<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_geometry.png">

# CPACSCreator

**Categories:** Geometry, CPACS, Aircraft modeling, CAO

**State**: :heavy_check_mark:

`CPACSCreator` module is just a launcher for [CPACSCreator](https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/) which has been developed in collaboration between CFS Engineering and DLR [[1]](#Drou18). CPACSCreator is a CAD tool for creating and modifying a CPACS file.

<p align="center">
<img height="340" src="https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/tuto_scratch_23.png">
</p>
<p align="center">
CPACSCreator can be used to create or modify existing CPACS file of aircraft.
</p>

## Inputs

In a CEASIOMpy workflow `CPACSCreator` takes as input a CPACS file, the other inputs are the modifications made by the user on the aircraft geometry.

## Analyses

`CPACSCreator` computes nothing, however it allows you to modify an aircraft geometry and add or remove some of theses parts.

## Outputs

`CPACSCreator` outputs a CPACS files with the modified aircraft geometry.

:warning: Do not forget to save the aircraft before you close CPACSCreator.

## Installation or requirements

`CPACSCreator` is installed automatically when install the CEASIOMpy Conda environement. To run it, you just have to be sure you are in the CEASIOMpy Conda environment.

## Limitations

`CPACSCreator` allows you to modify the wings and fuselage of an aircraft. For now it is not possible to add or modify things like engines, control surfaces, landing gear, etc.

## More information

* [CPACSCreator tutorial](https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/tuto.html#tuto_create_from_scratch)

* [CPACSCreator video tutorial](https://www.youtube.com/watch?v=M5ryc7HT3uA)

* Check out the CPACSCreator future features in the [TiGL repository](https://github.com/DLR-SC/tigl/issues?q=is%3Aopen+is%3Aissue+label%3ACPACS-Creator)

## References

<a id="Drou18">[1]</a> Drougard, M.: Computer-Aided Design for Aircraft. Master Thesis (2018). EPFL École polytechnique fédérale de Lausanne. LINK
