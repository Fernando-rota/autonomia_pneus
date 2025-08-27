import streamlit as st
import pandas as pd
import numpy as np
import re
import unicodedata

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

# ----------------- FUNÇÕES AUXILIARES -----------------
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

# ----------------- PROCESSAMENTO -----------------
if arquivo:
    sheets = pd.read_excel(arquivo, engine="openpyxl", sheet_name=None)
    if not {"pneus", "posição", "sulco"}.issubset(set(sheets.keys())):
        st.error("O arquivo precisa conter as abas: 'pneus', 'posição' e 'sulco'.")
        st.stop()

    df_pneus = sheets["pneus"].copy()
    df_posicao = sheets["posição"].copy()
    df_sulco = sheets["sulco"].copy()

    # Normaliza nomes de colunas
    df_pneus.columns = df_pneus.columns.str.strip()
    df_posicao.columns = df_posicao.columns.str.strip()
    df_sulco.columns  = df_sulco.columns.str.strip()

    # ----------------- NORMALIZAÇÕES -----------------
    df_pneus["Aferição - Sulco"] = df_pneus["Aferição - Sulco"].apply(to_float)
    df_sulco["Sulco"] = df_sulco["Sulco"].apply(to_float)
    df_pneus["Hodômetro Inicial"] = df_pneus.get("Hodômetro Inicial", np.nan).apply(to_float)
    df_pneus["Vida do Pneu - Km. Rodado"] = df_pneus.get("Vida do Pneu - Km. Rodado", np.nan).apply(to_float)
    df_pneus["Observação - Km"] = df_pneus.get("Observação", np.nan).apply(extrair_km_observacao)

    # Km rodado até aferição
    df_pneus["Km Rodado até Aferição"] = df_pneus["Vida do Pneu - Km. Rodado"]
    mask_km_vazio = df_pneus["Km Rodado até Aferição"].isna() | (df_pneus["Km Rodado até Aferição"] <= 0)
    df_pneus.loc[mask_km_vazio, "Km Rodado até Aferição"] = (
        df_pneus.loc[mask_km_vazio, "Observação - Km"] - df_pneus.loc[mask_km_vazio, "Hodômetro Inicial"]
    )
    df_pneus.loc[df_pneus["Km Rodado até Aferição"] <= 0, "Km Rodado até Aferição"] = np.nan

    # ----------------- MERGE POSIÇÃO -----------------
    df_posicao = df_posicao.rename(columns={"SIGLA": "Sigla da Posição", "POSIÇÃO": "Posição"})
    if "Sigla da Posição" in df_pneus.columns:
        df_pneus = df_pneus.merge(df_posicao, on="Sigla da Posição", how="left")

    # ----------------- SULCO INICIAL -----------------
    for col in ["Vida", "Modelo (Atual)"]:
        if col not in df_pneus.columns or col not in df_sulco.columns:
            st.error(f"Coluna '{col}' não encontrada.")
            st.stop()

    df_pneus["_VIDA"] = df_pneus["Vida"].apply(normalize_text)
    df_pneus["_MODELO"] = df_pneus["Modelo (Atual)"].apply(normalize_text).str.replace(r"\s+", " ", regex=True)
    df_sulco["_VIDA"] = df_sulco["Vida"].apply(normalize_text)
    df_sulco["_MODELO"] = df_sulco["Modelo (Atual)"].apply(normalize_text).str.replace(r"\s+", " ", regex=True)

    base = df_sulco[["_VIDA", "_MODELO", "Sulco"]].dropna(subset=["Sulco"]).drop_duplicates(subset=["_VIDA","_MODELO"])
    df_pneus = df_pneus.merge(base.rename(columns={"Sulco":"Sulco Inicial"}), on=["_VIDA","_MODELO"], how="left")

    map_model_novo = df_sulco[df_sulco["_VIDA"]=="NOVO"].dropna(subset=["Sulco"]).drop_duplicates("_MODELO").set_index("_MODELO")["Sulco"].to_dict()
    map_model_any = df_sulco.dropna(subset=["Sulco"]).groupby("_MODELO")["Sulco"].median().to_dict()
    mediana_por_vida = df_sulco.dropna(subset=["Sulco"]).groupby("_VIDA")["Sulco"].median()

    df_pneus["Sulco Inicial"] = (
        df_pneus["Sulco Inicial"]
        .combine_first(df_pneus["_MODELO"].map(map_model_novo))
        .combine_first(df_pneus["_MODELO"].map(map_model_any))
        .combine_first(df_pneus["_VIDA"].map(mediana_por_vida))
        .fillna(df_sulco["Sulco"].median())
    )

    # ----------------- CÁLCULOS -----------------
    df_pneus["Sulco Consumido"] = df_pneus["Sulco Inicial"] - df_pneus["Aferição - Sulco"]
    df_pneus["Desgaste (mm/km)"] = np.where(
        df_pneus["Km Rodado até Aferição"].notna() & (df_pneus["Km Rodado até Aferição"]>0),
        df_pneus["Sulco Consumido"] / df_pneus["Km Rodado até Aferição"],
        np.nan
    )
    df_pneus["Tipo Veículo"] = df_pneus.get("Veículo - Descrição", "").apply(classificar_veiculo)

    # ----------------- ORDEM DE COLUNAS -----------------
    cols = df_pneus.columns.tolist()
    def insert_after(col_list, new_col, after_col):
        if new_col not in col_list:
            return col_list
        col_list = [c for c in col_list if c != new_col]
        if after_col in col_list:
            idx = col_list.index(after_col)+1
        else:
            idx = 0
        return col_list[:idx] + [new_col] + col_list[idx:]
    if "Vida" in cols and "Sulco Inicial" in cols:
        cols = insert_after(cols, "Sulco Inicial", "Vida")
    if "Status" in cols and "Sulco Inicial" in cols:
        cols = [c for c in cols if c != "Status"]
        si_idx = cols.index("Sulco Inicial")
        cols = cols[:si_idx+1] + ["Status"] + cols[si_idx+1:]
    df_pneus = df_pneus[cols]

    # ----------------- ABAS -----------------
    aba1, aba2, aba3, aba4, aba5 = st.tabs([
        "📌 Indicadores",
        "📈 Gráficos",
        "📏 Medidas de Sulco",
        "📑 Tabela Completa",
        "📖 Legenda"
    ])

    # ----------------- INDICADORES -----------------
    with aba1:
        st.subheader("📌 Indicadores Gerais")
        total_pneus = df_pneus["Referência"].nunique() if "Referência" in df_pneus.columns else len(df_pneus)
        status_counts = df_pneus["Status"].value_counts(dropna=False) if "Status" in df_pneus.columns else pd.Series()
        estoque = int(status_counts.get("Estoque",0))
        sucata = int(status_counts.get("Sucata",0))
        caminhao = int(status_counts.get("Caminhão",0))

        col1,col2,col3,col4 = st.columns(4)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", estoque)
        col3.metric("♻️ Sucata", sucata)
        col4.metric("🚚 Caminhão", caminhao)

    # ----------------- MEDIDAS DE SULCO -----------------
    with aba3:
        st.subheader("📏 Medidas de Sulco (com cálculos)")
        cols_show = [c for c in [
            "Referência","Veículo - Placa","Veículo - Descrição","Marca (Atual)","Modelo (Atual)",
            "Vida","Sulco Inicial","Status","Aferição - Sulco","Sulco Consumido","Km Rodado até Aferição",
            "Desgaste (mm/km)","Posição","Sigla da Posição"
        ] if c in df_pneus.columns]
        df_show = df_pneus[cols_show].copy()
        df_show["Km Rodado até Aferição"] = df_show["Km Rodado até Aferição"].apply(
            lambda x: f"{x:,.0f} km" if pd.notna(x) and x>0 else "-"
        )
        st.dataframe(
            df_show.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]) \
                         .format({
                             "Sulco Inicial":"{:.2f}",
                             "Aferição - Sulco":"{:.2f}",
                             "Sulco Consumido":"{:.2f}",
                             "Desgaste (mm/km)":"{:.6f}"
                         }),
            use_container_width=True
        )
