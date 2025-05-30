import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Dashboard CRI")

# --- URL dei file ---
URL_TURNI = "https://docs.google.com/spreadsheets/d/1gnbV3CsLLcPoUzBqqntFJmWyTO-zx7NUCLJy0ThuH9A/export?format=csv"
URL_SERVIZI = "https://docs.google.com/spreadsheets/d/1lBUcDna2q8tnSBESFHBGLMLRtg3MSp0yCY3eheDvPoU/export?format=csv"

@st.cache_data
def load_data():
    df_turni = pd.read_csv(URL_TURNI)
    df_servizi = pd.read_csv(URL_SERVIZI)

    # --- Pulizia Turni ---
    df_turni['Inizio'] = pd.to_datetime(df_turni['Inizio'], errors='coerce')
    df_turni['Fine'] = pd.to_datetime(df_turni['Fine'], errors='coerce')
    df_turni = df_turni.dropna(subset=['Inizio', 'Fine'])

    # Estrai categoria da parentesi quadre
    df_turni['Categoria Pulita'] = df_turni['Categoria'].str.extract(r'\[([^\]]+)\]')

    # Calcola durata in ore
    df_turni['Durata'] = (df_turni['Fine'] - df_turni['Inizio']).dt.total_seconds() / 3600

    # --- Pulizia Servizi ---
    df_servizi['[P]Ore'] = pd.to_datetime(df_servizi['[P]Ore'], format='%H:%M', errors='coerce')
    df_servizi['[A]Ore'] = pd.to_datetime(df_servizi['[A]Ore'], format='%H:%M', errors='coerce')
    df_servizi['Data'] = pd.to_datetime(df_servizi['Data'], errors='coerce')
    df_servizi = df_servizi.dropna(subset=['[P]Ore', '[A]Ore', 'Data'])

    # Calcolo durata in minuti
    df_servizi['Durata Minuti'] = (df_servizi['[A]Ore'] - df_servizi['[P]Ore']).dt.total_seconds() / 60
    df_servizi['Durata Minuti'] = df_servizi['Durata Minuti'].apply(lambda x: x if x > 0 else x + 1440)

    return df_turni, df_servizi

df_turni, df_servizi = load_data()

# --- Intervallo temporale ---
min_data = min(df_turni['Inizio'].min(), df_servizi['Data'].min())
max_data = max(df_turni['Fine'].max(), df_servizi['Data'].max())

date_range = st.sidebar.date_input("Seleziona intervallo date", [min_data.date(), max_data.date()])
if len(date_range) != 2:
    st.error("Seleziona un intervallo valido.")
    st.stop()

start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

# --- Filtri ---
df_turni_filt = df_turni[(df_turni['Inizio'] >= start_date) & (df_turni['Fine'] <= end_date)]
df_servizi_filt = df_servizi[(df_servizi['Data'] >= start_date) & (df_servizi['Data'] <= end_date)]

# --- KPI Turni ---
st.header("🔁 KPI Turni")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Totale turni", len(df_turni_filt))
col2.metric("Ore totali", round(df_turni_filt['Durata'].sum(), 1))
col3.metric("Media ore/turno", round(df_turni_filt['Durata'].mean(), 2))
col4.metric("Turni per giorno", round(len(df_turni_filt) / (end_date - start_date).days, 2))

# --- Grafico turni per categoria ---
turni_cat = df_turni_filt.groupby('Categoria Pulita')['Durata'].sum().sort_values(ascending=False)
st.subheader("📊 Ore totali per categoria (turni)")
st.bar_chart(turni_cat)

# --- KPI Servizi ---
st.header("🚑 KPI Servizi")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Totale servizi", len(df_servizi_filt))
col2.metric("Durata media (min)", round(df_servizi_filt['Durata Minuti'].mean(), 1))
col3.metric("Km totali", round(df_servizi_filt['Km effet.'].sum(), 1))
col4.metric("Media km/servizio", round(df_servizi_filt['Km effet.'].mean(), 1))

# --- Distribuzione per giorno ---
st.subheader("📅 Distribuzione servizi per giorno della settimana")
giorni = df_servizi_filt['Data'].dt.day_name().value_counts()
st.bar_chart(giorni)

# --- Servizi per categoria (estratta da Intervento) ---
df_servizi_filt['Categoria Servizio'] = df_servizi_filt['Intervento'].str.extract(r'\[([^\]]+)\]')
servizi_cat = df_servizi_filt['Categoria Servizio'].value_counts()
st.subheader("🏷️ Servizi per categoria (Intervento)")
st.bar_chart(servizi_cat)

# --- Interni vs Esterni ---
interni = df_servizi_filt['Categoria Servizio'].str.upper().eq("INTERNI").sum()
esterni = len(df_servizi_filt) - interni
st.metric("Interni vs Esterni", f"{interni} / {esterni}")

# --- Analisi veicoli ---
mezzi = df_servizi_filt['Automezzo'].value_counts()
st.subheader("🚐 Utilizzo mezzi (servizi)")
st.bar_chart(mezzi)

# --- KPI Correlati Turni / Servizi (solo se <= 31 giorni) ---
if (end_date - start_date).days <= 31:
    st.header("🔄 KPI Correlati Turni/Servizi (per giorni)")

    # Turni per giorno
    turni_per_giorno = df_turni_filt.groupby(df_turni_filt['Inizio'].dt.date)['Durata'].sum()

    # Servizi per giorno
    servizi_per_giorno = df_servizi_filt.groupby(df_servizi_filt['Data'].dt.date)['Durata Minuti'].count()

    df_corr = pd.DataFrame({
        'Turni (h)': turni_per_giorno,
        'Servizi (n)': servizi_per_giorno
    }).fillna(0)

    st.line_chart(df_corr)
