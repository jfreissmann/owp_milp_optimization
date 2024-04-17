import os

import darkdetect
import streamlit as st

is_dark = darkdetect.isDark()
topopath = os.path.join(__file__, '..', '..', 'img', 'es_topology_')

tab1, tab2, tab3, tab4 = st.tabs(
    ['System', 'Anlagen','Wärmelast', 'Energiepreise']
    )

with tab1:
    st.header('Wärmeversorgungssystem')

    pngnames = {
        'Wärmepumpe': 'hp',
        'Gas- und Dampfkratwerk': 'ccet',
        'Blockheizkraftwerk': 'ice',
        'Solarthermie': 'sol',
        'Spitzenlastkessel': 'plb',
        'Wärmespeicher': 'tes',
    }

    units = st.multiselect(
        'Wähle die Wärmeversorgungsanlagen aus, die im System verwendet werden können:',
        list(pngnames.keys()),
        placeholder='Wärmeversorgungsanlagen'
        )

    st.image(f'{topopath}header.png', width=500)
    for unit in units:
        st.image(f'{topopath+pngnames[unit]}.png', width=500)

with tab2:
    st.write('Hier die ausgewählten Anlagen parametrisieren')

with tab3:
    st.write('Hier die Wärmelast und den Zeitraum auswählen')

with tab4:
    st.write('Hier alle Energiepreise aufzuzeigen')