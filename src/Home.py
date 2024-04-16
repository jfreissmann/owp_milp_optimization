import os

import darkdetect
import streamlit as st

st.set_page_config(
    layout='wide',
    page_title='OWP MILP Optimierung',
    page_icon=os.path.join(__file__, '..', 'img', 'page_icon_ZNES.png')
    )

is_dark = darkdetect.isDark()

# %% Sidebar
with st.sidebar:
    if is_dark:
        logo = os.path.join(
            __file__, '..', 'img', 'Logo_ZNES_mitUnisV2_dark.svg'
            )
    else:
        logo = os.path.join(__file__, '..', 'img', 'Logo_ZNES_mitUnisV2.svg')
    st.image(logo, use_column_width=True)

