"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed for CFS ENGINEERING, 1015 Lausanne, Switzerland

The script contains all the geometrical value required for the
weight unconventional analysis.

Python version: >=3.6

| Author : Stefano Piccini
| Date of creation: 2018-11-26
| Last modifiction: 2020-01-22 (AJ)

"""

# =============================================================================
#   IMPORTS
# =============================================================================

""" No import """


# =============================================================================
#   CLASSES
# =============================================================================


class AircraftWingGeometry:
    """
    The class contains all the geometry information extracted for the wings.

    Attributes:
        is_horiz (str): Define if a wing is horizontal [-].
        w_nb (int): Number of wings [-].
        wing_nb (int): Number of wings [-].
        main_wing_index (int): Main wing index.
        wing_sym (int_array): Wing symmetry plane [-].
        wing_sec_nb (int_array): Number of fuselage sections [-].
        fuse_seg_nb (int_array): Number of fuselage segments [-].
        wing_seg_nb (int_array): Number of wing segments [-].
        wing_span (float_array): Wing span [m].
        wing_seg_length (floar_array): Wings sements length [m].
        wing_sec_thicknes (float): Wing sections thicknes [m].
        wing_sec_mean_thick (float): Wing sections mean thicknes [m].
        wing_max_chord (float_array): Wing chord in the connection with fuselage [m].
        wing_min_chord (float_array): Wing tip chord [m].
        wing_mac (float_array): Wing m.a.c. length and position (x,y,z)[m,m,m,m].
        wing_center_seg_point (floar_array): 3D array containing the position of
                                             the point at the center of each
                                             segment of the wing (x,y,z - coord.) [m].
        wing_plt_area (float_array) : Wings plantform area [m^2].
        wing_plt_area_main (float): Main wing area [m^2].
        main_wing_surface (float): Main wing wetted area [m^2].
        tail_wings_surface (float_array): Wetted surface area of the tail wings. [m^2]
        total_wings_surface (float): Wings wetted area total [m^2].
        wing_seg_vol (float_array): Wing segments volume [m^3].
        wing_vol (float_array): Volume of each wing [m^3].
        wing_tot_vol (float): Total wing volume [m^3].
        w_seg_sec (float_array): Reordered segments with respective start and
                                 end sections for each wing.

        cabin_span (float): Width of the cabin [m].
        y_max_cabin (float): Maximum height of the cabin [m].
        cabin_area (float): Area of the BWB allowed for passenger [m^2].
        fuse_vol (float): Volume of the central part of the wing, calledas fuselage [m^3].
        cabin_vol (float): Volume of the cabin [m^3].
        fuse_fuel_vol (float): Volume of th fuselage allowed for fuel storage [m^3]
        wing_fuel_vol (float): Volume of the fuel inside the wings [m^3].
        fuel_vol_tot (float): Total fuel volume allowed [m^3].

    """

    def __init__(self):
        self.is_horiz = []
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
        self.wing_center_seg_point = 0
        self.wing_plt_area = []
        self.wing_plt_area_main = 0
        self.main_wing_surface = 0
        self.tail_wings_surface = []
        self.total_wings_surface = 0
        self.wing_seg_vol = 0
        self.wing_vol = []
        self.wing_tot_vol = 0
        self.w_seg_sec = 0

        # Cabin and Fuel
        self.cabin_span = 0
        self.y_max_cabin = 0
        self.cabin_area = 0
        self.fuse_vol = 0
        self.cabin_vol = 0
        self.fuse_fuel_vol = 0
        self.wing_fuel_vol = 0
        self.fuel_vol_tot = 0


class AircraftFuseGeometry:
    """
    The class contains all the geometry information extracted for the fuselage.

    Attributes:

        tot_length (float): Aircraft total length [m].
        fus_nb (int): Number of fuselage [-].
        fuse_nb (int): Number of fuselage counting simmetry [-].
        fuse_sym (int_array) : Fuselage symmetry plane [-].
        fuse_sec_nb (int_array) : Number of fuselage sections [-].
        fuse_seg_nb (int_array) : Number of fuselage sections [-].
        fuse_seg_index (int_array) : Number of fuselage sections [-].
        cabin_nb (int_array) : number if cabins per fuselage
        cabin_seg (int_array) : Array that will contain 1 if the segment
                                is a cabin segment or 0 otherwise.
        fuse_length (float_array): Fuselage length [m].
        fuse_sec_circ (float_array): Circumference of fuselage sections [m].
        fuse_sec_width (float_array): Width of fuselage sections [m].
        fuse_sec_rel_dist (float_array): Relative distance of each section to the start profile.
        fuse_seg_length (float_array): Length of each fuselage segments [m].
        fuse_sec_rel_dist (float_array): Relative distance of each section with the start one [m].
        fuse_nose_length (float_array): Length of each fuselage nose [m].
        fuse_cabin_length (float_array): Length of each fuselage cabin [m].
        fuse_tail_length (float_array): Length of each fuselage tail [m].
        fuse_mean_width (float_array): Mean fuselage width [m].
        fuse_center_seg_point (floar_array): 3D array containing the position of
                                             the point at the center of each segment
                                             of the fuselage (x,y,z - coord.) [m,m,m].
        fuse_center_sec_point (floar_array): 3D array containing the position of
                                             the point at the center of each section
                                             of th fuselage (x,y,z - coord.) [m,m,m].
        cabin_area (float_array): Area of the cabin of each fuselage [m^2].
        fuse_surface (float_array): Wetted area of each fuselage [m^2].
        fuse_seg_vol (float_array): Volume of fuselage segments [m^3].
        fuse_cabin_vol (float_array): Cabin volume of each fuselage [m^3].
        fuse_fuel (float_array): Volume of the fulage used as fuel tank [m^3].
        fuse_vol (float_array): Fuselage volume [m^3].
        f_seg_sec (float_array): Reordered segments with respective start
                                     and end sections for each fuselage.

    """

    def __init__(self, fus_nb):

        self.tot_length = 0
        self.fus_nb = fus_nb
        self.fuse_nb = fus_nb
        self.fuse_sym = []
        self.fuse_sec_nb = []
        self.fuse_seg_nb = []
        self.fuse_seg_index = 0
        self.cabin_nb = 0
        self.cabin_seg = 0
        self.fuse_length = []
        self.fuse_sec_per = 0
        self.fuse_sec_width = 0
        self.fuse_sec_abs_dist = 0
        self.fuse_seg_length = 0
        self.fuse_sec_rel_dist = 0
        self.fuse_nose_length = []
        self.fuse_cabin_length = []
        self.fuse_tail_length = []
        self.fuse_nose_length = []
        self.fuse_mean_width = []
        self.fuse_center_seg_point = 0
        self.fuse_center_sec_point = 0
        self.cabin_area = 0
        self.fuse_surface = []
        self.fuse_seg_vol = 0
        self.fuse_cabin_vol = []
        self.fuse_fuel_vol = []
        self.fuse_vol = []
        self.f_seg_sec = 0


# =============================================================================
#    MAIN
# =============================================================================

if __name__ == "__main__":

    print("##########################################################")
    print("############# ERROR NOT A STANDALONE PROGRAM #############")
    print("##########################################################")