else:
    st.info("Aguardando upload do arquivo Excel…")
import pandas as pd
import streamlit as st

st.title("Análise de Pneus")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Escolha um arquivo Excel (.xls ou .xlsx)", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # Lê todas as abas necessárias
        xls = pd.ExcelFile(uploaded_file)
        abas = [aba.lower().replace("ç", "c") for aba in xls.sheet_names]  # Normaliza nomes das abas
        
        if "pneus" not in abas or "posicao" not in abas or "sulco" not in abas:
            st.error("O arquivo deve conter as abas: pneus, posicao e sulco")
        else:
            pneus_df = pd.read_excel(xls, sheet_name="pneus")
            posicao_df = pd.read_excel(xls, sheet_name="posicao")
            sulco_df = pd.read_excel(xls, sheet_name="sulco")

            # Exemplo de cálculos de sulco
            # Ajuste os nomes das colunas conforme seu arquivo
            sulco_df['Sulco_Consumido'] = sulco_df['Sulco_Inicial'] - sulco_df['Sulco_Atual']
            sulco_df['Desgaste_%'] = sulco_df['Sulco_Consumido'] / sulco_df['Sulco_Inicial'] * 100

            # Exemplo de indicadores
            total_pneus = len(pneus_df)
            media_sulco = sulco_df['Sulco_Atual'].mean()
            st.metric("Total de Pneus", total_pneus)
            st.metric("Média de Sulco Atual", f"{media_sulco:.2f} mm")

            # Tabela completa
            st.subheader("Detalhes de Sulco")
            st.dataframe(sulco_df)

            # Ajuste de métricas de estoque, sucata e caminhão
            # Supondo que essas colunas existam em pneus_df
            estoque_total = pneus_df['Estoque'].sum()
            sucata_total = pneus_df['Sucata'].sum()
            caminhao_total = pneus_df['Caminhao'].sum()

            st.metric("Estoque Total", estoque_total)
            st.metric("Sucata Total", sucata_total)
            st.metric("Caminhão Total", caminhao_total)

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
