"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

List of CPACS xpath which are used in CEASIOMpy, if possible base xpath must be
called only from here to avoid mistakes.
XPath may be changed from here to avoid mistakes, but if it is the case, be careful to also change
xpath and field name in all the test CPACS files, which are in the CEASIOMpy repository.

Note:
    This contains only COMMON xpaths,
    please do NOT add specific xpaths of your module in here.
    You can always add specific xpaths in the __init__.py of your module.

"""

# =================================================================================================
#   CSTS
# =================================================================================================

# Header
AIRCRAFT_NAME_XPATH = "/cpacs/header/name"

# model
REF_XPATH = "/cpacs/vehicles/aircraft/model/reference"
AREA_XPATH = "/cpacs/vehicles/aircraft/model/reference/area"
LENGTH_XPATH = "/cpacs/vehicles/aircraft/model/reference/length"

FUSELAGES_XPATH = "/cpacs/vehicles/aircraft/model/fuselages"
WINGS_XPATH = "/cpacs/vehicles/aircraft/model/wings"
PYLONS_XPATH = "/cpacs/vehicles/aircraft/model/enginePylons"
ENGINES_XPATH = "/cpacs/vehicles/aircraft/model/engines"
AIRFOILS_XPATH = "/cpacs/vehicles/profiles/wingAirfoils"

# analyses
AEROPERFORMANCE_XPATH = "/cpacs/vehicles/aircraft/model/analyses/aeroPerformance"
MASSBREAKDOWN_XPATH = "/cpacs/vehicles/aircraft/model/analyses/massBreakdown"

MTOM_XPATH = MASSBREAKDOWN_XPATH + "/designMasses/mTOM/mass"
MZFM_XPATH = MASSBREAKDOWN_XPATH + "/designMasses/mZFM/mass"
MOEM_XPATH = MASSBREAKDOWN_XPATH + "/mOEM/massDescription/mass"
FUEL_MASS_XPATH = MASSBREAKDOWN_XPATH + "/fuel/massDescription/mass"
PAYLOAD_DESCRIPTION_XPATH = MASSBREAKDOWN_XPATH + "/payload/massDescription"
PAYLOAD_MASS_XPATH = MASSBREAKDOWN_XPATH + "/payload/mass"
PAYLOAD_CARGO_XPATH = MASSBREAKDOWN_XPATH + "/payload/mCargo"

F_XPATH = "/cpacs/vehicles/fuels/fuel"  # TODO remove
FUEL_DENSITY_XPATH = "/cpacs/vehicles/fuels/fuel/density"
MASS_CARGO_XPATH = MASSBREAKDOWN_XPATH + "/payload/mCargo/massDescription/mass"
