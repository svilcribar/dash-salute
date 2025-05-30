import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- URL dei dati ---
URL_SERVIZI = "https://docs.google.com/spreadsheets/d/1lBUcDna2q8tnSBESFHBGLMLRtg3MSp0yCY3eheDvPoU/export?format=csv"
URL_TURNI = "https://docs.google.com/spreadsheets/d/1gnbV3CsLLcPoUzBqqntFJmWyTO-zx7NUCLJy0ThuH9A/export?format=csv"

# --- Lettura file ---
df_servizi = pd.read_csv(URL_SERVIZI)
df_turni = pd.read_csv(URL_TURNI)

# --- Pre-processing SERVIZI ---
df_servizi["Data"] = pd.to_datetime(df_servizi["Data"], dayfirst=True, errors='coerce')
df_servizi["[P]Ore"] = pd.to_datetime(df_servizi["[P]Ore"], format="%H:%M", errors='coerce').dt.time
df_servizi["[A]Ore"] = pd.to_datetime(df_servizi["[A]Ore"], format="%H:%M", errors='coerce').dt.time
df_servizi["Durata (min)"] = (
    pd.to_datetime(df_servizi["[A]Ore"].astype(str)) - pd.to_datetime(df_servizi["[P]Ore"].astype(str))
).dt.total_seconds() / 60
df_servizi["Categoria"] = df_servizi["Intervento"].str.extract(r"\[(.*?)\]")

# --- Pre-processing TURNI ---
df_turni["Data"] = pd.to_datetime(df_turni["Data"], dayfirst=True, errors='coerce')
df_turni["Inizio"] = pd.to_datetime(df_turni["Inizio"], format="%H:%M", errors='coerce').dt.time
df_turni["Fine"] = pd.to_datetime(df_turni["Fine"], format="%H:%M", errors='coerce').dt.time
df_turni["Categoria"] = df_turni["Categoria"].str.extract(r"\[(.*?)\]")

# --- Mapping categorie ---
categoria_map = {
    "UFF": "UFFICIO",
    "ORDINARIO": "ORDINARI",
    "INTERNI": "INTERNI",
    "EMERGENZA": "EMERG",
    "PRIVATO": "PRIVATI",
    "SOC": "SOC",
    "GEN": "FORMAZIONE",
    "TSSA-APS": "TSSA",
    "TS": "TS",
    "POLI": "POLIAMB",
}
df_turni["Categoria Simplificata"] = df_turni["Categoria"].map(categoria_map).fillna("ALTRO")
df_servizi["Categoria Simplificata"] = df_servizi["Categoria"].map(categoria_map).fillna("ALTRO")

# --- Intervallo Date ---
min_date = max(df_servizi["Data"].min(), df_turni["Data"].min())
max_date = min(df_servizi["Data"].max(), df_turni["Data"].max())
data_range = st.sidebar.date_input("Intervallo Date", [min_date, max_date])

start_date, end_date = data_range
df_servizi_filtered = df_servizi[(df_servizi["Data"] >= start_date) & (df_servizi["Data"] <= end_date)]
df_turni_filtered = df_turni[(df_turni["Data"] >= start_date) & (df_turni["Data"] <= end_date)]

# --- KPI Turni ---
st.header("🔁 KPI Turni")

turni_count = len(df_turni_filtered)
ore_disponibili = (
    pd.to_datetime(df_turni_filtered["Fine"].astype(str)) -
    pd.to_datetime(df_turni_filtered["Inizio"].astype(str))
).dt.total_seconds() / 3600
media_ore_per_turno = ore_disponibili.mean()
media_turni_per_giorno = turni_count / ((end_date - start_date).days + 1)

st.metric("Totale Turni", turni_count)
st.metric("Media Ore per Turno", f"{media_ore_per_turno:.2f}")
st.metric("Media Turni per Giorno", f"{media_turni_per_giorno:.2f}")

# --- Grafico Turni per Categoria ---
st.subheader("Turni per Categoria (semplificata)")
turni_cat = df_turni_filtered["Categoria Simplificata"].value_counts().sort_values(ascending=False)
fig1, ax1 = plt.subplots()
turni_cat.plot(kind="bar", ax=ax1, color="skyblue")
st.pyplot(fig1)

# --- KPI Servizi ---
st.header("🚑 KPI Servizi")

tot_servizi = len(df_servizi_filtered)
tot_km = df_servizi_filtered["Km effet."].sum()
media_km_servizio = df_servizi_filtered["Km effet."].mean()
media_servizi_per_giorno = tot_servizi / ((end_date - start_date).days + 1)
tempo_medio_min = df_servizi_filtered["Durata (min)"].mean()

st.metric("Totale Servizi", tot_servizi)
st.metric("Media Km per Servizio", f"{media_km_servizio:.1f} km")
st.metric("Media Servizi per Giorno", f"{media_servizi_per_giorno:.2f}")
st.metric("Tempo Medio per Servizio", f"{tempo_medio_min:.1f} minuti")

# --- Grafico Servizi per Categoria Semplificata ---
st.subheader("Servizi per Categoria (semplificata)")
servizi_cat = df_servizi_filtered["Categoria Simplificata"].value_counts().sort_values(ascending=False)
fig2, ax2 = plt.subplots()
servizi_cat.plot(kind="bar", ax=ax2, color="salmon")
st.pyplot(fig2)

# --- KPI Correlati Turni / Servizi ---
if (end_date - start_date).days <= 31:
    st.header("🔄 KPI Correlati (entro 31gg)")

    servizi_per_giorno = df_servizi_filtered.groupby("Data").size()
    turni_per_giorno = df_turni_filtered.groupby("Data").size()
    joined = pd.concat([servizi_per_giorno, turni_per_giorno], axis=1)
    joined.columns = ["Servizi", "Turni"]
    joined["Rapporto"] = joined["Servizi"] / joined["Turni"]

    fig3, ax3 = plt.subplots()
    joined["Rapporto"].plot(ax=ax3, marker='o', linestyle='-')
    ax3.set_ylabel("Servizi per Turno")
    ax3.set_title("Rapporto Servizi / Turni (giornaliero)")
    st.pyplot(fig3)
