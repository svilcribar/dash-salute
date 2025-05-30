import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Dashboard Volontariato", layout="wide")
st.title("🏛️ Dashboard Attività Associazione di Volontariato")

# --- Upload file ---
turni_file = st.file_uploader("📄 Carica il file dei Turni", type=["xlsx"])
servizi_file = st.file_uploader("📄 Carica il file dei Servizi", type=["xlsx"])

if turni_file and servizi_file:
    df_turni = pd.read_excel(turni_file)
    df_servizi = pd.read_excel(servizi_file)

    # --- Preprocessing Turni ---
    df_turni['Data'] = pd.to_datetime(df_turni['Data'], errors='coerce')

    df_turni['Inizio'] = df_turni.apply(
        lambda row: datetime.combine(row['Data'].date(), row['Inizio']) if pd.notnull(row['Inizio']) else pd.NaT,
        axis=1
    )
    df_turni['Fine'] = df_turni.apply(
        lambda row: datetime.combine(row['Data'].date(), row['Fine']) if pd.notnull(row['Fine']) else pd.NaT,
        axis=1
    )
    df_turni['Durata (h)'] = (df_turni['Fine'] - df_turni['Inizio']).dt.total_seconds() / 3600
    df_turni['Categoria Pulita'] = df_turni['Categoria'].str.extract(r"\[(.*?)\]")

    # --- Preprocessing Servizi ---
    df_servizi['Data'] = pd.to_datetime(df_servizi['Data'], errors='coerce')

    df_servizi['[P]Ore'] = df_servizi.apply(
        lambda row: datetime.combine(row['Data'].date(), row['[P]Ore']) if pd.notnull(row['[P]Ore']) else pd.NaT,
        axis=1
    )
    df_servizi['[A]Ore'] = df_servizi.apply(
        lambda row: datetime.combine(row['Data'].date(), row['[A]Ore']) if pd.notnull(row['[A]Ore']) else pd.NaT,
        axis=1
    )
    df_servizi['Durata (min)'] = (df_servizi['[A]Ore'] - df_servizi['[P]Ore']).dt.total_seconds() / 60
    df_servizi['Categoria Servizio'] = df_servizi['Intervento'].str.extract(r"\[(.*?)\]")

    # --- Filtri ---
    st.sidebar.header("🎛️ Filtri")

    min_data = min(df_turni['Inizio'].min(), df_servizi['[P]Ore'].min())
    max_data = max(df_turni['Fine'].max(), df_servizi['[A]Ore'].max())

    if pd.isnull(min_data) or pd.isnull(max_data):
        st.error("Errore nei dati di data/ora.")
        st.stop()

    data_range = st.sidebar.date_input("Intervallo Date", [min_data.date(), max_data.date()])
    tipi_servizio = st.sidebar.multiselect("Tipo Servizio", options=sorted(df_servizi['Categoria Servizio'].dropna().unique()))
    mezzi = st.sidebar.multiselect("Automezzo", options=sorted(df_servizi['Automezzo'].dropna().unique()))

    # --- Applica filtri ---
    df_servizi_filt = df_servizi.copy()
    df_turni_filt = df_turni.copy()

    df_servizi_filt = df_servizi_filt[
        (df_servizi_filt['[P]Ore'].dt.date >= data_range[0]) &
        (df_servizi_filt['[P]Ore'].dt.date <= data_range[1])
    ]
    df_turni_filt = df_turni_filt[
        (df_turni_filt['Inizio'].dt.date >= data_range[0]) &
        (df_turni_filt['Inizio'].dt.date <= data_range[1])
    ]

    if tipi_servizio:
        df_servizi_filt = df_servizi_filt[df_servizi_filt['Categoria Servizio'].isin(tipi_servizio)]
    if mezzi:
        df_servizi_filt = df_servizi_filt[df_servizi_filt['Automezzo'].isin(mezzi)]

    # --- KPI ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("⏰ Turni Totali", len(df_turni_filt))
    col2.metric("⏳ Ore di Turno", f"{df_turni_filt['Durata (h)'].sum():.1f} h")
    col3.metric("✅ Servizi Svolti", len(df_servizi_filt))
    col4.metric("🚗 Km Totali", int(df_servizi_filt['Km effet.'].sum()))

    # --- Grafici ---
    st.subheader("📊 Distribuzione per Categoria")
    col5, col6 = st.columns(2)
    with col5:
        st.bar_chart(df_turni_filt['Categoria Pulita'].value_counts())
    with col6:
        st.bar_chart(df_servizi_filt['Categoria Servizio'].value_counts())

    st.subheader("📆 Servizi per Giorno della Settimana")
    if 'GG' in df_servizi_filt.columns:
        giorni = ["LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"]
        st.bar_chart(df_servizi_filt['GG'].value_counts().reindex(giorni).fillna(0))
    else:
        st.info("Colonna 'GG' non presente nei dati.")
else:
    st.info("🔽 Carica entrambi i file Excel per visualizzare la dashboard.")
