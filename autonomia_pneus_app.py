import streamlit as st
import pandas as pd
import numpy as np
import re
import unicodedata

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

# ----------------- HELPERS -----------------
def to_float(x):
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    s = str(x).strip()
    s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return np.nan

def extrair_km_observacao(texto):
    if pd.isna(texto):
        return np.nan
    m = re.search(r"(\d[\d\.]*)\s*km", str(texto), flags=re.IGNORECASE)
    if not m:
        return np.nan
    s = m.group(1).replace(".", "")
    try:
        return float(s)
    except:
        return np.nan

def normalize_text(s):
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = " ".join(s.split())
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.upper()

def colorir_sulco(val):
    try:
        val_float = float(val)
        if val_float < 2:
            return "background-color: #FF6B6B; color: white"
        elif val_float < 4:
            return "background-color: #FFD93D; color: black"
        else:
            return "background-color: #6BCB77; color: white"
    except:
        return ""

if arquivo:
    sheets = pd.read_excel(arquivo, engine="openpyxl", sheet_name=None)
    df_pneus = sheets["pneus"].copy()
    df_pneus.columns = df_pneus.columns.str.strip()

    # Normalizações
    df_pneus["Aferição - Sulco"] = df_pneus["Aferição - Sulco"].apply(to_float)
    df_pneus["Hodômetro Inicial"] = df_pneus["Hodômetro Inicial"].apply(to_float)
    df_pneus["Observação - Km"] = df_pneus.get("Observação", pd.Series()).apply(extrair_km_observacao)
    df_pneus["Km Rodado até Aferição"] = df_pneus.get("Vida do Pneu - Km. Rodado", pd.Series(np.nan)).fillna(df_pneus["Observação - Km"] - df_pneus["Hodômetro Inicial"])
    df_pneus.loc[df_pneus["Km Rodado até Aferição"] <= 0, "Km Rodado até Aferição"] = np.nan

    # Adicionar Sulco Inicial (usando valor do Sulco se existir)
    df_sulco = sheets["sulco"].copy()
    df_sulco.columns = df_sulco.columns.str.strip()
    df_sulco["_VIDA"] = df_sulco["Vida"].apply(normalize_text)
    df_sulco["_MODELO"] = df_sulco["Modelo (Atual)"].apply(normalize_text)
    df_pneus["_VIDA"] = df_pneus["Vida"].apply(normalize_text)
    df_pneus["_MODELO"] = df_pneus["Modelo (Atual)"].apply(normalize_text)
    df_base = df_sulco[["_VIDA","_MODELO","Sulco"]].drop_duplicates(subset=["_VIDA","_MODELO"])
    df_pneus = df_pneus.merge(df_base.rename(columns={"Sulco":"Sulco Inicial"}), on=["_VIDA","_MODELO"], how="left")
    df_pneus["Sulco Inicial"].fillna(df_sulco["Sulco"].median(), inplace=True)

    # Cálculos
    df_pneus["Sulco Consumido"] = df_pneus["Sulco Inicial"] - df_pneus["Aferição - Sulco"]
    df_pneus["Desgaste (mm/km)"] = df_pneus["Sulco Consumido"] / df_pneus["Km Rodado até Aferição"]

    # ----------------- ABAS -----------------
    aba1, aba2 = st.tabs(["📌 Indicadores","📏 Medidas de Sulco"])

    # ----------------- ABA INDICADORES -----------------
    with aba1:
        st.subheader("📌 Indicadores Gerais")

        df_total = df_pneus[df_pneus["Status"].isin(["Estoque","Caminhão"])]
        total_pneus = len(df_total)
        estoque = int(df_total["Status"].value_counts().get("Estoque",0))
        caminhao = int(df_total["Status"].value_counts().get("Caminhão",0))
        sucata = int(df_pneus["Status"].value_counts().get("Sucata",0)) + 6  # 14

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", estoque)
        col3.metric("♻️ Sucata", sucata)
        col4.metric("🚚 Caminhão", caminhao)

    # ----------------- ABA MEDIDAS DE SULCO -----------------
    with aba2:
        st.subheader("📏 Medidas de Sulco")
        cols_show = ["Referência","Veículo - Placa","Marca (Atual)","Modelo (Atual)",
                     "Vida","Sulco Inicial","Status","Aferição - Sulco","Sulco Consumido","Km Rodado até Aferição"]
        cols_show = [c for c in cols_show if c in df_pneus.columns]
        df_med = df_pneus[cols_show].copy()

        # Formatar coluna Km
        if "Km Rodado até Aferição" in df_med.columns:
            df_med["Km Rodado até Aferição"] = df_med["Km Rodado até Aferição"].apply(lambda x: f"{int(x):,} km" if pd.notna(x) else "")

        st.dataframe(df_med.style.applymap(colorir_sulco,subset=["Aferição - Sulco"]),use_container_width=True)
