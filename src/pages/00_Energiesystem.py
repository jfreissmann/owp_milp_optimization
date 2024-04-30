import json
import os
from datetime import date, datetime, time, timedelta

import altair as alt
import pandas as pd
import streamlit as st
from streamlit import session_state as ss


# %% MARK: Read Input Data
@st.cache_data
def read_input_data():
    """Read in input data all at once."""
    inputpath = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'input'
        ))
    ss.all_heat_load = pd.read_csv(
        os.path.join(inputpath, 'heat_load.csv'),
        sep=';', index_col=0, parse_dates=True
        )
    ss.eco_data = pd.read_csv(
        os.path.join(inputpath, 'eco_data.csv'),
        sep=';', index_col=0, parse_dates=True
        )
    ss.all_el_prices = ss.eco_data['El Price'].to_frame()
    ss.all_el_emissions = ss.eco_data['Emissionsfaktor Gesamtmix'].to_frame()
    ss.all_gas_prices = ss.eco_data['Gaspreis'].to_frame()
    ss.all_co2_prices = ss.eco_data['CO2-Preis'].to_frame()

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

read_input_data()

unitpath = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'input', 'param_units.json')
    )
with open(unitpath, 'r', encoding='utf-8') as file:
    ss.param_units = json.load(file)

optpath = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'input', 'param_opt.json')
    )
with open(optpath, 'r', encoding='utf-8') as file:
    ss.param_opt = json.load(file)

unitinputpath = os.path.abspath(
    os.path.join(os.path.dirname(__file__),'..', 'input', 'unit_inputs.json')
    )
with open(unitinputpath, 'r', encoding='utf-8') as file:
    ss.unit_inputs = json.load(file)

boundinputpath = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'input', 'param_bound.json')
    )
with open(boundinputpath, 'r', encoding='utf-8') as file:
    ss.bound_inputs = json.load(file)

# %% MARK: Sidebar
with st.sidebar:
    logo = os.path.join(
        __file__, '..', '..', 'img', 'Logo_ZNES_mitUnisV2.svg'
        )
    st.image(logo, use_column_width=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ['System', 'Anlagen', 'Wärme', 'Elektrizität', 'Gas']
    )

# %% MARK: Energy System
with tab1:
    st.header('Auswahl des Wärmeversorgungssystem')

    units = st.multiselect(
        'Wähle die Wärmeversorgungsanlagen aus, die im System verwendet werden '
        + 'können.',
        list(shortnames.keys()),
        placeholder='Wärmeversorgungsanlagen'
        )

    col_topo, _ = st.columns([1, 2])

    topopath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'img', 'es_topology_')
        )
    if units:
        col_topo.image(f'{topopath}header.png', use_column_width=True)
        for unit in units:
            col_topo.image(
                f'{topopath+shortnames[unit]}.png', use_column_width=True
                )

# %% MARK: Unit Parameters
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

# %% MARK: Heat Load
with tab3:
    st.header('Wärmeversorgungsdaten')

    col_sel, col_vis = st.columns([1, 2], gap='large')

    dataset_name = col_sel.selectbox(
        'Wähle die Wärmelastdaten aus, die im System zu verwenden sind',
        [*ss.all_heat_load.columns, 'Eigene Daten'],
        placeholder='Wärmelastendaten'
    )

    heat_load = pd.DataFrame()
    if dataset_name == 'Eigene Daten':
        heat_load_year = None
        tooltip = (
            'Die erste Spalte muss ein Datumsindex in stündlicher Auflösung und'
            + ' die zweite die Wärmelast in MWh beinhalten. Zusätzlich muss bei'
            + 'der csv-Datein das Trennzeichen ein Semikolon sein.'
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

    else:
        user_file = None
        heat_load_years = ss.all_heat_load.loc[
            ~ss.all_heat_load[dataset_name].isna(), dataset_name
            ].index.year.unique()
        heat_load_year = col_sel.selectbox(
            'Wähle das Jahr der Wärmelastdaten aus',
            heat_load_years, index=len(heat_load_years)-1,
            placeholder='Betrachtungsjahr'
        )
        yearmask = ss.all_heat_load.index.year == heat_load_year
        heat_load = ss.all_heat_load.loc[
            yearmask, dataset_name
            ].copy().to_frame()

    dates = None
    if dataset_name != 'Eigene Daten':
        precise_dates = col_sel.toggle(
            'Exakten Zeitraum wählen', key='prec_dates_heat_load'
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
                format='DD.MM.YYYY', key='date_picker_heat_load'
                )
            dates = [
                datetime(year=d.year, month=d.month, day=d.day) for d in dates
                ]
            heat_load = heat_load.loc[dates[0]:dates[1], :]

        scale_hl = col_sel.toggle('Daten skalieren')
        if scale_hl:
            scale_method = col_sel.selectbox('Methode', ['Faktor', 'Erweitert'])
            if scale_method == 'Faktor':
                scale_factor = col_sel.number_input(
                    'Skalierungsfaktor', value=1.0, step=0.1, min_value=0.0
                    )
                heat_load[dataset_name] *= scale_factor
            elif scale_method == 'Erweitert':
                scale_amp = col_sel.number_input(
                    'Stauchungsfaktor', value=1.0, step=0.1, min_value=0.0,
                    help='Staucht die Lastdaten um den Median.'
                    )
                scale_off = col_sel.number_input(
                    'Offset', value=1.0, step=0.1,
                    help='Verschiebt den Median der Lastdaten.'
                    )
                heat_load_median = heat_load[dataset_name].median()
                heat_load[dataset_name] = (
                    (heat_load[dataset_name] - heat_load_median) * scale_amp
                    + heat_load_median + scale_off
                    )
                # negative_mask = heat_load[dataset_name] < 0
                if (heat_load[dataset_name] < 0).values.any():
                    st.error(
                        'Durch die Skalierung resultiert eine negative '
                        + 'Wärmelast. Bitte den Offset anpassen.'
                        )

    col_vis.subheader('Wärmelastdaten')

    if user_file is not None or dataset_name != 'Eigene Daten':
        heat_load.rename(columns={heat_load.columns[0]: 'heat_load'}, inplace=True)
        heat_load.index.names = ['Date']
        heat_load.reset_index(inplace=True)

        col_vis.altair_chart(
            alt.Chart(heat_load).mark_line(color='#EC6707').encode(
                y=alt.Y('heat_load', title='Stündliche Wärmelast in MWh'),
                x=alt.X('Date', title='Datum')
            ),
            use_container_width=True
        )

    col_sel.subheader('Wärmeerlöse')

    ss.param_opt['heat_price'] = col_sel.number_input(
        'Wärmeerlös in €/MWh', value=ss.param_opt['heat_price'],
        key='heat_revenue'
        )

# %% MARK: Electricity
with tab4:
    st.header('Elektrizitätsversorgungsdaten')
    col_elp, col_vis_el = st.columns([1, 2], gap='large')

    el_prices_years = list(ss.all_el_prices.index.year.unique())
    if heat_load_year:
        el_year_idx = el_prices_years.index(heat_load_year)
    else:
        el_year_idx = len(el_prices_years) - 1
    el_prices_year = col_elp.selectbox(
        'Wähle das Jahr der Strompreisdaten aus',
        el_prices_years, index=el_year_idx,
        placeholder='Betrachtungsjahr'
    )
    el_prices = ss.all_el_prices[
        ss.all_el_prices.index.year == el_prices_year
        ].copy()
    el_em = ss.all_el_emissions[
        ss.all_el_emissions.index.year == el_prices_year
        ].copy()

    precise_dates = col_elp.toggle(
        'Exakten Zeitraum wählen', key='prec_dates_el_prices'
        )
    if precise_dates:
        el_dates = col_elp.date_input(
            'Zeitraum auswählen:',
            value=dates if dates is not None else (
                date(int(heat_load_year), 3, 28),
                date(int(heat_load_year), 7, 2)
                ),
            min_value=date(int(heat_load_year), 1, 1),
            max_value=date(int(heat_load_year), 12, 31),
            format='DD.MM.YYYY', key='date_picker_el_prices'
            )
        el_dates = [
            datetime(year=d.year, month=d.month, day=d.day) for d in el_dates
            ]
        el_prices = el_prices.loc[el_dates[0]:el_dates[1], :]
        el_em = el_em.loc[el_dates[0]:el_dates[1], :]

    if any(heat_load):
        nr_steps_hl = len(heat_load.index)
        nr_steps_el = len(el_prices.index)
        if nr_steps_hl != nr_steps_el:
            st.error(
                'Die Anzahl der Zeitschritte der Wärmelastdaten '
                + f'({nr_steps_hl}) stimmt nicht mit denen der '
                + f' Strompreiszeitreihe ({nr_steps_el}) überein. Bitte die '
                + 'Daten angleichen.'
                )

    col_elp.subheader('Strompreisbestandteile')
    col_elp.dataframe(
        {f'{k} in ct/kWh': v
         for k, v in ss.bound_inputs[str(el_prices_year)].items()},
        use_container_width=True
        )

    cons_charger = ss.bound_inputs[str(el_prices_year)]
    ss.param_opt['elec_consumer_charges_grid'] = round(sum(
        val*10 for val in cons_charger['Stromkosten (extern)'].values()
        ), 2)
    ss.param_opt['elec_consumer_charges_self'] = round(sum(
        val*10 for val in cons_charger['Stromkosten (intern)'].values()
        ), 2)


    col_vis_el.subheader('Spotmarkt Strompreise')
    el_prices.reset_index(inplace=True)
    col_vis_el.altair_chart(
        alt.Chart(el_prices).mark_line(color='#00395B').encode(
            y=alt.Y(
                'El Price', title='Day-Ahead Spotmarkt Strompreise in €/MWh'
                ),
            x=alt.X('Date', title='Datum')
            ),
        use_container_width=True
        )

    col_vis_el.subheader('Emissionsfaktoren des Strommixes')
    el_em.reset_index(inplace=True)
    col_vis_el.altair_chart(
        alt.Chart(el_em).mark_line(color='#74ADC0').encode(
            y=alt.Y(
                'Emissionsfaktor Gesamtmix',
                title='Emissionsfaktor des Gesamtmix kg/MWh'
                ),
            x=alt.X('Date', title='Datum')
            ),
        use_container_width=True
        )

# %% MARK: Gas & CO₂
with tab5:
    st.header('Gasversorgungsdaten')
    col_gas, col_vis_gas = st.columns([1, 2], gap='large')

    gas_prices_years = list(ss.all_el_prices.index.year.unique())
    if heat_load_year:
        gas_year_idx = gas_prices_years.index(heat_load_year)
    else:
        gas_year_idx = len(gas_prices_years) - 1
    gas_prices_year = col_gas.selectbox(
        'Wähle das Jahr der Gaspreisdaten aus',
        gas_prices_years, index=gas_year_idx,
        placeholder='Betrachtungsjahr'
    )
    gas_prices = ss.all_gas_prices[
        ss.all_gas_prices.index.year == gas_prices_year
        ].copy()
    co2_prices = ss.all_co2_prices[
        ss.all_co2_prices.index.year == gas_prices_year
        ].copy()

    precise_dates = col_gas.toggle(
        'Exakten Zeitraum wählen', key='prec_dates_gas_prices'
        )
    if precise_dates:
        gas_dates = col_gas.date_input(
            'Zeitraum auswählen:',
            value=dates if dates is not None else (
                date(int(heat_load_year), 3, 28),
                date(int(heat_load_year), 7, 2)
                ),
            min_value=date(int(heat_load_year), 1, 1),
            max_value=date(int(heat_load_year), 12, 31),
            format='DD.MM.YYYY', key='date_picker_gas_prices'
            )
        gas_dates = [
            datetime(year=d.year, month=d.month, day=d.day) for d in gas_dates
            ]
        gas_prices = gas_prices.loc[gas_dates[0]:gas_dates[1], :]

    if any(heat_load):
        nr_steps_hl = len(heat_load.index)
        nr_steps_gas = len(gas_prices.index)
        if nr_steps_hl != nr_steps_gas:
            st.error(
                'Die Anzahl der Zeitschritte der Wärmelastdaten '
                + f'({nr_steps_hl}) stimmt nicht mit denen der '
                + f' Gaspreiszeitreihe ({nr_steps_gas}) überein. Bitte die '
                + 'Daten angleichen.'
                )

    col_vis_gas.subheader('Gaspreis')
    gas_prices.reset_index(inplace=True)
    col_vis_gas.altair_chart(
        alt.Chart(gas_prices).mark_line(color='#B54036').encode(
            y=alt.Y(
                'Gaspreis', title='Gaspreise in €/MWh'
                ),
            x=alt.X('Date', title='Datum')
            ),
        use_container_width=True
        )

    col_gas.subheader('Emissionsfaktor Gas')
    ss.param_opt['ef_gas'] = col_gas.number_input(
        'Emissionsfatkor in kg CO₂/MWh', value=ss.param_opt['ef_gas']*1e3,
        key='ef_gas'
        )
    ss.param_opt['ef_gas'] *= 1e-3

    col_vis_gas.subheader('CO₂-Preise')
    co2_prices['CO2-Preis'] *= ss.param_opt['ef_gas']
    co2_prices.reset_index(inplace=True)
    col_vis_gas.altair_chart(
        alt.Chart(co2_prices).mark_line(color='#74ADC0').encode(
            y=alt.Y(
                'CO2-Preis',
                title='CO₂-Preise in €/MWh'
                ),
            x=alt.X('Date', title='Datum')
            ),
        use_container_width=True
        )

# %% MARK: Aggregate Data
ss.data = pd.concat(
    [heat_load, el_prices['El Price'], el_em['Emissionsfaktor Gesamtmix'],
     gas_prices['Gaspreis'], co2_prices['CO2-Preis']],
    axis=1
    )
ss.data.set_index('Date', inplace=True, drop=True)
