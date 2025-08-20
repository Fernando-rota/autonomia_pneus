import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# ---------------------------
# Função para download Excel
# ---------------------------
def download_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados Filtrados")
    return output.getvalue()

# ---------------------------
# Configuração do app
# ---------------------------
st.set_page_config(page_title="Dashboard de Pneus", layout="wide")
st.title("📊 Dashboard de Pneus")

# ---------------------------
# Upload do Excel
# ---------------------------
arquivo = st.file_uploader("📂 Envie a planilha de pneus (.xlsx)", type=["xlsx"])

if arquivo:
    excel_convertido = pd.ExcelFile(arquivo, engine="openpyxl")
    aba = st.selectbox("Selecione a aba da planilha:", excel_convertido.sheet_names)
    df = excel_convertido.parse(aba)

    # Converter colunas de data automaticamente
    for col in df.columns:
        if "Data" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # ---------------------------
    # Filtros
    # ---------------------------
    st.sidebar.header("🔎 Filtros")
    filtro_status = st.sidebar.multiselect("Status", df["Status"].dropna().unique(), default=df["Status"].dropna().unique())
    filtro_marca = st.sidebar.multiselect("Marca", df["Marca (Atual)"].dropna().unique(), default=df["Marca (Atual)"].dropna().unique())
    filtro_veiculo = st.sidebar.multiselect("Veículo", df["Veículo - Descrição"].dropna().unique(), default=df["Veículo - Descrição"].dropna().unique())

    df_filtrado = df[
        (df["Status"].isin(filtro_status)) &
        (df["Marca (Atual)"].isin(filtro_marca)) &
        (df["Veículo - Descrição"].isin(filtro_veiculo))
    ]

    # ---------------------------
    # KPIs
    # ---------------------------
    st.subheader("📌 Indicadores")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Pneus", len(df_filtrado))
    col2.metric("Total Km Acumulado", int(df_filtrado["Vida do Pneu - Km. Acumulado"].sum()))
    col3.metric("Modelos Únicos", df_filtrado["Modelo (Atual)"].nunique())
    pct_estoque = (len(df_filtrado[df_filtrado["Status"] == "Estoque"]) / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
    col4.metric("% Pneus em Estoque", f"{pct_estoque:.1f}%")

    # ---------------------------
    # Tabela
    # ---------------------------
    st.subheader("📋 Tabela de Dados Filtrados")
    st.dataframe(df_filtrado, use_container_width=True)

    st.download_button(
        label="📥 Baixar Excel (Filtrado)",
        data=download_excel(df_filtrado),
        file_name="pneus_filtrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # ---------------------------
    # Gráficos
    # ---------------------------
    st.subheader("📈 Gráficos")

    if "Status" in df_filtrado.columns:
        fig_status = px.histogram(df_filtrado, x="Status", color="Status", title="Distribuição por Status")
        st.plotly_chart(fig_status, use_container_width=True)

    if "Marca (Atual)" in df_filtrado.columns:
        fig_marca = px.histogram(df_filtrado, x="Marca (Atual)", color="Marca (Atual)", title="Distribuição por Marca")
        st.plotly_chart(fig_marca, use_container_width=True)

    if "Vida do Pneu - Km. Acumulado" in df_filtrado.columns and "Veículo - Descrição" in df_filtrado.columns:
        fig_km = px.bar(
            df_filtrado,
            x="Veículo - Descrição",
            y="Vida do Pneu - Km. Acumulado",
            color="Veículo - Descrição",
            title="Km Acumulado por Veículo",
            text="Vida do Pneu - Km. Acumulado"
        )
        st.plotly_chart(fig_km, use_container_width=True)

    # ---------------------------
    # Gráfico de evolução temporal
    # ---------------------------
    data_cols = [col for col in df_filtrado.columns if "Data" in col]
    if data_cols and "Vida do Pneu - Km. Acumulado" in df_filtrado.columns:
        st.subheader("📊 Evolução Temporal da Vida do Pneu")
        data_col = data_cols[0]
        fig_evolucao = px.line(
            df_filtrado.sort_values(data_col),
            x=data_col,
            y="Vida do Pneu - Km. Acumulado",
            color="Veículo - Descrição",
            title="Evolução da Quilometragem Acumulada por Veículo",
            markers=True
        )
        st.plotly_chart(fig_evolucao, use_container_width=True)

else:
    st.info("⬆️ Envie um arquivo Excel (.xlsx) para começar a análise.")
