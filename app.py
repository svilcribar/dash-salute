import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# === URL Google Sheets ===
URL_SERVIZI = "https://docs.google.com/spreadsheets/d/1lBUcDna2q8tnSBESFHBGLMLRtg3MSp0yCY3eheDvPoU/export?format=csv"
URL_TURNI = "https://docs.google.com/spreadsheets/d/1gnbV3CsLLcPoUzBqqntFJmWyTO-zx7NUCLJy0ThuH9A/export?format=csv"

# === Funzioni di parsing sicuro ===
def parse_ora(ora):
    try:
        return datetime.strptime(ora.strip(), "%H:%M").time()
    except:
        return None

def parse_data(data):
    try:
        return pd.to_datetime(data, dayfirst=True)
    except:
        return pd.NaT

# === Caricamento dati ===
@st.cache_data
def load_data():
    df_turni = pd.read_csv(URL_TURNI)
    df_servizi = pd.read_csv(URL_SERVIZI)

    # Parse dati e orari nei turni
    df_turni['Data'] = df_turni['Data'].apply(parse_data)
    df_turni['Inizio'] = df_turni['Inizio'].astype(str).apply(parse_ora)
    df_turni['Fine'] = df_turni['Fine'].astype(str).apply(parse_ora)
    df_turni = df_turni.dropna(subset=['Data', 'Inizio', 'Fine'])
    df_turni['Start'] = df_turni.apply(lambda row: datetime.combine(row['Data'], row['Inizio']), axis=1)
    df_turni['End'] = df_turni.apply(lambda row: datetime.combine(row['Data'], row['Fine']) if row['Fine'] > row['Inizio'] else datetime.combine(row['Data'], row['Fine']) + timedelta(days=1), axis=1)
    df_turni['Durata'] = (df_turni['End'] - df_turni['Start']).dt.total_seconds() / 3600

    # Parse dati nei servizi
    df_servizi['Data'] = df_servizi['Data'].apply(parse_data)
    df_servizi['[P]Ore'] = df_servizi['[P]Ore'].astype(str).apply(parse_ora)
    df_servizi['[A]Ore'] = df_servizi['[A]Ore'].astype(str).apply(parse_ora)
    df_servizi = df_servizi.dropna(subset=['Data', '[P]Ore', '[A]Ore'])
    df_servizi['Start'] = df_servizi.apply(lambda row: datetime.combine(row['Data'], row['[P]Ore']), axis=1)
    df_servizi['End'] = df_servizi.apply(lambda row: datetime.combine(row['Data'], row['[A]Ore']) if row['[A]Ore'] > row['[P]Ore'] else datetime.combine(row['Data'], row['[A]Ore']) + timedelta(days=1), axis=1)
    df_servizi['Durata'] = (df_servizi['End'] - df_servizi['Start']).dt.total_seconds() / 3600

    return df_turni, df_servizi

df_turni, df_servizi = load_data()

# === Intervallo di date ===
st.sidebar.title("🎛️ Filtri")
data_min = min(df_turni['Data'].min(), df_servizi['Data'].min())
data_max = max(df_turni['Data'].max(), df_servizi['Data'].max())
data_range = st.sidebar.date_input("Intervallo Date", [data_min, data_max])

# Filtro per data
if len(data_range) == 2:
    inizio, fine = data_range
    df_turni = df_turni[(df_turni['Data'] >= pd.to_datetime(inizio)) & (df_turni['Data'] <= pd.to_datetime(fine))]
    df_servizi = df_servizi[(df_servizi['Data'] >= pd.to_datetime(inizio)) & (df_servizi['Data'] <= pd.to_datetime(fine))]

# === KPI ===
st.title("📊 Dashboard KPI - CRI Servizi & Turni")

col1, col2, col3 = st.columns(3)
col1.metric("👥 Numero Turni", len(df_turni))
col2.metric("🚑 Numero Servizi", len(df_servizi))
col3.metric("🕒 Ore Totali", f"{df_turni['Durata'].sum() + df_servizi['Durata'].sum():.1f} h")

st.markdown("---")

# === Tabelle Dettaglio ===
with st.expander("📋 Dettaglio Turni"):
    st.dataframe(df_turni[['Data', 'Inizio', 'Fine', 'Durata']])

with st.expander("📋 Dettaglio Servizi"):
    st.dataframe(df_servizi[['Data', '[P]Ore', '[A]Ore', 'Durata']])
