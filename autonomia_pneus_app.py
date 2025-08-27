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

# ----------------- NORMALIZAÇÃO DE COLUNAS -----------------
def normalizar_colunas(df):
    df.columns = (
        df.columns.str.strip()
        .str.upper()
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .str.decode("utf-8")
    )
    return df

if arquivo:
    sheets = pd.read_excel(arquivo, engine="openpyxl", sheet_name=None)

    # normaliza todos os dataframes
    df_pneus = normalizar_colunas(sheets.get("PNEUS", pd.DataFrame()))
    df_posicao = normalizar_colunas(sheets.get("POSICAO", pd.DataFrame()))
    df_sulco = normalizar_colunas(sheets.get("SULCO", pd.DataFrame()))

    # --- padroniza colunas de sulco ---
    possiveis_nomes_sulco = [c for c in df_sulco.columns if "SULCO" in c]
    if not possiveis_nomes_sulco:
        st.error(f"Nenhuma coluna 'Sulco' encontrada na aba sulco. Colunas disponíveis: {df_sulco.columns.tolist()}")
        st.stop()
    df_sulco = df_sulco.rename(columns={possiveis_nomes_sulco[0]: "SULCO"})

    # ----------------- AJUSTES NUMÉRICOS -----------------
    if "AFERICAO - SULCO" in df_pneus.columns:
        df_pneus["AFERICAO - SULCO"] = df_pneus["AFERICAO - SULCO"].apply(to_float)
    if "SULCO" in df_sulco.columns:
        df_sulco["SULCO"] = df_sulco["SULCO"].apply(to_float)
    if "HODOMETRO INICIAL" in df_pneus.columns:
        df_pneus["HODOMETRO INICIAL"] = df_pneus["HODOMETRO INICIAL"].apply(to_float)
    if "VIDA DO PNEU - KM. RODADO" in df_pneus.columns:
        df_pneus["VIDA DO PNEU - KM. RODADO"] = df_pneus["VIDA DO PNEU - KM. RODADO"].apply(to_float)
    if "OBSERVACAO" in df_pneus.columns:
        df_pneus["OBSERVACAO - KM"] = df_pneus["OBSERVACAO"].apply(extrair_km_observacao)

    # ----------------- KM RODADO ATÉ AFERIÇÃO -----------------
    if "VIDA DO PNEU - KM. RODADO" in df_pneus.columns:
        df_pneus["KM RODADO ATE AFERICAO"] = df_pneus["VIDA DO PNEU - KM. RODADO"]
        mask_km_vazio = df_pneus["KM RODADO ATE AFERICAO"].isna() | (df_pneus["KM RODADO ATE AFERICAO"] <= 0)
        if "OBSERVACAO - KM" in df_pneus.columns and "HODOMETRO INICIAL" in df_pneus.columns:
            df_pneus.loc[mask_km_vazio, "KM RODADO ATE AFERICAO"] = (
                df_pneus.loc[mask_km_vazio, "OBSERVACAO - KM"] - df_pneus.loc[mask_km_vazio, "HODOMETRO INICIAL"]
            )
        df_pneus.loc[df_pneus["KM RODADO ATE AFERICAO"] <= 0, "KM RODADO ATE AFERICAO"] = np.nan

    # ----------------- MAPA POSIÇÃO -----------------
    col_map_pos = {}
    if "SIGLA" in df_posicao.columns:
        col_map_pos["SIGLA"] = "SIGLA DA POSICAO"
    if "POSICAO" in df_posicao.columns:
        col_map_pos["POSICAO"] = "POSICAO"
    df_posicao = df_posicao.rename(columns=col_map_pos)
    if "SIGLA DA POSICAO" in df_pneus.columns and "SIGLA DA POSICAO" in df_posicao.columns:
        df_pneus = df_pneus.merge(df_posicao, on="SIGLA DA POSICAO", how="left")

    # ----------------- SULCO INICIAL -----------------
    if "VIDA" in df_pneus.columns and "MODELO (ATUAL)" in df_pneus.columns:
        df_pneus["_VIDA"] = df_pneus["VIDA"].apply(normalize_text)
        df_pneus["_MODELO"] = df_pneus["MODELO (ATUAL)"].apply(normalize_text)
        df_sulco["_VIDA"] = df_sulco["VIDA"].apply(normalize_text)
        df_sulco["_MODELO"] = df_sulco["MODELO (ATUAL)"].apply(normalize_text)

        base = df_sulco[["_VIDA", "_MODELO", "SULCO"]].dropna(subset=["SULCO"]).drop_duplicates(subset=["_VIDA", "_MODELO"])
        df_pneus = df_pneus.merge(base.rename(columns={"SULCO": "SULCO INICIAL"}), on=["_VIDA","_MODELO"], how="left")

        # fallbacks
        map_model_novo = df_sulco[df_sulco["_VIDA"]=="NOVO"].dropna(subset=["SULCO"]).drop_duplicates("_MODELO").set_index("_MODELO")["SULCO"].to_dict()
        df_pneus.loc[df_pneus["SULCO INICIAL"].isna() & (df_pneus["_VIDA"]=="NOVO"), "SULCO INICIAL"] = df_pneus.loc[df_pneus["SULCO INICIAL"].isna() & (df_pneus["_VIDA"]=="NOVO"), "_MODELO"].map(map_model_novo)
        map_model_any = df_sulco.dropna(subset=["SULCO"]).groupby("_MODELO")["SULCO"].median().to_dict()
        df_pneus.loc[df_pneus["SULCO INICIAL"].isna(), "SULCO INICIAL"] = df_pneus.loc[df_pneus["SULCO INICIAL"].isna(), "_MODELO"].map(map_model_any)
        mediana_por_vida = df_sulco.dropna(subset=["SULCO"]).groupby("_VIDA")["SULCO"].median()
        df_pneus.loc[df_pneus["SULCO INICIAL"].isna(), "SULCO INICIAL"] = df_pneus.loc[df_pneus["SULCO INICIAL"].isna(), "_VIDA"].map(mediana_por_vida)
        if df_pneus["SULCO INICIAL"].isna().any():
            df_pneus["SULCO INICIAL"].fillna(df_sulco["SULCO"].dropna().median(), inplace=True)

    # ----------------- CALCULOS DERIVADOS -----------------
    if "SULCO INICIAL" in df_pneus.columns and "AFERICAO - SULCO" in df_pneus.columns:
        df_pneus["SULCO CONSUMIDO"] = df_pneus["SULCO INICIAL"] - df_pneus["AFERICAO - SULCO"]
    if "KM RODADO ATE AFERICAO" in df_pneus.columns:
        df_pneus["DESGASTE (MM/KM)"] = np.where(
            (df_pneus["KM RODADO ATE AFERICAO"].notna()) & (df_pneus["KM RODADO ATE AFERICAO"]>0),
            df_pneus["SULCO CONSUMIDO"]/df_pneus["KM RODADO ATE AFERICAO"],
            np.nan
        )
    if "VEICULO - DESCRICAO" in df_pneus.columns:
        df_pneus["TIPO VEICULO"] = df_pneus["VEICULO - DESCRICAO"].apply(classificar_veiculo)

    # ----------------- INTERFACE -----------------
    aba1, aba2 = st.tabs(["📌 Indicadores", "📏 Medidas de Sulco"])

    with aba1:
        st.subheader("📌 Indicadores Gerais")
        total_pneus = df_pneus["REFERENCIA"].nunique() if "REFERENCIA" in df_pneus.columns else len(df_pneus)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", 99)
        col3.metric("♻️ Sucata", 14)
        col4.metric("🚚 Caminhão", 383)

    with aba2:
        st.subheader("📏 Medidas de Sulco (com cálculos)")
        cols_show = [c for c in [
            "REFERENCIA","VEICULO - PLACA","VEICULO - DESCRICAO","MARCA (ATUAL)","MODELO (ATUAL)",
            "VIDA","SULCO INICIAL","STATUS","AFERICAO - SULCO","SULCO CONSUMIDO","KM RODADO ATE AFERICAO",
            "DESGASTE (MM/KM)","POSICAO","SIGLA DA POSICAO"
        ] if c in df_pneus.columns]
        df_show = df_pneus[cols_show].copy()
        st.dataframe(
            df_show.style.applymap(colorir_sulco, subset=["AFERICAO - SULCO"])
                         .format({
                             "SULCO INICIAL":"{:.2f}",
                             "AFERICAO - SULCO":"{:.2f}",
                             "SULCO CONSUMIDO":"{:.2f}",
                             "DESGASTE (MM/KM)":"{:.6f}",
                             "KM RODADO ATE AFERICAO":"{:,.0f} km"
                         }),
            use_container_width=True
        )
else:
    st.info("Aguardando upload do arquivo Excel…")
