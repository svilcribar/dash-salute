# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# --- Configurazione Streamlit ---
st.set_page_config(page_title="Dashboard Servizi & Turni", layout="wide")
st.title("🚑 Dashboard Servizi & Turni")

# --- URL dei dati ---
URL_SERVIZI = "https://docs.google.com/spreadsheets/d/1lBUcDna2q8tnSBESFHBGLMLRtg3MSp0yCY3eheDvPoU/export?format=csv"
URL_TURNI = "https://docs.google.com/spreadsheets/d/1gnbV3CsLLcPoUzBqqntFJmWyTO-zx7NUCLJy0ThuH9A/export?format=csv"

# --- Caricamento Dati ---
@st.cache_data
def carica_dati():
    df_servizi = pd.read_csv(URL_SERVIZI)
    df_turni = pd.read_csv(URL_TURNI)
    return df_servizi, df_turni

df_servizi, df_turni = carica_dati()

# --- Preprocessing Servizi ---
df_servizi['[P]Ore'] = pd.to_datetime(df_servizi['[P]Ore'], errors='coerce')
df_servizi['[A]Ore'] = pd.to_datetime(df_servizi['[A]Ore'], errors='coerce')
df_servizi['GG'] = pd.to_datetime(df_servizi['GG'], errors='coerce')
df_servizi['Durata'] = (df_servizi['[A]Ore'] - df_servizi['[P]Ore']).dt.total_seconds() / 60
df_servizi['Intervento Tipo'] = df_servizi['Intervento'].str.extract(r'\[([^\]]+)\]')

# --- Preprocessing Turni ---
df_turni['Inizio'] = pd.to_datetime(df_turni['Inizio'], errors='coerce')
df_turni['Fine'] = pd.to_datetime(df_turni['Fine'], errors='coerce')
df_turni['Data'] = pd.to_datetime(df_turni['Inizio'].dt.date, errors='coerce')
df_turni['Durata'] = (df_turni['Fine'] - df_turni['Inizio']).dt.total_seconds() / 3600
df_turni['Categoria Pulita'] = df_turni['Categoria'].str.extract(r'\[([^\]]+)\]')

# --- Filtri Intervallo Date ---
min_data = max(df_turni['Data'].min(), df_servizi['GG'].min())
max_data = min(df_turni['Data'].max(), df_servizi['GG'].max())
data_range = st.sidebar.date_input("📅 Intervallo Date", [min_data, max_data], min_value=min_data, max_value=max_data)

if len(data_range) == 2:
    start_date, end_date = data_range
    df_turni = df_turni[(df_turni['Data'] >= start_date) & (df_turni['Data'] <= end_date)]
    df_servizi = df_servizi[(df_servizi['GG'] >= start_date) & (df_servizi['GG'] <= end_date)]

# --- KPI Turni ---
st.header("🔁 KPI Turni")
tot_turni = len(df_turni)
tot_ore_turni = df_turni['Durata'].sum()
media_ore_turno = df_turni['Durata'].mean()
durata_giorni = (end_date - start_date).days + 1
media_turni_giorno = tot_turni / durata_giorni

col1, col2, col3, col4 = st.columns(4)
col1.metric("Totale Turni", tot_turni)
col2.metric("Ore Totali Turni", f"{tot_ore_turni:.1f}")
col3.metric("Media Ore per Turno", f"{media_ore_turno:.2f}")
col4.metric("Media Turni per Giorno", f"{media_turni_giorno:.2f}")

# --- Grafico ore per categoria ---
turni_cat = df_turni.groupby('Categoria Pulita')['Durata'].sum().sort_values(ascending=False)
fig_cat = px.bar(turni_cat.reset_index(), x='Categoria Pulita', y='Durata', title='Ore totali per categoria (turni)', labels={'Durata': 'Ore'})
st.plotly_chart(fig_cat, use_container_width=True)

# --- KPI Servizi ---
st.header("🚑 KPI Servizi")
tot_servizi = len(df_servizi)
tot_km = df_servizi['Km effet.'].sum()
media_km_serv = df_servizi['Km effet.'].mean()
media_durata = df_servizi['Durata'].mean()
media_servizi_giorno = tot_servizi / durata_giorni

col1, col2, col3, col4 = st.columns(4)
col1.metric("Totale Servizi", tot_servizi)
col2.metric("Km Totali", f"{tot_km:.1f}")
col3.metric("Media Km per Servizio", f"{media_km_serv:.1f}")
col4.metric("Media Servizi per Giorno", f"{media_servizi_giorno:.2f}")

# --- Grafico servizi per giorno settimana ---
giorni = df_servizi['GG'].dt.day_name()
fig_giorni = px.histogram(df_servizi, x=giorni, title="Distribuzione Servizi per Giorno della Settimana")
st.plotly_chart(fig_giorni, use_container_width=True)

# --- KPI Correlati Turni / Servizi ---
if durata_giorni <= 31:
    st.header("🔄 KPI Correlati Turni / Servizi")

    # Servizi per giorno
    servizi_giorno = df_servizi.groupby(df_servizi['GG'].dt.date).size()
    turni_giorno = df_turni.groupby(df_turni['Data'].dt.date).size()
    correlati = pd.concat([servizi_giorno, turni_giorno], axis=1)
    correlati.columns = ['Servizi', 'Turni']
    correlati.fillna(0, inplace=True)
    correlati['Rapporto'] = correlati['Servizi'] / correlati['Turni']

    fig_corr = px.line(correlati, y=['Servizi', 'Turni', 'Rapporto'], title="Rapporto Servizi / Turni per Giorno")
    st.plotly_chart(fig_corr, use_container_width=True)

# --- Fine ---
st.success("Dashboard generata con successo ✅")
