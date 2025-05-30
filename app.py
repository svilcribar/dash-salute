import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# --- URL dei Google Sheets (in formato CSV) ---
URL_SERVIZI = "https://docs.google.com/spreadsheets/d/1lBUcDna2q8tnSBESFHBGLMLRtg3MSp0yCY3eheDvPoU/export?format=csv"
URL_TURNI = "https://docs.google.com/spreadsheets/d/1gnbV3CsLLcPoUzBqqntFJmWyTO-zx7NUCLJy0ThuH9A/export?format=csv"

# --- Funzioni di supporto ---
def parse_orario(value):
    try:
        return datetime.strptime(str(value).strip(), "%H:%M").time()
    except:
        return None

def parse_data(value):
    try:
        return pd.to_datetime(value).date()
    except:
        return None

# --- Caricamento dati ---
@st.cache_data

def carica_dati():
    df_turni = pd.read_csv(URL_TURNI)
    df_servizi = pd.read_csv(URL_SERVIZI)
    return df_turni, df_servizi

df_turni, df_servizi = carica_dati()

# --- Pulizia df_turni ---
df_turni['Inizio'] = df_turni['Inizio'].apply(parse_orario)
df_turni['Fine'] = df_turni['Fine'].apply(parse_orario)
df_turni['Data'] = df_turni['Data'].apply(parse_data)

df_turni['Inizio_completo'] = df_turni.apply(
    lambda row: datetime.combine(row['Data'], row['Inizio']) if pd.notnull(row['Data']) and pd.notnull(row['Inizio']) else pd.NaT,
    axis=1
)
df_turni['Fine_completo'] = df_turni.apply(
    lambda row: datetime.combine(row['Data'], row['Fine']) if pd.notnull(row['Data']) and pd.notnull(row['Fine']) else pd.NaT,
    axis=1
)
# Aggiusta fine oltre la mezzanotte
mask_fine_mezzanotte = df_turni['Fine_completo'] < df_turni['Inizio_completo']
df_turni.loc[mask_fine_mezzanotte, 'Fine_completo'] += timedelta(days=1)

# --- Pulizia df_servizi ---
df_servizi['[P]Ore'] = df_servizi['[P]Ore'].apply(parse_orario)
df_servizi['[A]Ore'] = df_servizi['[A]Ore'].apply(parse_orario)

df_servizi['Data'] = df_servizi['Data'].apply(parse_data)
df_servizi['Partenza_completa'] = df_servizi.apply(
    lambda row: datetime.combine(row['Data'], row['[P]Ore']) if pd.notnull(row['Data']) and pd.notnull(row['[P]Ore']) else pd.NaT,
    axis=1
)
df_servizi['Arrivo_completa'] = df_servizi.apply(
    lambda row: datetime.combine(row['Data'], row['[A]Ore']) if pd.notnull(row['Data']) and pd.notnull(row['[A]Ore']) else pd.NaT,
    axis=1
)
# Aggiusta arrivi oltre la mezzanotte
mask_arrivo_mezzanotte = df_servizi['Arrivo_completa'] < df_servizi['Partenza_completa']
df_servizi.loc[mask_arrivo_mezzanotte, 'Arrivo_completa'] += timedelta(days=1)

# --- Controllo errori ---
righe_turni_invalidi = df_turni[df_turni['Inizio_completo'].isnull() | df_turni['Fine_completo'].isnull()]
righe_partenza_invalidi = df_servizi[df_servizi['Partenza_completa'].isnull()]
righe_arrivo_invalidi = df_servizi[df_servizi['Arrivo_completa'].isnull()]

if not righe_turni_invalidi.empty:
    st.warning("⚠️ Alcune righe dei turni hanno problemi di orario. Controlla i valori in 'Inizio' e 'Fine'.")
    st.dataframe(righe_turni_invalidi)

if not righe_partenza_invalidi.empty:
    st.warning("⚠️ Alcuni orari di partenza non sono validi. Controlla '[P]Ore'.")
    st.dataframe(righe_partenza_invalidi)

if not righe_arrivo_invalidi.empty:
    st.warning("⚠️ Alcuni orari di arrivo non sono validi. Controlla '[A]Ore'.")
    st.dataframe(righe_arrivo_invalidi)

# --- Filtro date ---
data_min = min(df_turni['Data'].min(), df_servizi['Data'].min())
data_max = max(df_turni['Data'].max(), df_servizi['Data'].max())

data_range = st.sidebar.date_input("Intervallo Date", [data_min, data_max])

data_start = pd.to_datetime(data_range[0])
data_end = pd.to_datetime(data_range[1])

# --- Filtro dataset ---
turni_filtrati = df_turni[(df_turni['Data'] >= data_start.date()) & (df_turni['Data'] <= data_end.date())]
servizi_filtrati = df_servizi[(df_servizi['Data'] >= data_start.date()) & (df_servizi['Data'] <= data_end.date())]

# --- Visualizzazione ---
st.subheader("Turni filtrati")
st.dataframe(turni_filtrati)

st.subheader("Servizi filtrati")
st.dataframe(servizi_filtrati)
