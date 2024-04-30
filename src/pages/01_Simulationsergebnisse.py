import json
import os

import streamlit as st
from streamlit import session_state as ss

# %% Sidebar
with st.sidebar:
    logo = os.path.join(
        __file__, '..', '..', 'img', 'Logo_ZNES_mitUnisV2.svg'
        )
    st.image(logo, use_column_width=True)
