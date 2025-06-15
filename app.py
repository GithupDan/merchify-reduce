
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Merchify.Reduce", layout="wide")
st.title("🧮 Merchify.Reduce – Abschriftenplanung mit Parametern")

# Parameter-Eingaben
col1, col2, col3 = st.columns(3)
with col1:
    abschlags_prozent = st.number_input("💥 Abschlags-Prozentsatz bei Bedarf", min_value=0, max_value=90, value=30, step=5)
with col2:
    rw_faktor_kritisch = st.number_input("⚠️ RW-Faktor für Kritisch (z. B. 2× Laufzeit)", min_value=0.5, max_value=5.0, value=2.0, step=0.1)
with col3:
    stichtag = st.date_input("📅 Heutiges Datum für Simulation", value=datetime.today())
heute = pd.to_datetime(stichtag)

# Datei-Upload
uploaded_file = st.file_uploader("📤 Excel-Datei mit Artikeldaten hochladen", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Datumsfelder konvertieren
    df["Wareneingang"] = pd.to_datetime(df["Wareneingang"], errors="coerce")
    df["Verkaufs_Enddatum"] = pd.to_datetime(df["Verkaufs_Enddatum"], errors="coerce")

    # Berechnungen
    df["Ø_Wochenabsatz"] = df[["Absatz W1", "Absatz W2", "Absatz W3", "Absatz W4"]].mean(axis=1)
    df["RW_in_Wochen"] = df["Bestand"] / df["Ø_Wochenabsatz"].replace(0, 0.1)
    df["RW_in_Tagen"] = df["RW_in_Wochen"] * 7
    df["Warenalter_Tage"] = (heute - df["Wareneingang"]).dt.days
    df["Tage_bis_Ende"] = (df["Verkaufs_Enddatum"] - heute).dt.days.abs()
    df["Wochen_bis_Ende"] = df["Tage_bis_Ende"] / 7

    # Entscheidungslogik
    df["Abschriftenbedarf"] = df.apply(
        lambda row: row["RW_in_Wochen"] > row["Wochen_bis_Ende"], axis=1
    )
    df["Vorgeschlagener_Abschlag_%"] = df["Abschriftenbedarf"].apply(lambda x: abschlags_prozent if x else 0)
    df["Neuer_Preis"] = df["Aktueller_Preis"] * (1 - df["Vorgeschlagener_Abschlag_%"] / 100)
    df["Bestandswert_EK"] = df["Bestand"] * df["EKP"]
    df["Deckungsbeitrag_neu"] = (df["Neuer_Preis"] - df["EKP"]) * df["Bestand"]
    df["Rohertragsverlust_%"] = (df["Aktueller_Preis"] - df["Neuer_Preis"]) / df["Aktueller_Preis"] * 100
    df["Absatz_summe"] = df[["Absatz W1", "Absatz W2", "Absatz W3", "Absatz W4"]].sum(axis=1)
    df["Abverkaufsquote"] = df["Absatz_summe"] / (df["Absatz_summe"] + df["Bestand"]) * 100
    df["RW_kritisch"] = df.apply(
        lambda row: row["RW_in_Wochen"] > (rw_faktor_kritisch * row["Wochen_bis_Ende"]) if row["Verkaufs_Enddatum"] > heute else False,
        axis=1
    )

    # Anzeige
    st.subheader("📋 Analyseergebnisse")
    st.dataframe(df[[
        "Artikelnummer", "Artikelname", "Kategorie", "Filiale", "Bestand",
        "Wareneingang", "Warenalter_Tage", "Verkaufs_Enddatum", "Tage_bis_Ende", "Wochen_bis_Ende",
        "Absatz W1", "Absatz W2", "Absatz W3", "Absatz W4", "Absatz_summe", "Abverkaufsquote",
        "Ø_Wochenabsatz", "RW_in_Wochen", "RW_in_Tagen", "RW_kritisch",
        "Aktueller_Preis", "Vorgeschlagener_Abschlag_%", "Neuer_Preis", "EKP",
        "Rohertragsverlust_%", "Bestandswert_EK", "Deckungsbeitrag_neu", "Abschriftenbedarf"
    ]].round(2))

    # Download
    df.to_excel("abschriften_dashboard_ergebnis.xlsx", index=False)
    with open("abschriften_dashboard_ergebnis.xlsx", "rb") as f:
        st.download_button("⬇️ Download Ergebnis als Excel", f, file_name="abschriften_dashboard_ergebnis.xlsx")

else:
    st.info("Bitte lade eine Excel-Datei hoch, um die Analyse zu starten.")
