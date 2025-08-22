import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestão de Pneus", layout="wide")
st.title("📊 Gestão de Pneus")

# Upload do arquivo Excel
arquivo = st.file_uploader("Carregue a planilha de pneus", type=["xlsx", "xls"])

if arquivo:
    # -------------------
    # Ler aba principal
    df = pd.read_excel(arquivo, sheet_name="principal", engine="openpyxl")
    df.columns = df.columns.str.strip()

    # Ler aba sulco
    df_sulco = pd.read_excel(arquivo, sheet_name="sulco", engine="openpyxl")
    df_sulco.columns = df_sulco.columns.str.strip()

    # Criar dicionário Modelo -> Sulco Novo
    sulco_novo_dict = df_sulco.set_index("Modelo (Atual)")["Sulco"].to_dict()

    # Mapear Sulco Novo no dataframe principal
    df["Sulco Novo"] = df["Modelo (Atual)"].map(sulco_novo_dict)

    # Calcular Sulco Consumido apenas quando houver dados
    df["Sulco Consumido"] = df.apply(
        lambda x: x["Sulco Novo"] - x["Aferição - Sulco"]
        if pd.notna(x["Sulco Novo"]) and pd.notna(x["Aferição - Sulco"]) else None,
        axis=1
    )

    # Calcular Desgaste por Km apenas quando houver Sulco Consumido e Km rodado
    df["Desgaste por Km"] = df.apply(
        lambda x: x["Sulco Consumido"] / x["Km Rodado até Aferição"]
        if pd.notna(x["Sulco Consumido"]) and pd.notna(x["Km Rodado até Aferição"]) and x["Km Rodado até Aferição"] > 0 else None,
        axis=1
    )

    # -------------------
    # Mostrar dataframe atualizado
    st.subheader("Dados Atualizados")
    st.dataframe(df)

    # -------------------
    # Exemplo de gráfico: Desgaste por Km por Modelo
    st.subheader("Desgaste por Km por Modelo")
    fig = px.bar(df, x="Modelo (Atual)", y="Desgaste por Km", color="Modelo (Atual)")
    st.plotly_chart(fig, use_container_width=True)
