import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- Configurazione pagina ---
st.set_page_config(page_title="Dashboard CRI", layout="wide")

# --- URL dei Google Sheets ---
URL_TURNI = "https://docs.google.com/spreadsheets/d/1gnbV3CsLLcPoUzBqqntFJmWyTO-zx7NUCLJy0ThuH9A/export?format=csv"
URL_SERVIZI = "https://docs.google.com/spreadsheets/d/1lBUcDna2q8tnSBESFHBGLMLRtg3MSp0yCY3eheDvPoU/export?format=csv"

# --- Caricamento dati ---
@st.cache_data
def carica_dati():
    df_turni = pd.read_csv(URL_TURNI)
    df_servizi = pd.read_csv(URL_SERVIZI)

    # Parse orari nei turni
    df_turni['Inizio'] = pd.to_datetime(df_turni['Inizio'], format="%H:%M", errors='coerce')
    df_turni['Fine'] = pd.to_datetime(df_turni['Fine'], format="%H:%M", errors='coerce')
    df_turni['Data'] = pd.to_datetime(df_turni['Data'], errors='coerce')

    # Calcolo durata
    df_turni['Ore'] = (df_turni['Fine'] - df_turni['Inizio']).dt.total_seconds() / 3600

    # Parse servizi
    df_servizi['[P]Ore'] = pd.to_datetime(df_servizi['[P]Ore'], format="%H:%M", errors='coerce')
    df_servizi['[A]Ore'] = pd.to_datetime(df_servizi['[A]Ore'], format="%H:%M", errors='coerce')
    df_servizi['Tempo'] = (df_servizi['[A]Ore'] - df_servizi['[P]Ore']).dt.total_seconds() / 60
    df_servizi['GG'] = df_servizi['GG'].astype(str).str.strip()
    
    return df_turni, df_servizi

df_turni, df_servizi = carica_dati()

# --- Filtro periodo ---
min_data = df_turni['Data'].min()
max_data = df_turni['Data'].max()

intervallo = st.sidebar.date_input("Intervallo date", [min_data, max_data])
if len(intervallo) == 2:
    start_date, end_date = intervallo
    df_turni = df_turni[(df_turni['Data'] >= pd.to_datetime(start_date)) & (df_turni['Data'] <= pd.to_datetime(end_date))]
    # supponiamo che non abbiamo la data nei servizi, quindi non filtriamo quelli

# --- KPI Turni ---
with st.expander("🔁 KPI Turni", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Totale turni", len(df_turni))
    col2.metric("Ore totali", f"{df_turni['Ore'].sum():.1f}")
    col3.metric("Ore medie/turno", f"{df_turni['Ore'].mean():.2f}")
    giorni_turni = df_turni['Data'].nunique()
    col4.metric("Turni/giorno", f"{len(df_turni)/giorni_turni:.2f}" if giorni_turni else "0")

    st.bar_chart(df_turni.groupby('Categoria')['Ore'].sum())

# --- KPI Servizi ---
with st.expander("🚑 KPI Servizi", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Totale servizi", len(df_servizi))
    col2.metric("Tempo medio (min)", f"{df_servizi['Tempo'].mean():.1f}")
    col3.metric("Km totali", f"{df_servizi['Km effet.'].sum():.1f}")
    col4.metric("Km medi/servizio", f"{df_servizi['Km effet.'].mean():.1f}")

    st.bar_chart(df_servizi['Intervento'].value_counts())

    st.subheader("Distribuzione settimanale")
    st.bar_chart(df_servizi['GG'].value_counts())

    st.subheader("Uso automezzi")
    st.bar_chart(df_servizi['Automezzo'].value_counts())

# --- KPI Correlati Turni / Servizi ---
with st.expander("🔄 KPI Correlati", expanded=True):
    servizi_per_giorno = df_servizi.groupby('GG').size().mean()
    turni_per_giorno = df_turni.groupby(df_turni['Data'].dt.dayofweek).size().mean()
    st.metric("Stima servizi/turno per giorno", f"{servizi_per_giorno / turni_per_giorno:.2f}" if turni_per_giorno else "N/A")

    # Percentuale servizi che cadono dentro a qualche turno (solo per match data e ora)
    df_servizi_valide = df_servizi.dropna(subset=['[P]Ore'])
    servizi_coperti = 0

    for _, srv in df_servizi_valide.iterrows():
        giorno = srv['GG'].upper()
        try:
            # match giorno con df_turni
            turni_gg = df_turni[df_turni['Data'].dt.strftime("%a").str.upper().str.startswith(giorno[:3])]
            for _, turno in turni_gg.iterrows():
                if pd.notnull(turno['Inizio']) and pd.notnull(turno['Fine']):
                    if turno['Inizio'].time() <= srv['[P]Ore'].time() <= turno['Fine'].time():
                        servizi_coperti += 1
                        break
        except:
            continue

    copertura_perc = servizi_coperti / len(df_servizi_valide) * 100 if len(df_servizi_valide) > 0 else 0
    st.metric("Copertura servizi su turni (approssimata)", f"{copertura_perc:.1f}%")

# --- Footer ---
st.markdown("---")
st.caption("🚑 Dashboard CRI · Powered by Streamlit")

