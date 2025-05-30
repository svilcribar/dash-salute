import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np

# --- CONFIG ---
st.set_page_config(page_title="Dashboard KPI", layout="wide")

# --- FUNZIONI ---
@st.cache_data

def carica_dati():
    URL_SERVIZI = "https://docs.google.com/spreadsheets/d/1lBUcDna2q8tnSBESFHBGLMLRtg3MSp0yCY3eheDvPoU/export?format=csv"
    URL_TURNI = "https://docs.google.com/spreadsheets/d/1gnbV3CsLLcPoUzBqqntFJmWyTO-zx7NUCLJy0ThuH9A/export?format=csv"

    df_serv = pd.read_csv(URL_SERVIZI)
    df_turni = pd.read_csv(URL_TURNI)

    df_serv['Data'] = pd.to_datetime(df_serv['Data'], errors='coerce')
    df_turni['Data'] = pd.to_datetime(df_turni['Data'], errors='coerce')

    df_turni['Inizio'] = pd.to_datetime(df_turni['Inizio'], errors='coerce').dt.time
    df_turni['Fine'] = pd.to_datetime(df_turni['Fine'], errors='coerce').dt.time
    df_turni = df_turni.dropna(subset=['Inizio', 'Fine'])

    # Calcolo durata in ore per i turni
    df_turni['Durata'] = df_turni.apply(lambda row: (
        datetime.combine(datetime.today(), row['Fine']) - datetime.combine(datetime.today(), row['Inizio'])).seconds / 3600, axis=1)

    # Calcolo durata servizio in ore
    df_serv['[P]Ore'] = pd.to_datetime(df_serv['[P]Ore'], errors='coerce')
    df_serv['[A]Ore'] = pd.to_datetime(df_serv['[A]Ore'], errors='coerce')
    df_serv['Durata_serv'] = (df_serv['[A]Ore'] - df_serv['[P]Ore']).dt.total_seconds() / 3600

    return df_serv, df_turni

def extract_categoria(turno_str):
    import re
    match = re.search(r'\[(.*?)\]', str(turno_str))
    return match.group(1) if match else 'ALTRO'

# --- CARICAMENTO DATI ---
df_serv, df_turni = carica_dati()
df_turni['Categoria'] = df_turni['Turno'].apply(extract_categoria)

# --- SIDEBAR FILTRI ---
with st.sidebar:
    st.title("Filtri")
    data_min = max(df_serv['Data'].min(), df_turni['Data'].min())
    data_max = min(df_serv['Data'].max(), df_turni['Data'].max())
    start_date, end_date = st.date_input("Intervallo date", [data_min, data_max])

# --- FILTRAGGIO DATI ---
df_serv_f = df_serv[(df_serv['Data'] >= pd.to_datetime(start_date)) & (df_serv['Data'] <= pd.to_datetime(end_date))]
df_turni_f = df_turni[(df_turni['Data'] >= pd.to_datetime(start_date)) & (df_turni['Data'] <= pd.to_datetime(end_date))]

# --- KPI TURNI ---
st.header("\U0001F501 KPI sui Turni")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Totale Turni", len(df_turni_f))
col2.metric("Ore Totali Disponibili", round(df_turni_f['Durata'].sum(), 1))
col3.metric("Media Ore per Turno", round(df_turni_f['Durata'].mean(), 2))
col4.metric("Media Turni per Giorno", round(len(df_turni_f) / (end_date - start_date).days, 2))

# --- GRAFICO TURNI PER CATEGORIA ---
kpi_turni_cat = df_turni_f.groupby('Categoria')['Durata'].sum().reset_index()
kpi_turni_cat = kpi_turni_cat.sort_values(by='Durata', ascending=False)

fig_turni = px.bar(kpi_turni_cat, x='Categoria', y='Durata', title="Ore Turno per Categoria", text_auto=True)
st.plotly_chart(fig_turni, use_container_width=True)

# --- KPI SERVIZI ---
st.header("\U0001F691 KPI sui Servizi")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Totale Servizi", len(df_serv_f))
col2.metric("Media Durata Servizio (h)", round(df_serv_f['Durata_serv'].mean(), 2))
col3.metric("Km Totali", int(df_serv_f['Km effet.'].sum()))
col4.metric("Media Km/Servizio", round(df_serv_f['Km effet.'].mean(), 1))

# --- GRAFICO SERVIZI PER GIORNO ---
df_serv_f['Giorno'] = df_serv_f['Data'].dt.day_name(locale='it_IT')
giorni = pd.CategoricalDtype(
    ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica'], ordered=True)
df_serv_f['Giorno'] = df_serv_f['Giorno'].astype(giorni)

fig_giorni = px.histogram(df_serv_f, x='Giorno', title="Distribuzione Servizi per Giorno")
st.plotly_chart(fig_giorni, use_container_width=True)

# --- KPI CORRELATI (SOLO SE <= 31 GIORNI) ---
if (end_date - start_date).days <= 31:
    st.header("\U0001F501 KPI Correlati Turni/Servizi")
    servizi_per_giorno = df_serv_f.groupby('Data').size()
    turni_per_giorno = df_turni_f.groupby('Data').size()
    kpi_corr = pd.DataFrame({
        'Servizi': servizi_per_giorno,
        'Turni': turni_per_giorno
    }).fillna(0)
    kpi_corr['Servizi/Turno'] = kpi_corr['Servizi'] / kpi_corr['Turni'].replace(0, np.nan)

    st.line_chart(kpi_corr[['Servizi', 'Turni']])
    st.bar_chart(kpi_corr['Servizi/Turno'])
