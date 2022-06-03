import streamlit as st


col1, col2 = st.columns(2)

with col1:
    st.title("CEASIOMpy")
    uploaded_file = st.file_uploader("Select a CPACS file", type=["xml"])

with col2:
    st.image("../documents/logos/CEASIOMpy_main_logos.png", width=400)
