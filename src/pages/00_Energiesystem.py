import datetime as dt
import json
import os
import shutil
import zipfile
from copy import deepcopy

import altair as alt
import pandas as pd
import streamlit as st
from streamlit import session_state as ss


# %% MARK: Read Input Data
@st.cache_data
def read_input_data():
    '''Read in input data all at once.'''
    inputpath = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'input'
        ))
    all_heat_load = pd.read_csv(
        os.path.join(inputpath, 'heat_load.csv'),
        sep=';', index_col=0, parse_dates=True
        )
    eco_data = pd.read_csv(
        os.path.join(inputpath, 'eco_data.csv'),
        sep=';', index_col=0, parse_dates=True
        )

    return all_heat_load, eco_data


# %% MARK: Parameters
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
longnames = {
    'hp': 'Wärmepumpe',
    'ccet': 'Gas- und Dampfkratwerk',
    'ice': 'Blockheizkraftwerk',
    'sol': 'Solarthermie',
    'plb': 'Spitzenlastkessel',
    'eb': 'Elektrodenheizkessel',
    'exhs': 'Externe Wärmequelle',
    'tes': 'Wärmespeicher'
}

if 'eco_data' not in ss:
    ss.all_heat_load, ss.eco_data = read_input_data()

    ss.all_el_prices = ss.eco_data['el_spot_price'].to_frame()
    ss.all_el_emissions = ss.eco_data['ef_om'].to_frame()
    ss.all_gas_prices = ss.eco_data['gas_price'].to_frame()
    ss.all_co2_prices = ss.eco_data['co2_price'].to_frame()
    ss.all_solar_heat_flow = ss.eco_data['solar_heat_flow'].to_frame()

unitpath = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'input', 'param_units.json')
    )
with open(unitpath, 'r', encoding='utf-8') as file:
    ss.param_units_all = json.load(file)

optpath = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'input', 'param_opt.json')
    )
with open(optpath, 'r', encoding='utf-8') as file:
    ss.param_opt = json.load(file)

unitinputpath = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'input', 'unit_inputs.json')
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
    st.subheader('Offene Wärmespeicherplanung')

    logo_inno = os.path.join(
        os.path.dirname(__file__), '..', 'img', 'Logo_InnoNord_OWP.png'
        )
    st.image(logo_inno, use_container_width=True)

    logo = os.path.join(
        os.path.dirname(__file__), '..', 'img', 'Logo_ZNES_mitUnisV2.svg'
        )
    st.image(logo, use_container_width=True)

    st.markdown('''---''')

    st.subheader('Assoziierte Projektpartner')
    logo_bo = os.path.join(
        os.path.dirname(__file__), '..', 'img', 'Logo_Boben_Op.svg'
        )
    st.image(logo_bo, use_container_width=True)

    logo_gp = os.path.join(
        os.path.dirname(__file__), '..', 'img', 'Logo_GP_Joule.png'
        )
    st.image(logo_gp, use_container_width=True)

    logo_sw = os.path.join(
        os.path.dirname(__file__), '..', 'img', 'Logo_SW_Flensburg.svg'
        )
    st.image(logo_sw, use_container_width=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ['System', 'Anlagen', 'Wärme', 'Elektrizität', 'Gas', 'Sonstiges']
    )

