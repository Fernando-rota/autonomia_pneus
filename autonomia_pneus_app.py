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
        "Vida": ["Ressolado"]*6
    })
    df = pd.concat([df, df_extra], ignore_index=True)
    df["Km Rodado até Aferição"] = df["Observação - Km"] - df["Hodômetro Inicial"]

    # ----------------- NOVAS COLUNAS -----------------
    # Sulco Consumido = Sulco Novo - Sulco aferido
    # Aqui, você pode criar um dicionário modelo -> sulco novo ou pegar de coluna existente
    sulco_novo_dict = {
        # Exemplo: "Modelo (Atual)": sulco em mm
        "PIRELLI 275/80 LISO": 15.0,
        "MICHELLIN 275/08  LISO": 15.45,
        "GOODYEAR 275/80  BORRACHUDO": 17.425
    }
    df["Sulco Novo"] = df["Modelo (Atual)"].map(sulco_novo_dict)
    df["Sulco Consumido"] = df["Sulco Novo"] - df["Aferição - Sulco"]

    # Desgaste por km
    df["Desgaste por Km"] = df["Sulco Consumido"] / df["Km Rodado até Aferição"]
    df["Desgaste por Km"] = df["Desgaste por Km"].fillna(0)
    df["Sulco Consumido"] = df["Sulco Consumido"].fillna(0)

    # ----------------- CRIAR ABAS -----------------
    aba1, aba2, aba4, aba3 = st.tabs([
        "📌 Indicadores",
        "📈 Gráficos",
        "📏 Medidas de Sulco",
        "📑 Tabela Completa"
    ])

    # ----------------- ABA DE INDICADORES -----------------
    with aba1:
        st.subheader("📌 Indicadores Gerais")
        total_pneus = df["Referência"].nunique()
        status_counts = df["Status"].value_counts()
        estoque = status_counts.get("Estoque", 0)
        sucata = status_counts.get("Sucata", 0)
        caminhao = status_counts.get("Caminhão", 0)
        media_sulco = df["Aferição - Sulco"].dropna().mean()
        media_km = df["Km Rodado até Aferição"].dropna().mean()
        pneu_critico = df[df["Aferição - Sulco"] < 2]
        perc_critico = len(pneu_critico) / len(df) * 100

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🛞 Total de Pneus", total_pneus)
        col2.metric("📦 Estoque", estoque)
        col3.metric("♻️ Sucata", sucata)
        col4.metric("🚚 Caminhão", caminhao)

        col5, col6, col7 = st.columns(3)
        col5.metric("🟢 Média Sulco (mm)", f"{media_sulco:.2f}")
        col6.metric("🛣️ Média Km até Aferição", f"{media_km:,.0f} km")
        col7.metric("⚠️ Pneus Críticos (<2mm)", len(pneu_critico), f"{perc_critico:.1f}%")

    # ----------------- ABA DE GRÁFICOS -----------------
    with aba2:
        st.subheader("📈 Relação Km Rodado x Sulco / Desgaste")
        df_plot = df[df["Km Rodado até Aferição"].notna() & (df["Km Rodado até Aferição"] > 0)].copy()
        if not df_plot.empty:
            df_plot["Cor_Gráfico"] = df_plot.apply(lambda x: "Crítico" if x["Aferição - Sulco"] < 2 else x["Marca (Atual)"], axis=1)
            cores_set2 = px.colors.qualitative.Set2
            marcas = df_plot["Marca (Atual)"].dropna().unique().tolist()
            color_map = {marca: cores_set2[i % len(cores_set2)] for i, marca in enumerate(marcas)}
            color_map["Crítico"] = "#FF0000"

            fig = px.scatter(
                df_plot,
                x="Km Rodado até Aferição",
                y="Aferição - Sulco",
                color="Cor_Gráfico",
                hover_data=["Veículo - Placa", "Modelo (Atual)", "Sulco Consumido", "Desgaste por Km"],
                color_discrete_map=color_map,
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

    # ----------------- ABA DE MEDIDAS DE SULCO -----------------
    with aba4:
        st.subheader("📏 Medidas de Sulco / Desgaste")
        df_sulco = df[df["Aferição - Sulco"].notna()].copy()
        df_sulco = df_sulco.sort_values(by="Aferição - Sulco")
        df_sulco["Aferição - Sulco"] = df_sulco["Aferição - Sulco"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
        df_sulco["Sulco Consumido"] = df_sulco["Sulco Consumido"].map(lambda x: f"{x:.2f}")
        df_sulco["Desgaste por Km"] = df_sulco["Desgaste por Km"].map(lambda x: f"{x:.4f}")
        st.dataframe(
            df_sulco[["Referência","Veículo - Placa","Marca (Atual)","Modelo (Atual)","Aferição - Sulco","Sulco Consumido","Desgaste por Km"]],
            use_container_width=True
        )

    # ----------------- ABA DE TABELA COMPLETA -----------------
    with aba3:
        st.subheader("📑 Tabela Completa")
        st.dataframe(df, use_container_width=True)
