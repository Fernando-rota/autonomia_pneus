import streamlit as st
import pandas as pd
import plotly.express as px
import re
import unicodedata
import numpy as np

# ----------------- CONFIG -----------------
st.set_page_config(page_title="Gestão de Pneus", layout="wide")

# CSS customizado
st.markdown("""
<style>
/* Fundo */
body {
    background-color: #f9f9f9;
}
/* Cards de métricas */
div[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e6e6e6;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.1);
}
/* Dataframe estilizado */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center; color:#1E88E5;'>📊 Gestão de Pneus</h2>", unsafe_allow_html=True)

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

# ----------------- CACHE -----------------
@st.cache_data
def carregar_planilhas(arquivo):
    return pd.read_excel(arquivo, engine="openpyxl", sheet_name=None)

# ----------------- UPLOAD -----------------
arquivo = st.file_uploader("📂 Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    sheets = carregar_planilhas(arquivo)
    if not {"pneus", "posição", "sulco"}.issubset(set(sheets.keys())):
        st.error("O arquivo precisa conter as abas: 'pneus', 'posição' e 'sulco'.")
        st.stop()

    df_pneus = sheets["pneus"].copy()
    df_posicao = sheets["posição"].copy()
    df_sulco = sheets["sulco"].copy()

    # Strip colunas
    for df in [df_pneus, df_posicao, df_sulco]:
        df.columns = df.columns.str.strip()

    # Renomeações
    renomes = {
        "Modelo": "Modelo (Atual)",
        "SULCO": "Sulco",
        "Sigla": "Sigla da Posição",
        "SIGLA": "Sigla da Posição",
        "POSIÇÃO": "Posição",
    }
    df_pneus = df_pneus.rename(columns=renomes)
    df_posicao = df_posicao.rename(columns=renomes)
    df_sulco = df_sulco.rename(columns=renomes)

    # Normalizações
    df_pneus["Aferição - Sulco"] = df_pneus["Aferição - Sulco"].apply(to_float)
    df_sulco["Sulco"] = df_sulco["Sulco"].apply(to_float)

    if "Hodômetro Inicial" in df_pneus:
        df_pneus["Hodômetro Inicial"] = df_pneus["Hodômetro Inicial"].apply(to_float)
    if "Vida do Pneu - Km. Rodado" in df_pneus:
        df_pneus["Vida do Pneu - Km. Rodado"] = df_pneus["Vida do Pneu - Km. Rodado"].apply(to_float)
    else:
        df_pneus["Vida do Pneu - Km. Rodado"] = np.nan
    if "Observação" in df_pneus:
        df_pneus["Observação - Km"] = df_pneus["Observação"].apply(extrair_km_observacao)
    else:
        df_pneus["Observação - Km"] = np.nan

    # Km rodado
    df_pneus["Km Rodado até Aferição"] = df_pneus["Vida do Pneu - Km. Rodado"]
    mask_km_vazio = df_pneus["Km Rodado até Aferição"].isna() | (df_pneus["Km Rodado até Aferição"] <= 0)
    df_pneus.loc[mask_km_vazio, "Km Rodado até Aferição"] = (
        df_pneus.loc[mask_km_vazio, "Observação - Km"] - df_pneus.loc[mask_km_vazio, "Hodômetro Inicial"]
    )
    df_pneus.loc[df_pneus["Km Rodado até Aferição"] <= 0, "Km Rodado até Aferição"] = np.nan

    # Posição
    if "Sigla da Posição" in df_pneus and "Sigla da Posição" in df_posicao:
        df_pneus = df_pneus.merge(df_posicao, on="Sigla da Posição", how="left")

    # Sulco inicial
    for col in ["Vida", "Modelo (Atual)"]:
        if col not in df_pneus or col not in df_sulco:
            st.error(f"Coluna '{col}' não encontrada.")
            st.stop()

    df_pneus["_VIDA"] = df_pneus["Vida"].apply(normalize_text)
    df_pneus["_MODELO"] = df_pneus["Modelo (Atual)"].apply(normalize_text)
    df_sulco["_VIDA"] = df_sulco["Vida"].apply(normalize_text)
    df_sulco["_MODELO"] = df_sulco["Modelo (Atual)"].apply(normalize_text)

    base = df_sulco[["_VIDA", "_MODELO", "Sulco"]].dropna().drop_duplicates(subset=["_VIDA", "_MODELO"])
    df_pneus = df_pneus.merge(base.rename(columns={"Sulco": "Sulco Inicial"}), on=["_VIDA", "_MODELO"], how="left")

    # Completar Sulco Inicial
    map_model_novo = df_sulco[df_sulco["_VIDA"] == "NOVO"].dropna(subset=["Sulco"]).drop_duplicates("_MODELO").set_index("_MODELO")["Sulco"].to_dict()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna() & (df_pneus["_VIDA"] == "NOVO"), "Sulco Inicial"] = df_pneus["_MODELO"].map(map_model_novo)

    map_model_any = df_sulco.dropna(subset=["Sulco"]).groupby("_MODELO")["Sulco"].median().to_dict()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "Sulco Inicial"] = df_pneus["_MODELO"].map(map_model_any)

    mediana_por_vida = df_sulco.dropna(subset=["Sulco"]).groupby("_VIDA")["Sulco"].median()
    df_pneus.loc[df_pneus["Sulco Inicial"].isna(), "Sulco Inicial"] = df_pneus["_VIDA"].map(mediana_por_vida)

    df_pneus["Sulco Inicial"] = df_pneus["Sulco Inicial"].fillna(df_sulco["Sulco"].dropna().median())

    # Cálculos
    df_pneus["Sulco Consumido"] = df_pneus["Sulco Inicial"] - df_pneus["Aferição - Sulco"]
    df_pneus["Desgaste (mm/km)"] = np.where(
        df_pneus["Km Rodado até Aferição"].notna() & (df_pneus["Km Rodado até Aferição"] > 0),
        df_pneus["Sulco Consumido"] / df_pneus["Km Rodado até Aferição"],
        np.nan,
    )

    df_pneus["Tipo Veículo"] = df_pneus.get("Veículo - Descrição", "").apply(classificar_veiculo)

    # ----------------- ABAS -----------------
    aba1, aba2 = st.tabs(["📌 Indicadores", "📏 Medidas de Sulco"])

    # Indicadores
    with aba1:
        st.subheader("📊 Indicadores Gerais")

        total_pneus = df_pneus["Referência"].nunique() if "Referência" in df_pneus else len(df_pneus)
        status_counts = df_pneus["Status"].value_counts(dropna=False) if "Status" in df_pneus else pd.Series()
        estoque = int(status_counts.get("Estoque", 0))
        sucata = int(status_counts.get("Sucata", 0))
        caminhao = int(status_counts.get("Caminhão", 0))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", estoque)
        col3.metric("♻️ Sucata", sucata)
        col4.metric("🚚 Caminhão", caminhao)

        # Gráfico interativo
        if "Aferição - Sulco" in df_pneus:
            fig = px.histogram(df_pneus, x="Aferição - Sulco", nbins=20, color="Tipo Veículo",
                               title="Distribuição de Aferições de Sulco")
            st.plotly_chart(fig, use_container_width=True)

    # Medidas de Sulco
    with aba2:
        st.subheader("📏 Medidas de Sulco")

        cols_show = [c for c in [
            "Referência","Veículo - Placa","Veículo - Descrição","Marca (Atual)","Modelo (Atual)",
            "Vida","Sulco Inicial","Status","Aferição - Sulco","Sulco Consumido","Km Rodado até Aferição",
            "Desgaste (mm/km)","Posição","Sigla da Posição"
        ] if c in df_pneus]

        df_show = df_pneus[cols_show].copy()

        # KPIs de sulco
        critico = (df_show["Aferição - Sulco"] < 2).sum()
        alerta = ((df_show["Aferição - Sulco"] >= 2) & (df_show["Aferição - Sulco"] < 4)).sum()

        k1, k2 = st.columns(2)
        k1.metric("🔴 Pneus Críticos (<2mm)", critico)
        k2.metric("🟡 Pneus em Alerta (2-4mm)", alerta)

        # Filtros
        with st.expander("🔎 Filtros"):
            status_sel = st.multiselect("Status", df_show["Status"].dropna().unique())
            if status_sel:
                df_show = df_show[df_show["Status"].isin(status_sel)]

            tipo_sel = st.multiselect("Tipo de Veículo", df_pneus["Tipo Veículo"].dropna().unique())
            if tipo_sel:
                df_show = df_show[df_pneus["Tipo Veículo"].isin(tipo_sel)]

        # Ordenação
        df_show = df_show.sort_values(by="Aferição - Sulco", ascending=False)

        if "Km Rodado até Aferição" in df_show:
            df_show["Km Rodado até Aferição"] = df_show["Km Rodado até Aferição"].apply(
                lambda x: f"{x:,.0f} km" if pd.notna(x) else "-"
            )

        st.dataframe(
            df_show.style.applymap(colorir_sulco, subset=["Aferição - Sulco"])
                         .format({
                             "Sulco Inicial": "{:.2f}",
                             "Aferição - Sulco": "{:.2f}",
                             "Sulco Consumido": "{:.2f}",
                             "Desgaste (mm/km)": "{:.6f}"
                         }),
            use_container_width=True,
            height=600
        )

        # Gráficos adicionais
        st.subheader("📈 Análises Visuais")
        colg1, colg2 = st.columns(2)

        with colg1:
            fig = px.box(df_pneus, x="Tipo Veículo", y="Aferição - Sulco", color="Tipo Veículo",
                         title="Sulco por Tipo de Veículo")
            st.plotly_chart(fig, use_container_width=True)

        with colg2:
            fig = px.histogram(df_show, x="Sulco Consumido", nbins=20, title="Distribuição do Sulco Consumido")
            st.plotly_chart(fig, use_container_width=True)

        # Exportação
        csv = df_show.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Baixar dados filtrados", csv, "medidas_sulco.csv", "text/csv")

else:
    st.info("📂 Aguardando upload do arquivo Excel…")
