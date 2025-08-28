import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
import unicodedata

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

# ----------------- UPLOAD -----------------
arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

# ----------------- FUNÇÕES AUXILIARES -----------------
def to_float(x):
    if pd.isna(x): return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)): return float(x)
    s = str(x).strip()
    s = s.replace(".", "").replace(",", ".") if "," in s else s
    try: return float(s)
    except: return np.nan

def extrair_km_observacao(texto):
    if pd.isna(texto): return np.nan
    m = re.search(r"(\d[\d\.]*)\s*km", str(texto), flags=re.IGNORECASE)
    return float(m.group(1).replace(".","")) if m else np.nan

def normalize_text(s):
    if pd.isna(s): return ""
    s = str(s).strip().lower()
    s = " ".join(s.split())
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.upper()

def colorir_sulco(val):
    try:
        val = float(val)
        if val < 3: return "background-color:#E74C3C; color:white"
        elif val < 4: return "background-color:#F1C40F; color:black"
        else: return "background-color:#2ECC71; color:white"
    except: return ""

def icon_sulco(val):
    try:
        v = float(val)
        if v < 3: return "❌"
        elif v < 4: return "⚠️"
        else: return "✅"
    except: return ""

def classificar_veiculo(desc):
    if pd.isna(desc): return "Outro"
    d = str(desc).lower()
    if "saveiro" in d: return "Leve"
    if "renault" in d: return "Utilitário (Renault)"
    if "iveco" in d or "daily" in d or "scudo" in d: return "Utilitário (Iveco/Scudo)"
    if "3/4" in d or "3-4" in d: return "3/4"
    if "toco" in d: return "Toco"
    if "truck" in d: return "Truck"
    if "cavalo" in d or "carreta" in d: return "Carreta"
    return "Outro"

# ----------------- PROCESSAMENTO -----------------
if arquivo:
    sheets = pd.read_excel(arquivo, sheet_name=None)
    if not {"pneus","posição","sulco"}.issubset(set(sheets.keys())):
        st.error("O arquivo precisa conter as abas: 'pneus', 'posição' e 'sulco'.")
        st.stop()

    df_pneus = sheets["pneus"].copy()
    df_posicao = sheets["posição"].copy()
    df_sulco = sheets["sulco"].copy()

    # Normalizações básicas
    df_pneus["Aferição - Sulco"] = df_pneus["Aferição - Sulco"].apply(to_float)
    df_sulco["Sulco"] = df_sulco["Sulco"].apply(to_float)
    df_pneus["Veículo - Descrição"] = df_pneus.get("Veículo - Descrição", "")
    df_pneus["Km Rodado até Aferição"] = df_pneus.get("Vida do Pneu - Km. Rodado", np.nan)
    df_pneus["Tipo Veículo"] = df_pneus["Veículo - Descrição"].apply(classificar_veiculo)

    # Status Sulco
    df_pneus["Status Sulco"] = df_pneus["Aferição - Sulco"].apply(icon_sulco)

    # ----------------- FILTROS -----------------
    st.sidebar.header("Filtros")
    modelos = ["Todos"] + df_pneus["Modelo (Atual)"].dropna().unique().tolist()
    modelo_sel = st.sidebar.selectbox("Modelo", modelos)
    if modelo_sel != "Todos":
        df_pneus = df_pneus[df_pneus["Modelo (Atual)"]==modelo_sel]

    veiculos = ["Todos"] + df_pneus["Veículo - Placa"].dropna().unique().tolist()
    veiculo_sel = st.sidebar.selectbox("Veículo", veiculos)
    if veiculo_sel != "Todos":
        df_pneus = df_pneus[df_pneus["Veículo - Placa"]==veiculo_sel]

    # ----------------- ABAS -----------------
    aba1, aba2, aba3 = st.tabs(["📌 KPIs","📏 Tabela Detalhada","🗺️ Heatmap de Pneus"])

    # ----------------- ABA KPIs -----------------
    with aba1:
        total_pneus = len(df_pneus)
        criticos = len(df_pneus[df_pneus["Aferição - Sulco"]<3])
        sulco_medio = round(df_pneus["Aferição - Sulco"].mean(),2)
        km_medio = round(df_pneus["Km Rodado até Aferição"].mean(),0)

        col1,col2,col3,col4 = st.columns(4)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("❌ Pneus Críticos (<3mm)", criticos, f"{round(criticos/total_pneus*100,1)}%")
        col3.metric("📏 Sulco Médio (mm)", sulco_medio)
        col4.metric("⏱️ Km Médio Rodado", f"{km_medio:,.0f} km")

        # Gráfico de barras por tipo de veículo
        tipo_count = df_pneus.groupby("Tipo Veículo")["Aferição - Sulco"].mean().reset_index()
        fig = px.bar(tipo_count, x="Tipo Veículo", y="Aferição - Sulco", color="Aferição - Sulco",
                     color_continuous_scale=["red","yellow","green"], title="Sulco Médio por Tipo de Veículo")
        st.plotly_chart(fig, use_container_width=True)

    # ----------------- ABA TABELA -----------------
    with aba2:
        cols_show = ["Referência","Veículo - Placa","Veículo - Descrição","Modelo (Atual)",
                     "Aferição - Sulco","Status Sulco","Km Rodado até Aferição"]
        df_show = df_pneus[cols_show].copy()
        df_show["Km Rodado até Aferição"] = df_show["Km Rodado até Aferição"].apply(lambda x: f"{x:,.0f} km" if pd.notna(x) else "-")
        st.dataframe(df_show.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]), use_container_width=True)

    # ----------------- ABA HEATMAP -----------------
    with aba3:
        st.subheader("🗺️ Heatmap da Posição dos Pneus")
        if {"Posição","Aferição - Sulco"}.issubset(df_pneus.columns):
            fig = go.Figure()
            for idx, row in df_pneus.iterrows():
                color = "#2ECC71" if row["Aferição - Sulco"]>=4 else "#F1C40F" if row["Aferição - Sulco"]>=3 else "#E74C3C"
                fig.add_trace(go.Scatter(x=[row["Posição"]], y=[1], mode="markers+text",
                                         marker=dict(size=50, color=color),
                                         text=row["Veículo - Placa"], textposition="bottom center"))
            fig.update_layout(height=300, xaxis_title="Posição", yaxis_visible=False, yaxis_showticklabels=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Não há dados de posição para gerar o heatmap.")
else:
    st.info("Aguardando upload do arquivo Excel…")
