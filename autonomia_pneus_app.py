import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus - Dashboard Profissional")

# ----------------- UPLOAD -----------------
arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    df = pd.read_excel(arquivo, engine="openpyxl")

    # ----------------- TRATAMENTO DE DADOS -----------------
    # Extrair km da coluna Observação
    df["Observação - Km"] = pd.to_numeric(df["Observação"].astype(str).str.extract(r"(\d+)\s*km")[0], errors='coerce')
    df["Km Rodado até Aferição"] = (df["Observação - Km"] - df["Hodômetro Inicial"]).fillna(0)
    df["Tipo Pneu"] = df["Vida"].fillna("Novo")

    # Criar coluna de alerta visual
    df["Alerta Sulco"] = pd.cut(df["Aferição - Sulco"],
                                bins=[-1, 2, 4, 100],
                                labels=["🔴 Crítico", "🟡 Atenção", "🟢 OK"])

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
        col1.markdown(f"<h2 style='text-align:center; color:blue;'>{total_pneus}</h2><p style='text-align:center;'>Total Pneus</p>", unsafe_allow_html=True)
        col2.markdown(f"<h2 style='text-align:center; color:green;'>{estoque}</h2><p style='text-align:center;'>Estoque</p>", unsafe_allow_html=True)
        col3.markdown(f"<h2 style='text-align:center; color:orange;'>{sucata}</h2><p style='text-align:center;'>Sucata</p>", unsafe_allow_html=True)
        col4.markdown(f"<h2 style='text-align:center; color:purple;'>{caminhao}</h2><p style='text-align:center;'>Caminhão</p>", unsafe_allow_html=True)

        col5, col6, col7 = st.columns(3)
        media_sulco = df["Aferição - Sulco"].dropna().mean()
        media_km = df["Km Rodado até Aferição"].dropna().mean()
        pneus_criticos = df[df["Alerta Sulco"]=="🔴 Crítico"]
        perc_critico = len(pneus_criticos) / len(df) * 100 if len(df) > 0 else 0

        col5.markdown(f"<h2 style='text-align:center; color:red;'>{len(pneus_criticos)}</h2><p style='text-align:center;'>Pneus Críticos</p><p style='text-align:center;'>{perc_critico:.1f}%</p>", unsafe_allow_html=True)
        col6.markdown(f"<h2 style='text-align:center; color:green;'>{media_sulco:.2f} mm</h2><p style='text-align:center;'>Média Sulco</p>", unsafe_allow_html=True)
        col7.markdown(f"<h2 style='text-align:center; color:blue;'>{media_km:,.0f} km</h2><p style='text-align:center;'>Média Km Rodado</p>", unsafe_allow_html=True)

    # ----------------- GRÁFICOS -----------------
    with aba2:
        st.subheader("📈 Gráficos Interativos")
        st.markdown("**Gráfico 1: Relação Km Rodado x Sulco**  \nMostra o desgaste do pneu em função da quilometragem. Cada ponto representa um pneu, colorido pelo tipo de pneu.")

        fig1 = px.scatter(
            df,
            x="Km Rodado até Aferição",
            y="Aferição - Sulco",
            color="Tipo Pneu",
            hover_data=["Veículo - Placa", "Modelo (Atual)", "Marca (Atual)", "Status"],
            color_discrete_sequence=px.colors.qualitative.Set2,
            height=500
        )
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("**Gráfico 2: Distribuição do Sulco por Marca**  \nPermite identificar marcas com maior durabilidade média.")
        fig2 = px.box(
            df,
            x="Marca (Atual)",
            y="Aferição - Sulco",
            color="Marca (Atual)",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            height=500
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ----------------- TABELA -----------------
    with aba3:
        st.subheader("📑 Tabela Completa")
        filtro_status = st.multiselect("Filtrar por Status", options=df["Status"].unique(), default=df["Status"].unique())
        filtro_veiculo = st.multiselect("Filtrar por Veículo", options=df["Veículo - Placa"].unique(), default=df["Veículo - Placa"].unique())
        df_filtrado = df[df["Status"].isin(filtro_status) & df["Veículo - Placa"].isin(filtro_veiculo)]

        def colorir_sulco(val):
            if val == "🔴 Crítico":
                return "background-color:#FF6B6B; color:white"
            elif val == "🟡 Atenção":
                return "background-color:#FFD93D; color:black"
            elif val == "🟢 OK":
                return "background-color:#6BCB77; color:white"
            return ""

        st.dataframe(df_filtrado.style.applymap(colorir_sulco, subset=["Alerta Sulco"]), use_container_width=True)

    # ----------------- HISTÓRICO DE TROCAS -----------------
    with aba4:
        st.subheader("📊 Histórico de Trocas e Vida Útil")
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
            color="Tipo Pneu",
            color_discrete_sequence=px.colors.qualitative.Set2,
            height=500
        )
        fig3.update_traces(texttemplate='%{y:.0f} km', textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)
