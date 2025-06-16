
import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

st.set_page_config(page_title="Merchify – Abschriftenmodul", layout="wide")

# Logo anzeigen
try:
    st.image("https://raw.githubusercontent.com/GithupDan/merchify-reduce/main/logo.png", width=180)
except:
    st.warning("Logo konnte nicht geladen werden.")
st.markdown("### *The markdown engine for modern retail.*")

st.sidebar.header("⚙️ Abschriften-Parameter")
rw_critical = st.sidebar.slider("RW-Faktor kritisch", 1.0, 5.0, 2.0)
abschlag_leicht = st.sidebar.slider("Abschlag leicht kritisch (%)", 0, 100, 20)
abschlag_stark = st.sidebar.slider("Abschlag stark kritisch (%)", 0, 100, 40)
min_db = st.sidebar.number_input("Mindest-Deckungsbeitrag (€)", value=0.0)
stichtag = st.sidebar.date_input("Stichtag", value=datetime.date.today())

uploaded_file = st.file_uploader("📤 Excel-Datei mit Artikeldaten hochladen", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df["Verkaufs_Enddatum"] = pd.to_datetime(df["Verkaufs_Enddatum"])
    df["RW_4W"] = df[["Absatz W1", "Absatz W2", "Absatz W3", "Absatz W4"]].sum(axis=1) / 4
    df["RW_Tage"] = df["Bestand"] / df["RW_4W"].replace(0, 0.01) * 7
    df["Tage_bis_Ende"] = (df["Verkaufs_Enddatum"] - pd.to_datetime(stichtag)).dt.days.clip(lower=1)
    df["RW_Faktor"] = df["RW_Tage"] / df["Tage_bis_Ende"]

    df["Abschlag_%"] = 0
    df.loc[(df["RW_Faktor"] > rw_critical) & (df["RW_Faktor"] <= rw_critical + 1), "Abschlag_%"] = abschlag_leicht
    df.loc[df["RW_Faktor"] > rw_critical + 1, "Abschlag_%"] = abschlag_stark

    df["Neuer_Preis"] = df["Aktueller_Preis"] * (1 - df["Abschlag_%"] / 100)
    df["Deckungsbeitrag_neu"] = df["Neuer_Preis"] - df["EKP"]
    df["Abschriftenwert"] = df["Bestand"] * (df["Aktueller_Preis"] - df["Neuer_Preis"])
    df["DB_alt"] = df["Bestand"] * (df["Aktueller_Preis"] - df["EKP"])
    df["DB_neu"] = df["Bestand"] * (df["Neuer_Preis"] - df["EKP"])
    df["Abschriftenquote_%"] = (df["Abschriftenwert"] / (df["Bestand"] * df["Aktueller_Preis"])) * 100
    df["Reduzierung empfohlen"] = (df["Abschlag_%"] > 0) & (df["Deckungsbeitrag_neu"] >= min_db)

    st.subheader("📊 Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Aktuelle Marge (€)", f"{df['DB_alt'].sum():,.0f}")
    col2.metric("Neue Marge (€)", f"{df['DB_neu'].sum():,.0f}")
    col3.metric("Abschriftenwert (€)", f"{df['Abschriftenwert'].sum():,.0f}")

    st.subheader("📋 Ergebnis-Tabelle")
    st.dataframe(df.style.format({
        "RW_Faktor": "{:.2f}",
        "Abschlag_%": "{:.0f}%",
        "Neuer_Preis": "€{:.2f}",
        "Deckungsbeitrag_neu": "€{:.2f}",
        "Abschriftenwert": "€{:.2f}",
        "Abschriftenquote_%": "{:.1f}%"
    }), use_container_width=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Ergebnis")
    processed_data = output.getvalue()

    st.download_button(
        label="📥 Download Ergebnis als Excel",
        data=processed_data,
        file_name="Merchify_Ergebnis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
