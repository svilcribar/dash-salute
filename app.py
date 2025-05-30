import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Dashboard Volontariato", layout="wide")
st.title("\U0001F6E0\ufe0f Dashboard Attivita Associazione di Volontariato")

# --- Upload file ---
turni_file = st.file_uploader("Carica il file dei Turni", type=["xlsx"])
servizi_file = st.file_uploader("Carica il file dei Servizi", type=["xlsx"])

def normalizza_orario(orario):
    if pd.isna(orario):
        return None
    try:
        orario = str(orario).replace(',', '.').strip()
        if ':' in orario:
            return orario
        elif '.' in orario:
            ore, minuti = orario.split('.')
            return f"{int(ore):02d}:{int(float('0.' + minuti) * 60):02d}"
        else:
            return f"{int(orario):02d}:00"
    except Exception:
        return None

if turni_file and servizi_file:
    df_turni = pd.read_excel(turni_file)
    df_servizi = pd.read_excel(servizi_file)

    # Mostra dati iniziali per debug
    st.subheader("Controllo qualità dati")
    st.write("Esempi dal file TURNI:")
    st.dataframe(df_turni.head())
    st.write("Esempi dal file SERVIZI:")
    st.dataframe(df_servizi.head())

    # Preprocessing TURNI
    df_turni['Data'] = pd.to_datetime(df_turni['Data'], errors='coerce')
    df_turni['Inizio_str'] = df_turni['Inizio'].apply(normalizza_orario)
    df_turni['Fine_str'] = df_turni['Fine'].apply(normalizza_orario)
    df_turni['Inizio'] = pd.to_datetime(df_turni['Data'].astype(str) + ' ' + df_turni['Inizio_str'], errors='coerce')
    df_turni['Fine'] = pd.to_datetime(df_turni['Data'].astype(str) + ' ' + df_turni['Fine_str'], errors='coerce')
    df_turni['Durata (h)'] = (df_turni['Fine'] - df_turni['Inizio']).dt.total_seconds() / 3600
    df_turni['Categoria Pulita'] = df_turni['Categoria'].str.extract(r"\[(.*?)\]")

    if df_turni['Inizio'].isnull().any():
        st.warning("⚠️ Alcune righe dei turni hanno problemi di orario. Controlla i valori in 'Inizio'.")

    # Preprocessing SERVIZI
    df_servizi['Data'] = pd.to_datetime(df_servizi['Data'], errors='coerce')
    df_servizi['P_str'] = df_servizi['[P]Ore'].apply(normalizza_orario)
    df_servizi['A_str'] = df_servizi['[A]Ore'].apply(normalizza_orario)
    df_servizi['[P]Ore'] = pd.to_datetime(df_servizi['Data'].astype(str) + ' ' + df_servizi['P_str'], errors='coerce')
    df_servizi['[A]Ore'] = pd.to_datetime(df_servizi['Data'].astype(str) + ' ' + df_servizi['A_str'], errors='coerce')
    df_servizi['Durata (min)'] = (df_servizi['[A]Ore'] - df_servizi['[P]Ore']).dt.total_seconds() / 60
    df_servizi['Categoria Servizio'] = df_servizi['Intervento'].str.extract(r"\[(.*?)\]")

    if df_servizi['[P]Ore'].isnull().any():
        st.warning("⚠️ Alcuni orari di partenza non sono validi. Controlla '[P]Ore'.")
    if df_servizi['[A]Ore'].isnull().any():
        st.warning("⚠️ Alcuni orari di arrivo non sono validi. Controlla '[A]Ore'.")

    # Filtri
    st.sidebar.header("\U0001F50D Filtri")
    min_data = min(df_turni['Inizio'].min(), df_servizi['[P]Ore'].min())
    max_data = max(df_turni['Fine'].max(), df_servizi['[A]Ore'].max())
    data_range = st.sidebar.date_input("Intervallo Date", [min_data.date(), max_data.date()])

    tipi_servizio = st.sidebar.multiselect("Tipo Servizio", options=sorted(df_servizi['Categoria Servizio'].dropna().unique()))
    mezzi = st.sidebar.multiselect("Automezzo", options=sorted(df_servizi['Automezzo'].dropna().unique()))

    # Applica filtri
    df_turni_filt = df_turni[(df_turni['Inizio'].dt.date >= data_range[0]) & (df_turni['Inizio'].dt.date <= data_range[1])]
    df_servizi_filt = df_servizi[(df_servizi['[P]Ore'].dt.date >= data_range[0]) & (df_servizi['[P]Ore'].dt.date <= data_range[1])]

    if tipi_servizio:
        df_servizi_filt = df_servizi_filt[df_servizi_filt['Categoria Servizio'].isin(tipi_servizio)]
    if mezzi:
        df_servizi_filt = df_servizi_filt[df_servizi_filt['Automezzo'].isin(mezzi)]

    # KPI
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("\u23f0 Turni Totali", len(df_turni_filt))
    col2.metric("\u231b Ore di Turno", f"{df_turni_filt['Durata (h)'].sum():.1f} h")
    col3.metric("\u2705 Servizi Svolti", len(df_servizi_filt))
    col4.metric("\ud83d\ude97 Km Totali", int(df_servizi_filt['Km effet.'].sum()))

    # Grafici
    st.subheader("\U0001F4C8 Distribuzione per Categoria")
    col5, col6 = st.columns(2)
    col5.bar_chart(df_turni_filt['Categoria Pulita'].value_counts())
    col6.bar_chart(df_servizi_filt['Categoria Servizio'].value_counts())

    st.subheader("\U0001F4C5 Servizi per Giorno della Settimana")
    if 'GG' in df_servizi_filt.columns:
        st.bar_chart(df_servizi_filt['GG'].value_counts().reindex(["LUN","MAR","MER","GIO","VEN","SAB","DOM"]))
else:
    st.info("Carica entrambi i file per iniziare.")
