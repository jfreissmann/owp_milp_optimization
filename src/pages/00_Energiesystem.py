import json
import os
from datetime import date

import darkdetect
import pandas as pd
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
unitinputpath = os.path.join(__file__, '..', '..', 'input', 'unit_inputs.json')
with open(unitinputpath, 'r', encoding='utf-8') as file:
    ss.unit_inputs = json.load(file)

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
    st.header('Auswahl des Wärmeversorgungssystem')

    units = st.multiselect(
        'Wähle die Wärmeversorgungsanlagen aus, die im System verwendet werden können',
        list(shortnames.keys()),
        placeholder='Wärmeversorgungsanlagen'
        )

    col_topo, _ = st.columns([1, 2])

    topopath = os.path.join(__file__, '..', '..', 'img', 'es_topology_')
    if units:
        col_topo.image(f'{topopath}header.png', use_column_width=True)
        for unit in units:
            col_topo.image(
                f'{topopath+shortnames[unit]}.png', use_column_width=True
                )

with tab2:
    st.header('Parametrisierung der Wärmeversorgungsanlagen')

    for unit in units:
        params = ss.param_units[shortnames[unit]]
        with st.expander(unit):
            col_tech, col_econ = st.columns(2, gap='large')

            col_tech.subheader('Technische Parameter')
            for uinput, uinfo in ss.unit_inputs['Technische Parameter'].items():
                if uinput in ss.param_units[shortnames[unit]]:
                    if uinput == 'balanced':
                        ss.param_units[shortnames[unit]][uinput] = col_tech.toggle(
                            uinfo['name'],
                            value=ss.param_units[shortnames[unit]][uinput]
                        )
                    else:
                        if uinfo['unit'] == '%':
                            ss.param_units[shortnames[unit]][uinput] *= 100
                        if uinfo['unit'] == '':
                            label = uinfo['name']
                        else:
                            label = f"{uinfo['name']} in {uinfo['unit']}"
                        ss.param_units[shortnames[unit]][uinput] = (
                            col_tech.number_input(
                                label,
                                value=float(
                                    ss.param_units[shortnames[unit]][uinput]
                                    ),
                                min_value=uinfo['min'],
                                max_value=uinfo['max'],
                                step=(uinfo['max']-uinfo['min'])/100,
                                key=f'input_{shortnames[unit]}_{uinput}'
                                )
                            )
                        if uinfo['unit'] == '%':
                            ss.param_units[shortnames[unit]][uinput] /= 100

            col_econ.subheader('Ökonomische Parameter')
            for uinput, uinfo in ss.unit_inputs['Ökonomische Parameter'].items():
                if uinput in ss.param_units[shortnames[unit]]:
                    ss.param_units[shortnames[unit]][uinput] = (
                        col_econ.number_input(
                            f"{uinfo['name']} in {uinfo['unit']}",
                            value=float(
                                ss.param_units[shortnames[unit]][uinput]
                                ),
                            min_value=uinfo['min'],
                            max_value=uinfo['max'],
                            step=(uinfo['max']-uinfo['min'])/100,
                            key=f'input_{shortnames[unit]}_{uinput}'
                            )
                        )

with tab3:
    st.header('Auswahl der Wärmelastdatem')

    col_sel, col_vis = st.columns([1, 2])

    dataset_name = col_sel.selectbox(
        'Wähle die Wärmelastdaten aus, die im System zu verwenden sind',
        ['Flensburg', 'Sønderborg', 'Eigene Daten'],
        placeholder='Wärmelastendaten'
    )

    if dataset_name == 'Eigene Daten':
        heat_load_year = None
        tooltip = (
            'Die erste Spalte muss ein Datumsindex und die zweite die Wärmelast'
            + 'in MWh beinhalten. Zusätzlich muss bei csv-Datein das'
            + 'Trennzeichen ein Semikolon sein.'
            )
        user_file = col_sel.file_uploader(
            'Datensatz einlesen', type=['csv', 'xlsx'], help=tooltip
            )
        if user_file is None:
            col_sel.info(
                'Bitte fügen Sie eine Datei ein.'
                )
        else:
            if user_file.lower().endswith('csv'):
                heat_load = pd.read_csv(
                    user_file, sep=';', index_col=0, parse_dates=True
                    )
            elif user_file.lower().endswith('xlsx'):
                heat_load = pd.read_excel(user_file, index_col=0)

    elif dataset_name == 'Flensburg':
        heat_load_year = col_sel.selectbox(
            'Wähle das Jahr der Wärmelastdaten aus',
            ['2014', '2015', '2016', '2017', '2018', '2019'],
            placeholder='Betrachtungsjahr'
        )
    elif dataset_name == 'Sønderborg':
        heat_load_year = col_sel.selectbox(
            'Wähle das Jahr der Wärmelastdaten aus',
            ['2016', '2017', '2018', '2019'],
            placeholder='Betrachtungsjahr'
        )
    heat_load_path = os.path.join(
        __file__, '..', '..', 'input', 'heat_load',
        f'heat_load_{dataset_name}_{heat_load_year}.csv'
    )
    heat_load = pd.read_csv(
        heat_load_path, sep=';', index_col=0, parse_dates=True
        )

    if heat_load_year:
        precise_dates = col_sel.toggle(
            'Exakten Zeitraum wählen'
        )
        if precise_dates:
            dates = col_sel.date_input(
                'Zeitraum auswählen:',
                value=(
                    date(int(heat_load_year), 3, 28),
                    date(int(heat_load_year), 7, 2)
                    ),
                min_value=date(int(heat_load_year), 1, 1),
                max_value=date(int(heat_load_year), 12, 31),
                format='DD.MM.YYYY'
                )

    col_vis.line_chart(
        heat_load, x='Datum', y='Wärmelast in MWh', color='#EC6707',
        use_container_width=True
    )

with tab4:
    st.header('Auswahl der Preiszeitreihen')
