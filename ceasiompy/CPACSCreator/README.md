

<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_geometry.png">

# CPACSCreator

**Categories:** Geometry, CPACS, Aircraft modeling, CAO

**State**: :white_check_mark:


`CPACSCrator` is just a launcher for [CPACSCrator](https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/) which has been devlopped in collaboration between CFS Engineering and DLR [[1]](#Drou18).


<p align="center">
<img height="340" src="https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/tuto_scratch_23.png">
</p>
<p align="center">
CPACSCrator can be use to create or modify existing CPACS file of aircraft.
</p>


## Inputs

In a CEASIOMpy workflow `CPACSCrator` takes as input a CPACS file, the other inputs are the modifications made by the user on the aircfat geomtry.

## Analyses

`CPACSCrator` computes nothing, however it allows you to modify an aircraft geometry and add or remove some of theses parts.


## Outputs

`CPACSCrator` outputs a CPACS files with the modified aircraft geometry.

:warning: Do not forget to save the aircraft before you close CPACSCreator.


## Installation or requirements

`CPACSCreator` is install automatically when install the CEASIOMpy Conda environement. To run it, you just have to be sure are you are in the CEASIOMpy Conda environment.


## Limitations

`CPACSCrator` allows to modify the wings and fuselage of an aircfat. For now it is not possible to add or modify things like engines, control surfaces, landing gear, etc.  


## More information

* [CPACSCreator turorial](https://dlr-sc.github.io/tigl/doc/cpacscreator-0.1/tuto.html#tuto_create_from_scratch)

* [CPACSCreator video turorial](https://www.youtube.com/watch?v=M5ryc7HT3uA)

* Check out the CPACSCreator futur features in the [TiGL repository](https://github.com/DLR-SC/tigl/issues?q=is%3Aopen+is%3Aissue+label%3ACPACS-Creator)


## References

<a id="Drou18">[1]</a> Drougard, M.: Computer-Aided Design for Aircraft. Master Thesis (2018). EPFL École polytechnique fédérale de Lausanne. LINK  
