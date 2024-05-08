import json
import os

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from streamlit import session_state as ss

# %% MARK: Parameters
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

# %% MARK: Sidebar
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

# %% MARK: Main Window
tes_used = 'tes' in ss.param_units.keys()
if tes_used:
    tab1, tab2, tab3 = st.tabs(
        ['Überblick', 'Jahresdauerlinien', 'Speicherstand']
        )
else:
    tab1, tab2 = st.tabs(
        ['Überblick', 'Jahresdauerlinien']
        )

with tab1:
    st.header('Überblick der Optimierungsergebnisse')

    overview_caps = ss.energy_system.data_caps.copy()
    if tes_used:
        overview_caps.drop(columns=['cap_in_tes', 'cap_out_tes'], inplace=True)
    overview_caps.rename(columns={
        c: longnames[c.split('_')[-1]] for c in overview_caps.columns
        }, inplace=True)
    overview_caps.rename(index={0: 'Kapazität (MW bzw. MWh)'}, inplace=True)
    overview_caps = overview_caps.apply(lambda x: round(x, 1))

    st.dataframe(overview_caps, use_container_width=True)

with tab2:
    st.header('Geordnete Jahresdauerlinien des Anlageneinsatzes')

    heatprod = pd.DataFrame()
    for col in ss.energy_system.data_all.columns:
        if 'Q_' in col:
            heatprod[col] = ss.energy_system.data_all[col].copy()
    heatprod = pd.DataFrame(
        np.sort(heatprod.values, axis=0)[::-1], columns=heatprod.columns
        )
    heatprod.index.names = ['Stunde']
    heatprod.reset_index(inplace=True)
    print(heatprod)

    st.altair_chart(
        alt.Chart(heatprod.melt('Stunde')).mark_line(color='#EC6707').encode(
            y=alt.Y('value', title='Stündliche Wärmeproduktion in MWh'),
            x=alt.X('Stunde', title='Datum'),
            color='variable'
        ),
        use_container_width=True
        )

if tes_used:
    with tab3:
        st.header('Füllstand des thermischen Energiespeichers')
