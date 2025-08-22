import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    df = pd.read_excel(arquivo, engine="openpyxl")

    # ----------------- FUNÇÕES -----------------
    def extrair_km_observacao(texto):
        if pd.isna(texto):
            return None
        match = re.search(r"(\d+)\s*km", str(texto))
        if match:
            return int(match.group(1))
        return None

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

    # ----------------- PREPARAR DADOS -----------------
    df["Observação - Km"] = df["Observação"].apply(extrair_km_observacao)
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]

    # Ajuste de estoque (6 pneus extras)
    df_extra = pd.DataFrame({
        "Referência": [f"Extra{i}" for i in range(1, 7)],
        "Status": ["Sucata"]*6,
        "Veículo - Placa": [None]*6,
        "Modelo (Atual)": [None]*6,
        "Marca (Atual)": [None]*6,
        "Aferição - Sulco": [0]*6,
        "Hodômetro Inicial": [0]*6,
        "Observação": [None]*6,
        "Vida": ["Ressolado"]*6,
        "Sigla da Posição": [None]*6
    })
    df = pd.concat([df, df_extra], ignore_index=True)
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]

    # ----------------- LEGENDA DE SULCO INICIAL -----------------
    df_legenda = df[df["Status"] == "Estoque"].copy()
    sulco_inicial_por_modelo = df_legenda.groupby("Modelo (Atual)")["Aferição - Sulco"].mean().to_dict()

    # Adicionar colunas calculadas
    df["Sulco Inicial"] = df["Modelo (Atual)"].map(sulco_inicial_por_modelo)
    df["Sulco Consumido"] = df["Sulco Inicial"] - df["Aferição - Sulco"]
    df["Desgaste (mm/km)"] = df["Sulco Consumido"] / df["Km Rodado até Aferição"]

    # ----------------- CLASSIFICAÇÃO DE VEÍCULOS -----------------
    def classificar_veiculo(desc):
        if pd.isna(desc):
            return "Indefinido"
        desc = str(desc).lower()
        if "saveiro" in desc:
            return "Leve"
        elif "renault" in desc or "scudo" in desc or "iveco daily" in desc:
            return "Utilitário"
        elif "3/4" in desc:
            return "3/4"
        elif "toco" in desc:
            return "Toco"
        elif "truck" in desc:
            return "Truck"
        elif "carreta" in desc or "cavalo" in desc:
            return "Carreta"
        return "Outros"

    df["Tipo Veículo"] = df["Veículo - Placa"].apply(classificar_veiculo)

    # ----------------- CRIAR ABAS -----------------
    aba1, aba2, aba3, aba4, aba5 = st.tabs([
        "📌 Indicadores",
        "📈 Gráficos",
        "📏 Medidas de Sulco",
        "📑 Tabela Completa",
        "📖 Legenda"
    ])

    # ----------------- ABA DE INDICADORES -----------------
    with aba1:
        st.subheader("📌 Indicadores Gerais")
        st.markdown(
            """
            Este painel de BI apresenta a **gestão de pneus das 3 unidades**.  
            Os indicadores refletem os dados cadastrados no sistema a partir de **maio/2025**.  

            O objetivo deste BI é fornecer uma visão geral do estoque, sucata, pneus em uso nos caminhões e alertas de pneus críticos.  
            Ele permite monitorar a **vida útil dos pneus**, identificar pneus próximos do limite de segurança e otimizar o gerenciamento da frota.
            """
        )

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

    # ----------------- ABA 2 - GRÁFICOS -----------------
    with aba2:
        st.subheader("📊 Distribuição do Sulco Atual por Tipo de Veículo")
        fig1 = px.box(
            df,
            x="Tipo Veículo",
            y="Aferição - Sulco",
            color="Tipo Veículo",
            points="all",
            title="Sulco Atual (mm) por Tipo de Veículo"
        )
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("📊 Sulco Consumido por Tipo de Veículo")
        fig2 = px.box(
            df,
            x="Tipo Veículo",
            y="Sulco Consumido",
            color="Tipo Veículo",
            points="all",
            title="Sulco Consumido (mm) por Tipo de Veículo"
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📊 Desgaste Relativo (mm/km) por Tipo de Veículo")
        fig3 = px.box(
            df,
            x="Tipo Veículo",
            y="Desgaste (mm/km)",
            color="Tipo Veículo",
            points="all",
            title="Sulco Consumido / Km Rodado"
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("📈 Evolução do Desgaste por Hodômetro")
        fig4 = px.scatter(
            df,
            x="Observação - Km",
            y="Aferição - Sulco",
            color="Tipo Veículo",
            hover_data=["Veículo - Placa", "Modelo (Atual)"],
            title="Aferição de Sulco vs. Hodômetro"
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ----------------- ABA DE MEDIDAS DE SULCO -----------------
    with aba3:
        st.subheader("📏 Medidas de Sulco")
        df_sulco = df[(df["Aferição - Sulco"].notna()) & (~df["Referência"].astype(str).str.contains("Extra"))].copy()
        df_sulco = df_sulco.sort_values(by="Aferição - Sulco", ascending=True)

        colunas_sulco = [
            "Referência", "Veículo - Placa", "Marca (Atual)", "Modelo (Atual)", 
            "Vida", "Sulco Inicial", "Status", "Aferição - Sulco", 
            "Sulco Consumido", "Desgaste (mm/km)"
        ]
        st.dataframe(
            df_sulco[colunas_sulco].style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )

    # ----------------- ABA DE TABELA COMPLETA -----------------
    with aba4:
        st.subheader("📑 Tabela Completa")
        df_filtrado = df[~df["Referência"].astype(str).str.contains("Extra")].copy()
        status_filter = st.multiselect(
            "Filtrar por Status",
            options=df_filtrado["Status"].unique(),
            default=df_filtrado["Status"].unique()
        )
        df_filtrado = df_filtrado[df_filtrado["Status"].isin(status_filter)].copy()
        st.dataframe(
            df_filtrado.style.applymap(colorir_sulco, subset=["Aferição - Sulco"]),
            use_container_width=True
        )

    # ----------------- ABA DE LEGENDA -----------------
    with aba5:
        st.subheader("📖 Legenda de Siglas e Sulcos Iniciais")
        st.markdown("**Siglas de Posição:**")
        st.dataframe(df[["Referência", "Sigla da Posição"]])

        st.markdown("**Sulco Inicial por Modelo de Pneu (Estoque):**")
        legenda_sulco_df = pd.DataFrame(list(sulco_inicial_por_modelo.items()), columns=["Modelo", "Sulco Inicial (mm)"])
        st.dataframe(legenda_sulco_df, use_container_width=True)
