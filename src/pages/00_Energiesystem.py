import json
import os

import darkdetect
import streamlit as st
from streamlit import session_state as ss

is_dark = darkdetect.isDark()
shortnames = {
    'Wärmepumpe': 'hp',
    'Gas- und Dampfkratwerk': 'ccet',
    'Blockheizkraftwerk': 'ice',
    'Solarthermie': 'sol',
    'Spitzenlastkessel': 'plb',
    'Wärmespeicher': 'tes'
}
longnames = {
    'hp': 'Wärmepumpe',
    'ccet': 'Gas- und Dampfkratwerk',
    'ice': 'Blockheizkraftwerk',
    'sol': 'Solarthermie',
    'plb': 'Spitzenlastkessel',
    'tes': 'Wärmespeicher'
}

unitpath = os.path.join(__file__, '..', '..', 'input', 'param_units.json')
with open(unitpath, 'r', encoding='utf-8') as file:
    ss.param_units = json.load(file)

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

tab1, tab2, tab3, tab4 = st.tabs(
    ['System', 'Anlagen','Wärmelast', 'Energiepreise']
    )

with tab1:
    st.header('Wärmeversorgungssystem')

    units = st.multiselect(
        'Wähle die Wärmeversorgungsanlagen aus, die im System verwendet werden können:',
        list(shortnames.keys()),
        placeholder='Wärmeversorgungsanlagen'
        )
    topopath = os.path.join(__file__, '..', '..', 'img', 'es_topology_')

    st.image(f'{topopath}header.png', width=500)
    for unit in units:
        st.image(f'{topopath+shortnames[unit]}.png', width=500)

with tab2:
    st.write('Hier die ausgewählten Anlagen parametrisieren')

    for unit, params in ss.param_units.items():
        with st.expander(longnames[unit]):
            for param, value in params.items():
                ss.param_units[unit][param] = st.number_input(
                    param, value=value, key=f'input_{unit}_{param}'
                )

with tab3:
    st.write('Hier die Wärmelast und den Zeitraum auswählen')

with tab4:
    st.write('Hier alle Energiepreise aufzuzeigen')