<img align="right" height="70" src="../../../documents/logos/CEASIOMpy_banner_aero.png">

# VSP2CPACS

**Categories:** CAD, Geometry.

**State:** :heavy_check_mark:

`VSP2CPACS` is a CEASIOMpy module that converts aircraft geometries created in [OpenVSP](https://openvsp.org/) into the CPACS format.

The geometry is first built and saved in OpenVSP as a `.vsp3` file.  
This module reads the OpenVSP model and generates an equivalent CPACS representation of the aircraft.

---

## Inputs

`VSP2CPACS` takes as input:
- An OpenVSP geometry file (`.vsp3`)

The following OpenVSP components are currently supported:
- Wings
- Fuselages
- Pods
- Ducts (used for engine modeling)

Parent–child relationships between components are preserved.

---

## Functionality

`VSP2CPACS`:
- Reads the OpenVSP geometry
- Extracts geometric and transformation parameters
- Converts the geometry into CPACS-compliant elements
- Preserves component hierarchy and transformations

---

## Outputs

The module generates:
- A CPACS file containing the aircraft geometry

The resulting CPACS file can be used as input for other CEASIOMpy modules for further analysis.

---

## Installation / Requirements

`VSP2CPACS` is installed automatically as part of CEASIOMpy.

Follow the standard installation procedure described in the CEASIOMpy installation guide.

---

## Limitations

- The conversion is limited to the supported OpenVSP components.
- Only geometric information is converted.
- Some advanced OpenVSP features may not have a direct CPACS equivalent.
- The accuracy of the conversion depends on the consistency of the OpenVSP model.

---

## More information

- [OpenVSP website](https://openvsp.org/)
- [CPACS documentation](https://cpacs.de/)
