import json
import os
import shutil

import pandas as pd
import streamlit as st
from streamlit import session_state as ss

from model import EnergySystem


@st.dialog('Energiesystem lokal speichern')
def download_energy_system():
    """Temporarely save data and zip it, then let user download zip archive."""
    with st.spinner('Daten werden verarbeitet...'):
        tmppath = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), '..', '_tmp'
            )
        )
        if not os.path.exists(tmppath):
            os.mkdir(tmppath)

        zippath = os.path.join(tmppath, 'energysystem')
        if not os.path.exists(zippath):
            os.mkdir(zippath)

        tspath = os.path.join(zippath, 'data_input.csv')
        ss.data.to_csv(tspath, sep=';')

        optpath = os.path.join(zippath, 'param_opt.json')
        with open(optpath, 'w', encoding='utf-8') as file:
            json.dump(ss.param_opt, file, indent=4, sort_keys=True)

        unitpath = os.path.join(zippath, 'param_units.json')
        with open(unitpath, 'w', encoding='utf-8') as file:
            json.dump(ss.param_units, file, indent=4, sort_keys=True)

        shutil.make_archive(zippath, 'zip', zippath)

    with open(f'{zippath}.zip', 'rb') as file:
        btn = st.download_button(
            label='Speichere dein Energiesystem',
            data=file,
            file_name='Energiesystem',
            mime='application/zip'
        )

    shutil.rmtree(tmppath)

shortnames = {
    'Wärmepumpe': 'hp',
    'Gas- und Dampfkratwerk': 'ccet',
    'Blockheizkraftwerk': 'ice',
    'Solarthermie': 'sol',
    'Spitzenlastkessel': 'plb',
    'Elektrodenheizkessel': 'eb',
    'Externe Wärmequelle': 'exhs',
    'Wärmespeicher': 'tes'
}

# %% MARK: Sidebar
with st.sidebar:
    st.subheader('Offene Wärmespeicherplanung')

    logo_inno = os.path.join(
        os.path.dirname(__file__), '..', 'img', 'Logo_InnoNord_OWP.png'
        )
    st.image(logo_inno, use_column_width=True)

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
st.header('Zusammenfassung')

col_es, col_over = st.columns([1, 4], gap='large')

col_es.subheader('Energiesystem')

topopath = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'img', 'es_topology_')
    )

col_es.image(f'{topopath}header.png', use_column_width=True)
for unit in ss.param_units.keys():
    unit = unit.rstrip('0123456789')
    col_es.image(
        f'{topopath+unit}.png', use_column_width=True
        )

col_over.subheader('Zeitreihen im Wärmeversorgungssystem')

data_overview = ss.data.describe()
data_overview.drop(index=['count', 'std', '25%', '75%'], inplace=True)
data_overview.rename(
    index={
        'mean': 'Mittelwert', 'min': 'Minimalwert',
        '50%': 'Median', 'max': 'Maximalwert'
        },
    columns={
        'heat_demand': 'Wärmelast (MWh)',
        'el_spot_price': 'Spotmarkt Strompreis (€/MWh)',
        'ef_om': 'Emissionsfaktor Strommix (kg/MWh)',
        'gas_price': 'Gaspreis (€/MWh)',
        'co2_price': 'CO₂-Preis (€/MWh)'
        }, inplace=True
    )

if 'Solarthermie' in ss.units:
    data_overview['solar_heat_flow'] *= 1e6
    data_overview.rename(columns={
        'solar_heat_flow': 'Spez. solare Einstrahlung (Wh/m²)'
        }, inplace=True
    )

col_over.dataframe(data_overview.T, use_container_width=True)

col_over.subheader('Parameter im Wärmeversorgungssystem')

param_overview = pd.DataFrame.from_dict(
    ss.param_opt, orient='index', columns=['Wert']
    )
param_overview.drop(
    index=['MIPGap', 'TimeLimit', 'heat_price', 'TEHG_bonus'], inplace=True
    )
param_overview.loc['ef_gas'] *= 1000
param_overview.loc['capital_interest'] *= 100
param_overview.rename(
    index={
        'ef_gas': 'Emissionsfaktor Gas (kg/MWh)',
        'elec_consumer_charges_grid': 'Strompreisbestandteile (Netz) (€/MWh)',
        'elec_consumer_charges_self': 'Strompreisbestandteile (Eigenbedarf) (€/MWh)',
        'energy_tax': 'Energiesteuer (€/MWh)',
        'vNNE': 'Vermiedene Netznutzungsentgelte (€/MWh)',
        'capital_interest': 'Kapitalzins (%)',
        'lifetime': 'Lebensdauer (a)'
        }, inplace=True
    )
col_over.dataframe(param_overview, use_container_width=True)

# %% MARK: Save Data
# _, col_save, col_reset, _ = st.columns([1.05, 1, 1, 2], gap='large')
# col_save, col_reset = col_over.columns([1, 1], gap='large')
col_save, col_dl_es, col_reset = col_over.columns([1, 1, 1], gap='large')
savepath = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'save')
    )

if not os.path.exists(savepath):
    os.mkdir(savepath)

download = False
download = col_save.button(
    label='💾 Input Daten speichern',
    key='download_button', use_container_width=True
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

download_es_btn = col_dl_es.button(
    label='📝 Energiesystem speichern',
    key='download_es_button_overview',
    use_container_width=True
    )
if download_es_btn:
    download_energy_system()

reset_es = col_reset.button(
    label='📝 Neues Energiesystem konfigurieren',
    key='reset_button_overview',
    use_container_width=True
    )

if reset_es:
    keys = list(ss.keys())
    exceptions = [
        'all_heat_load',
        'eco_data',
        'all_el_prices',
        'all_el_emissions',
        'all_gas_prices',
        'all_co2_prices',
        'all_solar_heat_flow'
        ]
    for key in keys:
        if key not in exceptions:
            ss.pop(key)
    st.switch_page('pages/00_Energiesystem.py')

with st.container(border=True):
    opt = st.button(label='🖥️**Optimierung starten**', use_container_width=True)
    if opt:
        with st.spinner('Optimierung wird durchgeführt...'):
            ss.energy_system = EnergySystem(
                ss.data, ss.param_units, ss.param_opt
                )
            st.toast('Energiesystem ist initialisiert')

            ss.energy_system.generate_buses()
            ss.energy_system.generate_sources()
            ss.energy_system.generate_sinks()
            ss.energy_system.generate_components()
            st.toast('Modell ist erzeugt')

            ss.energy_system.solve_model()
            st.toast('Optimierungsproblem ist gelöst')

            ss.energy_system.get_results()
            st.toast('Ergebnisse sind ausgelesen')

            ss.energy_system.calc_econ_params()
            ss.energy_system.calc_ecol_params()
            st.toast('Postprocessing ist durchgeführt')

            # breakpoint()

if opt:
    with st.container(border=True):
        st.page_link(
            'pages/02_Simulationsergebnisse.py',
            label='**Zu den Ergebnissen**',
            icon='📊', use_container_width=True
            )
