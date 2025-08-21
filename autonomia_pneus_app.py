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
    # Tratamento da coluna Observação
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
    # Abas
    # ---------------------------
    aba1, aba2 = st.tabs(["📌 Indicadores", "📈 Gráficos"])

    with aba1:
        st.subheader("📌 Indicadores Gerais")

        col1, col2, col3 = st.columns(3)
        total_pneus = df["Referência"].nunique()
        media_sulco = df["Aferição - Sulco"].dropna().mean()
        media_km = df["Km Rodado até Aferição"].dropna().mean()

        col1.metric("Total de Pneus", total_pneus)
        col2.metric("Média Sulco (mm)", f"{media_sulco:.2f}")
        col3.metric("Média Km até Aferição", f"{media_km:,.0f} km")

        st.dataframe(df)

    with aba2:
        st.subheader("📈 Gráficos")

        # Gráfico de desgaste (Sulco x Km Rodado até Aferição)
        if "Km Rodado até Aferição" in df.columns and "Aferição - Sulco" in df.columns:
            fig_desgaste = px.scatter(
                df,
                x="Km Rodado até Aferição",
                y="Aferição - Sulco",
                color="Marca (Atual)",
                title="Relação entre Km Rodado e Sulco",
                hover_data=["Veículo - Placa", "Modelo (Atual)"]
            )
            st.plotly_chart(fig_desgaste, use_container_width=True)
