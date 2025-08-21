import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Gestão de Pneus", layout="wide")

st.title("📊 Gestão de Pneus")

# Upload
arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    # Lê a planilha
    df = pd.read_excel(arquivo, engine="openpyxl")

    # ---------------------------
    # Tratamento da coluna Observação (extrair km)
    # ---------------------------
    def extrair_km_observacao(texto):
        if pd.isna(texto):
            return None
        match = re.search(r"(\d+)\s*km", str(texto))
        if match:
            return int(match.group(1))
        return None

    df["Observação - Km"] = df["Observação"].apply(extrair_km_observacao)

    # ---------------------------
    # Km Rodado até Aferição
    # ---------------------------
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]

    # ---------------------------
    # Criação das abas
    # ---------------------------
    aba1, aba2, aba3 = st.tabs(["📌 Indicadores", "📈 Gráficos", "📑 Tabela Completa"])

    # ---------------------------
    # Indicadores
    # ---------------------------
    with aba1:
        st.subheader("📌 Indicadores Gerais")

        # Total de pneus
        total_pneus = df["Referência"].nunique()

        # Contagem por status
        status_counts = df["Status"].value_counts()

        estoque = status_counts.get("Estoque", 0)
        sucata = status_counts.get("Sucata", 0)
        caminhao = status_counts.get("Caminhão", 0)

        # KPIs principais
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Pneus", total_pneus)
        col2.metric("Estoque", estoque)
        col3.metric("Sucata", sucata)
        col4.metric("Caminhão", caminhao)

        # Outras métricas
        col5, col6 = st.columns(2)
        media_sulco = df["Aferição - Sulco"].dropna().mean()
        media_km = df["Km Rodado até Aferição"].dropna().mean()

        col5.metric("Média Sulco (mm)", f"{media_sulco:.2f}")
        col6.metric("Média Km até Aferição", f"{media_km:,.0f} km")

    # ---------------------------
    # Gráficos
    # ---------------------------
    with aba2:
        st.subheader("📈 Gráficos")

        if "Km Rodado até Aferição" in df.columns and "Aferição - Sulco" in df.columns:
            fig_desgaste = px.scatter(
                df,
                x="Km Rodado até Aferição",
                y="Aferição - Sulco",
                color="Marca (Atual)",
                title="Relação entre Km Rodado e Sulco",
                hover_data=["Veículo - Placa", "Modelo (Atual)", "Status"]
            )
            st.plotly_chart(fig_desgaste, use_container_width=True)

    # ---------------------------
    # Tabela Completa
    # ---------------------------
    with aba3:
        st.subheader("📑 Tabela Completa")
        st.dataframe(df)
