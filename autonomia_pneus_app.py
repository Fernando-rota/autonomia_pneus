# ----------------- IMPORTS -----------------
import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    df = pd.read_excel(arquivo, engine="openpyxl", sheet_name=None)

    # Carregar abas
    df_pneus = df.get("pneus")
    df_posicao = df.get("posição")
    df_sulco = df.get("sulco")

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

    def classificar_veiculo(desc):
        if pd.isna(desc):
            return "Outro"
        desc_low = str(desc).lower()
        if "saveiro" in desc_low:
            return "Leve"
        elif "renault" in desc_low:
            return "Utilitário (Renault)"
        elif "iveco" in desc_low or "daily" in desc_low or "scudo" in desc_low:
            return "Utilitário (Iveco/Scudo)"
        elif "3/4" in desc_low:
            return "3/4"
        elif "toco" in desc_low:
            return "Toco"
        elif "truck" in desc_low:
            return "Truck"
        elif "cavalo" in desc_low or "carreta" in desc_low:
            return "Carreta"
        else:
            return "Outro"

    # ----------------- PREPARAR DADOS -----------------
    df_pneus["Observação - Km"] = df_pneus["Observação"].apply(extrair_km_observacao)
    df_pneus["Km Rodado até Aferição"] = df_pneus["Observação - Km"] - df_pneus["Hodômetro Inicial"]

    # Merge para obter sulco inicial (de acordo com vida e modelo)
    df_pneus = df_pneus.merge(
        df_sulco.rename(columns={"Sulco": "Sulco Inicial"}),
        how="left",
        left_on=["Vida", "Modelo (Atual)"],
        right_on=["Vida", "Modelo (Atual)"]
    )

    # Criar colunas de cálculo
    df_pneus["Sulco Consumido"] = df_pneus["Sulco Inicial"] - df_pneus["Aferição - Sulco"]
    df_pneus["Desgaste (mm/km)"] = df_pneus["Sulco Consumido"] / df_pneus["Km Rodado até Aferição"]

    # Classificação de veículos
    df_pneus["Tipo Veículo"] = df_pneus["Veículo - Descrição"].apply(classificar_veiculo)

    # ----------------- CRIAR ABAS -----------------
    aba1, aba2, aba4, aba3, aba5 = st.tabs([
        "📌 Indicadores",
        "📈 Gráficos",
        "📏 Medidas de Sulco",
        "📑 Tabela Completa",
        "📖 Legenda"
    ])

    # ----------------- NOVA ABA DE LEGENDA -----------------
    with aba5:
        st.subheader("📖 Legenda - Siglas de Posição")
        st.dataframe(df_posicao, use_container_width=True)

        st.subheader("📖 Legenda - Sulco Inicial por Modelo de Pneu")
        df_legenda_sulco = df_sulco[df_sulco["Vida"] == "Novo"].copy()
        st.dataframe(df_legenda_sulco, use_container_width=True)

        st.subheader("📊 Medida da Rodagem por Tipo de Veículo")
        df_rodagem = df_pneus.groupby("Tipo Veículo")["Desgaste (mm/km)"].mean().reset_index()
        df_rodagem = df_rodagem.sort_values(by="Desgaste (mm/km)", ascending=True)
        st.dataframe(df_rodagem, use_container_width=True)
