import json
import os

import streamlit as st
from streamlit import session_state as ss

# %% Sidebar
with st.sidebar:
    st.subheader('Offene Wärmespeicherplanung')

    logo_inno = os.path.join(
        os.path.dirname(__file__), '..', 'img', 'Logo_InnoNord_OWP.png'
        )
    st.image(logo_inno, use_column_width=True)

    # logo_foeder = os.path.join(
    #     os.path.dirname(__file__), '..', 'img', 'Logos_Förderer.png'
    #     )
    # st.image(logo_foeder, use_column_width=True)

    logo = os.path.join(
        os.path.dirname(__file__), '..', 'img', 'Logo_ZNES_mitUnisV2.svg'
        )
    st.image(logo, use_column_width=True)

    st.markdown("""---""")

    st.subheader('Assoziierte Projektpartner')
    logo_bo = os.path.join(
        os.path.dirname(__file__), '..', 'img', 'Logo_Boben_Op_2.png'
        )
    st.image(logo_bo, use_column_width=True)

    logo_gp = os.path.join(
        os.path.dirname(__file__), '..', 'img', 'Logo_GP_Joule.png'
        )
    st.image(logo_gp, use_column_width=True)

    logo_sw = os.path.join(
        os.path.dirname(__file__), '..', 'img', 'Logo_SW_Flensburg.png'
        )
    st.image(logo_sw, use_column_width=True)