# %% MARK: Energy System
with tab1:
    st.header('Auswahl des Wärmeversorgungssystem')

    col_system, col_unit = st.columns([1, 2], gap='large')

    # st.elements.utils._shown_default_value_warning = True

    if 'param_units' not in ss:
        ss.param_units = {}
    if 'units_multiselect' not in ss:
        if 'units' in ss:
            ss.units_multiselect = ss.units
        else:
            ss.units_multiselect = []
    if 'units' not in ss:
        ss.units = []

    ss.units = col_unit.multiselect(
        'Wähle die Wärmeversorgungsanlagen aus, die im System verwendet werden '
        + 'können.',
        options=list(shortnames.keys()),
        placeholder='Wärmeversorgungsanlagen',
        key='units_multiselect'
        )

    col_vis_unit, col_nr_unit = col_system.columns([0.8, 0.2])

    topopath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'img', 'es_topology_')
        )
    col_vis_unit.image(f'{topopath}header.png', use_container_width=True)
    if 'nr_units' not in ss:
        ss.nr_units = {}
    if ss.units:
        for unit in ss.units:
            col_vis_unit, col_nr_unit = col_system.columns(
                [0.8, 0.2], vertical_alignment='center'
            )
            col_vis_unit.image(
                f'{topopath+shortnames[unit]}.png', use_container_width=True
                )

            if unit in ss.nr_units:
                init_nr_units = ss.nr_units[unit]
            else:
                init_nr_units = 1

            ss.nr_units[unit] = col_nr_unit.number_input(
                f'Anzahl {unit}', value=init_nr_units, 
                min_value=1, max_value=99, step=1,
                label_visibility='collapsed'
            )

        removed_units = [u for u in ss.nr_units.keys() if u not in ss.units]
        for unit_cat in removed_units:
            ss.nr_units.pop(unit_cat, None)
            to_delete = [
                u for u in ss.param_units
                if longnames[u.rstrip('0123456789')] == unit_cat
                ]
            for key in to_delete:
                ss.param_units.pop(key, None)

        for u, params in ss.param_units_all.items():
            if longnames[u] in ss.units:
                for i in range(1, ss.nr_units[longnames[u]]+1):
                    if f'{u}{i}' not in ss.param_units.keys():
                        ss.param_units[f'{u}{i}'] = deepcopy(params)

        for unit_cat in ss.units:
            current_count = ss.nr_units[unit_cat]
            to_delete = [
                u for u in ss.param_units
                if longnames[u.rstrip('0123456789')] == unit_cat
                and int(u[len(u.rstrip('0123456789')):]) > current_count
                ]
            for key in to_delete:
                ss.param_units.pop(key, None)

    st.header('Eigenes Wärmeversorgungssystem laden')

    own_es = False
    esfile = st.file_uploader(
        'Datei auswählen:', type='zip',
        help='Aktuell nicht vollständig funktionsfähig'
    )
    if esfile is not None:
        tmppath = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), '..', '_tmp'
            )
        )
        if not os.path.exists(tmppath):
            os.mkdir(tmppath)

        zippath = os.path.join(tmppath, esfile.name.split('.')[0])
        with zipfile.ZipFile(esfile, 'r') as z:
            z.extractall(zippath)

        tspath = os.path.join(zippath, 'data_input.csv')
        ss.data = pd.read_csv(tspath, sep=';', index_col=0, parse_dates=True)

        optpath = os.path.join(zippath, 'param_opt.json')
        with open(optpath, 'r', encoding='utf-8') as file:
            ss.param_opt = json.load(file)

        unitpath = os.path.join(zippath, 'param_units.json')
        with open(unitpath, 'r', encoding='utf-8') as file:
            ss.param_units = json.load(file)

        ss.units = [longnames[u] for u in ss.param_units.keys()]

        shutil.rmtree(tmppath)
        own_es = True

# %% MARK: Unit Parameters
comb_opt_params = ['cap_max', 'cap_min', 'Q_max', 'Q_min', 'A_max', 'A_min']
disp_opt_params = ['cap_N', 'Q_N', 'A_N']

