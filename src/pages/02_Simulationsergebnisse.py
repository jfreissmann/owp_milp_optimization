import datetime as dt
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
        ['Überblick', 'Anlageneinsatz', 'Speicherstand']
        )
else:
    tab1, tab2 = st.tabs(
        ['Überblick', 'Anlageneinsatz']
        )

with tab1:
    # st.header('Überblick der Optimierungsergebnisse')

    col_cap, col_sum = st.columns([1, 2], gap='large')

    col_cap.subheader('Optimierte Anlagenkapazitäten')
    overview_caps = ss.energy_system.data_caps.copy()
    if tes_used:
        overview_caps.drop(columns=['cap_in_tes', 'cap_out_tes'], inplace=True)
    overview_caps.rename(columns={
        c: longnames[c.split('_')[-1]] for c in overview_caps.columns
        }, inplace=True)
    overview_caps.rename(index={0: 'Kapazität (MW bzw. MWh)'}, inplace=True)
    overview_caps = overview_caps.apply(lambda x: round(x, 1))

    col_cap.dataframe(overview_caps.T, use_container_width=True)

    col_sum.subheader('Wärmeproduktion')
    qsum = pd.DataFrame(columns=['unit', 'qsum'])
    idx = 0
    for unit in ss.units:
        unit = shortnames[unit]
        if unit == 'tes':
            tl = {'in': 'Ein', 'out': 'Aus'}
            for var in ['in', 'out']:
                unit_col = f'Q_{var}_{unit}'
                qsum.loc[idx, 'unit'] = longnames[unit] + ' ' + tl[var]
                qsum.loc[idx, 'qsum'] = ss.energy_system.data_all[unit_col].sum()
                idx += 1
        else:
            if (unit == 'hp') or (unit == 'tes'):
                unit_col = f'Q_out_{unit}'
            else:
                unit_col = f'Q_{unit}'
            qsum.loc[idx, 'unit'] = longnames[unit]
            qsum.loc[idx, 'qsum'] = ss.energy_system.data_all[unit_col].sum()
            idx += 1

    col_sum.altair_chart(
        alt.Chart(qsum).mark_bar(color='#B54036').encode(
            y=alt.Y('unit', title='Versorgungsanlage'),
            x=alt.X('qsum', title='Gesamtwärmebereitstellung in MWh')
            ),
        use_container_width=True
        )

    st.subheader('Wirtschaftliche Kennzahlen')
    col_lcoh, col_cost = st.columns([1, 5])
    col_lcoh.metric('LCOH in €/MWh', round(ss.energy_system.key_params['LCOH'], 2))

    unit_cost = ss.energy_system.cost_df.copy()
    unit_cost.rename(columns=longnames, inplace=True)
    unit_cost.rename(
        index={
            'invest': 'Investitionskosten',
            'op_cost_var': 'Variable Betriebskosten',
            'op_cost_fix': 'Fixe Betriebskosten',
            'op_cost': 'Gesamtbetriebskosten'
            },
        inplace=True
        )

    unit_cost.drop('Gesamtbetriebskosten', axis=0, inplace=True)
    unit_cost = unit_cost.apply(lambda x: round(x, 2))

    col_cost.dataframe(unit_cost, use_container_width=True)

    st.subheader('Ökologische Kennzahlen')
    met1, met2, met3, met4= st.columns([1, 1, 1, 1])
    met1.metric(
        'Gesamtemissionen in kT',
        round(ss.energy_system.key_params['Total Emissions OM']/1e6, 1)
        )
    met2.metric(
        'Emissionen durch Gasbezug in kT',
        round(ss.energy_system.key_params['Emissions OM (Gas)']/1e6, 1)
        )
    met3.metric(
        'Emissionen durch Strombezug in kT',
        round(ss.energy_system.key_params['Emissions OM (Electricity)']/1e6, 1)
        )
    met4.metric(
        'Emissionsgutschriften durch Stromproduktion in kT',
        round(ss.energy_system.key_params['Emissions OM (Spotmarket)']/1e6, 1)
        )

with tab2:
    st.subheader('Geordnete Jahresdauerlinien des Anlageneinsatzes')

    heatprod = pd.DataFrame()
    for col in ss.energy_system.data_all.columns:
        if 'Q_' in col:
            heatprod[col] = ss.energy_system.data_all[col].copy()
    heatprod_sorted = pd.DataFrame(
        np.sort(heatprod.values, axis=0)[::-1], columns=heatprod.columns
        )
    heatprod_sorted.index.names = ['Stunde']
    heatprod_sorted.reset_index(inplace=True)

    st.altair_chart(
        alt.Chart(heatprod_sorted.melt('Stunde')).mark_line().encode(
            y=alt.Y('value', title='Stündliche Wärmeproduktion in MWh'),
            x=alt.X('Stunde', title='Stunden'),
            color='variable'
            ),
        use_container_width=True
        )

    st.subheader('Tatsächlicher Anlageneinsatzes')

    if tes_used:
        heatprod['Q_in_tes'] *= -1
    heatprod.drop('Q_demand', axis=1, inplace=True)
    heatprod.index.names = ['Date']
    heatprod.reset_index(inplace=True)

    st.altair_chart(
        alt.Chart(heatprod.melt('Date')).mark_line().encode(
            y=alt.Y('value', title='Stündliche Wärmeproduktion in MWh'),
            x=alt.X('Date', title='Datum'),
            color='variable'
            ),
        use_container_width=True
        )

if tes_used:
    with tab3:
        st.header('Füllstand des thermischen Energiespeichers')

        col_sel, col_tes = st.columns([1, 2], gap='large')

        dates = col_sel.date_input(
            'Zeitraum auswählen:',
            value=(
                ss.energy_system.data_all.index[0],
                ss.energy_system.data_all.index[-1]
                ),
            min_value=ss.energy_system.data_all.index[0],
            max_value=ss.energy_system.data_all.index[-1],
            format='DD.MM.YYYY', key='date_picker_storage_content'
            )
        dates = [
            dt.datetime(year=d.year, month=d.month, day=d.day) for d in dates
            ]
        # Avoid error while only one date is picked
        if len(dates) == 1:
            dates.append(dates[0] + dt.timedelta(days=1))

        tessoc = ss.energy_system.data_all.loc[
            dates[0]:dates[1], 'storage_content_tes'
            ].copy().to_frame()
        tessoc.index.names = ['Date']
        tessoc.reset_index(inplace=True)

        col_tes.altair_chart(
            alt.Chart(tessoc).mark_line(color='#EC6707').encode(
                y=alt.Y('storage_content_tes', title='Speicherstand in MWh'),
                x=alt.X('Date', title='Datum')
            ),
            use_container_width=True
            )
