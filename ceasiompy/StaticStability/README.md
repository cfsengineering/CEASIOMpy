<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_mission.png">

# StaticStability

**Categories:** Aerodynamics, Static, Stability

**State**: :heavy_check_mark:

`StaticStability` module checks the three main static stabilities, that is the sign of the slope corresponding to its stability:

- Pitch moment `Cm` vs `angleOfAttack` for the longitudinal stability (negative slope means stable)
- Yaw moment `Cn` vs `angleOfSideslip` for the directional stability (positive slope means stable)
- Roll moment `Cl` vs `angleOfSideslip` for the lateral stability (negative slope means stable)

(Names and reference system are those used by CPACS, more info [here](https://www.cpacs.de/documentation/CPACS_3_4_0_Docs/html/89b6a288-0944-bd56-a1ef-8d3c8e48ad95.htm))

## Inputs

`StaticStability` only takes as input a CPACS file. However the CPACS file must contained at least one aeromap. In the settings, the user can choose on which aeromap and which stability the calculation will be performed.

## Analyses

1. If you use the pyAVL module before the StaticStability module :
A unique (Mach, Altitude, AoA, AoS) in the aeromap suffices to do the Static Stability analysis as the necessary derivates are already computed.

2. If you are not using pyAVL, then the model does a linear regression (it assumes that the moments are linear wrt to the angles of interest). Therefore you need to add strictly more then one different angle of attack and sideslip angle in the aeromap to access the stability derivatives.  

## Outputs

In the results directory you can find:
    1. a Markdown file which contains a table with the stability results (Stable/Unstable wrt to the 3 different axes) for the specific aeromap.

    2. A longitudinal, directional and lateral html plot of the Pitch, Yaw and Roll moments wrt AoA, AoS and AoS respectively.

## Installation or requirements

`StaticStability` is a native CEASIOMpy module, hence it is available and installed by default. To run it, you just have to be sure that you are in the CEASIOMpy Conda environment.

## Limitations

`StaticStability` module makes the assumption that the pitch, roll and yaw moments are a linear function of the angle of attack and sidelip angle.

## More information

- <https://www.cpacs.de/documentation/CPACS_3_4_0_Docs/html/89b6a288-0944-bd56-a1ef-8d3c8e48ad95.htm>