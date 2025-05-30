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
df_servizi["GG"] = df_servizi["Data"].dt.day_name()

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
start_date = pd.to_datetime(data_range[0])
end_date = pd.to_datetime(data_range[1])

# --- Filtri aggiuntivi ---
mezzi_disponibili = df_servizi["Automezzo"].dropna().unique()
mezzo_selezionato = st.sidebar.multiselect("Filtro per Automezzo", sorted(mezzi_disponibili))

tipi_servizio = df_servizi["Categoria Simplificata"].dropna().unique()
categoria_selezionata = st.sidebar.multiselect("Filtro per Categoria Servizio", sorted(tipi_servizio))

# --- Filtro dataframe servizi ---
df_servizi_filtered = df_servizi[
    (df_servizi["Data"] >= start_date) &
    (df_servizi["Data"] <= end_date)
]

if mezzo_selezionato:
    df_servizi_filtered = df_servizi_filtered[df_servizi_filtered["Automezzo"].isin(mezzo_selezionato)]

if categoria_selezionata:
    df_servizi_filtered = df_servizi_filtered[df_servizi_filtered["Categoria Simplificata"].isin(categoria_selezionata)]

# --- Filtro dataframe turni ---
df_turni_filtered = df_turni[(df_turni["Data"] >= start_date) & (df_turni["Data"] <= end_date)]


# --- KPI TURNI ---
st.header("🔁 KPI Turni")

turni_count = len(df_turni_filtered)
ore_disponibili = (
    pd.to_datetime(df_turni_filtered["Fine"].astype(str)) - pd.to_datetime(df_turni_filtered["Inizio"].astype(str))
).dt.total_seconds() / 3600
media_ore_per_turno = ore_disponibili.mean()
media_turni_per_giorno = turni_count / ((end_date - start_date).days + 1)

st.metric("Totale Turni", turni_count)
st.metric("Media Ore per Turno", f"{media_ore_per_turno:.2f}")
st.metric("Media Turni per Giorno", f"{media_turni_per_giorno:.2f}")

# Turni per Categoria Semplificata
st.subheader("Turni per Categoria (semplificata)")
turni_cat = df_turni_filtered["Categoria Simplificata"].value_counts().sort_values(ascending=False)
fig1, ax1 = plt.subplots()
turni_cat.plot(kind="bar", ax=ax1, color="skyblue")
ax1.set_ylabel("Numero Turni")
ax1.set_title("Distribuzione Turni per Categoria")
ax1.tick_params(axis='x', rotation=45)
st.pyplot(fig1)

# --- KPI SERVIZI ---
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

# Servizi per Categoria
st.subheader("Servizi per Categoria (semplificata)")
servizi_cat = df_servizi_filtered["Categoria Simplificata"].value_counts().sort_values(ascending=False)
fig2, ax2 = plt.subplots()
servizi_cat.plot(kind="bar", ax=ax2, color="salmon")
ax2.set_ylabel("Numero Servizi")
ax2.set_title("Distribuzione Servizi per Categoria")
ax2.tick_params(axis='x', rotation=45)
st.pyplot(fig2)

# Distribuzione per giorno della settimana
st.subheader("Distribuzione Servizi per Giorno della Settimana")
gg_servizi = df_servizi_filtered["GG"].value_counts().reindex([
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
])
fig3, ax3 = plt.subplots()
gg_servizi.plot(kind="bar", ax=ax3, color="orange")
ax3.set_ylabel("Servizi")
st.pyplot(fig3)

# Interni vs Esterni
st.subheader("Interni vs Esterni")
interni_mask = df_servizi_filtered["Categoria Simplificata"] == "INTERNI"
interni_count = interni_mask.sum()
esterni_count = len(df_servizi_filtered) - interni_count
st.metric("Servizi Interni", interni_count)
st.metric("Servizi Esterni", esterni_count)

# Automezzi
st.subheader("Media Servizi per Automezzo")
media_per_mezzo = df_servizi_filtered["Automezzo"].value_counts()
fig4, ax4 = plt.subplots()
media_per_mezzo.plot(kind="bar", ax=ax4, color="green")
ax4.set_ylabel("Numero Servizi")
ax4.set_title("Servizi per Automezzo")
ax4.tick_params(axis='x', rotation=45)
st.pyplot(fig4)

# --- KPI Correlati Turni / Servizi (entro 31 giorni) ---
if (end_date - start_date).days <= 31:
    st.header("🔄 KPI Correlati Turni / Servizi")

    servizi_per_giorno = df_servizi_filtered.groupby("Data").size()
    turni_per_giorno = df_turni_filtered.groupby("Data").size()
    joined = pd.concat([servizi_per_giorno, turni_per_giorno], axis=1).fillna(0)
    joined.columns = ["Servizi", "Turni"]
    joined["Rapporto"] = joined["Servizi"] / joined["Turni"].replace(0, np.nan)

    fig5, ax5 = plt.subplots()
    joined["Rapporto"].plot(ax=ax5, marker='o', linestyle='-')
    ax5.set_ylabel("Servizi per Turno")
    ax5.set_title("Rapporto Servizi / Turni (giornaliero)")
    st.pyplot(fig5)

    # Match temporale
    servizi_inside_turno = 0
    for _, s in df_servizi_filtered.iterrows():
        p_ora = pd.to_datetime(s["[P]Ore"].strftime("%H:%M"))
        for _, t in df_turni_filtered[df_turni_filtered["Data"] == s["Data"]].iterrows():
            start = pd.to_datetime(t["Inizio"].strftime("%H:%M"))
            end = pd.to_datetime(t["Fine"].strftime("%H:%M"))
            if start <= p_ora <= end:
                servizi_inside_turno += 1
                break

    percent_inside = (servizi_inside_turno / len(df_servizi_filtered)) * 100
    st.metric("Servizi dentro turni (tempo)", f"{percent_inside:.1f}%")

