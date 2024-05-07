import json
import os
from datetime import date, datetime, time, timedelta

import altair as alt
import pandas as pd
import streamlit as st
from streamlit import session_state as ss

from model import EnergySystem


def run_es_model(es):
    with st.spinner('Optimierung wird durchgeführt...'):
        es.run_model()
    with st.spinner('Postprocessing wird durchgeführt...'):
        es.run_postprocessing()
        breakpoint()


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

    st.markdown('''---''')

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


# %% Overview

st.header('Überblick')

col_es, col_over = st.columns([1, 1], gap='large')

col_es.subheader('Energiesystem')

col_over.subheader('Überblick')

st.markdown('''---''')

# %% MARK: Save Data
savepath = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'save')
    )

if not os.path.exists(savepath):
    os.mkdir(savepath)

download = False
download = st.button(
    label='💾 Input Daten speichern',
    key='download_button'
    )

if download:
    tspath = os.path.join(savepath, 'data_input.csv')
    ss.data.to_csv(tspath, sep=';')

    optpath = os.path.join(savepath, 'param_opt.json')
    with open(optpath, 'w', encoding='utf-8') as file:
        json.dump(ss.param_opt, file, indent=4, sort_keys=True)

    unitpath = os.path.join(savepath, 'param_units.json')
    with open(unitpath, 'w', encoding='utf-8') as file:
        json.dump(ss.param_units, file, indent=4, sort_keys=True)

with st.container(border=True):
        if st.button(label='📊**Optimierung starten**', use_container_width=True):
            ss.energy_system = EnergySystem(
                ss.data, ss.param_units, ss.param_opt
                )
            run_es_model(ss.energy_system)