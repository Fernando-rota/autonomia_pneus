import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    # ----------------- LER PLANILHAS -----------------
    df_pneus = pd.read_excel(arquivo, sheet_name="pneus", engine="openpyxl")
    df_pneus.columns = df_pneus.columns.str.strip()

    df_posicao = pd.read_excel(arquivo, sheet_name="posição", engine="openpyxl")
    df_posicao.columns = df_posicao.columns.str.strip()

    df_sulco = pd.read_excel(arquivo, sheet_name="sulco", engine="openpyxl")
    df_sulco.columns = df_sulco.columns.str.strip()

    # ----------------- FUNÇÕES -----------------
    def extrair_km_observacao(texto):
        """Extrai valor em km do campo Observação"""
        if pd.isna(texto):
            return None
        match = re.search(r"(\d+)\s*km", str(texto))
        if match:
            return int(match.group(1))
        return None

    def colorir_sulco(val):
        """Colore células de acordo com o sulco"""
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

    # ----------------- PREPARAR DADOS -----------------
    # Mapear posição (SIGLA -> POSIÇÃO)
    df_pneus = df_pneus.merge(
        df_posicao.rename(columns={"SIGLA": "Sigla da Posição", "POSIÇÃO": "Posição"}),
        on="Sigla da Posição",
        how="left"
    )

    # Calcular km rodado
    df_pneus["Observação - Km"] = df_pneus["Observação"].apply(extrair_km_observacao)
    df_pneus["Km Rodado até Aferição"] = df_pneus["Vida do Pneu - Km. Rodado"]

    # Mapear sulco novo
    sulco_novo_dict = df_sulco.set_index("Modelo (Atual)")["Sulco"].to_dict()
    df_pneus["Sulco Novo"] = df_pneus["Modelo (Atual)"].map(sulco_novo_dict)

    # Calcular sulco consumido
    df_pneus["Sulco Consumido"] = df_pneus.apply(
        lambda x: x["Sulco Novo"] - x["Aferição - Sulco"]
        if pd.notna(x["Sulco Novo"]) and pd.notna(x["Aferição - Sulco"]) else None,
        axis=1
    )

    # Desgaste por km
    df_pneus["Desgaste por Km"] = df_pneus.apply(
        lambda x: x["Sulco Consumido"] / x["Km Rodado até Aferição"]
        if pd.notna(x["Sulco Consumido"]) and pd.notna(x["Km Rodado até Aferição"]) and x["Km Rodado até Aferição"] > 0 else None,
        axis=1
    )

    # ----------------- CRIAR ABAS -----------------
    aba1, aba2, aba3, aba4 = st.tabs([
        "📌 Indicadores",
        "📈 Gráficos",
        "📏 Medidas de Sulco",
        "📑 Tabela Completa"
    ])

    # ----------------- ABA INDICADORES -----------------
    with aba1:
        st.subheader("📌 Indicadores Gerais")

        total_pneus = df_pneus["Referência"].nunique()
        status_counts = df_pneus["Status"].value_counts()
        estoque = status_counts.get("Estoque", 0)
        sucata = status_counts.get("Sucata", 0)
        caminhao = status_counts.get("Caminhão", 0)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", estoque)
        col3.metric("♻️ Sucata", sucata)
        col4.metric("🚚 Caminhão", caminhao)

        col5, col6, col7 = st.columns(3)
        media_sulco = df_pneus["Aferição - Sulco"].dropna().mean()
        media_km = df_pneus["Km Rodado até Aferição"].dropna().mean()
        pneu_critico = df_pneus[df_pneus["Aferição - Sulco"] < 2]
        perc_critico = len(pneu_critico) / len(df_pneus) * 100

        col5.metric("🟢 Média Sulco (mm)", f"{media_sulco:.2f}")
        col6.metric("🛣️ Média Km até Aferição", f"{media_km:,.0f} km")
        col7.metric("⚠️ Pneus Críticos (<2mm)", len(pneu_critico), f"{perc_critico:.1f}%")

    # ----------------- ABA GRÁFICOS -----------------
    with aba2:
        st.subheader("📈 Relação Km Rodado x Sulco")
        df_com_km = df_pneus[df_pneus["Km Rodado até Aferição"].notna()].copy()

        if not df_com_km.empty:
            df_com_km["Crítico"] = df_com_km["Aferição - Sulco"].apply(
                lambda x: "Crítico" if pd.notna(x) and x < 2 else "Normal"
            )

            fig = px.scatter(
                df_com_km,
                x="Km Rodado até Aferição",
                y="Aferição - Sulco",
                color="Crítico",
                hover_data=["Referência", "Modelo (Atual)", "Marca (Atual)", "Posição", "Vida", "Status"],
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📈 Tabela: Relação Km Rodado x Sulco")
            df_tabela = df_com_km[["Referência", "Veículo - Placa", "Marca (Atual)", "Modelo (Atual)", "Vida", "Status", "Km Rodado até Aferição", "Aferição - Sulco"]].copy()
            df_tabela = df_tabela.sort_values(by="Km Rodado até Aferição", ascending=True)
            st.dataframe(df_tabela.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]), use_container_width=True)

    # ----------------- ABA MEDIDAS DE SULCO -----------------
    with aba3:
        st.subheader("📏 Medidas de Sulco")
        df_sulco_tabela = df_pneus[df_pneus["Aferição - Sulco"].notna()].copy()
        df_sulco_tabela = df_sulco_tabela.sort_values(by="Aferição - Sulco", ascending=True)
        colunas_sulco = ["Referência", "Veículo - Placa", "Marca (Atual)", "Modelo (Atual)", "Vida", "Status", "Aferição - Sulco"]
        st.dataframe(
            df_sulco_tabela[colunas_sulco].style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )

    # ----------------- ABA TABELA COMPLETA -----------------
    with aba4:
        st.subheader("📑 Tabela Completa")
        status_filter = st.multiselect(
            "Filtrar por Status",
            options=df_pneus["Status"].unique(),
            default=df_pneus["Status"].unique()
        )
        df_filtrado = df_pneus[df_pneus["Status"].isin(status_filter)].copy()
        st.dataframe(
            df_filtrado.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )
