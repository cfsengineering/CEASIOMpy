"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Utility functions for CPACS file creation and manipulation.
"""

from pathlib import Path

from tixi3.tixi3wrapper import Tixi3
from cpacspy.cpacspy import AeroMap


class SimpleCPACS:
    """
    Simplified CPACS wrapper for 2D airfoil cases.

    This class provides minimal CPACS-like interface without full TIGL validation,
    suitable for 2D airfoil analysis where aircraft wings are not present.
    Now includes support for aeromaps to manage CFD conditions (AoA, Mach, etc.).
    """

    def __init__(self, cpacs_file: str):
        self.cpacs_file = cpacs_file
        self.tixi = Tixi3()
        self.tixi.open(cpacs_file)

    def save_cpacs(self, file_path: str, overwrite: bool = True):
        """Save the CPACS file."""
        # Convert Path to string if needed
        file_path = str(file_path)
        self.tixi.save(file_path, overwrite)

    def get_aeromap_uid_list(self):
        """Get list of aeromap UIDs from CPACS."""
        aeromap_list = []
        aeromaps_xpath = "/cpacs/vehicles/aircraft/model/analyses/aeroPerformance"
        if self.tixi.checkElement(aeromaps_xpath):
            n_aeromaps = self.tixi.getNamedChildrenCount(aeromaps_xpath, "aeroMap")
            for i in range(1, n_aeromaps + 1):
                aeromap_xpath = f"{aeromaps_xpath}/aeroMap[{i}]"
                uid = self.tixi.getTextAttribute(aeromap_xpath, "uID")
                aeromap_list.append(uid)
        return aeromap_list

    def get_aeromap_by_uid(self, uid: str):
        """Get aeromap by UID."""
        try:
            return AeroMap(self.tixi, uid)
        except Exception as e:
            raise ValueError(f"AeroMap with uid '{uid}' not found: {e}")

    def create_aeromap(self, uid: str):
        """Create a new aeromap."""
        if " " in uid:
            raise ValueError("AeroMap uid should not contain any space!")

        if uid in self.get_aeromap_uid_list():
            raise ValueError(f"AeroMap with uid '{uid}' already exists!")

        return AeroMap(self.tixi, uid, create_new=True)

    def delete_aeromap(self, uid: str):
        """Delete an aeromap by UID."""
        try:
            aeromap = AeroMap(self.tixi, uid)
            aeromap.delete()
        except Exception as e:
            raise ValueError(f"Cannot delete aeromap '{uid}': {e}")

    def close(self):
        """Close the TIXI handle."""
        if self.tixi:
            self.tixi.close()


def create_minimal_cpacs_2d(name: str = "2D Airfoil Analysis") -> Tixi3:
    """
    Create a minimal valid CPACS file for 2D airfoil analysis.

    This function creates a simplified CPACS structure without wings,
    suitable for 2D airfoil analysis. Returns a TIXI object instead of CPACS
    since the minimal structure is not compatible with full TIGL/CPACS validation.

    Args:
        cpacs_path: Path where the CPACS file will be created
        name: Name of the model (default: "2D Airfoil Analysis")

    Returns:
        Tixi3 object of the created file
    """

    # Create minimal CPACS structure using TIXI directly
    tixi = Tixi3()
    tixi.create("cpacs")

    # Add XML namespace attributes (TIXI uses underscore instead of colon)
    tixi.addTextAttribute("/cpacs", "xmlns_xsi", "http://www.w3.org/2001/XMLSchema-instance")
    tixi.addTextAttribute("/cpacs", "xsi_noNamespaceSchemaLocation", "CPACS_30_Schema.xsd")

    # Header
    tixi.createElement("/cpacs", "header")
    tixi.createElement("/cpacs/header", "name")
    tixi.updateTextElement("/cpacs/header/name", name)
    tixi.createElement("/cpacs/header", "version")
    tixi.updateTextElement("/cpacs/header/version", "1.0")
    tixi.createElement("/cpacs/header", "cpacsVersion")
    tixi.updateTextElement("/cpacs/header/cpacsVersion", "3.0")
    tixi.createElement("/cpacs/header", "versionInfos")

    # Vehicles structure with aircraft/model
    tixi.createElement("/cpacs", "vehicles")
    tixi.createElement("/cpacs/vehicles", "aircraft")
    tixi.createElement("/cpacs/vehicles/aircraft", "model")
    tixi.addTextAttribute("/cpacs/vehicles/aircraft/model", "uID", "model_1")
    tixi.createElement("/cpacs/vehicles/aircraft/model", "name")
    tixi.updateTextElement("/cpacs/vehicles/aircraft/model/name", name)

    # Add reference section
    tixi.createElement("/cpacs/vehicles/aircraft/model", "reference")
    tixi.addTextAttribute("/cpacs/vehicles/aircraft/model/reference", "uID", "reference_1")
    tixi.createElement("/cpacs/vehicles/aircraft/model/reference", "area")
    tixi.updateDoubleElement("/cpacs/vehicles/aircraft/model/reference/area", 1.0, "%g")
    tixi.createElement("/cpacs/vehicles/aircraft/model/reference", "length")
    tixi.updateDoubleElement("/cpacs/vehicles/aircraft/model/reference/length", 1.0, "%g")

    # Profiles
    tixi.createElement("/cpacs/vehicles", "profiles")
    tixi.createElement("/cpacs/vehicles/profiles", "wingAirfoils")

    # Return the TIXI object without saving (caller must save and close)
    return tixi
