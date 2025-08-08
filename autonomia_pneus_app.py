import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Indicadores Manutenção e Pneus", layout="wide")
st.title("📊 Indicadores de Manutenção e Pneus")

def achar_coluna_km(df):
    colunas_km_possiveis = [
        'KM DO VEÍCULO', 'KM VEÍCULO', 'KM VEICULO', 'KM', 'KM ATUAL',
        'HODÔMETRO', 'HODOMETRO', 'KM_RODADOS'
    ]
    for col in colunas_km_possiveis:
        if col in df.columns:
            return col
    return None

uploaded_file = st.file_uploader("Faça upload da planilha Excel (.xlsx) com abas 'manutencao' e 'pneu'", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    if 'manutencao' in xls.sheet_names and 'pneu' in xls.sheet_names:
        df_manut = pd.read_excel(xls, sheet_name='manutencao')
        df_pneu = pd.read_excel(xls, sheet_name='pneu')

        df_manut.columns = df_manut.columns.str.strip().str.upper()
        df_pneu.columns = df_pneu.columns.str.strip().str.upper()

        for df in [df_manut, df_pneu]:
            if 'VEÍCULO - PLACA' in df.columns:
                df.rename(columns={'VEÍCULO - PLACA': 'PLACA'}, inplace=True)

        # Identifica coluna KM na manutenção
        col_km = achar_coluna_km(df_manut)
        if col_km is None:
            st.error("❌ Não foi encontrada uma coluna válida de KM na aba 'manutencao'.")
            st.write("Colunas encontradas:", df_manut.columns.tolist())
            st.stop()
        else:
            df_manut['KM_DO_VEICULO'] = pd.to_numeric(df_manut[col_km], errors='coerce')

        # Datas
        df_manut['DATA DA MANUTENÇÃO'] = pd.to_datetime(df_manut.get('DATA DA MANUTENÇÃO'), errors='coerce')
        df_pneu['DATA DA MOVIMENTAÇÃO'] = pd.to_datetime(df_pneu.get('DATA DA MOVIMENTAÇÃO'), errors='coerce')

        # ----------- Indicador 1: Frequência e intervalo entre manutenções -----------
        manut_freq = df_manut.groupby('PLACA').agg(
            total_manut=('PLACA', 'count'),
            km_medio_entre_manut=(
                'KM_DO_VEICULO', lambda x: x.sort_values().diff().mean()
            ),
            dias_medio_entre_manut=(
                'DATA DA MANUTENÇÃO', lambda x: x.sort_values().diff().dt.days.mean()
            )
        ).reset_index()

        # ----------- Indicador 2: Tipos de manutenção mais comuns -----------
        manut_tipo = df_manut['DESCRIÇÃO DA MANUTENÇÃO'].value_counts().reset_index()
        manut_tipo.columns = ['Tipo de Manutenção', 'Quantidade']

        # ----------- Indicador 4: Análise da movimentação dos pneus -----------
        pneu_analise = df_pneu.groupby('PLACA').agg(
            total_pneus_trocados=('PLACA', 'count'),
        ).reset_index()

        # ----------- Indicador 5: Pneus com baixa autonomia -----------
        if 'AUTONOMIA' in df_pneu.columns:
            autonomia_media = df_pneu['AUTONOMIA'].mean()
            pneus_baixa_autonomia = df_pneu[df_pneu['AUTONOMIA'] < autonomia_media]
        else:
            pneus_baixa_autonomia = pd.DataFrame()

        abas = st.tabs([
            "Frequência e Intervalo de Manutenção",
            "Tipos de Manutenção",
            "Movimentação de Pneus",
            "Pneus com Baixa Autonomia"
        ])

        with abas[0]:
            st.subheader("Frequência e Intervalo entre Manutenções por Veículo")
            st.dataframe(manut_freq)
            fig = px.histogram(manut_freq, x='km_medio_entre_manut',
                               nbins=30, title="Distribuição do Intervalo Médio de KM entre Manutenções")
            st.plotly_chart(fig, use_container_width=True)

        with abas[1]:
            st.subheader("Tipos de Manutenção mais Comuns")
            st.dataframe(manut_tipo)
            fig = px.bar(manut_tipo.head(20), x='Quantidade', y='Tipo de Manutenção',
                         orientation='h', title='Top 20 Tipos de Manutenção')
            st.plotly_chart(fig, use_container_width=True)

        with abas[2]:
            st.subheader("Total de Pneus Trocados por Veículo")
            st.dataframe(pneu_analise)
            fig = px.bar(pneu_analise, x='PLACA', y='total_pneus_trocados',
                         title='Pneus Trocados por Veículo')
            st.plotly_chart(fig, use_container_width=True)

        with abas[3]:
            st.subheader("Pneus com Autonomia Abaixo da Média")
            if not pneus_baixa_autonomia.empty:
                st.dataframe(pneus_baixa_autonomia)
                fig = px.histogram(pneus_baixa_autonomia, x='AUTONOMIA',
                                   nbins=20, title='Distribuição de Autonomia Baixa')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Coluna 'AUTONOMIA' não encontrada na planilha de pneus.")

    else:
        st.error("A planilha deve conter abas chamadas 'manutencao' e 'pneu'.")
else:
    st.info("Faça upload da planilha para iniciar a análise.")
