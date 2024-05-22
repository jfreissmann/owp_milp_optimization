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

colors = {
    'Wärmepumpe': '#B54036',
    'Gas- und Dampfkratwerk': '#00395B',
    'Blockheizkraftwerk': '#00395B',
    'Spitzenlastkessel': '#EC6707',
    'Solarthermie': '#EC6707',
    'Wärmespeicher Ein': 'slategrey',
    'Wärmespeicher Aus': 'dimgrey',
    'Wärmebedarf': '#31333f'
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
chp_used = ('ice' in ss.param_units.keys()) or ('ccet' in ss.param_units.keys())

if chp_used:
    if tes_used:
        tab_ov, tab_unit, tab_el, tab_tes = st.tabs(
            ['Überblick', 'Anlageneinsatz', 'Stromproduktion', 'Speicherstand']
            )
    else:
        tab_ov, tab_unit, tab_el = st.tabs(
            ['Überblick', 'Anlageneinsatz', 'Stromproduktion']
            )
else:
    if tes_used:
        tab_ov, tab_unit, tab_tes = st.tabs(
            ['Überblick', 'Anlageneinsatz', 'Speicherstand']
            )
    else:
        tab_ov, tab_unit = st.tabs(
            ['Überblick', 'Anlageneinsatz']
            )

# %% MARK: Overview
with tab_ov:
    # st.header('Überblick der Optimierungsergebnisse')

    col_cap, col_sum = st.columns([1, 2], gap='large')

    col_cap.subheader('Optimierte Anlagenkapazitäten')
    overview_caps = ss.energy_system.data_caps.copy()
    if tes_used:
        overview_caps.drop(columns=['cap_in_tes', 'cap_out_tes'], inplace=True)
    renamedict = {}
    for col in overview_caps.columns:
        if 'tes' in col:
            renamedict[col] = longnames[col.split('_')[-1]] + ' (MWh)'
        elif 'sol' in col:
            renamedict[col] = longnames[col.split('_')[-1]] + ' (m²)'
        else:
            renamedict[col] = longnames[col.split('_')[-1]] + ' (MW)'

    overview_caps.rename(columns=renamedict, inplace=True)
    overview_caps.rename(index={0: 'Kapazität'}, inplace=True)
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
        'Gesamtemissionen in T',
        round(ss.energy_system.key_params['Total Emissions OM']/1e3, 1)
        )
    met2.metric(
        'Emissionen durch Gasbezug in T',
        round(ss.energy_system.key_params['Emissions OM (Gas)']/1e3, 1)
        )
    met3.metric(
        'Emissionen durch Strombezug in T',
        round(ss.energy_system.key_params['Emissions OM (Electricity)']/1e3, 1)
        )
    met4.metric(
        'Emissionsgutschriften durch Stromproduktion in T',
        round(ss.energy_system.key_params['Emissions OM (Spotmarket)']/1e3, 1)
        )

# %% MARK: Unit Commitment
with tab_unit:
    st.subheader('Geordnete Jahresdauerlinien des Anlageneinsatzes')

    heatprod = pd.DataFrame()
    for col in ss.energy_system.data_all.columns:
        if 'Q_' in col:
            this_unit = None
            for unit in ss.units:
                unit = shortnames[unit]
                if unit in col:
                    this_unit = unit
            if this_unit is None:
                collabel = 'Wärmebedarf'
            elif this_unit == 'tes':
                if '_in' in col:
                    collabel = longnames[this_unit] + ' Ein'
                elif '_out' in col:
                    collabel = longnames[this_unit] + ' Aus'
            else:
                collabel = longnames[this_unit]
            heatprod[collabel] = ss.energy_system.data_all[col].copy()
    heatprod_sorted = pd.DataFrame(
        np.sort(heatprod.values, axis=0)[::-1], columns=heatprod.columns
        )
    heatprod_sorted.index.names = ['Stunde']
    heatprod_sorted.reset_index(inplace=True)

    hprod_sorted_melt = heatprod_sorted.melt('Stunde')
    hprod_sorted_melt.rename(
        columns={'variable': 'Versorgungsanlage'}, inplace=True
        )

    st.altair_chart(
        alt.Chart(hprod_sorted_melt).mark_line().encode(
            y=alt.Y('value', title='Stündliche Wärmeproduktion in MWh'),
            x=alt.X('Stunde', title='Stunden'),
            color=alt.Color('Versorgungsanlage').scale(
                domain=list(heatprod.columns),
                range=[colors[c] for c in heatprod.columns]
                )
            ),
        use_container_width=True
        )

    st.subheader('Tatsächlicher Anlageneinsatz')

    if tes_used:
        # heatprod['Q_in_tes'] *= -1
        heatprod['Wärmespeicher Ein'] *= -1
    # heatprod.drop('Wärmebedarf', axis=1, inplace=True)
    heatprod.index.names = ['Date']
    heatprod.reset_index(inplace=True)

    hprod_melt = heatprod.melt('Date')
    hprod_melt.rename(
        columns={'variable': 'Versorgungsanlage'}, inplace=True
        )

    st.altair_chart(
        alt.Chart(hprod_melt).mark_line().encode(
            y=alt.Y('value', title='Stündliche Wärmeproduktion in MWh'),
            x=alt.X('Date', title='Datum'),
            color=alt.Color('Versorgungsanlage').scale(
                domain=[c for c in heatprod.columns if c != 'Date'],
                range=[colors[c] for c in heatprod.columns if c != 'Date']
                )
            ),
        use_container_width=True
        )

