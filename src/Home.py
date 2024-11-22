import os

import pandas as pd
import streamlit as st
from streamlit import session_state as ss

st.set_page_config(
    layout='wide',
    page_title='OWP MILP Optimierung',
    page_icon=os.path.join(os.path.dirname(__file__), 'img',  'page_icon_ZNES.png')
    )

@st.cache_data
def read_input_data():
    '''Read in input data all at once.'''
    inputpath = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'input'
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

if 'eco_data' not in ss:
    ss.all_heat_load, ss.eco_data = read_input_data()

    ss.all_el_prices = ss.eco_data['el_spot_price'].to_frame()
    ss.all_el_emissions = ss.eco_data['ef_om'].to_frame()
    ss.all_gas_prices = ss.eco_data['gas_price'].to_frame()
    ss.all_co2_prices = ss.eco_data['co2_price'].to_frame()
    ss.all_solar_heat_flow = ss.eco_data['solar_heat_flow'].to_frame()

# %% Sidebar
with st.sidebar:
    st.subheader('Offene Wärmespeicherplanung')

    logo_inno = os.path.join(
        os.path.dirname(__file__), 'img', 'Logo_InnoNord_OWP.png'
        )
    st.image(logo_inno, use_column_width=True)

    logo = os.path.join(
        os.path.dirname(__file__), 'img', 'Logo_ZNES_mitUnisV2.svg'
        )
    st.image(logo, use_column_width=True)

# %% Main Window
col_inno, _, col_foerder = st.columns([0.3, 0.4, 0.3])
logo = os.path.join(os.path.dirname(__file__), 'img',  'Logo_InnoNord_OWP.png')
col_inno.image(logo, use_column_width=True)

logo_foederer = os.path.join(os.path.dirname(__file__), 'img',  'Logos_Förderer_ohnePTJ.png')
col_foerder.image(logo_foederer, use_column_width=True)

st.write(
    """
    Willkommen in dem Optimierungsdashboard des Projektes "Offene Wärmespeicherplanung"
    (OWP) der Initiative Inno!Nord. 

    Mit diesem Dashboard lassen sich multivalente Wärmeversorgungssysteme und
    die darin eingesetzen Versorgungsanlagen simulieren. Dazu kann aus einer
    Reihe von Anlagentypen gewählt werden, die Ihr individuelles Wärmesystem
    bilden. Diese Anlagen werden anschließend parametrisiert, die
    energiewirtschaftlichen und -politischen Rahmenbedingungen festgelegt und
    eine kombinierte Auslegungs- und Einsatzoptimierung durchgeführt. Dazu wird
    die Methode der gemischt ganzzahlig linearen Optimierung (kurz MILP, aus dem
    Englischen: Mixed Integer Linear Programming) verwendet.

    ### Key Features

    - Kombiniert Auslegungs- und Einsatzoptimierung basierend auf [oemof.solph](https://github.com/oemof/oemof-solph)
    - Parametrisierung and Ergebnisvisualisierung mithilfe eines [Streamlit](https://github.com/streamlit/streamlit) Dashboards
    - Breite Auswahl typischer Wärmeversorgungsanlagen
    - Umfangreiche Datenbank von Lastdaten, Preiszeitreihen und Emissionsfaktoren
    """
    )

with st.container(border=True):
    st.page_link(
        'pages/00_Energiesystem.py', label='**Energiesystem konfigurieren**',
        icon='📝', use_container_width=True,
        )

st.write(
    """
    ### Assoziierte Projektpartner
    """
    )

_, col_partner, _ = st.columns([0.1 ,0.8, 0.1])
logo_partner = os.path.join(os.path.dirname(__file__), 'img',  'Logos_Partner.svg')
col_partner.image(logo_partner, use_column_width=True)

st.markdown('''---''')

with st.expander('Verwendete Software'):
    st.info(
        """
        #### Verwendete Software:

        Zur Modellerstellung und Simulationen wird die
        Open Source Software oemof.solph verwendet. Des Weiteren werden
        eine Reihe weiterer Pythonpakete zur Datenverarbeitung,
        -aufbereitung und -visualisierung genutzt.

        ---

        #### oemof.solph:

        Das Softwarepaket oemof.solpf als Teil des Open Energy Modelling
        Framework ist ein leistungsfähiges Simulationswerkzeug für
        Energiesysteme. Mit dem Paket ist es möglich, den Anlageneinsatz zu
        optimieren und die Kapazität dieser auszulegen. Die komponentenbasierte
        Struktur in Kombination mit den generischen Anlagenklassen bieten eine
        sehr hohe Flexibilität hinsichtlich der Systemtopologie und der
        Parametrisierung. Weitere Informationen zu oemof.solph sind in dessen
        [Onlinedokumentation](https://oemof-solph.readthedocs.io) in
        englischer Sprache zu finden.

        #### Weitere Pakete:

        - [Streamlit](https://docs.streamlit.io) (Graphische Oberfläche)
        - [NumPy](https://numpy.org) (Datenverarbeitung)
        - [pandas](https://pandas.pydata.org) (Datenverarbeitung)
        - [Matplotlib](https://matplotlib.org) (Datenvisualisierung)
        """
        )

with st.expander('Disclaimer'):
    st.warning(
        """
        #### Simulationsergebnisse:

        Numerische Simulationen sind Berechnungen mittels geeigneter
        Iterationsverfahren in Bezug auf die vorgegebenen und gesetzten
        Randbedingungen und Parameter. Eine Berücksichtigung aller
        möglichen Einflüsse ist in Einzelfällen nicht möglich, so dass
        Abweichungen zu Erfahrungswerten aus Praxisanwendungen
        entstehen können und bei der Bewertung berücksichtigt werden
        müssen. Entsprechend sind alle Angaben und Ergebnisse ohne Gewähr.
        """
        )

with st.expander('Copyright'):
    licpath = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'LICENSE'
        ))
    with open(licpath, 'r', encoding='utf-8') as file:
        lictext = file.read()

    st.success('#### Softwarelizenz\n' + lictext.replace('(c)', '©'))

