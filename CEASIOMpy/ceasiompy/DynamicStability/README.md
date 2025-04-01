<img align="right" height="70" src="../../documents/logos/CEASIOMpy_banner_mission.png">

# DynamicStability

**Categories:** Aerodynamics, Dynamic, Stability

**State**: :heavy_check_mark:

## Inputs

Before hand, you need to use the PyAVL module and store enough data into ceasiompy.db to use this module.

Once you done that, you can:
    1. Choose the different mach numbers for your stability analysis.
    2. Choose the aircraft
    3. If you haven't computed any dot-derivatives 'DynamicStability' will use the Doublet Lattice Method in the frequency domain to compute those.

## Analyses

1. Computes unsteady derivatives through the Doublet Lattice Method (PanelAero).
2. Opens SDSA with all the necessary computed aerodynamic coefficients.

## Outputs

Outputs SDSA_Input.xml, which is given as input to SDSA.

## Installation or requirements

Following the automatic installation procedure on the [CEASIOMpy installation page](../../installation/INSTALLATION.md) should install `DynamicStability` automatically along with the other tools.

## Not implemented

1. Landing gear configuration
2. Collision points

## Limitations

1. Depends on SDSA software.
2. Altitude fixed at 1000 meters.
3. Pilot Eye is by default the tip of fuselage.

## More information

Dynamic Stability Software: [SDSA](https://www.meil.pw.edu.pl/add/ADD/Teaching/Software/SDSA)
Doublet Lattice Solver: [PanelAero](https://github.com/DLR-AE/PanelAero)
Dot derivatives algorithm: [DotDerivatives](https://fr.overleaf.com/read/qjffvmtrzzhb#8fc920)