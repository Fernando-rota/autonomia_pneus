import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

# ----------------- UPLOAD -----------------
arquivo = st.file_uploader("📂 Carregue o arquivo Excel", type=["xls", "xlsx"])

if arquivo:
    xls = pd.ExcelFile(arquivo)

    # Mostra todas as abas para o usuário
    st.write("📑 Abas encontradas no arquivo:", xls.sheet_names)

    # Selecionar aba principal e aba legenda
    aba_principal = st.selectbox("Selecione a aba principal (dados dos pneus)", xls.sheet_names)
    aba_legenda = st.selectbox("Selecione a aba da legenda (Modelos x Sulco Novo)", xls.sheet_names)

    # Ler as abas
    df = pd.read_excel(xls, sheet_name=aba_principal, engine="openpyxl")
    df_legenda = pd.read_excel(xls, sheet_name=aba_legenda, engine="openpyxl")

    # Criar dicionário modelo -> sulco novo
    sulco_legenda = df_legenda.set_index("Modelo (Atual)")["Sulco"].to_dict()

    # ----------------- CALCULAR NOVAS COLUNAS -----------------
    df.columns = df.columns.str.strip()
    df["Sulco Novo"] = df["Modelo (Atual)"].map(sulco_legenda)
    df["Sulco Consumido"] = df["Sulco Novo"] - df["Aferição - Sulco"]
    df["Desgaste por Km"] = df["Sulco Consumido"] / df["Km Rodado até Aferição"]

    # ----------------- LAYOUT EM ABAS -----------------
    aba1, aba2, aba3, aba4 = st.tabs([
        "📑 Tabela Completa",
        "📊 Relação Km Rodado x Sulco",
        "📉 Distribuição do Sulco por Marca",
        "📈 Desgaste por Km"
    ])

    with aba1:
        st.subheader("📑 Tabela Completa")
        st.dataframe(df, use_container_width=True)

    with aba2:
        st.subheader("📊 Relação Km Rodado x Sulco")
        ordem = st.radio("Ordenar por:", ["Crescente", "Decrescente"], horizontal=True)
        df_sorted = df.sort_values(by="Km Rodado até Aferição", ascending=(ordem == "Crescente"))

        fig = px.scatter(
            df_sorted,
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
