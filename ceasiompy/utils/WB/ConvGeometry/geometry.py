"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

This file will connect the wing/fuse/output modules.

| Works with Python 2.7/3.4
| Author : Stefano Piccini
| Date of creation: 2018-09-27
| Last modifiction: 2020-07-03 (AJ)
"""

#=============================================================================
#   IMPORTS
#=============================================================================

from .Fuselage.fusegeom import fuse_geom_eval
from .Wings.winggeom import wing_geom_eval
from .Output.outputgeom import produce_output_txt

from ceasiompy.utils.ceasiomlogger import get_logger

log = get_logger(__file__.split('.')[0])


#=============================================================================
#   CLASSES
#=============================================================================

class AircraftGeometry:
    """
    The class contains all the information about the geometry of
    the aircraft analyzed.

    """

    def __init__(self):

        # General
        self.tot_length = 0             # (float) Aircraft total length [m]

        # Fuselage
        self.fus_nb = 0                 # (int) Number of fuselage [-]
        self.fuse_nb = 0                # (int)  Number of fuselage counting symmetry [-]
        self.fuse_sym = []              # (int_array) Fuselage symmetry plane [-]
        self.fuse_sec_nb = []           # (int_array) Number of fuselage sections [-]
        self.fuse_seg_nb = []           # (int_array) Number of fuselage sections [-]
        self.fuse_seg_index = 0         # (int_array) Number of fuselage sections [-]
        self.cabin_nb = 0               # (int_array) Number if cabins per fuselage
        self.cabin_seg = 0              # (int_array) Array that will contain 1 if the segment is a cabin segment or 0 otherwise.
        self.fuse_length = []           # (float_array) Fuselage length [m].
        self.fuse_sec_circ = 0          # (float_array) Circumference of fuselage sections [m].
        self.fuse_sec_width = 0         # (float_array) Width of fuselage sections [m].
        self.fuse_sec_abs_dist = 0      # (float_array) Relative distance of each section to the start profile.
        self.fuse_seg_length = 0        # (float_array) Length of each fuselage segments [m].
        self.fuse_nose_length = []      # (float_array) Length of each fuselage nose [m].
        self.fuse_cabin_length = []     # (float_array) Length of each fuselage cabin [m].
        self.fuse_tail_length = []      # (float_array) Length of each fuselage tail [m].
        self.fuse_mean_width = []       # (float_array) Mean fuselage width [m].
        self.fuse_center_seg_point = 0  # (floar_array) 3D array containing the position of the point at the center of each segment of the fuselage (x,y,z - coord.) [m,m,m]. Balance Analysis Only
        self.fuse_center_sec_point = 0  # (floar_array) 3D array containing the position of the point at the center of each section of th fuselage (x,y,z - coord.) [m,m,m]. Balance Analysis Only
        self.fuse_seg_vol = 0           # (float_array) Volume of fuselage segments [m^3]
        self.fuse_cabin_vol = []        # (float_array) Cabin volume of each fuselage [m^3]
        self.fuse_vol = []              # (float_array) Fuselage volume [m^3]
        self.f_seg_sec = 0              # (float_array) Reordered segments with respective start and end sections for each fuselage.

        # Wing
        self.w_nb = 0                   # (int) Number of wings [-]
        self.wing_nb = 0                # (int) Number of wings [-]
        self.main_wing_index = 0        # (int) Main wing index
        self.wing_sym = []              # (int_array) Wing symmetry plane [-]
        self.wing_sec_nb = []           # (int_array) Number of fuselage sections [-]
        self.wing_seg_nb = []           # (int_array) Number of fuselage segments [-]
        self.wing_span = []             # (float_array) Wing span [m]
        self.wing_seg_length = 0        # (floar_array) Wings sements length [m].
        self.wing_sec_thicknes = 0      # (float) Wing sections thicknes [m]
        self.wing_sec_mean_thick = []   # (float) Wing sections mean thicknes [m]
        self.wing_max_chord = []        # (float_array) Wing chord in the connection with fuselage [m]
        self.wing_min_chord = []        # (float_array) Wing tip chord [m]
        self.wing_mac = 0               # (float_array) Wing m.a.c. length and position (x,y,z)[m,m,m,m]
        self.wing_center_seg_point = 0  # (floar_array) 3D array containing the position of the point at the center of each segment of the wing (x,y,z - coord.) [m]. Balance Analysis Only
        self.wing_plt_area = []         # (float_array) Wings plantform area [m^2]
        self.wing_plt_area_main = 0     # (float) Main wing area [m^2]
        self.wing_seg_vol = 0           # (float_array) Wing segments volume [m^3]
        self.wing_vol = []              # (float_array) Volume of each wing [m^3]
        self.wing_tot_vol = 0           # (float) Total wing volume [m^3]
        self.wing_fuel_vol = 0          # (float_array) Wing volume available for fuel storage for each wing or couple of wings if symmetry defined [m^3]
        self.wing_fuel_seg_vol = 0      # (float_array) Wing volume available for fuel storage for each wing segment or couple of wing segments
        self.w_seg_sec = 0              # (float_array) Reordered segments with respective start and end sections for each wing
        self.is_horiz = []              # (boolean_array) Define if a wing is horizontal [-]


#=============================================================================
#   FUNCTIONS
#=============================================================================

def geometry_eval(cpacs_in, NAME):
    """This function exectute the functions to analyze the cpacs file and
       evaluate the wings and fuselage geometry.

    ARGUMENTS
    (str) cpacs_in    -- Arg.: Cpacs xml file location.
    (str) NAME        -- Arg.: Name of the aircraft.

    OUTPUTS
    (class) AircraftGeometry    --Out.: Updated aircraft_geometry class.

    """

    ag = AircraftGeometry()
    ag = fuse_geom_eval(ag, cpacs_in)
    ag = wing_geom_eval(ag, cpacs_in)

    # Output txt file generation
    produce_output_txt(ag, NAME)

    return(ag)


#=============================================================================
#   MAIN
#==============================================================================

if __name__ == '__main__':
    
    log.warning('##########################################################')
    log.warning('############# ERROR NOT A STANDALONE PROGRAM #############')
    log.warning('##########################################################')
