import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard Volontariato", layout="wide")

st.title(" Dashboard Attivita Associazione di Volontariato")

# --- Upload file ---
turni_file = st.file_uploader("Carica il file dei Turni", type=["xlsx"])
servizi_file = st.file_uploader("Carica il file dei Servizi", type=["xlsx"])

if turni_file and servizi_file:
    df_turni = pd.read_excel(turni_file)
    df_servizi = pd.read_excel(servizi_file)

    # --- Preprocessing Turni ---
    df_turni['Inizio'] = pd.to_datetime(df_turni['Data'].astype(str) + ' ' + df_turni['Inizio'].astype(str))
    df_turni['Fine'] = pd.to_datetime(df_turni['Data'].astype(str) + ' ' + df_turni['Fine'].astype(str))
    df_turni['Durata (h)'] = (df_turni['Fine'] - df_turni['Inizio']).dt.total_seconds() / 3600
    df_turni['Categoria Pulita'] = df_turni['Categoria'].str.extract(r"\[(.*?)\]")

    # --- Preprocessing Servizi ---
    df_servizi['[P]Ore'] = pd.to_datetime(df_servizi['Data'].astype(str) + ' ' + df_servizi['[P]Ore'].astype(str))
    df_servizi['[A]Ore'] = pd.to_datetime(df_servizi['Data'].astype(str) + ' ' + df_servizi['[A]Ore'].astype(str))
    df_servizi['Durata (min)'] = (df_servizi['[A]Ore'] - df_servizi['[P]Ore']).dt.total_seconds() / 60
    df_servizi['Categoria Servizio'] = df_servizi['Intervento'].str.extract(r"\[(.*?)\]")

    # --- Filtri ---
    st.sidebar.header(" Filtri")

    min_data = min(df_turni['Inizio'].min(), df_servizi['[P]Ore'].min())
    max_data = max(df_turni['Fine'].max(), df_servizi['[A]Ore'].max())

    data_range = st.sidebar.date_input("Intervallo Date", [min_data.date(), max_data.date()])
    tipi_servizio = st.sidebar.multiselect("Tipo Servizio", options=sorted(df_servizi['Categoria Servizio'].dropna().unique()), default=None)
    mezzi = st.sidebar.multiselect("Automezzo", options=sorted(df_servizi['Automezzo'].dropna().unique()), default=None)

    # --- Applica filtri ---
    df_servizi_filt = df_servizi.copy()
    df_turni_filt = df_turni.copy()

    df_servizi_filt = df_servizi_filt[(df_servizi_filt['[P]Ore'].dt.date >= data_range[0]) & (df_servizi_filt['[P]Ore'].dt.date <= data_range[1])]
    df_turni_filt = df_turni_filt[(df_turni_filt['Inizio'].dt.date >= data_range[0]) & (df_turni_filt['Inizio'].dt.date <= data_range[1])]

    if tipi_servizio:
        df_servizi_filt = df_servizi_filt[df_servizi_filt['Categoria Servizio'].isin(tipi_servizio)]

    if mezzi:
        df_servizi_filt = df_servizi_filt[df_servizi_filt['Automezzo'].isin(mezzi)]

    # --- KPI ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("\u23f0 Turni Totali", len(df_turni_filt))
    col2.metric("\u231b Ore di Turno", f"{df_turni_filt['Durata (h)'].sum():.1f} h")
    col3.metric("\u2705 Servizi Svolti", len(df_servizi_filt))
    col4.metric("\ud83d\ude97 Km Totali", int(df_servizi_filt['Km effet.'].sum()))

    # --- Grafici ---
    st.subheader(" Distribuzione per Categoria")
    col5, col6 = st.columns(2)

    with col5:
        st.bar_chart(df_turni_filt['Categoria Pulita'].value_counts())
    with col6:
        st.bar_chart(df_servizi_filt['Categoria Servizio'].value_counts())

    st.subheader(" Servizi per Giorno della Settimana")
    st.bar_chart(df_servizi_filt['GG'].value_counts().reindex(["LUN","MAR","MER","GIO","VEN","SAB","DOM"]))

else:
    st.info("Carica entrambi i file per iniziare.")
