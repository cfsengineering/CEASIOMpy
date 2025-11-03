from enum import StrEnum


class PartType(StrEnum):
    wing = "wing"
    rotor = "rotor"
    engine = "engine"
    fanCowl = "fanCowl"
    coreCowl = "coreCowl"
    fuselage = "fuselage"
    centerCowl = "centerCowl"
    enginePylon = "enginePylon"
