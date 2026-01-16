# Imports
import os
import streamlit as st


# Methods
def _enforce_session_token() -> None:
    """Ensure the Streamlit UI is accessed only via a matching session token."""
    expected_token = os.environ.get("CEASIOMPY_SESSION_TOKEN")
    if not expected_token:
        return None
    params = st.experimental_get_query_params()
    provided_token = (params.get("session_token") or [""])[0]
    if provided_token != expected_token:
        st.error(
            "Unauthorized access. Launch CEASIOMpy from the web portal to continue your session."
        )
        st.stop()


_enforce_session_token()
