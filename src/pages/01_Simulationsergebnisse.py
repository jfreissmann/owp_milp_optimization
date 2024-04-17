import json
import os

import darkdetect
import streamlit as st
from streamlit import session_state as ss

is_dark = darkdetect.isDark()
# %% Sidebar
with st.sidebar:
    if is_dark:
        logo = os.path.join(
            __file__, '..', '..', 'img', 'Logo_ZNES_mitUnisV2_dark.svg'
            )
    else:
        logo = os.path.join(
            __file__, '..', '..', 'img', 'Logo_ZNES_mitUnisV2.svg'
            )
    st.image(logo, use_column_width=True)
