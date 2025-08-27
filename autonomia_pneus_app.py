import pandas as pd
import streamlit as st

st.title("Análise de Pneus")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Escolha um arquivo Excel (.xls ou .xlsx)", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # Lê todas as abas necessárias
        xls = pd.ExcelFile(uploaded_file)
        abas = [aba.lower().replace("ç", "c") for aba in xls.sheet_names]  # Normaliza nomes das abas
        
        if "pneus" not in abas or "posicao" not in abas or "sulco" not in abas:
            st.error("O arquivo deve conter as abas: pneus, posicao e sulco")
        else:
            pneus_df = pd.read_excel(xls, sheet_name="pneus")
            posicao_df = pd.read_excel(xls, sheet_name="posicao")
            sulco_df = pd.read_excel(xls, sheet_name="sulco")

            # Exemplo de cálculos de sulco
            # Ajuste os nomes das colunas conforme seu arquivo
            sulco_df['Sulco_Consumido'] = sulco_df['Sulco_Inicial'] - sulco_df['Sulco_Atual']
            sulco_df['Desgaste_%'] = sulco_df['Sulco_Consumido'] / sulco_df['Sulco_Inicial'] * 100

            # Exemplo de indicadores
            total_pneus = len(pneus_df)
            media_sulco = sulco_df['Sulco_Atual'].mean()
            st.metric("Total de Pneus", total_pneus)
            st.metric("Média de Sulco Atual", f"{media_sulco:.2f} mm")

            # Tabela completa
            st.subheader("Detalhes de Sulco")
            st.dataframe(sulco_df)

            # Ajuste de métricas de estoque, sucata e caminhão
            # Supondo que essas colunas existam em pneus_df
            estoque_total = pneus_df['Estoque'].sum()
            sucata_total = pneus_df['Sucata'].sum()
            caminhao_total = pneus_df['Caminhao'].sum()

            st.metric("Estoque Total", estoque_total)
            st.metric("Sucata Total", sucata_total)
            st.metric("Caminhão Total", caminhao_total)

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
