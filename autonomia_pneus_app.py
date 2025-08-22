import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

# Upload do arquivo Excel
arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    # -------------------
    # Ler aba pneus (principal)
    df_pneus = pd.read_excel(arquivo, sheet_name="pneus", engine="openpyxl")
    df_pneus.columns = df_pneus.columns.str.strip()

    # Ler aba posição
    df_posicao = pd.read_excel(arquivo, sheet_name="posição", engine="openpyxl")
    df_posicao.columns = df_posicao.columns.str.strip()

    # Ler aba sulco
    df_sulco = pd.read_excel(arquivo, sheet_name="sulco", engine="openpyxl")
    df_sulco.columns = df_sulco.columns.str.strip()

    # -------------------
    # Mapear posição
    df_pneus = df_pneus.merge(df_posicao, on="ID Pneu", how="left")

    # Criar dicionário Modelo -> Sulco Novo
    sulco_novo_dict = df_sulco.set_index("Modelo (Atual)")["Sulco"].to_dict()

    # Mapear Sulco Novo no dataframe principal
    df_pneus["Sulco Novo"] = df_pneus["Modelo (Atual)"].map(sulco_novo_dict)

    # Calcular Sulco Consumido apenas quando houver dados
    df_pneus["Sulco Consumido"] = df_pneus.apply(
        lambda x: x["Sulco Novo"] - x["Aferição - Sulco"]
        if pd.notna(x["Sulco Novo"]) and pd.notna(x["Aferição - Sulco"]) else None,
        axis=1
    )

    # Calcular Desgaste por Km apenas quando houver Sulco Consumido e Km rodado
    df_pneus["Desgaste por Km"] = df_pneus.apply(
        lambda x: x["Sulco Consumido"] / x["Km Rodado até Aferição"]
        if pd.notna(x["Sulco Consumido"]) and pd.notna(x["Km Rodado até Aferição"]) and x["Km Rodado até Aferição"] > 0 else None,
        axis=1
    )

    # -------------------
    # Filtros interativos
    st.sidebar.subheader("Filtros")
    modelos = st.sidebar.multiselect("Selecione Modelo", df_pneus["Modelo (Atual)"].unique(), default=df_pneus["Modelo (Atual)"].unique())
    posicoes = st.sidebar.multiselect("Selecione Posição", df_pneus["Posição"].unique(), default=df_pneus["Posição"].unique())

    df_filtrado = df_pneus[(df_pneus["Modelo (Atual)"].isin(modelos)) & (df_pneus["Posição"].isin(posicoes))]

    # -------------------
    # Mostrar dataframe filtrado
    st.subheader("Dados Atualizados")
    st.dataframe(df_filtrado)

    # -------------------
    # Gráfico: Desgaste por Km
    st.subheader("Desgaste por Km por Modelo e Posição")
    fig = px.bar(df_filtrado, x="Modelo (Atual)", y="Desgaste por Km", color="Posição", barmode="group")
    st.plotly_chart(fig, use_container_width=True)
