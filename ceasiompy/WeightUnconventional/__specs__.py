#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut
from ceasiompy.utils.commonxpath import (
    CAB_CREW_XPATH,
    FUEL_XPATH,
    GEOM_XPATH,
    MASSBREAKDOWN_XPATH,
    ML_XPATH,
    PASS_XPATH,
    PILOTS_XPATH,
    PROP_XPATH,
)


# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

# User inputs
cpacs_inout.add_input(
    var_name="IS_DOUBLE_FLOOR",
    var_type=list,
    default_value=[0, 1, 2],
    unit=None,
    descr="0: no 2nd floor, 1: full 2nd floor (A380), 2: half 2nd floor (B747)",
    xpath=GEOM_XPATH + "/isDoubleFloor",
    gui=True,
    gui_name="Double deck",
    gui_group="Cabin",
)

cpacs_inout.add_input(
    var_name="H_LIM_CABIN",
    var_type=float,
    default_value=2.3,
    unit="m",
    descr="Concorde 1.5m, Conventional 2.3m",
    xpath=GEOM_XPATH + "/cabinHeight",
    gui=True,
    gui_name="Cabin height",
    gui_group="Cabin",
)

cpacs_inout.add_input(
    var_name="VRT_THICK",
    var_type=float,
    default_value=0.00014263,
    unit="m",
    descr="to check",
    xpath=GEOM_XPATH + "/virtualThick",
    gui=True,
    gui_name="virtual Thickness",
    gui_group="Structure",
)

cpacs_inout.add_input(
    var_name="VRT_STR_DENSITY",
    var_type=float,
    default_value=2700.0,
    unit="kg/m^3",
    descr="to check",
    xpath=GEOM_XPATH + "/virtualDensity",
    gui=True,
    gui_name="virtual Density",
    gui_group="Structure",
)

cpacs_inout.add_input(
    var_name="PASS_BASE_DENSITY",
    var_type=float,
    default_value=1.66,
    unit="[pax/m^2]",
    descr="Passenger surface density (Concorde: 1.16, B77: 1.66, ATR72: 1.39, BWB: 1.69)",
    xpath=PASS_XPATH + "/passDensity",
    gui=True,
    gui_name="Passenger density",
    gui_group="Passengers",
)

cpacs_inout.add_input(
    var_name="FUEL_DENSITY",
    var_type=float,
    default_value=800.0,
    unit="[kg/m^3]",
    descr="Fuel density [kg/m^3]",
    xpath=FUEL_XPATH + "/density",
    gui=True,
    gui_name="Fuel density",
    gui_group="Fuel",
)

cpacs_inout.add_input(
    var_name="FUEL_ON_CABIN",
    var_type=float,
    default_value=0.0,
    unit="[-]",
    descr=(
        " % of the free volume fuel allowed inside the central wing area,"
        " near the cabin for the blended wing body"
    ),
    xpath=FUEL_XPATH + "/fuelOnCabin",
    gui=True,
    gui_name="Fuel % on cabin",
    gui_group="Fuel",
)

cpacs_inout.add_input(
    var_name="MAX_PAYLOAD",
    var_type=float,
    default_value=0.0,
    unit="[kg]",
    descr="Maximum payload allowed, set 0 if equal to max passenger mass.",
    xpath=ML_XPATH + "/maxPayload",
    gui=True,
    gui_name="Max payload",
    gui_group="Weight",
)

cpacs_inout.add_input(
    var_name="MAX_FUEL_VOL",
    var_type=float,
    default_value=0.0,
    unit="[l]",
    descr="Maximum fuel volume allowed [l]",
    xpath=ML_XPATH + "/maxFuelVol",
    gui=True,
    gui_name="Max Fuel volume",
    gui_group="Weight",
)

cpacs_inout.add_input(
    var_name="MASS_CARGO",
    var_type=float,
    default_value=0.0,
    unit="[kg]",
    descr="Cargo mass [kg]",
    xpath=MASSBREAKDOWN_XPATH + "/payload/mCargo/massDescription/mass",
    gui=True,
    gui_name="Mass cargo",
    gui_group="Weight",
)

cpacs_inout.add_input(
    var_name="TSFC_CRUISE",
    var_type=float,
    default_value=0.5,
    unit="[1/h]",
    descr=(
        "Thrust specific fuel consumption for cruise [1/h]"
        "(Truboprop 0.6, Trubofan 0.5, Concorde 0.8)"
    ),
    xpath=PROP_XPATH + "/tSFC",
    gui=True,
    gui_name="TSFC",
    gui_group="Cruise",
)

# TODO: Missing engines inputs!!!

# ----- Output -----

cpacs_inout.add_output(
    var_name="maximum_take_off_mass",
    default_value=None,
    unit="[kg]",
    descr="Maximum take of mass",
    xpath=MASSBREAKDOWN_XPATH + "/designMasses/mTOM/mass",
)

cpacs_inout.add_output(
    var_name="zero_fuel_mass",
    default_value=None,
    unit="[kg]",
    descr="Zero fuel mass",
    xpath=MASSBREAKDOWN_XPATH + "/designMasses/mZFM/mass",
)

cpacs_inout.add_output(
    var_name="mass_fuel_max",
    default_value=None,
    unit="[kg]",
    descr="Maximum fuel mass",
    xpath=MASSBREAKDOWN_XPATH + "/fuel/massDescription/mass",
)

cpacs_inout.add_output(
    var_name="mass_fuel_maxpass",
    default_value=None,
    unit="[kg]",
    descr="Maximum fuel mass with maximum payload",
    xpath=PASS_XPATH + "/fuelMassMaxpass/mass",
)

cpacs_inout.add_output(
    var_name="operating_empty_mass",
    default_value=None,
    unit="[kg]",
    descr="Operating empty mass",
    xpath=MASSBREAKDOWN_XPATH + "/mOEM/massDescription/mass",
)

cpacs_inout.add_output(
    var_name="mass_payload",
    default_value=None,
    unit="[kg]",
    descr="Maximum payload mass",
    xpath=MASSBREAKDOWN_XPATH + "/payload/massDescription/mass",
)

cpacs_inout.add_output(
    var_name="mass_cargo",
    default_value=None,
    unit="[kg]",
    descr="xtra payload mass in case of max fuel and total mass less than MTOM",
    xpath=MASSBREAKDOWN_XPATH + "/mCargo/massCargo",
)

cpacs_inout.add_output(
    var_name="pass_nb",
    default_value=None,
    unit="[-]",
    descr="Maximum number of passengers",
    xpath=PASS_XPATH + "/passNb",
)

cpacs_inout.add_output(
    var_name="cabin_crew_nb",
    default_value=None,
    unit="[-]",
    descr="Number of cabin crew members",
    xpath=CAB_CREW_XPATH + "/cabinCrewMemberNb",
)

cpacs_inout.add_output(
    var_name="toilet_nb",
    default_value=None,
    unit="[-]",
    descr="Number of toilets",
    xpath=PASS_XPATH + "/toiletNb",
)
