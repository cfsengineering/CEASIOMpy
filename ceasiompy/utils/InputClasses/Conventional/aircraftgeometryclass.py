"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script contains all the geometrical value required for the
weight and Balance analysis.

| Works with Python 2.7
| Author : Stefano Piccini
| Date of creation: 2018-11-26
| Last modifiction: 2019-02-20
"""


#=============================================================================
#   IMPORTS
#=============================================================================


""" No Inports Required """


#=============================================================================
#   CLASSES
#=============================================================================

class AircraftGeometry:
    """
    The class contains all the information about the geometry of
    the aircraft analyzed.

    ATTRIBUTES
    # General
    (float) tot_length             --Att.: Aircraft total length [m].

    # Fuselage
    (int) fus_nb                 --Att.: Number of fuselage [-].
    (int) fuse_nb              --Att.: Number of fuselage counting\
                                           simmetry [-].
    (int_array) fuse_sym       --Att.: Fuselage symmetry plane [-].
    (int_array) fuse_sec_nb    --Att.: Number of fuselage sections [-].
    (int_array) fuse_seg_nb    --Att.: Number of fuselage sections [-].
    (int_array) fuse_seg_index --Att.: Number of fuselage sections [-].
    (int_array) cabin_nb  --Out.: number if cabins per fuselage
    (int_array) cabin_seg --Out.: Array that will contain 1 if the
                                  segment is a cabin segment or
                                  0 otherwise.
    (float_array) fuse_length      --Att.: Fuselage length [m].
    (float_array) fuse_sec_circ    --Att.: Circumference of fuselage
                                           sections [m].
    (float_array) fuse_sec_width    --Att.: Width of fuselage sections [m].
    (float_array) fuse_sec_rel_dist --Att.: Relative distance of each section
                                            to the start profile.
    (float_array) fuse_seg_length   --Att.: Length of each fuselage
                                            segments [m].
    (float_array) fuse_nose_length  --Att.: Length of each fuselage nose [m].
    (float_array) fuse_cabin_length --Att.: Length of each fuselage cabin [m].
    (float_array) fuse_tail_length  --Att.: Length of each fuselage tail [m].
    (float_array) fuse_mean_width   --Att.: Mean fuselage width [m].
    (floar_array) fuse_center_seg_point --Att.: 3D array containing the
                                                position of the point
                                                at the center of each segment
                                                of the fuselage
                                                (x,y,z - coord.) [m,m,m].
    (floar_array) fuse_center_sec_point --Att.: 3D array containing the
                                                position of the point
                                                at the center of each section
                                                of th fuselage
                                                (x,y,z - coord.) [m,m,m].
    (float_array) fuse_seg_vol    --Att.: Volume of fuselage segments [m^3].
    (float_array) fuse_cabin_vol  --Att.: Cabin volume of each fuselage [m^3].
    (float_array) fuse_vol        --Att.: Fuselage volume [m^3].
    (float_array) f_seg_sec       --Att.: Reordered segments with
                                          respective start and end
                                          sections for each fuselage.

    # Wing
    (int) w_nb                 --Att.: Number of wings [-].
    (int) wing_nb              --Att.: Number of wings [-].
    (int) main_wing_index      --Att.: Main wing index.
    (int_array) wing_sym       --Att.: Wing symmetry plane [-].

    (int_array) wing_sec_nb    --Att.: Number of fuselage sections [-].
    (int_array) fuse_seg_nb    --Att.: Number of fuselage segments [-].
    (int_array) wing_seg_nb    --Att.: Number of fuselage segments [-].
    (float_array) wing_span        --Att.: Wing span [m].
    (floar_array) wing_seg_length  --Att.: Wings sements length [m].
    (float) wing_sec_thicknes     --Att.: Wing sections thicknes [m].
    (float) wing_sec_mean_thick   --Att.: Wing sections mean thicknes [m].
    (float_array) wing_max_chord   --Att.: Wing chord in the connection
                                           with fuselage [m].
    (float_array) wing_min_chord   --Att.: Wing tip chord [m].
    (float_array) wing_mac         --Att.: Wing m.a.c. length and position
                                           (x,y,z)[m,m,m,m].
    (floar_array) wing_center_seg_point --Att.: 3D array containing the
                                                position of the point at the
                                                center of each segment of the
                                                wing (x,y,z - coord.) [m].
    (float_array) wing_plt_area   --Att.: Wings plantform area [m^2].
    (float) wing_plt_area_main    --Att.: Main wing area [m^2].
    (float_array) wing_seg_vol    --Att.: Wing segments volume [m^3].
    (float_array) wing_vol        --Att.: Volume of each wing [m^3].
    (float) wing_tot_vol          --Att.: Total wing volume [m^3].
    (float_array) wing_fuel_vol   --Att.: Wing volume available for fuel
                                          storage for each wing or couple of
                                          wings if symmetry defined [m^3].
    (float_array) wing_fuel_seg_vol --Att.: Wing volume available for fuel
                                            storage for each wing segment
                                            or couple of wing segments
    (float_array) w_seg_sec  --Att.: Reordered segments with
                                     respective start and end
                                     sections for each wing.
    (boolean_array) is_horiz --Att.: Define if a wing is horizontal [-].
    METHODS
    Name            Description
    """

    def __init__(self):
        # General
        self.tot_length = 0

        # Fuselage
        self.fus_nb = 0
        self.fuse_nb = 0
        self.fuse_sym = []
        self.fuse_sec_nb = []
        self.fuse_seg_nb = []
        self.fuse_seg_index = 0
        self.cabin_nb = 0
        self.cabin_seg = 0
        self.fuse_length = []
        self.fuse_sec_circ = 0
        self.fuse_sec_width = 0
        self.fuse_sec_abs_dist = 0
        self.fuse_seg_length = 0
        self.fuse_nose_length = []
        self.fuse_cabin_length = []
        self.fuse_tail_length = []
        self.fuse_mean_width = []
        self.fuse_center_seg_point = 0  # Balance Analysis Only
        self.fuse_center_sec_point = 0  # Balance Analysis Only
        self.fuse_seg_vol = 0
        self.fuse_cabin_vol = []
        self.fuse_vol = []
        self.f_seg_sec = 0

        # Wing
        self.w_nb = 0
        self.wing_nb = 0
        self.main_wing_index = 0
        self.wing_sym = []
        self.wing_sec_nb = []
        self.wing_seg_nb = []
        self.wing_span = []
        self.wing_seg_length = 0
        self.wing_sec_thicknes = 0
        self.wing_sec_mean_thick = []
        self.wing_max_chord = []
        self.wing_min_chord = []
        self.wing_mac = 0
        self.wing_center_seg_point = 0 # Balance Analysis Only
        self.wing_plt_area = []
        self.wing_plt_area_main = 0
        self.wing_seg_vol = 0
        self.wing_vol = []
        self.wing_tot_vol = 0
        self.wing_fuel_vol = 0
        self.wing_fuel_seg_vol = 0
        self.w_seg_sec = 0
        self.is_horiz = []


#=============================================================================
#    MAIN
#=============================================================================

if __name__ == '__main__':
    log.warning('##########################################################')
    log.warning('############# ERROR NOT A STANDALONE PROGRAM #############')
    log.warning('##########################################################')


