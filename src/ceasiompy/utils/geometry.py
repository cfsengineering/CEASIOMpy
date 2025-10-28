
import streamlit as st

from typing import Union
from cpacspy.cpacspy import CPACS
from ceasiompy.utils.stp import STP

from ceasiompy import log


def get_geometry_aeromaps_uid() -> None:
    if "cpacs" in st.session_state:
        return st.session_state.cpacs.get_aeromap_uid_list()

    if "stp" in st.session_state:
        return st.session_state.stp.get_aeromaps_uid()

    log.error("Did not find geometry.")
    return None


def get_aeromaps_uid_from_geometry(
    geometry: Union[CPACS, STP],
) -> None:
    if isinstance(geometry, CPACS):
        return geometry.get_aeromap_uid_list()

    if isinstance(geometry, STP):
        return geometry.get_aeromaps_uid()

    log.error("Did not find geometry.")
    return None
