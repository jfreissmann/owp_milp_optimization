import os

import darkdetect
import streamlit as st

is_dark = darkdetect.isDark()
logo = os.path.join(__file__, '..', '..', 'img', 'Logo_ZNES_mitUnisV2.svg')

tab1, tab2, tab3, tab4 = st.tabs(
    ['System', 'Anlagen','Wärmelast', 'Energiepreise']
    )

with tab1:
    st.header('Wärmeversorgungssystem')

    units = st.multiselect(
        'Wähle die Wärmeversorgungsanlagen aus, die im System verwendet werden können:',
        ['Wärmepumpe', 'GuD', 'BHKW', 'Solarthermie', 'SLK', 'TES'],
        placeholder='Wärmeversorgungsanlagen'
        )
    print(units)

    for i in units:
        st.image(logo)
        st.write(i)

with tab2:
    st.write('Hier die ausgewählten Anlagen parametrisieren')

with tab3:
    st.write('Hier die Wärmelast und den Zeitraum auswählen')

with tab4:
    st.write('Hier alle Energiepreise aufzuzeigen')