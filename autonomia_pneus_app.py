import streamlit as st
import pandas as pd
import plotly.express as px
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
            return "background-color: #FF6B6B; color: white"
        elif val_float < 4:
            return "background-color: #FFD93D; color: black"
        else:
            return "background-color: #6BCB77; color: white"
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

if arquivo:
    sheets = pd.read_excel(arquivo, engine="openpyxl", sheet_name=None)
    if not {"pneus", "posição", "sulco"}.issubset(set(sheets.keys())):
        st.error("O arquivo precisa conter as abas: 'pneus', 'posição' e 'sulco'.")
        st.stop()

    df_pneus = sheets["pneus"].copy()
    df_posicao = sheets["posição"].copy()
    df_sulco = sheets["sulco"].copy()

    df_pneus.columns = df_pneus.columns.str.strip()
    df_posicao.columns = df_posicao.columns.str.strip()
    df_sulco.columns  = df_sulco.columns.str.strip()

    # Normalizações
    df_pneus["Aferição - Sulco"] = df_pneus["Aferição - Sulco"].apply(to_float)
    df_sulco["Sulco"] = df_sulco["Sulco"].apply(to_float)
    df_pneus["Hodômetro Inicial"] = df_pneus["Hodômetro Inicial"].apply(to_float)
    df_pneus["Vida do Pneu - Km. Rodado"] = df_pneus.get("Vida do Pneu - Km. Rodado", pd.Series(np.nan)).apply(to_float)
    df_pneus["Observação - Km"] = df_pneus.get("Observação", pd.Series()).apply(extrair_km_observacao)

    # Km Rodado até Aferição
    df_pneus["Km Rodado até Aferição"] = df_pneus["Vida do Pneu - Km. Rodado"]
    mask_km_vazio = df_pneus["Km Rodado até Aferição"].isna() | (df_pneus["Km Rodado até Aferição"] <= 0)
    df_pneus.loc[mask_km_vazio, "Km Rodado até Aferição"] = df_pneus.loc[mask_km_vazio, "Observação - Km"] - df_pneus.loc[mask_km_vazio, "Hodômetro Inicial"]
    df_pneus.loc[df_pneus["Km Rodado até Aferição"] <= 0, "Km Rodado até Aferição"] = np.nan

    # Mapear posição
    col_map_pos = {"SIGLA": "Sigla da Posição", "POSIÇÃO": "Posição"}
    df_posicao = df_posicao.rename(columns={k:v for k,v in col_map_pos.items() if k in df_posicao.columns})
    if "Sigla da Posição" in df_pneus.columns and "Sigla da Posição" in df_posicao.columns:
        df_pneus = df_pneus.merge(df_posicao, on="Sigla da Posição", how="left")

    # Sulco inicial robusto
    df_pneus["_VIDA"]   = df_pneus["Vida"].apply(normalize_text)
    df_pneus["_MODELO"] = df_pneus["Modelo (Atual)"].apply(normalize_text)
    df_sulco["_VIDA"]   = df_sulco["Vida"].apply(normalize_text)
    df_sulco["_MODELO"] = df_sulco["Modelo (Atual)"].apply(normalize_text)

    base = df_sulco[["_VIDA","_MODELO","Sulco"]].dropna(subset=["Sulco"]).drop_duplicates(subset=["_VIDA","_MODELO"])
    df_pneus = df_pneus.merge(base.rename(columns={"Sulco":"Sulco Inicial"}), on=["_VIDA","_MODELO"], how="left")

    map_model_novo = df_sulco[df_sulco["_VIDA"]=="NOVO"].drop_duplicates("_MODELO").set_index("_MODELO")["Sulco"].to_dict()
    cond_f1 = df_pneus["Sulco Inicial"].isna() & (df_pneus["_VIDA"]=="NOVO")
    df_pneus.loc[cond_f1,"Sulco Inicial"] = df_pneus.loc[cond_f1,"_MODELO"].map(map_model_novo)
    map_model_any = df_sulco.dropna(subset=["Sulco"]).groupby("_MODELO")["Sulco"].median().to_dict()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "Sulco Inicial"] = df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "_MODELO"].map(map_model_any)
    mediana_por_vida = df_sulco.dropna(subset=["Sulco"]).groupby("_VIDA")["Sulco"].median()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "Sulco Inicial"] = df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "_VIDA"].map(mediana_por_vida)
    df_pneus["Sulco Inicial"].fillna(df_sulco["Sulco"].median(), inplace=True)

    # Cálculos derivados
    df_pneus["Sulco Consumido"] = df_pneus["Sulco Inicial"] - df_pneus["Aferição - Sulco"]
    df_pneus["Desgaste (mm/km)"] = np.where((df_pneus["Km Rodado até Aferição"].notna()) & (df_pneus["Km Rodado até Aferição"]>0),
                                             df_pneus["Sulco Consumido"] / df_pneus["Km Rodado até Aferição"], np.nan)
    df_pneus["Tipo Veículo"] = df_pneus.get("Veículo - Descrição", pd.Series()).apply(classificar_veiculo)

    # Reorganizar colunas
    cols = df_pneus.columns.tolist()
    if "Sulco Inicial" in cols:
        cols.remove("Sulco Inicial")
        idx = cols.index("Vida")+1 if "Vida" in cols else 0
        cols.insert(idx, "Sulco Inicial")
    if "Status" in cols:
        cols.remove("Status")
        cols.append("Status")
    df_pneus = df_pneus[cols]

    # ----------------- ABAS -----------------
    aba1, aba2, aba3, aba4, aba5 = st.tabs(["📌 Indicadores","📈 Gráficos","📏 Medidas de Sulco","📑 Tabela Completa","📖 Legenda"])

    # ----------------- ABA INDICADORES -----------------
    with aba1:
        st.subheader("📌 Indicadores Gerais")

        # Total de Pneus: apenas Estoque + Caminhão
        df_total = df_pneus[df_pneus["Status"].isin(["Estoque","Caminhão"])]
        total_pneus = len(df_total)

        # Pneus ativos: Status "Pneus"
        df_pneus_status = df_pneus[df_pneus["Status"]=="Pneus"]
        total_pneus_ativos = len(df_pneus_status)

        # Estoque
        estoque = int(df_total["Status"].value_counts().get("Estoque",0))
        # Caminhão
        caminhao = int(df_total["Status"].value_counts().get("Caminhão",0))
        # Sucata: +6
        sucata = int(df_pneus["Status"].value_counts().get("Sucata",0)) + 6

        # Km Total Rodado (somente Estoque + Caminhão)
        km_total = df_total["Km Rodado até Aferição"].dropna().sum()
        km_total_str = f"{int(km_total):,} km" if km_total > 0 else "0 km"

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", estoque)
        col3.metric("🚚 Caminhão", caminhao)
        col4.metric("♻️ Sucata", sucata)
        col5.metric("🛣️ Km Total Rodado", km_total_str)

    # ----------------- ABA MEDIDAS DE SULCO -----------------
    with aba3:
        st.subheader("📏 Medidas de Sulco")
        cols_show = ["Referência","Veículo - Placa","Veículo - Descrição","Marca (Atual)","Modelo (Atual)",
                     "Vida","Sulco Inicial","Status","Aferição - Sulco","Sulco Consumido","Km Rodado até Aferição",
                     "Desgaste (mm/km)","Posição","Sigla da Posição"]
        cols_show = [c for c in cols_show if c in df_pneus.columns]

        df_med = df_pneus[cols_show].copy()
        # Formatar coluna Km
        if "Km Rodado até Aferição" in df_med.columns:
            df_med["Km Rodado até Aferição"] = df_med["Km Rodado até Aferição"].apply(lambda x: f"{int(x):,} km" if pd.notna(x) else "")
        st.dataframe(df_med.style.applymap(colorir_sulco,subset=["Aferição - Sulco"]),use_container_width=True)
