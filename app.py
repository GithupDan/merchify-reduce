
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Merchify.Reduce", layout="wide")
st.title("Merchify.Reduce – Abschriftenplanung")

# Datei-Upload
uploaded_file = st.file_uploader("Lade deine Artikelliste hoch (Excel)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("Datei erfolgreich geladen!")

    # Verkaufs-Enddatum umwandeln
    df["Verkaufs_Enddatum"] = pd.to_datetime(df["Verkaufs_Enddatum"], errors="coerce")

    # Durchschnittlicher Absatz (W1–W4)
    df["Ø_Wochenabsatz"] = df[["Absatz W1", "Absatz W2", "Absatz W3", "Absatz W4"]].mean(axis=1)
    df["RW_in_Wochen"] = df["Bestand"] / df["Ø_Wochenabsatz"].replace(0, 0.1)

    # Zeit bis Verkaufsende
    heute = datetime.today()
    df["Tage_bis_Ende"] = (df["Verkaufs_Enddatum"] - heute).dt.days
    df["RW_in_Tagen"] = df["RW_in_Wochen"] * 7

    # Abschriftenregel
    df["Abschriftenbedarf"] = df["RW_in_Tagen"] > df["Tage_bis_Ende"]
    df["Vorgeschlagener_Abschlag_%"] = df["Abschriftenbedarf"].apply(lambda x: 30 if x else 0)
    df["Neuer_Preis"] = df["Aktueller_Preis"] * (1 - df["Vorgeschlagener_Abschlag_%"] / 100)
    df["Neue_Marge"] = df["Neuer_Preis"] - df["EKP"]

    st.subheader("Vorschlagsliste")
    st.dataframe(df[[
        "Artikelnummer", "Artikelname", "Bestand", "Ø_Wochenabsatz", "RW_in_Wochen",
        "Tage_bis_Ende", "Abschriftenbedarf", "Vorgeschlagener_Abschlag_%",
        "Aktueller_Preis", "Neuer_Preis", "Neue_Marge"]].round(2))

    # Download als Excel
    output_file = "abschriften_vorschlag.xlsx"
    df.to_excel(output_file, index=False)
    with open(output_file, "rb") as f:
        st.download_button("Download Excel-Ergebnis", f, file_name=output_file)
else:
    st.info("Bitte lade zuerst deine Excel-Datei hoch.")