# %% MARK: Electricity Production
if chp_used:
    with tab_el:
        st.subheader('Stromproduktion und -erlöse')

        col_sel, col_el = st.columns([1, 2], gap='large')

        dates = col_sel.date_input(
            'Zeitraum auswählen:',
            value=(
                ss.energy_system.data_all.index[0],
                ss.energy_system.data_all.index[-1]
                ),
            min_value=ss.energy_system.data_all.index[0],
            max_value=ss.energy_system.data_all.index[-1],
            format='DD.MM.YYYY', key='date_picker_el_production'
            )
        dates = [
            dt.datetime(year=d.year, month=d.month, day=d.day) for d in dates
            ]
        # Avoid error while only one date is picked
        if len(dates) == 1:
            dates.append(dates[0] + dt.timedelta(days=1))

        elprod = ss.energy_system.data_all.loc[
            dates[0]:dates[1], 'P_spotmarket'
            ].copy().to_frame()
        elprod.index.names = ['Date']
        elprod.reset_index(inplace=True)

        col_el.altair_chart(
            alt.Chart(elprod).mark_line(color='#00395B').encode(
                y=alt.Y(
                    'P_spotmarket',
                    title='Ins Netz eingespeiste Elektrizität in MWh'
                    ),
                x=alt.X('Date', title='Datum')
            ),
            use_container_width=True
            )

        elprice = ss.all_el_prices.loc[
            dates[0]:dates[1], 'el_spot_price'
            ].copy().to_frame()
        elprice.index.names = ['Date']
        elprice.reset_index(inplace=True)

        col_el.altair_chart(
            alt.Chart(elprice).mark_line(color='#00395B').encode(
                y=alt.Y('el_spot_price', title='Spotmarkt Strompreis in €/MWh'),
                x=alt.X('Date', title='Datum')
            ),
            use_container_width=True
            )

# %% MARK: TES Content
if tes_used:
    with tab_tes:
        st.subheader('Füllstand des thermischen Energiespeichers')

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

        tesdata = ss.energy_system.data_all.loc[
            dates[0]:dates[1], ['storage_content_tes', 'Q_in_tes', 'Q_out_tes']
            ].copy()
        tesdata['Q_in_tes'] *= -1
        tesdata.rename(
            columns={
                'Q_in_tes': 'Wärmespeicher Ein',
                'Q_out_tes': 'Wärmespeicher Aus'},
            inplace=True
            )
        tesdata.index.names = ['Date']
        tesdata.reset_index(inplace=True)

        col_tes.altair_chart(
            alt.Chart(tesdata).mark_line(color='#EC6707').encode(
                y=alt.Y('storage_content_tes', title='Speicherstand in MWh'),
                x=alt.X('Date', title='Datum'),
                ),
            use_container_width=True
            )

        domain = ['Wärmespeicher Aus', 'Wärmespeicher Ein']
        col_tes.altair_chart(
            alt.Chart(tesdata[['Date', *domain]].melt('Date')).mark_bar(size=0.5).encode(
                y=alt.Y('value', title='Speicherbe- & -entladung in MWh'),
                x=alt.X('Date', title='Datum'),
                color=alt.Color('variable').scale(
                    domain=domain, range=[colors[d] for d in domain]
                    ).legend(None)
                ),
            use_container_width=True
            )