import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dashboard Volontariato", layout="wide")
st.title("📊 Dashboard Attività Associazione di Volontariato")

# --- Link ai Google Sheets (in formato CSV) ---
URL_SERVIZI = "https://docs.google.com/spreadsheets/d/1lBUcDna2q8tnSBESFHBGLMLRtg3MSp0yCY3eheDvPoU/export?format=csv"
URL_TURNI = "https://docs.google.com/spreadsheets/d/1gnbV3CsLLcPoUzBqqntFJmWyTO-zx7NUCLJy0ThuH9A/export?format=csv"

# --- Caricamento dei dati ---
try:
    df_turni = pd.read_csv(URL_TURNI)
    df_servizi = pd.read_csv(URL_SERVIZI)
except Exception as e:
    st.error("❌ Errore durante il caricamento dei dati dai Google Sheets.")
    st.stop()

# --- Preprocessing TURNI ---
df_turni['Data'] = pd.to_datetime(df_turni['Data'], errors='coerce')

# Pulizia orari
df_turni['Inizio_str'] = df_turni['Inizio'].astype(str).str.strip()
df_turni['Fine_str'] = df_turni['Fine'].astype(str).str.strip()

# Forzatura formato HH:MM se solo ore (es. "8" → "8:00")
df_turni['Inizio_str'] = df_turni['Inizio_str'].str.replace(r'^(\d{1,2})(\.\d+)?$', r'\1:00', regex=True)
df_turni['Fine_str'] = df_turni['Fine_str'].str.replace(r'^(\d{1,2})(\.\d+)?$', r'\1:00', regex=True)

# Parsing
df_turni['Inizio'] = pd.to_datetime(df_turni['Data'].astype(str) + ' ' + df_turni['Inizio_str'], errors='coerce')
df_turni['Fine'] = pd.to_datetime(df_turni['Data'].astype(str) + ' ' + df_turni['Fine_str'], errors='coerce')
df_turni['Durata (h)'] = (df_turni['Fine'] - df_turni['Inizio']).dt.total_seconds() / 3600

# Categoria pulita (se formato "[xxx]")
df_turni['Categoria Pulita'] = df_turni['Categoria'].str.extract(r"\[(.*?)\]")

# Righe con problemi di parsing in 'Inizio' o 'Fine'
righe_turni_non_valide = df_turni[df_turni['Inizio'].isnull() | df_turni['Fine'].isnull()]
if not righe_turni_non_valide.empty:
    st.warning("⚠️ Alcune righe dei turni hanno problemi di orario. Controlla i valori in 'Inizio' e 'Fine'.")
    st.dataframe(righe_turni_non_valide)

# --- Preprocessing SERVIZI ---
df_servizi['Data'] = pd.to_datetime(df_servizi['Data'], errors='coerce')

# Pulizia orari
df_servizi['[P]Ore_str'] = df_servizi['[P]Ore'].astype(str).str.strip()
df_servizi['[A]Ore_str'] = df_servizi['[A]Ore'].astype(str).str.strip()

df_servizi['[P]Ore_str'] = df_servizi['[P]Ore_str'].str.replace(r'^(\d{1,2})(\.\d+)?$', r'\1:00', regex=True)
df_servizi['[A]Ore_str'] = df_servizi['[A]Ore_str'].str.replace(r'^(\d{1,2})(\.\d+)?$', r'\1:00', regex=True)

df_servizi['[P]Ore'] = pd.to_datetime(df_servizi['Data'].astype(str) + ' ' + df_servizi['[P]Ore_str'], errors='coerce')
df_servizi['[A]Ore'] = pd.to_datetime(df_servizi['Data'].astype(str) + ' ' + df_servizi['[A]Ore_str'], errors='coerce')

df_servizi['Durata (min)'] = (df_servizi['[A]Ore'] - df_servizi['[P]Ore']).dt.total_seconds() / 60
df_servizi['Categoria Servizio'] = df_servizi['Intervento'].str.extract(r"\[(.*?)\]")

# Righe con problemi in orario partenza
righe_partenza_non_valide = df_servizi[df_servizi['[P]Ore'].isnull()]
if not righe_partenza_non_valide.empty:
    st.warning("⚠️ Alcuni orari di partenza non sono validi. Controlla '[P]Ore'.")
    st.dataframe(righe_partenza_non_valide)

# Righe con problemi in orario arrivo
righe_arrivo_non_valide = df_servizi[df_servizi['[A]Ore'].isnull()]
if not righe_arrivo_non_valide.empty:
    st.warning("⚠️ Alcuni orari di arrivo non sono validi. Controlla '[A]Ore'.")
    st.dataframe(righe_arrivo_non_valide)

# --- Filtri ---
st.sidebar.header("🔍 Filtri")

min_data = pd.to_datetime(
    min(df_turni['Inizio'].min(), df_servizi['[P]Ore'].min()), errors='coerce'
)
max_data = pd.to_datetime(
    max(df_turni['Fine'].max(), df_servizi['[A]Ore'].max()), errors='coerce'
)

if pd.isnull(min_data) or pd.isnull(max_data):
    st.error("❌ Errore nei dati di data/ora. Alcuni campi non sono interpretabili.")
    st.stop()

data_range = st.sidebar.date_input("Intervallo Date", [min_data.date(), max_data.date()])
tipi_servizio = st.sidebar.multiselect(
    "Tipo Servizio", options=sorted(df_servizi['Categoria Servizio'].dropna().unique())
)
mezzi = st.sidebar.multiselect(
    "Automezzo", options=sorted(df_servizi['Automezzo'].dropna().unique())
)

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
col1.metric("🕒 Turni Totali", len(df_turni_filt))
col2.metric("⏳ Ore di Turno", f"{df_turni_filt['Durata (h)'].sum():.1f} h")
col3.metric("✅ Servizi Svolti", len(df_servizi_filt))
col4.metric("🚗 Km Totali", int(df_servizi_filt['Km effet.'].sum()))

# --- Grafici ---
st.subheader("📌 Distribuzione per Categoria")
col5, col6 = st.columns(2)

with col5:
    st.bar_chart(df_turni_filt['Categoria Pulita'].value_counts())

with col6:
    st.bar_chart(df_servizi_filt['Categoria Servizio'].value_counts())

st.subheader("📅 Servizi per Giorno della Settimana")
if 'GG' in df_servizi_filt.columns:
    st.bar_chart(df_servizi_filt['GG'].value_counts().reindex(["LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"]))
else:
    st.info("Colonna 'GG' non presente nel file SERVIZI.")

