import streamlit as st

tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("City", ["City1", "City2"])
    with col2:
        st.selectbox("District", ["District1", "District2"])

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("City", ["AnotherCity1", "AnotherCity2"])
    with col2:
        st.selectbox("District", ["AnotherDistrict1", "AnotherDistrict2"])
