import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

# --- URL DATI ---
URL_SERVIZI = "https://docs.google.com/spreadsheets/d/1lBUcDna2q8tnSBESFHBGLMLRtg3MSp0yCY3eheDvPoU/export?format=csv"
URL_TURNI = "https://docs.google.com/spreadsheets/d/1gnbV3CsLLcPoUzBqqntFJmWyTO-zx7NUCLJy0ThuH9A/export?format=csv"

# --- MAPPING CATEGORIE ---
categoria_map = {
    'POLI': 'Poliambulatori',
    'GEN': 'Formazione',
    'TS': 'Soccorso ECHO',
    'TSSA-APS': 'Bravo',
    'SOC': 'UDS / Servizi Sociali',
    'ORDINARIO': 'Ordinari',
    'PRIVATO': 'Privati',
    'INTERNI': 'Interni',
    'EMERGENZA': 'Emergenze',
}

# --- CARICA DATI ---
df_servizi = pd.read_csv(URL_SERVIZI)
df_turni = pd.read_csv(URL_TURNI)

# --- PREPARA TURNI ---
df_turni['Data'] = pd.to_datetime(df_turni['Data'], errors='coerce')
df_turni['Categoria Grezza'] = df_turni['Servizio'].str.extract(r'\[(.*?)\]')
df_turni['Categoria'] = df_turni['Categoria Grezza'].map(categoria_map).fillna('Altre')

# Calcola ore turno
for col in ['Inizio', 'Fine']:
    df_turni[col] = pd.to_datetime(df_turni[col], format="%H:%M", errors='coerce')
df_turni['Durata Ore'] = (df_turni['Fine'] - df_turni['Inizio']).dt.total_seconds() / 3600

# --- PREPARA SERVIZI ---
df_servizi['[P]Ore'] = pd.to_datetime(df_servizi['[P]Ore'], format="%H:%M", errors='coerce')
df_servizi['[A]Ore'] = pd.to_datetime(df_servizi['[A]Ore'], format="%H:%M", errors='coerce')
df_servizi['Durata Servizio'] = (df_servizi['[A]Ore'] - df_servizi['[P]Ore']).dt.total_seconds() / 60

df_servizi['Data'] = pd.to_datetime(df_servizi['Data'], errors='coerce')
df_servizi['Categoria'] = df_servizi['Intervento'].str.extract(r'\[(.*?)\]')
df_servizi['Categoria'] = df_servizi['Categoria'].map(categoria_map).fillna('Altre')

# --- FILTRO DATA ---
min_date = min(df_turni['Data'].min(), df_servizi['Data'].min())
max_date = max(df_turni['Data'].max(), df_servizi['Data'].max())
data_range = st.sidebar.date_input("Intervallo Date", [min_date, max_date])
start_date, end_date = data_range

# --- FILTRA DATI ---
df_turni_f = df_turni[(df_turni['Data'] >= pd.to_datetime(start_date)) & (df_turni['Data'] <= pd.to_datetime(end_date))]
df_servizi_f = df_servizi[(df_servizi['Data'] >= pd.to_datetime(start_date)) & (df_servizi['Data'] <= pd.to_datetime(end_date))]

# --- KPI TURNI ---
st.subheader("🔁 KPI Turni")

col1, col2, col3 = st.columns(3)
col1.metric("Numero Turni", len(df_turni_f))
col2.metric("Ore Totali", round(df_turni_f['Durata Ore'].sum(), 1))
col3.metric("Media Ore per Turno", round(df_turni_f['Durata Ore'].mean(), 2))

# Media turni/giorno
media_turni_giorno = df_turni_f.groupby('Data').size().mean()
st.metric("📅 Media Turni per Giorno", round(media_turni_giorno, 2))

# Turni per Categoria
turni_categoria = df_turni_f.groupby('Categoria').size().reset_index(name='Turni')
fig_turni = px.bar(turni_categoria, x='Categoria', y='Turni', title='Turni per Categoria', color='Categoria')
st.plotly_chart(fig_turni, use_container_width=True)

# --- KPI SERVIZI ---
st.subheader("🚑 KPI Servizi")

col1, col2, col3 = st.columns(3)
col1.metric("Numero Servizi", len(df_servizi_f))
col2.metric("Tempo Medio (min)", round(df_servizi_f['Durata Servizio'].mean(), 1))
col3.metric("Km Totali", df_servizi_f['Km effet.'].sum())

st.metric("Media Km per Servizio", round(df_servizi_f['Km effet.'].mean(), 1))

# Media servizi/giorno
media_servizi_giorno = df_servizi_f.groupby('Data').size().mean()
st.metric("📅 Media Servizi per Giorno", round(media_servizi_giorno, 2))

# Servizi per Categoria
servizi_categoria = df_servizi_f.groupby('Categoria').size().reset_index(name='Servizi')
fig_servizi = px.bar(servizi_categoria, x='Categoria', y='Servizi', title='Servizi per Categoria', color='Categoria')
st.plotly_chart(fig_servizi, use_container_width=True)

# Servizi Interni vs Esterni
interni = df_servizi_f[df_servizi_f['Categoria'] == 'Interni'].shape[0]
esterni = df_servizi_f.shape[0] - interni
st.metric("Interni vs Esterni", f"{interni} / {esterni}")

# Uso Mezzi
mezzi = df_servizi_f['Automezzo'].value_counts().reset_index()
mezzi.columns = ['Automezzo', 'Servizi']
fig_mezzi = px.bar(mezzi, x='Automezzo', y='Servizi', title='Utilizzo Automezzi')
st.plotly_chart(fig_mezzi, use_container_width=True)

# --- KPI Correlati solo se intervallo <= 31 gg ---
if (end_date - start_date).days <= 31:
    st.subheader("🔄 KPI Correlati Turni/Servizi")
    servizi_per_giorno = df_servizi_f.groupby('Data').size()
    turni_per_giorno = df_turni_f.groupby('Data').size()
    joined = pd.concat([servizi_per_giorno, turni_per_giorno], axis=1, keys=['Servizi', 'Turni']).fillna(0)
    joined['Servizi per Turno'] = joined['Servizi'] / joined['Turni'].replace(0, pd.NA)

    st.line_chart(joined[['Servizi', 'Turni']])
    st.bar_chart(joined['Servizi per Turno'])
