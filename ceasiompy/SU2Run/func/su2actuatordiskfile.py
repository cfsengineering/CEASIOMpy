"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

Functions to generate the actuator disk file for SU2.

Source: https://github.com/su2code/SU2/blob/master/TestCases/rans/
        actuatordisk_variable_load/ActuatorDisk.dat

Python version: >=3.7

| Author : Aidan Jungo
| Creation: 2022-05-31

TODO:


"""

# =================================================================================================
#   IMPORTS
# =================================================================================================

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger()


# =================================================================================================
#   CLASSES
# =================================================================================================


# =================================================================================================
#   FUNCTIONS
# =================================================================================================


def write_header(file):
    """Write the header of the actuator disk file

    Args:
        file (file): File to write the header

    """

    file.write("# TEST CASE PROPELLER DATA.\n")
    file.write("# ADV_RATIO defined as Vinf/(nD) where: \n")
    file.write("#    n: propeller rounds per second,\n")
    file.write("#    D: propeller diameter.\n")
    file.write("# 'Renard' definition of propeller coefficients:\n")
    file.write("# reference force = rho*n^2*D^4, reference power = rho*n^3*D^5.\n")
    file.write("# Propeller center in grid coordinates.\n")
    file.write("# Propeller axis versor pointing backward.\n")
    file.write("# Total thrust coefficient CT = 0.15.\n")
    file.write("# --------------------------------------------------------------------------- #\n")

    return file


def write_actuator_disk_data(file, inlet_marker, outlet_marker, center, axis, radius):
    """Function to create a ActuatorDisk.dat file which is used to when rotor/propeller are define
    in the CPACS file.

    Args:
        file (file): File to write the actuator disk file
        inlet_marker (str): Marker of the inlet of the actuator disk
        outlet_marker (str): Marker of the outlet of the actuator disk
        center (tuple): Center of the actuator disk (x,y,z)
        axis (tuple): Axis of the actuator disk (x,y,z)
        radius (float): Radius of the actuator disk

    """

    file.write(f"MARKER_ACTDISK= {inlet_marker} {outlet_marker}\n")
    file.write(f"CENTER= {center[0]} {center[1]} {center[2]}\n")
    file.write(f"AXIS= {axis[0]} {axis[1]} {axis[2]}\n")
    file.write(f"RADIUS= {radius}\n")

    # These value must be specific to a propeller, but how to genereate them?
    file.write("ADV_RATIO= 2.0\n")
    file.write("NROW= 37\n")
    file.write("# rs=r/R    dCT/drs     dCP/drs     dCR/drs\n")
    file.write("0.2031   0.20066   00.890674         0.0\n")
    file.write("0.2235   0.19963   00.932674         0.0\n")
    file.write("0.2439   0.21707   00.982980         0.0\n")
    file.write("0.2644   0.24667   01.064153         0.0\n")
    file.write("0.2848   0.29147   01.189045         0.0\n")
    file.write("0.3257   0.43674   01.588513         0.0\n")
    file.write("0.3461   0.53380   01.849900         0.0\n")
    file.write("0.3665   0.64327   02.145367         0.0\n")
    file.write("0.3870   0.76521   02.471873         0.0\n")
    file.write("0.4278   1.03679   03.203392         0.0\n")
    file.write("0.4483   1.18918   03.609085         0.0\n")
    file.write("0.4687   1.35619   04.051864         0.0\n")
    file.write("0.4891   1.52986   04.518863         0.0\n")
    file.write("0.5096   1.71453   05.011266         0.0\n")
    file.write("0.5300   1.90755   05.528521         0.0\n")
    file.write("0.5504   2.11062   06.072281         0.0\n")
    file.write("0.5709   2.31313   06.620508         0.0\n")
    file.write("0.5913   2.51252   07.161404         0.0\n")
    file.write("0.6117   2.71376   07.700722         0.0\n")
    file.write("0.6322   2.90980   08.219708         0.0\n")
    file.write("0.6526   3.09848   08.715231         0.0\n")
    file.write("0.6730   3.28502   09.202496         0.0\n")
    file.write("0.6935   3.46774   09.681596         0.0\n")
    file.write("0.7139   3.64895   10.156277         0.0\n")
    file.write("0.7343   3.81991   10.603740         0.0\n")
    file.write("0.7548   3.98417   11.036331         0.0\n")
    file.write("0.7752   4.13550   11.442054         0.0\n")
    file.write("0.7956   4.27447   11.820164         0.0\n")
    file.write("0.8161   4.40093   12.163819         0.0\n")
    file.write("0.8365   4.51007   12.453084         0.0\n")
    file.write("0.8569   4.60535   12.682212         0.0\n")
    file.write("0.8774   4.67765   12.823500         0.0\n")
    file.write("0.8978   4.71296   12.839416         0.0\n")
    file.write("0.9182   4.70303   12.701343         0.0\n")
    file.write("0.9387   4.60921   12.317719         0.0\n")
    file.write("0.9591   4.34937   11.470356         0.0\n")
    file.write("0.9795   3.77288   9.7460480         0.0\n")
    file.write("\n")

    return file


# =================================================================================================
#    MAIN
# =================================================================================================

if __name__ == "__main__":

    print("Nothing to execute!")
