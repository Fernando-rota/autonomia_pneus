import streamlit as st
import pandas as pd

st.set_page_config(page_title="Autonomia dos Pneus", layout="wide")
st.title("🚛 Autonomia dos Pneus - Análise por Número de Série")

# Upload
arquivo = st.file_uploader("📂 Envie a planilha com abas 'manutencao' e 'movi-pneus'", type=["xlsx"])

if arquivo:
    try:
        xls = pd.ExcelFile(arquivo)
        movi = pd.read_excel(xls, "movi-pneus")

        # Limpeza de dados
        movi["Data da Movimentação"] = pd.to_datetime(movi["Data da Movimentação"], errors="coerce")
        movi["Pneu - Hodômetro"] = pd.to_numeric(movi["Pneu - Hodômetro"], errors="coerce")
        movi["Pneu - Série"] = movi["Pneu - Série"].astype(str)

        # Separar entradas e retiradas
        entradas = movi[movi["Tipo de Movimentação"].str.lower().str.contains("entrada")].copy()
        retiradas = movi[movi["Tipo de Movimentação"].str.lower().str.contains("retirada")].copy()

        # Renomear colunas para juntar
        entradas = entradas.rename(columns={
            "Data da Movimentação": "Data Entrada",
            "Pneu - Hodômetro": "KM Entrada"
        })

        retiradas = retiradas.rename(columns={
            "Data da Movimentação": "Data Retirada",
            "Pneu - Hodômetro": "KM Retirada"
        })

        # Juntar pelas séries
        df_autonomia = pd.merge(
            entradas[["Pneu - Série", "Data Entrada", "KM Entrada", "Veículo - Placa", "Pneu - Marca (Atual)", "Pneu - Modelo (Atual)"]],
            retiradas[["Pneu - Série", "Data Retirada", "KM Retirada"]],
            on="Pneu - Série",
            how="left"
        )

        # Calcular autonomia
        df_autonomia["Autonomia (KM)"] = df_autonomia["KM Retirada"] - df_autonomia["KM Entrada"]

        # Ordenar por maior autonomia
        df_autonomia = df_autonomia.sort_values(by="Autonomia (KM)", ascending=False)

        st.success(f"✅ {len(df_autonomia)} pneus analisados com sucesso!")

        # Mostrar tabela
        st.dataframe(df_autonomia, use_container_width=True)

        # Download CSV
        csv = df_autonomia.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar resultados (.csv)", data=csv, file_name="autonomia_pneus.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
