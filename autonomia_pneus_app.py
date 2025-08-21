import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus - Dashboard Interativo")

# ----------------- UPLOAD -----------------
arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    df = pd.read_excel(arquivo, engine="openpyxl")

    # ----------------- TRATAMENTO DE DADOS -----------------
    def extrair_km(texto):
        if pd.isna(texto):
            return None
        match = re.search(r"(\d+)\s*km", str(texto))
        if match:
            return int(match.group(1))
        return None

    df["Observação - Km"] = df["Observação"].apply(extrair_km)
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]
    df["Km Rodado até Aferição"] = df["Km Rodado até Aferição"].fillna(0)
    df["Tipo Pneu"] = df["Vida"].fillna("Novo")

    # ----------------- ABAS -----------------
    aba1, aba2, aba3, aba4 = st.tabs(["📌 Indicadores", "📈 Gráficos", "📑 Tabela Completa", "📊 Histórico de Trocas"])

    # ----------------- INDICADORES -----------------
    with aba1:
        st.subheader("📌 KPIs Gerais")
        total_pneus = df["Referência"].nunique()
        estoque = df["Status"].value_counts().get("Estoque", 0)
        sucata = df["Status"].value_counts().get("Sucata", 0)
        caminhao = df["Status"].value_counts().get("Caminhão", 0)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label="🛞 Total Pneus", value=f"{total_pneus:,}", delta=None)
        col2.metric(label="📦 Estoque", value=f"{estoque:,}", delta=None)
        col3.metric(label="♻️ Sucata", value=f"{sucata:,}", delta=None)
        col4.metric(label="🚚 Caminhão", value=f"{caminhao:,}", delta=None)

        col5, col6, col7 = st.columns(3)
        media_sulco = df["Aferição - Sulco"].dropna().mean()
        media_km = df["Km Rodado até Aferição"].dropna().mean()
        pneus_criticos = df[df["Aferição - Sulco"] < 2]
        perc_critico = len(pneus_criticos) / len(df) * 100 if len(df) > 0 else 0

        # Indicadores maiores usando markdown
        col5.markdown(f"<h2 style='text-align:center; color:green;'>{media_sulco:.2f} mm</h2><p style='text-align:center;'>Média Sulco</p>", unsafe_allow_html=True)
        col6.markdown(f"<h2 style='text-align:center; color:blue;'>{media_km:,.0f} km</h2><p style='text-align:center;'>Média Km até Aferição</p>", unsafe_allow_html=True)
        col7.markdown(f"<h2 style='text-align:center; color:red;'>{len(pneus_criticos)}</h2><p style='text-align:center;'>Pneus Críticos (<2mm)</p><p style='text-align:center;'>{perc_critico:.1f}%</p>", unsafe_allow_html=True)

    # ----------------- GRÁFICOS -----------------
    with aba2:
        st.subheader("📈 Gráficos Interativos")

        if not df.empty and "Km Rodado até Aferição" in df.columns and "Aferição - Sulco" in df.columns:
            st.markdown("**Gráfico 1: Relação Km Rodado x Sulco**  \nVisualiza como o desgaste do pneu (sulco em mm) está relacionado com a quilometragem rodada. Cada ponto representa um pneu e é colorido pelo tipo de pneu.")
            fig1 = px.scatter(
                df,
                x="Km Rodado até Aferição",
                y="Aferição - Sulco",
                color="Tipo Pneu",
                hover_data=["Veículo - Placa", "Modelo (Atual)", "Marca (Atual)", "Status"],
                title="Relação Km Rodado x Sulco",
                color_discrete_sequence=px.colors.qualitative.Set2,
                height=500
            )
            st.plotly_chart(fig1, use_container_width=True)

        st.markdown("**Gráfico 2: Distribuição do Sulco por Marca**  \nMostra a variação do sulco dos pneus de cada marca, permitindo identificar quais marcas tendem a durar mais ou menos.")
        fig2 = px.box(
            df,
            x="Marca (Atual)",
            y="Aferição - Sulco",
            color="Marca (Atual)",
            title="Distribuição do Sulco por Marca",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            height=500
        )
        st.plotly_chart(fig2, use_container_width=True)

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

        st.dataframe(df_filtrado.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]), use_container_width=True)

    # ----------------- HISTÓRICO DE TROCAS -----------------
    with aba4:
        st.subheader("📊 Histórico de Trocas e Vida Útil dos Pneus")
        if not df.empty:
            resumo = df.groupby("Tipo Pneu")["Km Rodado até Aferição"].agg(
                Total_Pneus="count",
                Km_Médio="mean",
                Km_Mínimo="min",
                Km_Máximo="max"
            ).reset_index()

            resumo["Km_Médio"] = resumo["Km_Médio"].apply(lambda x: f"{x:,.0f} km")
            resumo["Km_Mínimo"] = resumo["Km_Mínimo"].apply(lambda x: f"{x:,.0f} km")
            resumo["Km_Máximo"] = resumo["Km_Máximo"].apply(lambda x: f"{x:,.0f} km")

            st.dataframe(resumo, use_container_width=True)

            fig3 = px.bar(
                df.groupby("Tipo Pneu")["Km Rodado até Aferição"].mean().reset_index(),
                x="Tipo Pneu",
                y="Km Rodado até Aferição",
                text="Km Rodado até Aferição",
                title="Km Médio por Tipo de Pneu",
                color="Tipo Pneu",
                color_discrete_sequence=px.colors.qualitative.Set2,
                height=500
            )
            fig3.update_traces(texttemplate='%{y:.0f} km', textposition='outside')
            st.plotly_chart(fig3, use_container_width=True)