with tab2:
    st.header('Parametrisierung der Wärmeversorgungsanlagen')

    for unit, unit_params in ss.param_units.items():
        unit_cat = unit.rstrip('0123456789')
        unit_nr = unit[len(unit_cat):]

        with st.expander(f'{longnames[unit_cat]} {unit_nr}'):
            col_tech, col_econ = st.columns(2, gap='large')

            col_tech.subheader('Technische Parameter')
            unit_params['invest_mode'] = col_tech.toggle(
                'Kapazität optimieren',
                value=unit_params['invest_mode'],
                key=f'toggle_{unit}_invest_mode'
            )
            for uinput, uinfo in ss.unit_inputs['Technische Parameter'].items():
                if uinput in unit_params:
                    if unit_params['invest_mode'] and uinput in disp_opt_params:
                        continue
                    if not unit_params['invest_mode'] and uinput in comb_opt_params:
                        continue

                    if uinfo['type'] == 'bool':
                        unit_params[uinput] = col_tech.toggle(
                            uinfo['name'],
                            value=unit_params[uinput],
                            key=f'toggle_{unit}_{uinput}',
                            help=uinfo.get('tooltip', None)
                        )
                    else:
                        if uinfo['unit'] == '%':
                            unit_params[uinput] *= 100
                        if uinfo['unit'] == '':
                            label = uinfo['name']
                        else:
                            label = f"{uinfo['name']} in {uinfo['unit']}"
                        unit_params[uinput] = (
                            col_tech.number_input(
                                label,
                                value=float(
                                    unit_params[uinput]
                                    ),
                                min_value=uinfo['min'],
                                max_value=uinfo['max'],
                                step=(uinfo['max']-uinfo['min'])/100,
                                key=f'input_{unit}_{uinput}',
                                help=uinfo.get('tooltip', None)
                                )
                            )
                        if uinfo['unit'] == '%':
                            unit_params[uinput] /= 100

            col_econ.subheader('Ökonomische Parameter')
            for uinput, uinfo in ss.unit_inputs['Ökonomische Parameter'].items():
                if uinput in unit_params:
                    if unit_cat == 'sol':
                        if uinput == 'inv_spez':
                            label = f"{uinfo['name']} in €/m²"
                        elif uinput == 'op_cost_fix':
                            label = f"{uinfo['name']} in €/MWh"
                        else:
                            label = f"{uinfo['name']} in {uinfo['unit']}"
                    elif unit_cat == 'tes':
                        label = f"{uinfo['name']} in €/MWh"
                    else:
                        label = f"{uinfo['name']} in {uinfo['unit']}"

                    tooltip = uinfo.get('tooltip', None)
                    if unit_cat == 'sol' and uinput == 'op_cost_var':
                        if tooltip is None:
                            tooltip = (
                                'Die variablen Betriebskosten von '
                                + 'Solarthermie  werden in der '
                                + 'zugrundeliegenden Quelle anhand der '
                                + 'insgesamt produzierten Wärmemenge '
                                + 'berechnet.'
                                )
                        else:
                            tooltip += (
                                '\nDie variablen Betriebskosten von '
                                + 'Solarthermie  werden in der '
                                + 'zugrundeliegenden Quelle anhand der '
                                + 'insgesamt produzierten Wärmemenge '
                                + 'berechnet.'
                                )


                    unit_params[uinput] = (
                        col_econ.number_input(
                            label,
                            value=float(
                                unit_params[uinput]
                                ),
                            min_value=uinfo['min'],
                            max_value=uinfo['max'],
                            step=(uinfo['max']-uinfo['min'])/100,
                            key=f'input_{unit}_{uinput}',
                            help=tooltip
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
                    dt.date(int(heat_load_year), 3, 28),
                    dt.date(int(heat_load_year), 7, 2)
                    ),
                min_value=dt.date(int(heat_load_year), 1, 1),
                max_value=dt.date(int(heat_load_year), 12, 31),
                format='DD.MM.YYYY', key='date_picker_heat_load'
                )
            dates = [
                dt.datetime(year=d.year, month=d.month, day=d.day) for d in dates
                ]
            heat_load = heat_load.loc[dates[0]:dates[1], :]

        scale_hl = col_sel.toggle('Daten skalieren', key='scale_hl')
        if scale_hl:
            scale_method_hl = col_sel.selectbox(
                'Methode', ['Haushalte', 'Faktor', 'Erweitert'],
                key='scale_method_hl'
                )
            if scale_method_hl == 'Haushalte':
                if dataset_name == 'Flensburg':
                    base_households = 50000
                elif dataset_name == 'Sonderburg':
                    base_households = 13000
                scale_households_hl = col_sel.number_input(
                    'Anzahl Haushalte', value=base_households,
                    min_value=1, step=100, key='scale_households_hl'
                    )
                heat_load[dataset_name] *= scale_households_hl / base_households
            elif scale_method_hl == 'Faktor':
                scale_factor_hl = col_sel.number_input(
                    'Skalierungsfaktor', value=1.0, step=0.1, min_value=0.0,
                    key='scale_factor_hl'
                    )
                heat_load[dataset_name] *= scale_factor_hl
            elif scale_method_hl == 'Erweitert':
                scale_amp_hl = col_sel.number_input(
                    'Stauchungsfaktor', value=1.0, step=0.1, min_value=0.0,
                    help='Staucht die Lastdaten um den Median.',
                    key='scale_amp_hl'
                    )
                scale_off_hl = col_sel.number_input(
                    'Offset', value=1.0, step=0.1,
                    help='Verschiebt den Median der Lastdaten.',
                    key='scale_off_hl'
                    )
                heat_load_median = heat_load[dataset_name].median()
                heat_load[dataset_name] = (
                    (heat_load[dataset_name] - heat_load_median) * scale_amp_hl
                    + heat_load_median + scale_off_hl
                    )
                # negative_mask = heat_load[dataset_name] < 0
                if (heat_load[dataset_name] < 0).values.any():
                    st.error(
                        'Durch die Skalierung resultiert eine negative '
                        + 'Wärmelast. Bitte den Offset anpassen.'
                        )

    col_vis.subheader('Wärmelastdaten')

    if user_file is not None or dataset_name != 'Eigene Daten':
        heat_load.rename(
            columns={heat_load.columns[0]: 'heat_demand'}, inplace=True
            )
        heat_load.index.names = ['Date']
        heat_load.reset_index(inplace=True)

        col_vis.altair_chart(
            alt.Chart(heat_load).mark_line(color='#EC6707').encode(
                y=alt.Y('heat_demand', title='Stündliche Wärmelast in MWh'),
                x=alt.X('Date', title='Datum')
            ),
            use_container_width=True
        )

    col_sel.subheader('Wärmeerlöse')

    ss.param_opt['heat_price'] = col_sel.number_input(
        'Wärmeerlös in €/MWh', value=ss.param_opt['heat_price'],
        key='heat_revenue'
        )

    if 'Solarthermie' in ss.units:
        solar_heat_flow = ss.all_solar_heat_flow[
            ss.all_solar_heat_flow.index.year == heat_load_year
            ].copy()
        if precise_dates:
            solar_heat_flow = solar_heat_flow.loc[dates[0]:dates[1], :]
        solar_heat_flow.reset_index(inplace=True)
        solar_heat_flow['solar_heat_flow'] *= 1e6

        col_vis.subheader('Solathermie')
        col_vis.altair_chart(
            alt.Chart(solar_heat_flow).mark_line(color='#EC6707').encode(
                y=alt.Y('solar_heat_flow',
                        title='Spezifische Einstrahlung in Wh/m²'),
                x=alt.X('Date', title='Datum')
            ),
            use_container_width=True
        )
        solar_heat_flow['solar_heat_flow'] *= 1e-6

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
                dt.date(int(heat_load_year), 3, 28),
                dt.date(int(heat_load_year), 7, 2)
                ),
            min_value=dt.date(int(heat_load_year), 1, 1),
            max_value=dt.date(int(heat_load_year), 12, 31),
            format='DD.MM.YYYY', key='date_picker_el_prices'
            )
        el_dates = [
            dt.datetime(year=d.year, month=d.month, day=d.day) for d in el_dates
            ]
        el_prices = el_prices.loc[el_dates[0]:el_dates[1], :]
        el_em = el_em.loc[el_dates[0]:el_dates[1], :]

    scale_el = col_elp.toggle('Daten skalieren', key='scale_el')
    if scale_el:
        scale_method_el = col_elp.selectbox(
            'Methode', ['Faktor', 'Erweitert'], key='scale_method_el'
            )
        if scale_method_el == 'Faktor':
            scale_factor_el = col_elp.number_input(
                'Skalierungsfaktor', value=1.0, step=0.1, min_value=0.0,
                key='scale_factor_el'
                )
            el_prices['el_spot_price'] *= scale_factor_el
        elif scale_method_el == 'Erweitert':
            scale_amp_el = col_elp.number_input(
                'Stauchungsfaktor', value=1.0, step=0.1, min_value=0.0,
                help='Staucht die Strompreise um den Median.', key='scale_amp_el'
                )
            scale_off_el = col_elp.number_input(
                'Offset', value=1.0, step=0.1,
                help='Verschiebt den Median der Strompreise.', key='scale_off_el'
                )
            el_prices_median = el_prices['el_spot_price'].median()
            el_prices['el_spot_price'] = (
                (el_prices['el_spot_price'] - el_prices_median) * scale_amp_el
                + el_prices_median + scale_off_el
                )

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

    col_elp.subheader('Strompreisbestandteile in ct/kWh')
    col_elp.dataframe(
        {k: v for k, v in ss.bound_inputs[str(el_prices_year)].items()},
        use_container_width=True
        )

    cons_charger = ss.bound_inputs[str(el_prices_year)]
    ss.param_opt['elec_consumer_charges_grid'] = round(sum(
        val*10 for val in cons_charger['Netzbezug'].values()
        ), 2)
    ss.param_opt['elec_consumer_charges_self'] = round(sum(
        val*10 for val in cons_charger['Eigennutzung'].values()
        ), 2)


    col_vis_el.subheader('Spotmarkt Strompreise')
    el_prices.reset_index(inplace=True)
    col_vis_el.altair_chart(
        alt.Chart(el_prices).mark_line(color='#00395B').encode(
            y=alt.Y(
                'el_spot_price', title='Day-Ahead Spotmarkt Strompreise in €/MWh'
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
                'ef_om',
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
                dt.date(int(heat_load_year), 3, 28),
                dt.date(int(heat_load_year), 7, 2)
                ),
            min_value=dt.date(int(heat_load_year), 1, 1),
            max_value=dt.date(int(heat_load_year), 12, 31),
            format='DD.MM.YYYY', key='date_picker_gas_prices'
            )
        gas_dates = [
            dt.datetime(year=d.year, month=d.month, day=d.day) for d in gas_dates
            ]
        gas_prices = gas_prices.loc[gas_dates[0]:gas_dates[1], :]
        co2_prices = co2_prices.loc[gas_dates[0]:gas_dates[1], :]

    scale_gas = col_gas.toggle('Daten skalieren', key='scale_gas')
    if scale_gas:
        scale_method_gas = col_gas.selectbox(
            'Methode', ['Faktor', 'Erweitert'], key='scale_method_gas'
            )
        if scale_method_gas == 'Faktor':
            scale_factor_gas = col_gas.number_input(
                'Skalierungsfaktor', value=1.0, step=0.1, min_value=0.0,
                key='scale_factor_gas'
                )
            gas_prices['gas_price'] *= scale_factor_gas
        elif scale_method_gas == 'Erweitert':
            scale_amp_gas = col_gas.number_input(
                'Stauchungsfaktor', value=1.0, step=0.1, min_value=0.0,
                help='Staucht die Gaspreise um den Median.', key='scale_amp_gas'
                )
            scale_off_gas = col_gas.number_input(
                'Offset', value=1.0, step=0.1,
                help='Verschiebt den Median der Gaspreise.', key='scale_off_gas'
                )
            gas_prices_median = gas_prices['gas_price'].median()
            gas_prices['gas_price'] = (
                (gas_prices['gas_price'] - gas_prices_median) * scale_amp_gas
                + gas_prices_median + scale_off_gas
                )

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
                'gas_price', title='Gaspreise in €/MWh'
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
    co2_prices['co2_price'] *= ss.param_opt['ef_gas']
    co2_prices.reset_index(inplace=True)
    col_vis_gas.altair_chart(
        alt.Chart(co2_prices).mark_line(color='#74ADC0').encode(
            y=alt.Y(
                'co2_price',
                title='CO₂-Preise in €/MWh'
                ),
            x=alt.X('Date', title='Datum')
            ),
        use_container_width=True
        )

# %% MARK: Aggregate Data
if not own_es:
    ss.data = pd.concat(
        [heat_load, el_prices['el_spot_price'], el_em['ef_om'],
        gas_prices['gas_price'], co2_prices['co2_price']], axis=1
        )
    if 'Solarthermie' in ss.units:
        ss.data['solar_heat_flow'] = solar_heat_flow['solar_heat_flow']
    ss.data.set_index('Date', inplace=True, drop=True)

# %% MARK: Sonstiges
with tab6:
    st.header('Sonstige Paramter')

    col_econ, col_opt = st.columns([1, 1], gap='large')

    col_econ.subheader('Wirtschaft')
    ss.param_opt['capital_interest'] *= 100
    ss.param_opt['capital_interest'] = col_econ.number_input(
        'Kapitalzins in %', value=ss.param_opt['capital_interest'],
        key='capital_interest'
        )
    ss.param_opt['capital_interest'] *= 1/100

    ss.param_opt['lifetime'] = col_econ.number_input(
        'Lebensdauer in Jahre', value=ss.param_opt['lifetime'],
        key='lifetime'
        )

    help_tax =(
        'Beim Einsatz von Kraft- und Brennstoffen fällt die sogenannte '
        + 'Energiesteuer an, was für die Nutzung von gasbefeuerten KWK-Anlangen '
        + 'und Spitzenlastkesseln relevant ist '
        + '[[Zoll (2021)](https://www.zoll.de/DE/Fachthemen/Steuern/Verbrauchsteuern/Energie/Steuerbeguenstigung/Steuerentlastung/KWK-Anlagen/Vollstaendige-Steuerentlastung/Steuerentlastungstatbestand/steuerentlastungstatbestand_node.html)].'
    )
    ss.param_opt['energy_tax'] = col_econ.number_input(
        'Energiesteuer in €/MWh', value=ss.param_opt['energy_tax'],
        help=help_tax, key='energy_tax'
        )

    ss.param_opt['vNNE'] = col_econ.number_input(
        'Vermiedene Netznutzungsentgelte in €/MWh', value=ss.param_opt['vNNE'],
        key='vNNE'
        )

    help_mip = (
        'Der MIPGap-Parameter steuert die minimale Qualität der '
        + 'zurückgegebenen Lösung. Er ist eine Obergrenze für die tatsächliche '
        + 'Lücke der endgültigen Lösung.'
    )
    col_opt.subheader('Optimierung')

    ss.param_opt['Solver'] = col_opt.selectbox(
        'Solver', options=['Gurobi', 'HiGHS']
        )

    ss.param_opt['MIPGap'] *= 100
    ss.param_opt['MIPGap'] = col_opt.number_input(
        'MIP Gap in %', value=ss.param_opt['MIPGap'], help=help_mip,
        key='MIPGap'
        )
    ss.param_opt['MIPGap'] *= 1/100

    ss.param_opt['TimeLimit'] = None
    timelimit = col_opt.toggle(
        'Simulationsdauer begrenzen', key='ToggleTimeLimit'
        )
    if timelimit:
        ss.param_opt['TimeLimit'] = col_opt.number_input(
            'Zeitlimit in Minuten', value=ss.param_opt['TimeLimit'],
            key='TimeLimit'
            )
        if ss.param_opt['TimeLimit'] is not None:
            ss.param_opt['TimeLimit'] *= 60

    st.markdown('''---''')

    with st.container(border=True):
        st.page_link(
            'pages/01_Optimierung.py', label='**Zur Optimierung**',
            icon='📝', use_container_width=True
            )
