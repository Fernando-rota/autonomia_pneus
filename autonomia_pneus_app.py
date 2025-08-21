import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    df = pd.read_excel(arquivo, engine="openpyxl")

    # Função para extrair km da observação
    def extrair_km_observacao(texto):
        if pd.isna(texto):
            return None
        match = re.search(r"(\d+)\s*km", str(texto))
        if match:
            return int(match.group(1))
        return None

    df["Observação - Km"] = df["Observação"].apply(extrair_km_observacao)
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]

    # ----------------- AJUSTE DE ESTOQUE -----------------
    # Adicionar 6 pneus extras em Sucata
    df_extra = pd.DataFrame({
        "Referência": [f"Extra{i}" for i in range(1, 7)],
        "Status": ["Sucata"]*6,
        "Veículo - Placa": [None]*6,
        "Modelo (Atual)": [None]*6,
        "Marca (Atual)": [None]*6,
        "Aferição - Sulco": [0]*6,
        "Hodômetro Inicial": [0]*6,
        "Observação": [None]*6,
        "Vida": ["Ressolado"]*6
    })
    df = pd.concat([df, df_extra], ignore_index=True)
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]

    aba1, aba2, aba3 = st.tabs(["📌 Indicadores", "📈 Gráficos", "📑 Tabela Completa"])

    # ----------------- INDICADORES -----------------
    with aba1:
        st.subheader("📌 Indicadores Gerais")

        total_pneus = df["Referência"].nunique()
        status_counts = df["Status"].value_counts()
        estoque = status_counts.get("Estoque", 0)
        sucata = status_counts.get("Sucata", 0)
        caminhao = status_counts.get("Caminhão", 0)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", estoque)
        col3.metric("♻️ Sucata", sucata)
        col4.metric("🚚 Caminhão", caminhao)

        col5, col6, col7 = st.columns(3)
        media_sulco = df["Aferição - Sulco"].dropna().mean()
        media_km = df["Km Rodado até Aferição"].dropna().mean()
        pneu_critico = df[df["Aferição - Sulco"] < 2]
        perc_critico = len(pneu_critico) / len(df) * 100

        col5.metric("🟢 Média Sulco (mm)", f"{media_sulco:.2f}")
        col6.metric("🛣️ Média Km até Aferição", f"{media_km:,.0f} km")
        col7.metric("⚠️ Pneus Críticos (<2mm)", len(pneu_critico), f"{perc_critico:.1f}%")

    # ----------------- GRÁFICOS -----------------
    with aba2:
        st.subheader("📈 Gráficos Interativos")

        # Scatter Km x Sulco
        st.markdown(
            "**Gráfico 1: Relação Km Rodado x Sulco**  \n"
            "Cada ponto representa um pneu. O eixo X mostra a quilometragem rodada até a aferição, "
            "e o eixo Y mostra a profundidade do sulco. "
            "As cores representam a marca atual do pneu."
        )
        if "Km Rodado até Aferição" in df.columns and "Aferição - Sulco" in df.columns:
            fig_desgaste = px.scatter(
                df,
                x="Km Rodado até Aferição",
                y="Aferição - Sulco",
                color="Marca (Atual)",
                hover_data=["Veículo - Placa", "Modelo (Atual)", "Status"],
                color_discrete_sequence=px.colors.qualitative.Set2,
                height=500
            )
            st.plotly_chart(fig_desgaste, use_container_width=True)

        # Boxplot de sulco por marca
        st.markdown(
            "**Gráfico 2: Distribuição do Sulco por Marca**  \n"
            "Este gráfico mostra a distribuição da profundidade do sulco por marca de pneu. "
            "Permite identificar quais marcas estão mais desgastadas ou mais conservadas."
        )
        fig_box = px.box(
            df,
            x="Marca (Atual)",
            y="Aferição - Sulco",
            color="Marca (Atual)",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            height=500
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # ----------------- TABELA -----------------
    with aba3:
        st.subheader("📑 Tabela Completa")
        status_filter = st.multiselect("Filtrar por Status", options=df["Status"].unique(), default=df["Status"].unique())
        df_filtrado = df[df["Status"].isin(status_filter)]

        def colorir_sulco(val):
            if pd.isna(val):
                return ""
            elif val < 2:
                return "background-color: #FF6B6B; color: white"
            elif val < 4:
                return "background-color: #FFD93D; color: black"
            else:
                return "background-color: #6BCB77; color: white"

        st.dataframe(
            df_filtrado.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )
