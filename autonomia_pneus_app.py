import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    df = pd.read_excel(arquivo, engine="openpyxl")

    # ----------------- Extrair Km da observação -----------------
    def extrair_km_observacao(texto):
        if pd.isna(texto):
            return None
        match = re.search(r"(\d+)\s*km", str(texto))
        if match:
            return int(match.group(1))
        return None

    df["Observação - Km"] = df["Observação"].apply(extrair_km_observacao)
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

        # Indicadores maiores e chamativos
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(f"<h1 style='color:#1f77b4'>{total_pneus}</h1><p>Total de Pneus</p>", unsafe_allow_html=True)
        col2.markdown(f"<h1 style='color:#2ca02c'>{estoque}</h1><p>Estoque</p>", unsafe_allow_html=True)
        col3.markdown(f"<h1 style='color:#d62728'>{sucata}</h1><p>Sucata</p>", unsafe_allow_html=True)
        col4.markdown(f"<h1 style='color:#ff7f0e'>{caminhao}</h1><p>Caminhão</p>", unsafe_allow_html=True)

        col5, col6, col7 = st.columns(3)
        media_sulco = df["Aferição - Sulco"].dropna().mean()
        media_km = df["Km Rodado até Aferição"].dropna().mean()
        pneu_critico = df[df["Aferição - Sulco"] < 2]
        perc_critico = len(pneu_critico) / len(df) * 100

        col5.metric("Média Sulco (mm)", f"{media_sulco:.2f}")
        st.caption("Profundidade média do sulco dos pneus aferidos (mm).")

        col6.metric("Média Km até Aferição", f"{media_km:,.0f} km")
        st.caption("Quilometragem média rodada pelos pneus até a última aferição.")

        col7.metric("Pneus Críticos (<2mm)", len(pneu_critico), f"{perc_critico:.1f}%")
        st.caption("Pneus com sulco menor que 2mm, considerados críticos para uso.")

        # ----------------- Comparativo Vida Útil -----------------
        st.subheader("⚙️ Comparativo Vida Útil por Tipo de Pneu")
        SULCO_NOVO = 8  # mm
        KM_MAX_NOVO = 120000
        KM_MAX_RESSOLADO = 80000

        def vida_util(row):
            sulco_pct = row["Aferição - Sulco"] / SULCO_NOVO * 100
            km_pct = row["Km Rodado até Aferição"] / (KM_MAX_NOVO if row["Tipo Pneu"]=="Novo" else KM_MAX_RESSOLADO) * 100
            return pd.Series([sulco_pct, km_pct])

        df[["% Sulco Restante", "% Km Rodado"]] = df.apply(vida_util, axis=1)

        tipos = df["Tipo Pneu"].unique()
        for tipo in tipos:
            sub = df[df["Tipo Pneu"]==tipo]
            media_sulco_pct = sub["% Sulco Restante"].mean()
            media_km_pct = sub["% Km Rodado"].mean()
            cor = "#2ca02c" if media_sulco_pct > 30 else "#ff7f0e" if media_sulco_pct > 15 else "#d62728"
            st.markdown(f"<h2 style='color:{cor}'>{tipo}</h2>", unsafe_allow_html=True)
            st.markdown(f"💠 Média Sulco Restante: {media_sulco_pct:.1f}%  \n💠 Média Km Rodado: {media_km_pct:.1f}%", unsafe_allow_html=True)
            st.caption("Comparativo entre desgaste real e quilometragem percorrida. Avalia se a vida útil está adequada.")

    # ----------------- GRÁFICOS -----------------
    with aba2:
        st.subheader("📈 Gráficos Interativos")
        if "Km Rodado até Aferição" in df.columns and "Aferição - Sulco" in df.columns:
            # Scatter Km x Sulco
            fig_desgaste = px.scatter(
                df,
                x="Km Rodado até Aferição",
                y="Aferição - Sulco",
                color="Marca (Atual)",
                title="Relação entre Km Rodado e Sulco",
                hover_data=["Veículo - Placa", "Modelo (Atual)", "Status", "Tipo Pneu"],
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_desgaste.update_layout(
                title_font_size=22,
                xaxis_title_font_size=18,
                yaxis_title_font_size=18,
                legend_title_font_size=16,
                font=dict(size=16)
            )
            st.plotly_chart(fig_desgaste, use_container_width=True)

            # Boxplot Sulco por Marca
            fig_box = px.box(
                df,
                x="Marca (Atual)",
                y="Aferição - Sulco",
                color="Marca (Atual)",
                title="Distribuição do Sulco por Marca",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_box.update_layout(
                title_font_size=22,
                xaxis_title_font_size=18,
                yaxis_title_font_size=18,
                legend_title_font_size=16,
                font=dict(size=16)
            )
            st.plotly_chart(fig_box, use_container_width=True)

    # ----------------- TABELA -----------------
    with aba3:
        st.subheader("📑 Tabela Completa")
        status_filter = st.multiselect("Filtrar por Status", options=df["Status"].unique(), default=df["Status"].unique())
        st.dataframe(df[df["Status"].isin(status_filter)], use_container_width=True)
