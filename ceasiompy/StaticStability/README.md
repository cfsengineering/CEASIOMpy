<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_mission.png">

# StaticStability

**Categories:** Aerodynamics, Static, Stability

**State**: :heavy_check_mark:

`StaticStability` module checks the three main static stabilities, for one or several aeromaps. In order to assert those stability, it only check the sign of the slope corresponding to its stability:

- `cms` vs `angleOfAttack` for the longitudinal stability (negative means stable)
- `cml` vs `angleOfSideslip` for the directional stability (positive means stable)
- `cmd` vs `angleOfSideslip` for the lateral stability (negative means stable)

(Names and reference system are those used by CPACS, more info [here](https://www.cpacs.de/documentation/CPACS_3_4_0_Docs/html/89b6a288-0944-bd56-a1ef-8d3c8e48ad95.htm))

## Inputs

`StaticStability` only takes as input a CPACS file. However the CPACS file must contained at least one aeromap. In the settings, the user can chose on which aeromap and which stability the calculation will be performed.

## Analyses

Depending how much points are stored in the aeromap, the different stability could be calculated or not. In order to check a stability the aeromap must contain at least two point with the same altitude, mach number, angle of attack/sideslip and with a different and of sideslip/attack. The moment coefficient corresponding the stability must also be present.

## Outputs

 The output of `StaticStability` outputs a Markdown file (in the results) which contains a table for each different stability. In every table the flight conditions and the stability are shown.

## Installation or requirements

`StaticStability` is a native CEASIOMpy module, hence it is available and installed by default. To run it, you just have to be sure that you are in the CEASIOMpy Conda environment.

## Limitations

`StaticStability` module only uses a simple linear regression to check the sign of the slop depending how the data are distributed it could leads to errors.

## More information

- <https://en.wikipedia.org/wiki/Longitudinal_stability>
- <https://www.cpacs.de/documentation/CPACS_3_4_0_Docs/html/89b6a288-0944-bd56-a1ef-8d3c8e48ad95.htm>
