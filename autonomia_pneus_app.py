import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

# ----------------- UPLOAD -----------------
arquivo = st.file_uploader("📂 Carregue o arquivo Excel", type=["xls", "xlsx"])

if arquivo:
    xls = pd.ExcelFile(arquivo)

    # Selecionar abas
    aba_principal = st.selectbox("Selecione a aba principal (dados dos pneus)", xls.sheet_names)
    aba_legenda = st.selectbox("Selecione a aba da legenda (Modelos x Sulco Novo)", xls.sheet_names)

    # Ler abas
    df = pd.read_excel(xls, sheet_name=aba_principal, engine="openpyxl")
    df_legenda = pd.read_excel(xls, sheet_name=aba_legenda, engine="openpyxl")

    # ----------------- PREPARAR DADOS -----------------
    df.columns = df.columns.str.strip()
    df_legenda.columns = df_legenda.columns.str.strip()

    # Dicionário modelo -> sulco novo
    sulco_legenda = df_legenda.set_index("Modelo (Atual)")["Sulco"].to_dict()

    # Adicionar colunas
    df.insert(df.columns.get_loc("Vida") + 1, "Sulco Novo", df["Modelo (Atual)"].map(sulco_legenda))
    df["Sulco Consumido"] = df["Sulco Novo"] - df["Aferição - Sulco"]
    df["Desgaste por Km"] = df["Sulco Consumido"] / df["Km Rodado até Aferição"]

    # ----------------- CLASSIFICAÇÃO POR TIPO DE VEÍCULO -----------------
    def classificar_veiculo(desc):
        desc = str(desc).lower()
        if "saveiro" in desc:
            return "Leve"
        elif any(x in desc for x in ["renault", "iveco", "scudo", "daily"]):
            return "Utilitário"
        elif any(x in desc for x in ["3/4", "toco", "truck", "carreta", "cavalo"]):
            return "Pesado"
        else:
            return "Outros"

    df["Tipo de Veículo"] = df["Veículo - Descrição"].apply(classificar_veiculo)

    # ----------------- RODAGEM POR TIPO -----------------
    rodagem_tipo = df.groupby("Tipo de Veículo")["Km Rodado até Aferição"].mean().reset_index()
    rodagem_tipo.rename(columns={"Km Rodado até Aferição": "Rodagem Média"}, inplace=True)

    # ----------------- LAYOUT EM ABAS -----------------
    aba1, aba2, aba3, aba4, aba5 = st.tabs([
        "📑 Tabela Completa",
        "📊 Relação Km Rodado x Sulco",
        "📉 Distribuição do Sulco por Marca",
        "📈 Desgaste por Km",
        "🚛 Rodagem por Tipo de Veículo"
    ])

    with aba1:
        st.subheader("📑 Tabela Completa")
        st.dataframe(df, use_container_width=True)

    with aba2:
        st.subheader("📊 Relação Km Rodado x Sulco")
        fig = px.scatter(
            df,
            x="Km Rodado até Aferição",
            y="Aferição - Sulco",
            color="Modelo (Atual)",
            hover_data=["Veículo - Placa", "Sigla da Posição", "Sulco Novo"],
            title="Relação Km Rodado x Sulco"
        )
        st.plotly_chart(fig, use_container_width=True)

    with aba3:
        st.subheader("📉 Distribuição do Sulco por Marca")
        fig = px.box(
            df,
            x="Marca (Atual)",
            y="Aferição - Sulco",
            color="Marca (Atual)",
            title="Distribuição do Sulco por Marca"
        )
        st.plotly_chart(fig, use_container_width=True)

    with aba4:
        st.subheader("📈 Desgaste por Km")
        fig = px.scatter(
            df,
            x="Km Rodado até Aferição",
            y="Desgaste por Km",
            color="Modelo (Atual)",
            hover_data=["Veículo - Placa", "Sigla da Posição", "Sulco Novo"],
            title="Desgaste por Km"
        )
        st.plotly_chart(fig, use_container_width=True)

    with aba5:
        st.subheader("🚛 Rodagem Média por Tipo de Veículo")
        st.dataframe(rodagem_tipo, use_container_width=True)
        fig = px.bar(
            rodagem_tipo,
            x="Tipo de Veículo",
            y="Rodagem Média",
            color="Tipo de Veículo",
            title="Rodagem Média por Tipo de Veículo"
        )
        st.plotly_chart(fig, use_container_width=True)
