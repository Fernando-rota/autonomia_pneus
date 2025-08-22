import streamlit as st
import pandas as pd
import re
import unicodedata
import numpy as np

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
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
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
            return "background-color: #FF6B6B; color: white; font-weight:bold"
        elif val_float < 4:
            return "background-color: #FFD93D; color: black; font-weight:bold"
        else:
            return "background-color: #6BCB77; color: white; font-weight:bold"
    except:
        return ""

def classificar_veiculo(desc):
    if pd.isna(desc):
        return "Outro"
    d = str(desc).lower()
    if "saveiro" in d:
        return "Leve"
    if "renault" in d:
        return "Utilitário (Renault)"
    if "iveco" in d or "daily" in d or "dayli" in d or "scudo" in d:
        return "Utilitário (Iveco/Scudo)"
    if "3/4" in d or "3-4" in d:
        return "3/4"
    if "toco" in d:
        return "Toco"
    if "truck" in d:
        return "Truck"
    if "cavalo" in d or "carreta" in d:
        return "Carreta"
    return "Outro"

# ----------------- MAIN -----------------
if arquivo:
    sheets = pd.read_excel(arquivo, engine="openpyxl", sheet_name=None)
    required_sheets = {"pneus", "posição", "sulco"}
    if not required_sheets.issubset(sheets.keys()):
        st.error(f"O arquivo precisa conter as abas: {', '.join(required_sheets)}")
        st.stop()

    df_pneus = sheets["pneus"].copy()
    df_posicao = sheets["posição"].copy()
    df_sulco = sheets["sulco"].copy()

    df_pneus.columns = df_pneus.columns.str.strip()
    df_posicao.columns = df_posicao.columns.str.strip()
    df_sulco.columns = df_sulco.columns.str.strip()

    # Normalizações
    df_pneus["Aferição - Sulco"] = df_pneus["Aferição - Sulco"].apply(to_float)
    df_sulco["Sulco"] = df_sulco["Sulco"].apply(to_float)
    if "Hodômetro Inicial" in df_pneus.columns:
        df_pneus["Hodômetro Inicial"] = df_pneus["Hodômetro Inicial"].apply(to_float)
    df_pneus["Vida do Pneu - Km. Rodado"] = df_pneus.get("Vida do Pneu - Km. Rodado", np.nan).apply(to_float)
    df_pneus["Observação - Km"] = df_pneus.get("Observação", np.nan).apply(extrair_km_observacao)

    df_pneus["Km Rodado até Aferição"] = df_pneus["Vida do Pneu - Km. Rodado"]
    mask_km_vazio = df_pneus["Km Rodado até Aferição"].isna() | (df_pneus["Km Rodado até Aferição"] <= 0)
    df_pneus.loc[mask_km_vazio, "Km Rodado até Aferição"] = (
        df_pneus.loc[mask_km_vazio, "Observação - Km"] - df_pneus.loc[mask_km_vazio, "Hodômetro Inicial"]
    )
    df_pneus.loc[df_pneus["Km Rodado até Aferição"] <= 0, "Km Rodado até Aferição"] = np.nan

    # Sulco Inicial
    for col in ["Vida","Modelo (Atual)"]:
        if col not in df_pneus.columns or col not in df_sulco.columns:
            st.error(f"Coluna '{col}' não encontrada.")
            st.stop()

    df_pneus["_VIDA"] = df_pneus["Vida"].apply(normalize_text)
    df_pneus["_MODELO"] = df_pneus["Modelo (Atual)"].apply(normalize_text)
    df_sulco["_VIDA"] = df_sulco["Vida"].apply(normalize_text)
    df_sulco["_MODELO"] = df_sulco["Modelo (Atual)"].apply(normalize_text)

    base = df_sulco[["_VIDA","_MODELO","Sulco"]].dropna(subset=["Sulco"]).drop_duplicates(subset=["_VIDA","_MODELO"])
    df_pneus = df_pneus.merge(base.rename(columns={"Sulco":"Sulco Inicial"}), on=["_VIDA","_MODELO"], how="left")

    map_model_novo = df_sulco[df_sulco["_VIDA"]=="NOVO"].dropna(subset=["Sulco"]).drop_duplicates("_MODELO").set_index("_MODELO")["Sulco"].to_dict()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna() & (df_pneus["_VIDA"]=="NOVO"), "Sulco Inicial"] = df_pneus.loc[df_pneus["Sulco Inicial"].isna() & (df_pneus["_VIDA"]=="NOVO"), "_MODELO"].map(map_model_novo)

    map_model_any = df_sulco.dropna(subset=["Sulco"]).groupby("_MODELO")["Sulco"].median().to_dict()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "Sulco Inicial"] = df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "_MODELO"].map(map_model_any)

    med_por_vida = df_sulco.dropna(subset=["Sulco"]).groupby("_VIDA")["Sulco"].median()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "Sulco Inicial"] = df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "_VIDA"].map(med_por_vida)

    if df_pneus["Sulco Inicial"].isna().any():
        df_pneus["Sulco Inicial"] = df_pneus["Sulco Inicial"].fillna(df_sulco["Sulco"].dropna().median())

    # Cálculos
    df_pneus["Sulco Consumido"] = df_pneus["Sulco Inicial"] - df_pneus["Aferição - Sulco"]
    df_pneus["Desgaste (mm/km)"] = np.where(
        df_pneus["Km Rodado até Aferição"].notna() & (df_pneus["Km Rodado até Aferição"]>0),
        df_pneus["Sulco Consumido"]/df_pneus["Km Rodado até Aferição"], np.nan
    )
    df_pneus["Tipo Veículo"] = df_pneus.get("Veículo - Descrição", "").apply(classificar_veiculo)

    # ----------------- INDICADORES -----------------
    st.subheader("📌 Indicadores Gerais")
    total_pneus = df_pneus["Referência"].nunique() if "Referência" in df_pneus.columns else len(df_pneus)
    status_counts = df_pneus["Status"].value_counts(dropna=False) if "Status" in df_pneus.columns else pd.Series()
    estoque = int(status_counts.get("Estoque",0))
    sucata = int(status_counts.get("Sucata",0)) + 2  # Acrescentando 2 pneus
    caminhao = int(status_counts.get("Caminhão",0))

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("🛞 Total de Pneus", total_pneus)
    col2.metric("📦 Estoque", estoque)
    col3.metric("♻️ Sucata", sucata)
    col4.metric("🚚 Caminhão", caminhao)

    # ----------------- MEDIDAS DE SULCO -----------------
    st.subheader("📏 Medidas de Sulco (com Km Rodado)")
    cols_show = [c for c in [
        "Referência","Veículo - Placa","Veículo - Descrição","Marca (Atual)","Modelo (Atual)",
        "Vida","Sulco Inicial","Status","Aferição - Sulco","Sulco Consumido","Km Rodado até Aferição",
        "Desgaste (mm/km)","Posição","Sigla da Posição"
    ] if c in df_pneus.columns]
    df_show = df_pneus[cols_show].copy()
    df_show["Km Rodado até Aferição"] = df_show["Km Rodado até Aferição"].apply(lambda x: f"{x:,.0f} km" if pd.notna(x) else "-")

    st.dataframe(
        df_show.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]) \
                     .format({"Sulco Inicial":"{:.2f}","Aferição - Sulco":"{:.2f}","Sulco Consumido":"{:.2f}","Desgaste (mm/km)":"{:.6f}"}),
        use_container_width=True
    )
else:
    st.info("Aguardando upload do arquivo Excel…")
